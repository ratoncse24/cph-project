
from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.model import (
    ModelCreateWithRelations, ModelUpdate, ModelUpdateWithRelations,
    ModelCreatedEventData, ModelUpdatedEventData
)
from app.repository import model as model_crud
from app.repository import user as user_crud
from app.core.logger import logger
from app.models.model import Model
from app.events.models import PublishEventRequest, EventType, ServiceTarget
from app.events.sns_publisher import sns_publisher



async def _publish_model_event(
    event_type: EventType,
    model: Model,
    request_data: Optional[dict] = None,
    updated_fields: Optional[List[str]] = None
) -> bool:
    """
    Publish model event to USER_SERVICE and SELECTION_SERVICE
    
    Args:
        event_type: Type of event (MODEL_CREATED or MODEL_UPDATED)
        model: Model instance
        request_data: Original request data containing information and clothing_sizes
        updated_fields: List of updated fields (for update events only)
        
    Returns:
        True if event was published successfully, False otherwise
    """
    try:
        # Check if SNS publisher is configured
        if not sns_publisher.is_configured():
            logger.warning("SNS publisher not configured. Skipping model event publishing.")
            return False
        
        # Convert model to dict to avoid SQLAlchemy session issues
        model_dict = model_to_dict(model)
        
        # Prepare information and clothing_sizes from request data if available
        information_data = None
        clothing_sizes_data = None
        
        if request_data:
            # Extract information from request data
            if 'information' in request_data and request_data['information']:
                information_data = request_data['information']
                if hasattr(information_data, 'model_dump'):
                    information_data = information_data.model_dump()
            
            # Extract clothing_sizes from request data
            if 'clothing_sizes' in request_data and request_data['clothing_sizes']:
                clothing_sizes_data = request_data['clothing_sizes']
                if hasattr(clothing_sizes_data, 'model_dump'):
                    clothing_sizes_data = clothing_sizes_data.model_dump()
        
        # Create event data manually to avoid lazy loading issues
        if event_type == EventType.MODEL_CREATED:
            event_data_dict = {
                "event_type": "model_created",
                "id": model_dict['id'],
                "user_id": model_dict['user_id'],
                "first_name": model_dict['first_name'],
                "last_name": model_dict['last_name'],
                "phone": model_dict['phone'],
                "email": model_dict['email'],
                "last_login": model_dict['last_login'].isoformat() if model_dict['last_login'] else None,
                "is_approved": model_dict['is_approved'],
                "status": model_dict['status'],
                "visibility_status": model_dict['visibility_status'],
                "is_online": model_dict['is_online'],
                "is_featured": model_dict['is_featured'],
                "created_at": model_dict['created_at'].isoformat() if model_dict['created_at'] else None,
                "updated_at": model_dict['updated_at'].isoformat() if model_dict['updated_at'] else None,
                "information": information_data,  # Use request data instead of None
                "clothing_sizes": clothing_sizes_data  # Use request data instead of None
            }
        elif event_type == EventType.MODEL_UPDATED:
            event_data_dict = {
                "event_type": "model_updated",
                "id": model_dict['id'],
                "user_id": model_dict['user_id'],
                "first_name": model_dict['first_name'],
                "last_name": model_dict['last_name'],
                "phone": model_dict['phone'],
                "email": model_dict['email'],
                "last_login": model_dict['last_login'].isoformat() if model_dict['last_login'] else None,
                "is_approved": model_dict['is_approved'],
                "status": model_dict['status'],
                "visibility_status": model_dict['visibility_status'],
                "is_online": model_dict['is_online'],
                "is_featured": model_dict['is_featured'],
                "created_at": model_dict['created_at'].isoformat() if model_dict['created_at'] else None,
                "updated_at": model_dict['updated_at'].isoformat() if model_dict['updated_at'] else None,
                "information": information_data,  # Use request data instead of None
                "clothing_sizes": clothing_sizes_data,  # Use request data instead of None
                "updated_fields": updated_fields or []
            }
        else:
            logger.error(f"Unsupported event type: {event_type}")
            return False
            
        print(event_data_dict)
        # Create publish request targeting USER_SERVICE and SELECTION_SERVICE
        publish_request = PublishEventRequest(
            event_type=event_type,
            target_services=[ServiceTarget.USER_SERVICE, ServiceTarget.SELECTION_SERVICE],
            data=event_data_dict,
            source_service="model_management"
        )
        
        # Publish the event
        message_id = await sns_publisher.publish_event(publish_request)
        
        if message_id:
            logger.info(f"✅ Published {event_type} event for model {model.email} (ID: {model.id})")
            logger.info(f"   Event targets: USER_SERVICE, SELECTION_SERVICE")
            if information_data or clothing_sizes_data:
                logger.info(f"   Included related data: information={bool(information_data)}, clothing_sizes={bool(clothing_sizes_data)}")
            return True
        else:
            logger.error(f"❌ Failed to publish {event_type} event for model {model.id}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error publishing {event_type} event for model {model.id}: {e}")
        return False


