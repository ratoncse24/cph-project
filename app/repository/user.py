from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from typing import Optional

from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserListResponse
from app.utils.pagination import PaginationParams, PaginationHandler
import datetime
import logging

logger = logging.getLogger(__name__)


async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str):
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_email_or_username(db: AsyncSession, identifier: str):
    """Get user by email or username"""
    result = await db.execute(
        select(User).where(
            or_(User.email == identifier, User.username == identifier)
        )
    )
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_data: UserCreate):
    # Convert password to password_hash for the model
    user_dict = user_data.model_dump()
    if 'password' in user_dict:
        user_dict['password_hash'] = user_dict.pop('password')
    
    user = User(**user_dict)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_all_users(db: AsyncSession):
    result = await db.execute(select(User))
    return result.scalars().all()


async def get_users_paginated(
    db: AsyncSession, 
    pagination: PaginationParams,
    query_params: Optional[dict] = None
) -> UserListResponse:
    """
    Get paginated list of users with optional filters
    
    Repository builds the query with business logic from query_params, 
    then delegates pagination to PaginationHandler
    
    Args:
        db: Database session
        pagination: Pure pagination parameters (page, size)
        query_params: Dict of query parameters for filtering (search, role, status, etc.)
        
    Returns:
        UserListResponse with paginated users and metadata
    """
    # Build the base query - this is the repository's responsibility
    query = select(User).where(User.deleted_at.is_(None))  # Exclude soft-deleted users
    
    # Apply business logic filters from query_params - repository handles the "what" and "how" to filter
    if query_params:
        # Handle search parameter
        if query_params.get('search'):
            search_term = f"%{query_params['search']}%"
            # Build search conditions
            search_conditions = [
                User.username.ilike(search_term),
                User.email.ilike(search_term),
                User.role_name.ilike(search_term)
            ]
            # Only add phone search if phone is not null
            search_conditions.append(User.phone.ilike(search_term))
            
            query = query.where(or_(*search_conditions))
        
        # Handle role filter
        if query_params.get('role'):
            query = query.where(User.role_name == query_params['role'])
        
        # Handle status filter
        if query_params.get('status'):
            query = query.where(User.status == query_params['status'])
    
    # Delegate pagination to the utility - it handles the "pagination mechanics"
    return await PaginationHandler.paginate_query(
        db=db,
        query=query,
        pagination=pagination,
        response_schema=UserRead
    )


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """
    Get user by ID
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        User object or None if not found
    """
    try:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error fetching user by ID {user_id}: {e}")
        return None


async def update_user(db: AsyncSession, user_id: int, user_data: dict) -> Optional[User]:
    """
    Update user information
    
    Args:
        db: Database session
        user_id: User ID to update
        user_data: Dictionary with fields to update
        
    Returns:
        Updated User object or None if not found
    """
    try:
        # Get existing user
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"User not found for update: {user_id}")
            return None
        
        # Update fields
        for field, value in user_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        # Update timestamp
        user.updated_at = datetime.datetime.utcnow()
        
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"User updated successfully: {user.username} (ID: {user_id})")
        return user
        
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        await db.rollback()
        return None


async def soft_delete_user(db: AsyncSession, user_id: int) -> bool:
    """
    Soft delete user by setting deleted_at timestamp
    
    Args:
        db: Database session
        user_id: User ID to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"User not found for deletion: {user_id}")
            return False
        
        # Soft delete
        user.deleted_at = datetime.datetime.utcnow()
        user.status = "deleted"
        
        await db.commit()
        
        logger.info(f"User soft deleted successfully: {user.username} (ID: {user_id})")
        return True
        
    except Exception as e:
        logger.error(f"Error soft deleting user {user_id}: {e}")
        await db.rollback()
        return False
