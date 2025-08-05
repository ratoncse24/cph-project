from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, and_
from typing import Optional
import datetime
import logging

from app.models.role import Role
from app.models.project import Project
from app.schemas.role import RoleCreate, RoleUpdate, RoleReadWithRelations, RoleListResponse
from app.utils.pagination import PaginationParams, PaginationHandler

logger = logging.getLogger(__name__)


async def create_role(db: AsyncSession, role_data: RoleCreate) -> Role:
    """Create a new role"""
    try:
        role = Role(**role_data.model_dump())
        db.add(role)
        await db.commit()
        await db.refresh(role)
        
        logger.info(f"Created role: {role.name} (ID: {role.id})")
        return role
        
    except Exception as e:
        logger.error(f"Error creating role: {e}")
        await db.rollback()
        raise


async def get_role_by_id(db: AsyncSession, role_id: int) -> Optional[Role]:
    """Get role by ID"""
    try:
        result = await db.execute(
            select(Role).where(Role.id == role_id)
        )
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error fetching role by ID {role_id}: {e}")
        return None


async def get_roles_paginated(
    db: AsyncSession, 
    pagination: PaginationParams,
    query_params: Optional[dict] = None
) -> RoleListResponse:
    """
    Get paginated list of roles with optional filters
    
    Args:
        db: Database session
        pagination: Pure pagination parameters (page, size)
        query_params: Dict of query parameters for filtering (search, project_id, etc.)
        
    Returns:
        RoleListResponse with paginated roles and metadata
    """
    # Build the base query with joins for related data
    query = select(
        Role,
        Project.name.label('project_name')
    ).join(
        Project, Role.project_id == Project.id
    )
    
    # Apply business logic filters from query_params
    if query_params:
        # Handle search parameter
        if query_params.get('search'):
            search_term = f"%{query_params['search']}%"
            search_conditions = [
                Role.name.ilike(search_term),
                Role.gender.ilike(search_term),
                Role.ethnicity.ilike(search_term),
                Role.language.ilike(search_term),
                Role.category.ilike(search_term),
                Role.hair_color.ilike(search_term),
                Project.name.ilike(search_term)
            ]
            query = query.where(or_(*search_conditions))
        
        # Handle project_id filter
        if query_params.get('project_id'):
            query = query.where(Role.project_id == query_params['project_id'])
        
        # Handle status filter
        if query_params.get('status'):
            query = query.where(Role.status == query_params['status'])
        
        # Handle gender filter
        if query_params.get('gender'):
            query = query.where(Role.gender == query_params['gender'])
        
        # Handle category filter
        if query_params.get('category'):
            query = query.where(Role.category == query_params['category'])
        
        # Handle age range filter
        if query_params.get('age_from'):
            query = query.where(Role.age_from >= query_params['age_from'])
        if query_params.get('age_to'):
            query = query.where(Role.age_to <= query_params['age_to'])
        
        # Handle height range filter
        if query_params.get('height_from'):
            query = query.where(Role.height_from >= query_params['height_from'])
        if query_params.get('height_to'):
            query = query.where(Role.height_to <= query_params['height_to'])
    
    # Delegate pagination to the utility
    return await PaginationHandler.paginate_query(
        db=db,
        query=query,
        pagination=pagination,
        response_schema=RoleReadWithRelations
    )


async def update_role(db: AsyncSession, role_id: int, role_data: RoleUpdate) -> Optional[Role]:
    """Update role"""
    try:
        # Get existing role
        result = await db.execute(
            select(Role).where(Role.id == role_id)
        )
        role = result.scalar_one_or_none()
        
        if not role:
            logger.warning(f"Role not found for update: {role_id}")
            return None
        
        # Update fields
        update_data = role_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(role, field):
                setattr(role, field, value)
        
        # Update timestamp
        role.updated_at = datetime.datetime.utcnow()
        
        await db.commit()
        await db.refresh(role)
        
        logger.info(f"Role updated successfully: {role.name} (ID: {role_id})")
        return role
        
    except Exception as e:
        logger.error(f"Error updating role {role_id}: {e}")
        await db.rollback()
        return None


async def delete_role(db: AsyncSession, role_id: int) -> bool:
    """Delete role"""
    try:
        result = await db.execute(
            select(Role).where(Role.id == role_id)
        )
        role = result.scalar_one_or_none()
        
        if not role:
            logger.warning(f"Role not found for deletion: {role_id}")
            return False
        
        await db.delete(role)
        await db.commit()
        
        logger.info(f"Role deleted successfully: {role.name} (ID: {role_id})")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting role {role_id}: {e}")
        await db.rollback()
        return False


async def get_roles_by_project_id(db: AsyncSession, project_id: int) -> list[Role]:
    """Get all roles for a specific project"""
    try:
        result = await db.execute(
            select(Role).where(Role.project_id == project_id)
        )
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error fetching roles for project {project_id}: {e}")
        return []


async def check_project_exists(db: AsyncSession, project_id: int) -> bool:
    """Check if project exists"""
    try:
        result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalar_one_or_none() is not None
    except Exception as e:
        logger.error(f"Error checking project existence {project_id}: {e}")
        return False 