def model_to_dict(model) -> dict:
    """Convert SQLAlchemy model to dict to avoid async session issues with Pydantic"""
    return {
        'id': model.id,
        'user_id': model.user_id,
        'first_name': model.first_name,
        'last_name': model.last_name,
        'phone': model.phone,
        'email': model.email,
        'last_login': model.last_login,
        'is_approved': model.is_approved,
        'status': model.status,
        'visibility_status': model.visibility_status,
        'is_online': model.is_online,
        'is_featured': model.is_featured,
        'created_at': model.created_at,
        'updated_at': model.updated_at,
        'deleted_at': model.deleted_at,
        'information': None,  # Will be loaded separately if needed
        'clothing_sizes': None,  # Will be loaded separately if needed
        'media': []  # Will be loaded separately if needed
    }

async def register_model(
    db: AsyncSession,
    model_data: ModelCreateWithRelations,
    created_by_admin: bool = False,
    admin_user_id: Optional[int] = None
) -> Model:
    """
    Register a new model with all related information
    
    Args:
        db: Database session
        model_data: Complete model data including optional information, clothing sizes, and media
        created_by_admin: Whether this registration is done by an admin
        admin_user_id: ID of the admin user (if created by admin)
        
    Returns:
        Created Model object with all relationships
        
    Raises:
        ValueError: If email already exists or validation fails
    """
    try:
        logger.info(f"Starting model registration for email: {model_data.email}")
        
        # Check if model with this email already exists
        existing_model = await model_crud.get_model_by_email(db, model_data.email)
        if existing_model:
            logger.warning(f"Model registration failed - email already exists: {model_data.email}")
            raise ValueError("Email already registered")
        
        # Check if email is available as username in user table
        existing_user = await user_crud.get_user_by_email_or_username(db, model_data.email)
        if existing_user:
            logger.warning(f"Model registration failed - email/username already exists in user table: {model_data.email}")
            raise ValueError("Email already exists as username in user accounts")
        
        # Apply business rules based on registration type
        if not created_by_admin:
            # Public registration - enforce security defaults
            model_data.is_approved = False
            model_data.status = 'pending'
            model_data.visibility_status = 'visible'
            model_data.is_featured = False
            model_data.is_online = False
            logger.info(f"Applied public registration defaults for: {model_data.email}")
        else:
            # Admin registration - can set any values
            logger.info(f"Admin {admin_user_id} registering model: {model_data.email}")
        
        # Important: Set user_id to null initially - will be linked when USER_SERVICE creates the user
        model_data.user_id = None
        
        # Create the model with all relationships
        new_model = await model_crud.create_model_with_relations(db, model_data)
        
        # Check if model creation was successful
        if new_model is None:
            logger.error(f"Model creation failed - create_model_with_relations returned None for email: {model_data.email}")
            raise Exception("Model creation failed - repository returned None")
        
        # Log successful creation
        log_message = f"✅ Model registered successfully: {new_model.email}"
        if created_by_admin:
            log_message += f" by admin {admin_user_id}"
        else:
            log_message += " via public registration"
        logger.info(log_message)
        
        # Publish model created event to other services
        # Pass the original request data to include information and clothing_sizes
        request_data = {
            'information': model_data.information,
            'clothing_sizes': model_data.clothing_sizes
        }
        await _publish_model_event(EventType.MODEL_CREATED, new_model, request_data)
        
        return new_model
        
    except ValueError:
        # Re-raise validation errors as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error during model registration for {model_data.email}: {e}")
        raise Exception("Model registration failed due to unexpected error")


async def get_model_by_id(db: AsyncSession, model_id: int) -> Optional[Model]:
    """
    Get model by ID with all relationships loaded and user status validation
    
    Args:
        db: Database session
        model_id: Model ID
        
    Returns:
        Model object with all relationships or None if not found/active
    """
    try:
        logger.info(f"Fetching model by ID: {model_id}")
        
        model = await model_crud.get_model_by_id(db, model_id)
        
        if not model:
            logger.info(f"Model not found: {model_id}")
            return None
        
        return model
        
    except Exception as e:
        logger.error(f"Error fetching model {model_id}: {e}")
        raise Exception("Failed to fetch model")


