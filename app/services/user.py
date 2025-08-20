from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import UserCreate, UserEventData, UserUpdatedEventData
from app.repository import user as user_crud
from app.core.logger import logger
from app.db.session import get_db
from app.models.user import User


async def register_user(db: AsyncSession, user_data: UserCreate):
    existing_user = await user_crud.get_user_by_email(db, user_data.email)
    if existing_user:
        raise ValueError("Email already registered")
    
    # Create user in database
    new_user = await user_crud.create_user(db, user_data)
    
    return new_user


async def create_user(data: UserCreate):
    return True

async def update_user(data: UserCreate):
    return False


def map_event_data_to_user_fields(event_data: UserEventData) -> Dict[str, Any]:
    """
    Map validated event data to user model fields, filtering out fields not in our model
    
    Args:
        event_data: Validated event data schema
        
    Returns:
        Dict with fields that match our User model
    """
    # Fields that exist in our User model
    allowed_fields = {
        'name', 'username', 'email', 'phone', 'role_name', 'profile_picture_url',
        'temporary_profile_picture_url', 'temporary_profile_picture_expires_at',
        'status', 'token_version', 'created_at', 'updated_at'
    }
    
    # Convert to dict and filter
    event_dict = event_data.model_dump()
    user_data = {}
    
    for key, value in event_dict.items():
        if key in allowed_fields and value is not None:
            # Handle datetime strings
            if key in ['created_at', 'updated_at', 'temporary_profile_picture_expires_at']:
                if isinstance(value, str):
                    try:
                        user_data[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        logger.warning(f"Invalid datetime format for {key}: {value}")
                else:
                    user_data[key] = value
            else:
                user_data[key] = value
    
    return user_data


async def create_user_from_event_data(event_data: UserEventData) -> Optional[User]:
    """
    Create a new user from validated event data
    
    Args:
        event_data: Validated event data schema
        
    Returns:
        Created User object or None if creation failed
    """
    try:
        user_data = map_event_data_to_user_fields(event_data)
        
        # Convert user_id to integer
        try:
            user_data['id'] = int(event_data.user_id)
        except (ValueError, TypeError):
            logger.warning(f"Invalid integer format for user_id: {event_data.user_id}")
            return None
        
        async for db in get_db():
            try:
                # Check if user already exists by ID or username
                existing_user = None
                existing_user = await user_crud.get_user_by_id(db, user_data['id'])
                
                if not existing_user:
                    existing_user = await user_crud.get_user_by_username(db, event_data.username)
                
                if existing_user:
                    logger.info(f"User already exists with ID/username, skipping creation: {event_data.username}")
                    return existing_user
                
                # Create new user directly in the database
                user = User(**user_data)
                db.add(user)
                await db.commit()
                await db.refresh(user)
                
                logger.info(f"Created user from event: {user.username} (ID: {user.id})")
                return user
                
            except Exception as db_error:
                await db.rollback()
                logger.error(f"Database error creating user: {db_error}")
                raise
            finally:
                await db.close()
                
    except Exception as e:
        logger.error(f"Error creating user from event data: {e}")
        return None


async def update_user_from_event_data(event_data: UserUpdatedEventData) -> Optional[User]:
    """
    Update an existing user from validated event data
    
    Args:
        event_data: Validated event data schema
        
    Returns:
        Updated User object or None if update failed
    """
    try:
        user_data = map_event_data_to_user_fields(event_data)
        
        # Get user ID from event data
        try:
            user_id = int(event_data.user_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid integer format for user_id: {event_data.user_id}")
            return None
        
        async for db in get_db():
            try:
                # Get existing user
                existing_user = await user_crud.get_user_by_id(db, user_id)
                if not existing_user:
                    logger.warning(f"User not found for update: {user_id}")
                    # Create user if it doesn't exist (event might arrive out of order)
                    # Convert to UserEventData for creation
                    create_data = UserEventData(**event_data.model_dump())
                    return await create_user_from_event_data(create_data)
                
                # Update user fields
                updated_fields = []
                for key, value in user_data.items():
                    if hasattr(existing_user, key):
                        old_value = getattr(existing_user, key)
                        if old_value != value:
                            setattr(existing_user, key, value)
                            updated_fields.append(key)
                
                if updated_fields:
                    # Set updated_at timestamp
                    existing_user.updated_at = datetime.utcnow()
                    
                    await db.commit()
                    await db.refresh(existing_user)
                    
                    logger.info(f"Updated user {existing_user.username} (ID: {user_id}), fields: {updated_fields}")
                else:
                    logger.info(f"No changes detected for user {existing_user.username} (ID: {user_id})")
                
                return existing_user
                
            except Exception as db_error:
                await db.rollback()
                logger.error(f"Database error updating user: {db_error}")
                raise
            finally:
                await db.close()
                
    except Exception as e:
        logger.error(f"Error updating user from event data: {e}")
        return None


# Event-specific service methods for external events
async def process_external_user_created(event_data: dict, source_service: str) -> bool:
    """Process user created event from external microservice"""
    try:
        logger.info(f"📝 Processing external user creation from {source_service}")
        logger.info(f"   User ID: {event_data.get('user_id')}")
        logger.info(f"   Username: {event_data.get('username')}")
        logger.info(f"   Email: {event_data.get('email')}")
        
        # Validate event data using Pydantic schema
        try:
            validated_data = UserEventData(**event_data)
        except Exception as validation_error:
            logger.error(f"Invalid event data format: {validation_error}")
            return False
        
        # Create user from validated event data
        user = await create_user_from_event_data(validated_data)
        
        if user:
            logger.info(f"✅ Successfully created user: {user.username} (ID: {user.id})")
            return True
        else:
            logger.error("❌ Failed to create user from event data")
            return False
        
    except Exception as e:
        logger.error(f"Error processing external user created: {e}")
        return False


async def process_external_user_updated(event_data: dict, source_service: str) -> bool:
    """Process user updated event from external microservice"""
    try:
        logger.info(f"📝 Processing external user update from {source_service}")
        logger.info(f"   User ID: {event_data.get('user_id')}")
        logger.info(f"   Updated fields: {event_data.get('updated_fields', [])}")
        
        # Validate event data using Pydantic schema
        try:
            validated_data = UserUpdatedEventData(**event_data)
        except Exception as validation_error:
            logger.error(f"Invalid event data format: {validation_error}")
            return False
        
        # Update user from validated event data
        user = await update_user_from_event_data(validated_data)
        
        if user:
            logger.info(f"✅ Successfully updated user: {user.username} (ID: {user.id})")
            return True
        else:
            logger.error("❌ Failed to update user from event data")
            return False
        
    except Exception as e:
        logger.error(f"Error processing external user updated: {e}")
        return False
