from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.role_notes import RoleNotesCreate, RoleNotesUpdate, RoleNotesReadWithRelations, RoleNotesListResponse
from app.repository import role_notes as role_notes_repo
from app.core.logger import logger
from app.utils.pagination import PaginationParams, PaginationHandler


async def create_role_note(db: AsyncSession, note_data: RoleNotesCreate, user_id: int):
    """
    Create a new role note with business logic validation
    
    Args:
        db: Database session
        note_data: Note creation data
        user_id: ID of the user creating the note
        
    Returns:
        Created role note
        
    Raises:
        ValueError: If project or role doesn't exist or validation fails
    """
    try:
        # Business logic: Check if project exists
        project_exists = await role_notes_repo.check_project_exists(db, note_data.project_id)
        if not project_exists:
            raise ValueError(f"Project with ID {note_data.project_id} does not exist")
        
        # Business logic: Check if role exists
        role_exists = await role_notes_repo.check_role_exists(db, note_data.role_id)
        if not role_exists:
            raise ValueError(f"Role with ID {note_data.role_id} does not exist")
        
        # Create the note
        note = await role_notes_repo.create_role_note(db, note_data, user_id)
        
        logger.info(f"Role note created successfully by user {user_id}: {note.title}")
        
        # Get the created note with relations
        note_with_relations = await role_notes_repo.get_role_note_with_relations(db, note.id)
        if note_with_relations:
            return RoleNotesReadWithRelations.model_validate(note_with_relations)
        else:
            return RoleNotesReadWithRelations.model_validate(note)
        
    except Exception as e:
        logger.error(f"Error in create_role_note service: {e}")
        raise


async def get_role_note(db: AsyncSession, note_id: int) -> Optional[RoleNotesReadWithRelations]:
    """
    Get a role note by ID with business logic
    
    Args:
        db: Database session
        note_id: Note ID
        
    Returns:
        Role note with relations or None if not found
    """
    try:
        note_with_relations = await role_notes_repo.get_role_note_with_relations(db, note_id)
        if not note_with_relations:
            logger.warning(f"Role note not found: {note_id}")
            return None
        
        # Convert to response schema with relations
        return RoleNotesReadWithRelations.model_validate(note_with_relations)
        
    except Exception as e:
        logger.error(f"Error in get_role_note service: {e}")
        return None


async def get_role_notes_list(
    db: AsyncSession, 
    pagination: PaginationParams,
    query_params: Optional[Dict[str, Any]] = None
) -> RoleNotesListResponse:
    """
    Get paginated list of role notes with filtering and search
    
    Args:
        db: Database session
        pagination: Pagination parameters
        query_params: Query parameters for filtering and search
        
    Returns:
        Paginated response with role notes
    """
    try:
        # Business logic validation for query parameters
        if query_params:
            # Validate project_id if provided
            if query_params.get('project_id'):
                try:
                    project_id = int(query_params['project_id'])
                    project_exists = await role_notes_repo.check_project_exists(db, project_id)
                    if not project_exists:
                        logger.warning(f"Filtering by non-existent project ID: {project_id}")
                        # Return empty result instead of error
                        return PaginationHandler.create_response([], pagination, 0)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid project_id in query params: {query_params['project_id']}")
                    return PaginationHandler.create_response([], pagination, 0)
            
            # Validate role_id if provided
            if query_params.get('role_id'):
                try:
                    role_id = int(query_params['role_id'])
                    role_exists = await role_notes_repo.check_role_exists(db, role_id)
                    if not role_exists:
                        logger.warning(f"Filtering by non-existent role ID: {role_id}")
                        # Return empty result instead of error
                        return PaginationHandler.create_response([], pagination, 0)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid role_id in query params: {query_params['role_id']}")
                    return PaginationHandler.create_response([], pagination, 0)
            
            # Validate added_by_user_id if provided
            if query_params.get('added_by_user_id'):
                try:
                    int(query_params['added_by_user_id'])
                except (ValueError, TypeError):
                    logger.warning(f"Invalid added_by_user_id in query params: {query_params['added_by_user_id']}")
                    return PaginationHandler.create_response([], pagination, 0)
        
        # Get paginated results
        result = await role_notes_repo.get_role_notes_paginated(db, pagination, query_params)
        
        logger.info(f"Retrieved {len(result.results)} role notes out of {result.meta.total} total")
        return result
        
    except Exception as e:
        logger.error(f"Error in get_role_notes_list service: {e}")
        raise


async def update_role_note(
    db: AsyncSession, 
    note_id: int, 
    note_data: RoleNotesUpdate
) -> Optional[RoleNotesReadWithRelations]:
    """
    Update a role note with business logic validation
    
    Args:
        db: Database session
        note_id: Note ID to update
        note_data: Update data
        
    Returns:
        Updated role note or None if not found
    """
    try:
        # Check if note exists
        existing_note = await role_notes_repo.get_role_note_by_id(db, note_id)
        if not existing_note:
            logger.warning(f"Role note not found for update: {note_id}")
            return None
        
        # Business logic: Validate update data
        if note_data.title is not None and len(note_data.title.strip()) == 0:
            raise ValueError("Note title cannot be empty")
        
        # Update the note
        updated_note = await role_notes_repo.update_role_note(db, note_id, note_data)
        if not updated_note:
            return None
        
        logger.info(f"Role note updated successfully: {updated_note.title} (ID: {note_id})")
        
        # Get the updated note with relations
        updated_note_with_relations = await role_notes_repo.get_role_note_with_relations(db, note_id)
        if updated_note_with_relations:
            return RoleNotesReadWithRelations.model_validate(updated_note_with_relations)
        else:
            return None
        
    except Exception as e:
        logger.error(f"Error in update_role_note service: {e}")
        raise


async def delete_role_note(db: AsyncSession, note_id: int) -> bool:
    """
    Delete a role note with business logic validation
    
    Args:
        db: Database session
        note_id: Note ID to delete
        
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        # Check if note exists
        existing_note = await role_notes_repo.get_role_note_by_id(db, note_id)
        if not existing_note:
            logger.warning(f"Role note not found for deletion: {note_id}")
            return False
        
        # Business logic: Additional validation could go here
        # For example, check if user has permission to delete this note
        
        # Delete the note
        success = await role_notes_repo.delete_role_note(db, note_id)
        
        if success:
            logger.info(f"Role note deleted successfully: {existing_note.title} (ID: {note_id})")
        else:
            logger.error(f"Failed to delete role note: {note_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error in delete_role_note service: {e}")
        return False


async def get_notes_by_role(db: AsyncSession, role_id: int) -> list[RoleNotesReadWithRelations]:
    """
    Get all notes for a specific role
    
    Args:
        db: Database session
        role_id: Role ID
        
    Returns:
        List of role notes
    """
    try:
        # Business logic: Check if role exists
        role_exists = await role_notes_repo.check_role_exists(db, role_id)
        if not role_exists:
            logger.warning(f"Role not found: {role_id}")
            return []
        
        # Get notes for the role
        notes = await role_notes_repo.get_notes_by_role_id(db, role_id)
        
        # Convert to response schema
        result = [RoleNotesReadWithRelations.model_validate(note) for note in notes]
        
        logger.info(f"Retrieved {len(result)} notes for role {role_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error in get_notes_by_role service: {e}")
        return [] 