async def get_model_by_user_id(db: AsyncSession, user_id: int) -> Optional[Model]:
    """
    Get model by user ID with all relationships loaded and user status validation
    
    Args:
        db: Database session
        user_id: User ID linked to the model
        
    Returns:
        Model object with all relationships or None if not found/active
    """
    try:
        logger.info(f"Fetching model by user ID: {user_id}")
        
        # Get the model
        model = await model_crud.get_model_by_user_id(db, user_id)
        
        if model:
            logger.info(f"Model found: {model.email} (User ID: {user_id})")
        else:
            logger.warning(f"Model not found for user ID: {user_id}")
        
        return model
        
    except Exception as e:
        logger.error(f"Error fetching model by user ID {user_id}: {e}")
        raise Exception("Failed to fetch model")


async def update_model(
    db: AsyncSession,
    model_id: int,
    model_data: ModelUpdateWithRelations,
    updated_by_admin: bool = False,
    admin_user_id: Optional[int] = None
) -> Optional[Model]:
    """
    Update model information with business logic validation
    
    Args:
        db: Database session
        model_id: Model ID to update
        model_data: Update data
        updated_by_admin: Whether this update is done by an admin
        admin_user_id: ID of the admin user (if updated by admin)
        
    Returns:
        Updated Model object or None if not found
        
    Raises:
        ValueError: If validation fails
        Exception: If update fails
    """
    try:
        logger.info(f"Starting model update for ID: {model_id}")
        
        core_model_dict = model_data.model_dump(exclude={'information', 'clothing_sizes', 'media'}, exclude_unset=True)

        # Check if model exists
        existing_model = await model_crud.get_model_by_id(db, model_id)
        if not existing_model:
            logger.warning(f"Model update failed - model not found: {model_id}")
            return None
        
        # If email is being updated, check for conflicts
        if model_data.email and model_data.email != existing_model.email:
            email_conflict = await model_crud.get_model_by_email(db, model_data.email)
            if email_conflict and email_conflict.id != model_id:
                logger.warning(f"Model update failed - email already exists: {model_data.email}")
                raise ValueError("Email already registered to another model")
        
        # Apply business rules based on who is updating
        if not updated_by_admin:
            # Non-admin (model self-updates) - restrict certain fields
            restricted_fields = ['is_approved', 'is_featured', 'status', 'visibility_status', 'user_id']
            for field in restricted_fields:
                if hasattr(model_data, field) and getattr(model_data, field) is not None:
                    logger.warning(f"Model attempted to update restricted field '{field}' for model {model_id}")
                    core_model_dict.pop(field)
            
            logger.info(f"Model self-update for model: {model_id}")
        else:
            logger.info(f"Admin {admin_user_id} updating model: {model_id}")
        
        # Track which fields are being updated for event publishing
        updated_fields = []
        
        # Track core model field changes
        for field_name, new_value in core_model_dict.items():
            if hasattr(existing_model, field_name):
                current_value = getattr(existing_model, field_name)
                if current_value != new_value:
                    updated_fields.append(field_name)
        
        # Track related data changes
        if model_data.information is not None:
            updated_fields.append('information')
        if model_data.clothing_sizes is not None:
            updated_fields.append('clothing_sizes')
        if model_data.media is not None:
            updated_fields.append('media')
        
        try:
            # Perform the core model update
            core_model_data = ModelUpdate(**core_model_dict)
            updated_model = await model_crud.update_model(db, model_id, core_model_data)
            
            if not updated_model:
                return None
            
            # Update related information if provided
            if model_data.information is not None:
                await model_crud.create_model_information(
                    db=db,
                    model_id=model_id,
                    info_data=model_data.information
                )
            
            # Update clothing sizes if provided
            if model_data.clothing_sizes is not None:
                await model_crud.create_model_clothing_sizes(
                    db=db,
                    model_id=model_id,
                    clothing_data=model_data.clothing_sizes
                )
            
            # Add new media if provided
            if model_data.media is not None:
                for media_item in model_data.media:
                    await model_crud.add_model_media(
                        db=db,
                        model_id=model_id,
                        media_data=media_item
                    )
            
            # Fetch the updated model with all relationships
            final_model = await model_crud.get_model_by_id(db, model_id)
            
            if final_model:
                log_message = f"✅ Model updated successfully: {final_model.email} (ID: {model_id})"
                if updated_by_admin:
                    log_message += f" by admin {admin_user_id}"
                logger.info(log_message)
                
                # Create activity logs for specific field updates
                performed_by_user_id = admin_user_id if updated_by_admin else final_model.user_id
                
                # Import the activity log service
                from app.services import model_activity_log as activity_log_service
                
                # Create activity log for information updates
                if 'information' in updated_fields:
                    await activity_log_service.create_activity_log(
                        db=db,
                        model_id=model_id,
                        title="Model Information Updated",
                        description="Model information has been updated",
                        action_type="information_update",
                        performed_by=performed_by_user_id,
                    )
                
                # Create activity log for clothing size updates
                if 'clothing_sizes' in updated_fields:
                    await activity_log_service.create_activity_log(
                        db=db,
                        model_id=model_id,
                        title="Clothing Sizes Updated",
                        description="Model clothing sizes have been updated",
                        action_type="clothing_sizes_update",
                        performed_by=performed_by_user_id,
                    )

                # Publish model updated event to other services (only if there were actual changes)
                if updated_fields:
                    # Pass the original request data to include information and clothing_sizes
                    request_data = {
                        'information': model_data.information,
                        'clothing_sizes': model_data.clothing_sizes
                    }
                    await _publish_model_event(EventType.MODEL_UPDATED, final_model, request_data, updated_fields)
            
            return final_model
            
        except Exception as update_error:
            logger.error(f"Error during model update for {model_id}: {update_error}")
            raise Exception("Model update failed due to database error")
        
    except ValueError:
        # Re-raise validation errors as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error during model update for {model_id}: {e}")
        raise Exception("Model update failed due to unexpected error")


