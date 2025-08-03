from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List
import datetime
import logging

from app.models.role_options import RoleOptions
from app.schemas.role_options import RoleOptionsCreate, RoleOptionsUpdate, RoleOptionsRead

logger = logging.getLogger(__name__)


async def create_role_option(db: AsyncSession, role_option_data: RoleOptionsCreate) -> RoleOptions:
    """Create a new role option"""
    try:
        role_option_dict = role_option_data.model_dump()
        role_option = RoleOptions(**role_option_dict)
        db.add(role_option)
        await db.commit()
        await db.refresh(role_option)
        return role_option
    except Exception as e:
        logger.error(f"Error creating role option: {e}")
        await db.rollback()
        raise


async def get_all_role_options(
    db: AsyncSession, 
    status: Optional[str] = None, 
    option_type: Optional[str] = None
) -> List[RoleOptions]:
    """Get all role options with optional status and option_type filtering"""
    query = select(RoleOptions).where(RoleOptions.deleted_at.is_(None))
    
    if status:
        query = query.where(RoleOptions.status == status)
    
    if option_type:
        query = query.where(RoleOptions.option_type == option_type)
    
    # Order by ID descending (newest first)
    query = query.order_by(RoleOptions.id.desc())
    
    result = await db.execute(query)
    return result.scalars().all()


async def get_role_option_by_id(db: AsyncSession, role_option_id: int) -> Optional[RoleOptions]:
    """Get role option by ID"""
    try:
        result = await db.execute(
            select(RoleOptions).where(RoleOptions.id == role_option_id)
        )
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error fetching role option by ID {role_option_id}: {e}")
        return None


async def update_role_option(db: AsyncSession, role_option_id: int, role_option_data: dict) -> Optional[RoleOptions]:
    """Update role option information"""
    try:
        # Get existing role option
        result = await db.execute(
            select(RoleOptions).where(RoleOptions.id == role_option_id)
        )
        role_option = result.scalar_one_or_none()
        
        if not role_option:
            logger.warning(f"Role option not found for update: {role_option_id}")
            return None
        
        # Update fields
        for field, value in role_option_data.items():
            if hasattr(role_option, field) and value is not None:
                setattr(role_option, field, value)
        
        # Update timestamp
        role_option.updated_at = datetime.datetime.utcnow()
        
        await db.commit()
        await db.refresh(role_option)
        
        logger.info(f"Role option updated successfully: {role_option.name} (ID: {role_option_id})")
        return role_option
        
    except Exception as e:
        logger.error(f"Error updating role option {role_option_id}: {e}")
        await db.rollback()
        return None


async def soft_delete_role_option(db: AsyncSession, role_option_id: int) -> bool:
    """Soft delete role option by setting deleted_at timestamp"""
    try:
        result = await db.execute(
            select(RoleOptions).where(RoleOptions.id == role_option_id)
        )
        role_option = result.scalar_one_or_none()
        
        if not role_option:
            logger.warning(f"Role option not found for deletion: {role_option_id}")
            return False
        
        # Soft delete
        role_option.deleted_at = datetime.datetime.utcnow()
        role_option.status = "deleted"
        
        await db.commit()
        
        logger.info(f"Role option soft deleted successfully: {role_option.name} (ID: {role_option_id})")
        return True
        
    except Exception as e:
        logger.error(f"Error soft deleting role option {role_option_id}: {e}")
        await db.rollback()
        return False 