from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.role import RoleCreate, RoleUpdate, RoleReadWithRelations, RoleListResponse
from app.repository import role as role_repo
from app.core.logger import logger
from app.utils.pagination import PaginationParams, PaginationHandler
from app.events.sns_publisher import sns_publisher
from app.events.models import PublishEventRequest, EventType, ServiceTarget


async def create_role(db: AsyncSession, role_data: RoleCreate):
    """
    Create a new role with business logic validation and event publishing
    
    Args:
        db: Database session
        role_data: Role creation data
        
    Returns:
        Created role
        
    Raises:
        ValueError: If project doesn't exist or validation fails
    """
    try:
        # Business logic: Check if project exists
        project_exists = await role_repo.check_project_exists(db, role_data.project_id)
        if not project_exists:
            raise ValueError(f"Project with ID {role_data.project_id} does not exist")
        
        # Business logic: Validate age range
        if role_data.age_from and role_data.age_to and role_data.age_from > role_data.age_to:
            raise ValueError("age_from cannot be greater than age_to")
        
        # Business logic: Validate height range
        if role_data.height_from and role_data.height_to and role_data.height_from > role_data.height_to:
            raise ValueError("height_from cannot be greater than height_to")
        
        # Create the role
        role = await role_repo.create_role(db, role_data)
        
        # Publish event to SELECTION service
        await _publish_role_event(EventType.ROLE_CREATED, role, "role_created")
        
        logger.info(f"Role created successfully: {role.name} (ID: {role.id})")
        return role
        
    except Exception as e:
        logger.error(f"Error in create_role service: {e}")
        raise


async def get_role(db: AsyncSession, role_id: int) -> Optional[RoleReadWithRelations]:
    """
    Get a role by ID with business logic
    
    Args:
        db: Database session
        role_id: Role ID
        
    Returns:
        Role with relations or None if not found
    """
    try:
        role = await role_repo.get_role_by_id(db, role_id)
        if not role:
            logger.warning(f"Role not found: {role_id}")
            return None
        
        # Convert to response schema with relations
        return RoleReadWithRelations.model_validate(role)
        
    except Exception as e:
        logger.error(f"Error in get_role service: {e}")
        return None


async def get_roles_list(
    db: AsyncSession, 
    pagination: PaginationParams,
    query_params: Optional[Dict[str, Any]] = None,
    current_user_role: str = None,
    current_user_username: str = None
) -> RoleListResponse:
    """
    Get paginated list of roles with filtering and search and role-based access control
    
    Args:
        db: Database session
        pagination: Pagination parameters
        query_params: Query parameters for filtering and search
        current_user_role: Current user's role (admin or project)
        current_user_username: Current user's username (for PROJECT role validation)
        
    Returns:
        Paginated response with roles
    """
    try:
        # Role-based access control for PROJECT role users
        if current_user_role == "project" and current_user_username:
            # Get the user's project ID
            user_project_id = await role_repo.get_user_project_id(db, current_user_username)
            if not user_project_id:
                logger.warning(f"Project not found for user: {current_user_username}")
                return PaginationHandler.create_response([], pagination, 0)
            
            # Force the query to only return roles for the user's project
            if query_params is None:
                query_params = {}
            query_params['project_id'] = user_project_id
            
            logger.info(f"PROJECT role user {current_user_username} accessing roles for their project ID: {user_project_id}")
        
        # Business logic validation for query parameters
        if query_params:
            # Validate project_id if provided
            if query_params.get('project_id'):
                try:
                    project_id = int(query_params['project_id'])
                    project_exists = await role_repo.check_project_exists(db, project_id)
                    if not project_exists:
                        logger.warning(f"Filtering by non-existent project ID: {project_id}")
                        # Return empty result instead of error
                        return PaginationHandler.create_response([], pagination, 0)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid project_id in query params: {query_params['project_id']}")
                    return PaginationHandler.create_response([], pagination, 0)
            
            # Validate age range filters
            if query_params.get('age_from'):
                try:
                    age_from = int(query_params['age_from'])
                    if age_from < 0 or age_from > 150:
                        logger.warning(f"Invalid age_from in query params: {age_from}")
                        return PaginationHandler.create_response([], pagination, 0)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid age_from in query params: {query_params['age_from']}")
                    return PaginationHandler.create_response([], pagination, 0)
            
            if query_params.get('age_to'):
                try:
                    age_to = int(query_params['age_to'])
                    if age_to < 0 or age_to > 150:
                        logger.warning(f"Invalid age_to in query params: {age_to}")
                        return PaginationHandler.create_response([], pagination, 0)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid age_to in query params: {query_params['age_to']}")
                    return PaginationHandler.create_response([], pagination, 0)
            
            # Validate height range filters
            if query_params.get('height_from'):
                try:
                    height_from = float(query_params['height_from'])
                    if height_from < 0 or height_from > 300:
                        logger.warning(f"Invalid height_from in query params: {height_from}")
                        return PaginationHandler.create_response([], pagination, 0)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid height_from in query params: {query_params['height_from']}")
                    return PaginationHandler.create_response([], pagination, 0)
            
            if query_params.get('height_to'):
                try:
                    height_to = float(query_params['height_to'])
                    if height_to < 0 or height_to > 300:
                        logger.warning(f"Invalid height_to in query params: {height_to}")
                        return PaginationHandler.create_response([], pagination, 0)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid height_to in query params: {query_params['height_to']}")
                    return PaginationHandler.create_response([], pagination, 0)
        
        # Get paginated results
        result = await role_repo.get_roles_paginated(db, pagination, query_params)
        
        logger.info(f"Retrieved {len(result.results)} roles out of {result.meta.total} total")
        return result
        
    except Exception as e:
        logger.error(f"Error in get_roles_list service: {e}")
        raise