async def approve_model(
    db: AsyncSession,
    model_id: int,
    admin_user_id: int,
    approved: bool = True
) -> Optional[Model]:
    """
    Approve or reject a model (admin only operation)
    
    Args:
        db: Database session
        model_id: Model ID to approve/reject
        admin_user_id: ID of the admin user performing the action
        approved: Whether to approve (True) or reject (False)
        
    Returns:
        Updated Model object or None if not found
    """
    try:
        action = "approve" if approved else "reject"
        logger.info(f"Admin {admin_user_id} attempting to {action} model: {model_id}")
        
        # Prepare update data
        update_data = ModelUpdate(
            is_approved=approved,
            status='active' if approved else 'inactive'
        )
        
        # Use the regular update method with admin privileges
        updated_model = await update_model(
            db=db,
            model_id=model_id,
            model_data=update_data,
            updated_by_admin=True,
            admin_user_id=admin_user_id
        )
        
        if updated_model:
            logger.info(f"✅ Model {action}ed successfully: {updated_model.email} (ID: {model_id})")
            
            # Publish model updated event for approval status change
            await _publish_model_event(
                EventType.MODEL_UPDATED, 
                updated_model, 
                None,  # No request data for approval changes
                ['is_approved', 'status']
            )
        
        return updated_model
        
    except Exception as e:
        logger.error(f"Error {action}ing model {model_id}: {e}")
        raise Exception(f"Model {action} failed")


async def toggle_model_featured_status(
    db: AsyncSession,
    model_id: int,
    admin_user_id: int,
    featured: bool
) -> Optional[Model]:
    """
    Toggle model featured status (admin only operation)
    
    Args:
        db: Database session
        model_id: Model ID
        admin_user_id: ID of the admin user performing the action
        featured: Whether to set as featured (True) or not (False)
        
    Returns:
        Updated Model object or None if not found
    """
    try:
        action = "feature" if featured else "unfeature"
        logger.info(f"Admin {admin_user_id} attempting to {action} model: {model_id}")
        
        # Prepare update data
        update_data = ModelUpdate(is_featured=featured)
        
        # Use the regular update method with admin privileges
        updated_model = await update_model(
            db=db,
            model_id=model_id,
            model_data=update_data,
            updated_by_admin=True,
            admin_user_id=admin_user_id
        )
        
        if updated_model:
            logger.info(f"✅ Model {action}ed successfully: {updated_model.email} (ID: {model_id})")
            
            # Publish model updated event for featured status change
            await _publish_model_event(
                EventType.MODEL_UPDATED, 
                updated_model, 
                None,  # No request data for featured status changes
                ['is_featured']
            )
        
        return updated_model
        
    except Exception as e:
        logger.error(f"Error {action}ing model {model_id}: {e}")
        raise Exception(f"Model {action} failed")


