from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.role_options import RoleOptionsCreate, RoleOptionsUpdate, RoleOptionsRead, RoleOptionsListResponse
from app.repository import role_options as role_options_repository
from app.core.logger import logger


async def create_role_option_service(db: AsyncSession, role_option_data: RoleOptionsCreate) -> RoleOptionsRead:
    """
    Create a new role option with business logic validation
    
    Args:
        db: Database session
        role_option_data: Role option creation data
        
    Returns:
        Created role option data
    """
    # Create role option in database
    new_role_option = await role_options_repository.create_role_option(db, role_option_data)
    
    logger.info(f"Role option created successfully: {new_role_option.name} (ID: {new_role_option.id})")
    return RoleOptionsRead.model_validate(new_role_option)


async def get_role_options_list_service(
    db: AsyncSession, 
    status: Optional[str] = None, 
    option_type: Optional[str] = None
) -> RoleOptionsListResponse:
    """
    Get list of role options with optional status and option_type filtering
    
    Args:
        db: Database session
        status: Optional status filter
        option_type: Optional option_type filter
        
    Returns:
        List of role options with total count
    """
    # Get role options from repository
    role_options = await role_options_repository.get_all_role_options(db, status, option_type)
    
    # Convert to response schema
    role_options_list = [RoleOptionsRead.model_validate(role_option) for role_option in role_options]
    
    filter_info = []
    if status:
        filter_info.append(f"status '{status}'")
    if option_type:
        filter_info.append(f"option_type '{option_type}'")
    
    filter_text = f" with {' and '.join(filter_info)}" if filter_info else ""
    
    logger.info(f"Retrieved {len(role_options_list)} role options{filter_text}")
    
    return RoleOptionsListResponse(
        role_options=role_options_list,
        total=len(role_options_list)
    )


async def update_role_option_service(db: AsyncSession, role_option_id: int, role_option_data: RoleOptionsUpdate) -> Optional[RoleOptionsRead]:
    """
    Update role option information with business logic validation
    
    Args:
        db: Database session
        role_option_id: Role option ID to update
        role_option_data: Role option update data
        
    Returns:
        Updated role option data or None if not found
    """
    # Check if role option exists
    existing_role_option = await role_options_repository.get_role_option_by_id(db, role_option_id)
    if not existing_role_option:
        logger.warning(f"Role option not found for update: {role_option_id}")
        return None
    
    # Prepare update data (only non-None values)
    update_data = {}
    for field, value in role_option_data.model_dump().items():
        if value is not None:
            update_data[field] = value
    
    # Update role option in database
    updated_role_option = await role_options_repository.update_role_option(db, role_option_id, update_data)
    
    if updated_role_option:
        logger.info(f"Role option updated successfully: {updated_role_option.name} (ID: {role_option_id})")
        return RoleOptionsRead.model_validate(updated_role_option)
    
    return None


async def get_role_option_by_id_service(db: AsyncSession, role_option_id: int) -> Optional[RoleOptionsRead]:
    """
    Get role option by ID
    
    Args:
        db: Database session
        role_option_id: Role option ID
        
    Returns:
        Role option data or None if not found
    """
    role_option = await role_options_repository.get_role_option_by_id(db, role_option_id)
    
    if role_option:
        return RoleOptionsRead.model_validate(role_option)
    
    return None 