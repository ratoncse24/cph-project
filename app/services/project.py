from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectRead
from app.repository import project as project_repository
from app.utils.pagination import PaginationParams
from app.events.sns_publisher import sns_publisher
from app.events.models import PublishEventRequest, EventType, ServiceTarget
from app.core.logger import logger


async def create_project_service(db: AsyncSession, project_data: ProjectCreate) -> ProjectRead:
    """
    Create a new project with business logic validation and event publishing
    
    Args:
        db: Database session
        project_data: Project creation data
        
    Returns:
        Created project data
        
    Raises:
        ValueError: If username already exists or client doesn't exist
    """
    # Check if project with same username already exists
    existing_project = await project_repository.get_project_by_username(db, project_data.username)
    if existing_project:
        raise ValueError(f"Project with username {project_data.username} already exists")
    
    # Check if client exists
    client_exists = await project_repository.check_client_exists(db, project_data.client_id)
    if not client_exists:
        raise ValueError(f"Client with ID {project_data.client_id} does not exist")
    
    # Create project in database
    new_project = await project_repository.create_project(db, project_data)
    
    # Publish project created event
    await _publish_project_event(
        event_type=EventType.MODEL_CREATED,
        project_id=new_project.id,
        project_name=new_project.name,
        username=new_project.username,
        password=project_data.password,  # Include password in event
        client_id=new_project.client_id
    )
    
    logger.info(f"Project created successfully: {new_project.name} (ID: {new_project.id})")
    return _convert_to_project_read(new_project)


async def get_projects_list_service(
    db: AsyncSession, 
    pagination: PaginationParams,
    status: Optional[str] = None,
    search: Optional[str] = None,
    client_id: Optional[int] = None
):
    """
    Get list of projects with pagination, filtering, and search
    
    Args:
        db: Database session
        pagination: Pagination parameters
        status: Optional status filter
        search: Optional search term
        client_id: Optional client ID filter
        
    Returns:
        PaginatedResponse with projects and metadata
    """
    # Build query parameters dict for filtering
    query_params = {}
    if status:
        query_params['status'] = status
    if search:
        query_params['search'] = search
    if client_id:
        query_params['client_id'] = client_id
    
    # Repository handles query building and delegates pagination
    result = await project_repository.get_projects_paginated(db, pagination, query_params)
    return result


async def update_project_service(db: AsyncSession, project_id: int, project_data: ProjectUpdate) -> Optional[ProjectRead]:
    """
    Update project information with business logic validation and event publishing
    
    Args:
        db: Database session
        project_id: Project ID to update
        project_data: Project update data
        
    Returns:
        Updated project data or None if not found
        
    Raises:
        ValueError: If username already exists for another project or client doesn't exist
    """
    # Check if project exists
    existing_project = await project_repository.get_project_by_id(db, project_id)
    if not existing_project:
        logger.warning(f"Project not found for update: {project_id}")
        return None
    
    # If username is being updated, check if it's already used by another project
    if project_data.username and project_data.username != existing_project.username:
        username_exists = await project_repository.get_project_by_username(db, project_data.username)
        if username_exists:
            raise ValueError(f"Project with username {project_data.username} already exists")
    
    # If client_id is being updated, check if client exists
    if project_data.client_id and project_data.client_id != existing_project.client_id:
        client_exists = await project_repository.check_client_exists(db, project_data.client_id)
        if not client_exists:
            raise ValueError(f"Client with ID {project_data.client_id} does not exist")
    
    # Prepare update data (only non-None values)
    update_data = {}
    for field, value in project_data.model_dump().items():
        if value is not None:
            update_data[field] = value
    
    # Update project in database
    updated_project = await project_repository.update_project(db, project_id, update_data)
    
    if updated_project:
        # Publish project updated event
        await _publish_project_event(
            event_type=EventType.MODEL_UPDATED,
            project_id=updated_project.id,
            project_name=updated_project.name,
            username=updated_project.username,
            password=project_data.password if project_data.password else None,  # Include password if provided
            client_id=updated_project.client_id
        )
        
        logger.info(f"Project updated successfully: {updated_project.name} (ID: {project_id})")
        return _convert_to_project_read(updated_project)
    
    return None


async def get_project_by_id_service(db: AsyncSession, project_id: int) -> Optional[ProjectRead]:
    """
    Get project by ID
    
    Args:
        db: Database session
        project_id: Project ID
        
    Returns:
        Project data or None if not found
    """
    project = await project_repository.get_project_by_id(db, project_id)
    
    if project:
        return _convert_to_project_read(project)
    
    return None


async def delete_project_service(db: AsyncSession, project_id: int) -> bool:
    """
    Soft delete project
    
    Args:
        db: Database session
        project_id: Project ID to delete
        
    Returns:
        True if deleted successfully, False otherwise
    """
    success = await project_repository.soft_delete_project(db, project_id)
    
    if success:
        logger.info(f"Project soft deleted successfully: {project_id}")
    
    return success


def _convert_to_project_read(project) -> ProjectRead:
    """Convert project model to ProjectRead schema with client information"""
    project_dict = {
        "id": project.id,
        "name": project.name,
        "username": project.username,
        "client_id": project.client_id,
        "deadline": project.deadline,
        "status": project.status,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "deleted_at": project.deleted_at,
        "client_name": getattr(project.client, 'name', None) if hasattr(project, 'client') and project.client else None,
        "client_email": getattr(project.client, 'email', None) if hasattr(project, 'client') and project.client else None
    }
    return ProjectRead(**project_dict)


async def _publish_project_event(
    event_type: EventType,
    project_id: int,
    project_name: str,
    username: str,
    password: Optional[str] = None,
    client_id: int = None
):
    """Publish project event to SNS"""
    try:
        event_data = {
            "project_id": project_id,
            "project_name": project_name,
            "username": username,
            "client_id": client_id
        }
        
        # Include password in event data if provided
        if password:
            event_data["password"] = password
        
        publish_request = PublishEventRequest(
            event_type=event_type,
            target_services=ServiceTarget.ALL,  # Broadcast to all services
            data=event_data,
            source_service="project_management"
        )
        
        message_id = await sns_publisher.publish_event(publish_request)
        
        if message_id:
            logger.info(f"✅ Published {event_type} event for project {project_id} (Message ID: {message_id})")
        else:
            logger.warning(f"⚠️ Failed to publish {event_type} event for project {project_id}")
            
    except Exception as e:
        logger.error(f"❌ Error publishing {event_type} event for project {project_id}: {e}") 