async def update_model_online_status(
    db: AsyncSession,
    model_id: int,
    is_online: bool,
    admin_user_id: Optional[int] = None
) -> Optional[Model]:
    """
    Update model online status
    
    Args:
        db: Database session
        model_id: Model ID
        is_online: Online status to set
        admin_user_id: Optional admin user ID if updated by admin
        
    Returns:
        Updated Model object or None if not found
    """
    try:
        status = "online" if is_online else "offline"
        logger.info(f"Setting model {model_id} to {status}")
        
        # Prepare update data
        update_data = ModelUpdate(is_online=is_online)
        
        # Use the regular update method
        updated_model = await update_model(
            db=db,
            model_id=model_id,
            model_data=update_data,
            updated_by_admin=admin_user_id is not None,
            admin_user_id=admin_user_id
        )
        
        if updated_model:
            logger.info(f"✅ Model status updated to {status}: {updated_model.email} (ID: {model_id})")
            
            # Publish model updated event for online status change
            await _publish_model_event(
                EventType.MODEL_UPDATED, 
                updated_model, 
                None,  # No request data for online status changes
                ['is_online']
            )
        
            return updated_model
        
    except Exception as e:
        logger.error(f"Error updating model online status for {model_id}: {e}")
        raise Exception("Model status update failed")


async def process_external_user_created(event_data: dict, source_service: str) -> bool:
    """
    Process user created event from USER_SERVICE and automatically link to model if role is 'model'
    
    When USER_SERVICE creates a user account, this method checks if the user has role='model'.
    If so, it finds the corresponding model by matching username/email and links them.
    
    Args:
        event_data: User created event data from USER_SERVICE
        source_service: Source service name
        
    Returns:
        True if processing was successful, False otherwise
    """
    try:
        logger.info(f"📝 Processing external user creation from {source_service}")
        logger.info(f"   User ID: {event_data.get('user_id')}")
        logger.info(f"   Username: {event_data.get('username')}")
        logger.info(f"   Email: {event_data.get('email')}")
        logger.info(f"   Role: {event_data.get('role_name')}")
        
        # Extract relevant data
        user_id = event_data.get('user_id')
        username = event_data.get('username')
        email = event_data.get('email')
        role_name = event_data.get('role_name')
        
        if not user_id or not username:
            logger.error("❌ Missing required user data (user_id or username)")
            return False
        
        # Only process if this is a model user
        if role_name != 'model':
            logger.info(f"ℹ️  User {username} has role '{role_name}', not 'model' - skipping model linking")
            return True
        
        logger.info(f"🔗 Detected model user creation - attempting to link user {user_id} to model")
        
        # Find model by email where user_id is null and link them
        success = await _auto_link_model_user(username, email, user_id)
        
        if success:
            logger.info(f"✅ Successfully auto-linked user {user_id} to model")
            return True
        else:
            logger.warning(f"⚠️  Could not find matching model for user {username} - this may be normal if model doesn't exist")
            return True  # Not an error - user might not have a model profile
                
    except Exception as e:
        logger.error(f"Error processing external user created event: {e}")
        return False


async def _auto_link_model_user(username: str, email: str, user_id: int) -> bool:
    """
    Automatically find and link a model user where user_id is null
    
    Searches for a model with matching email and null user_id, then links the new user.
    
    Args:
        username: Username from user account
        email: Email from user account  
        user_id: User ID to link to model
        
    Returns:
        True if model was found and linked, False otherwise
    """
    try:
        from app.db.session import get_db
        
        async for db in get_db():
            try:
                # Search for model by email (username should match email)
                search_email = email or username
                logger.info(f"Searching for model with email: {search_email}")
                
                model = await model_crud.get_model_by_email(db, search_email)
                if not model:
                    logger.info(f"No model found with email {search_email}")
                    return False
                
                # Check if model already has a user_id
                if model.user_id is not None:
                    logger.warning(f"Model {model.id} already has user_id {model.user_id}")
                    return False
                
                # Convert user_id to integer and update model
                user_int_id = int(user_id)
                update_data = ModelUpdate(user_id=user_int_id)
                updated_model = await model_crud.update_model(db, model.id, update_data)
                
                if updated_model:
                    logger.info(f"✅ Auto-linked user {user_id} to model {model.email} (ID: {model.id})")
                    
                    return True
                else:
                    logger.error(f"Failed to update model {model.id} with user_id {user_id}")
                    return False
                    
            except Exception as db_error:
                logger.error(f"Database error auto-linking model user: {db_error}")
                return False
            finally:
                await db.close()
                
    except ValueError as e:
        logger.error(f"Invalid integer format for user_id: {e}")
        return False
    except Exception as e:
        logger.error(f"Error auto-linking model user {username}: {e}")
        return False

