from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, and_
from sqlalchemy.orm import selectinload
from typing import Optional, List
import datetime
import logging

from app.models.project import Project
from app.models.client import Client
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectRead
from app.utils.pagination import PaginationParams, PaginationHandler

logger = logging.getLogger(__name__)


async def create_project(db: AsyncSession, project_data: ProjectCreate) -> Project:
    """Create a new project"""
    # Remove password from project data as it's not stored in DB
    project_dict = project_data.model_dump(exclude={"password"})
    project = Project(**project_dict)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    # Load the client relationship using selectinload
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.client))
        .where(Project.id == project.id)
    )
    project_with_client = result.scalar_one()
    
    return project_with_client


async def get_projects_paginated(
    db: AsyncSession, 
    pagination: PaginationParams,
    query_params: Optional[dict] = None
):
    """
    Get paginated list of projects with optional filters
    
    Repository builds the query with business logic from query_params, 
    then delegates pagination to PaginationHandler
    
    Args:
        db: Database session
        pagination: Pure pagination parameters (page, size)
        query_params: Dict of query parameters for filtering (search, status, client_id, etc.)
        
    Returns:
        PaginatedResponse with paginated projects and metadata
    """
    # Build the base query with client relationship
    query = select(Project).options(selectinload(Project.client)).where(Project.deleted_at.is_(None))
    
    # Apply business logic filters from query_params
    if query_params:
        # Handle status filter
        if query_params.get('status'):
            query = query.where(Project.status == query_params['status'])
        
        # Handle client_id filter
        if query_params.get('client_id'):
            query = query.where(Project.client_id == query_params['client_id'])
        
        # Handle search parameter
        if query_params.get('search'):
            search_term = f"%{query_params['search']}%"
            # Build search conditions across project name and username
            # Note: Client name search would require a separate query or different approach
            search_conditions = [
                Project.name.ilike(search_term),
                Project.username.ilike(search_term)
            ]
            query = query.where(or_(*search_conditions))
    
    # Order by ID descending (newest first)
    query = query.order_by(Project.id.desc())
    
    # Delegate pagination to the utility - it handles the "pagination mechanics"
    return await PaginationHandler.paginate_query(
        db=db,
        query=query,
        pagination=pagination,
        response_schema=ProjectRead
    )


async def get_project_by_id(db: AsyncSession, project_id: int) -> Optional[Project]:
    """Get project by ID with client information"""
    try:
        from sqlalchemy.orm import selectinload
        
        result = await db.execute(
            select(Project)
            .options(selectinload(Project.client))
            .where(Project.id == project_id)
        )
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error fetching project by ID {project_id}: {e}")
        return None


async def get_project_by_username(db: AsyncSession, username: str) -> Optional[Project]:
    """Get project by username"""
    try:
        result = await db.execute(
            select(Project).where(Project.username == username)
        )
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error fetching project by username {username}: {e}")
        return None


async def update_project(db: AsyncSession, project_id: int, project_data: dict) -> Optional[Project]:
    """Update project information"""
    try:
        # Get existing project
        result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        
        if not project:
            logger.warning(f"Project not found for update: {project_id}")
            return None
        
        # Update fields
        for field, value in project_data.items():
            if hasattr(project, field) and value is not None:
                setattr(project, field, value)
        
        # Update timestamp
        project.updated_at = datetime.datetime.utcnow()
        
        await db.commit()
        await db.refresh(project)
        
        # Load the client relationship
        result = await db.execute(
            select(Project)
            .options(selectinload(Project.client))
            .where(Project.id == project_id)
        )
        project_with_client = result.scalar_one()
        
        logger.info(f"Project updated successfully: {project_with_client.name} (ID: {project_id})")
        return project_with_client
        
    except Exception as e:
        logger.error(f"Error updating project {project_id}: {e}")
        await db.rollback()
        return None


async def soft_delete_project(db: AsyncSession, project_id: int) -> bool:
    """Soft delete project by setting deleted_at timestamp"""
    try:
        result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        
        if not project:
            logger.warning(f"Project not found for deletion: {project_id}")
            return False
        
        # Soft delete
        project.deleted_at = datetime.datetime.utcnow()
        project.status = "archive"
        
        await db.commit()
        
        logger.info(f"Project soft deleted successfully: {project.name} (ID: {project_id})")
        return True
        
    except Exception as e:
        logger.error(f"Error soft deleting project {project_id}: {e}")
        await db.rollback()
        return False


async def check_client_exists(db: AsyncSession, client_id: int) -> bool:
    """Check if client exists"""
    try:
        result = await db.execute(
            select(Client).where(Client.id == client_id)
        )
        return result.scalar_one_or_none() is not None
    except Exception as e:
        logger.error(f"Error checking client existence {client_id}: {e}")
        return False 