async def update_role(
    db: AsyncSession, 
    role_id: int, 
    role_data: RoleUpdate
) -> Optional[RoleReadWithRelations]:
    """
    Update a role with business logic validation and event publishing
    
    Args:
        db: Database session
        role_id: Role ID to update
        role_data: Update data
        
    Returns:
        Updated role or None if not found
    """
    try:
        # Check if role exists
        existing_role = await role_repo.get_role_by_id(db, role_id)
        if not existing_role:
            logger.warning(f"Role not found for update: {role_id}")
            return None
        
        # Business logic: Validate update data
        if role_data.name is not None and len(role_data.name.strip()) == 0:
            raise ValueError("Role name cannot be empty")
        
        # Business logic: Validate age range
        if role_data.age_from and role_data.age_to and role_data.age_from > role_data.age_to:
            raise ValueError("age_from cannot be greater than age_to")
        
        # Business logic: Validate height range
        if role_data.height_from and role_data.height_to and role_data.height_from > role_data.height_to:
            raise ValueError("height_from cannot be greater than height_to")
        
        # Update the role
        updated_role = await role_repo.update_role(db, role_id, role_data)
        if not updated_role:
            return None
        
        # Publish event to SELECTION service
        await _publish_role_event(EventType.ROLE_UPDATED, updated_role, "role_updated")
        
        logger.info(f"Role updated successfully: {updated_role.name} (ID: {role_id})")
        return RoleReadWithRelations.model_validate(updated_role)
        
    except Exception as e:
        logger.error(f"Error in update_role service: {e}")
        raise


async def delete_role(db: AsyncSession, role_id: int) -> bool:
    """
    Delete a role with business logic validation and event publishing
    
    Args:
        db: Database session
        role_id: Role ID to delete
        
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        # Check if role exists
        existing_role = await role_repo.get_role_by_id(db, role_id)
        if not existing_role:
            logger.warning(f"Role not found for deletion: {role_id}")
            return False
        
        # Business logic: Additional validation could go here
        # For example, check if role can be deleted (not in use, etc.)
        
        # Delete the role
        success = await role_repo.delete_role(db, role_id)
        
        if success:
            # Publish event to SELECTION service
            await _publish_role_event(EventType.ROLE_DELETED, existing_role, "role_deleted")
            logger.info(f"Role deleted successfully: {existing_role.name} (ID: {role_id})")
        else:
            logger.error(f"Failed to delete role: {role_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error in delete_role service: {e}")
        return False


async def get_roles_by_project(db: AsyncSession, project_id: int) -> list[RoleReadWithRelations]:
    """
    Get all roles for a specific project
    
    Args:
        db: Database session
        project_id: Project ID
        
    Returns:
        List of roles
    """
    try:
        # Business logic: Check if project exists
        project_exists = await role_repo.check_project_exists(db, project_id)
        if not project_exists:
            logger.warning(f"Project not found: {project_id}")
            return []
        
        # Get roles for the project
        roles = await role_repo.get_roles_by_project_id(db, project_id)
        
        # Convert to response schema
        result = [RoleReadWithRelations.model_validate(role) for role in roles]
        
        logger.info(f"Retrieved {len(result)} roles for project {project_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error in get_roles_by_project service: {e}")
        return []


async def _publish_role_event(event_type: EventType, role, action: str):
    """
    Publish role event to SELECTION service
    
    Args:
        event_type: Type of event
        role: Role object
        action: Action description
    """
    try:
        if not sns_publisher.is_configured():
            logger.warning("SNS publisher not configured. Skipping event publishing.")
            return
        
        # Prepare event data
        event_data = {
            "role_id": role.id,
            "project_id": role.project_id,
            "name": role.name,
            "gender": role.gender,
            "ethnicity": role.ethnicity,
            "language": role.language,
            "native_language": role.native_language,
            "age_from": role.age_from,
            "age_to": role.age_to,
            "height_from": float(role.height_from) if role.height_from else None,
            "height_to": float(role.height_to) if role.height_to else None,
            "tags": role.tags,
            "category": role.category,
            "hair_color": role.hair_color,
            "status": role.status,
            "action": action,
            "timestamp": role.updated_at.isoformat() if role.updated_at else None
        }
        
        # Create publish request
        publish_request = PublishEventRequest(
            event_type=event_type,
            target_services=[ServiceTarget.SELECTION_SERVICE],
            data=event_data,
            source_service="model_management"
        )
        
        # Publish event
        message_id = await sns_publisher.publish_event(publish_request)
        
        if message_id:
            logger.info(f"✅ Published {action} event for role {role.name} (ID: {role.id}) to SELECTION service")
        else:
            logger.error(f"❌ Failed to publish {action} event for role {role.name} (ID: {role.id})")
            
    except Exception as e:
        logger.error(f"Error publishing role event: {e}")
        # Don't raise the exception - event publishing failure shouldn't break the main operation 