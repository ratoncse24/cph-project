from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.project_notes import ProjectNotesCreate, ProjectNotesUpdate, ProjectNotesReadWithRelations, ProjectNotesListResponse
from app.repository import project_notes as project_notes_repo
from app.core.logger import logger
from app.utils.pagination import PaginationParams, PaginationHandler


async def create_project_note(db: AsyncSession, note_data: ProjectNotesCreate, user_id: int):
    """
    Create a new project note with business logic validation
    
    Args:
        db: Database session
        note_data: Note creation data
        user_id: ID of the user creating the note
        
    Returns:
        Created project note
        
    Raises:
        ValueError: If project doesn't exist or validation fails
    """
    try:
        # Business logic: Check if project exists
        project_exists = await project_notes_repo.check_project_exists(db, note_data.project_id)
        if not project_exists:
            raise ValueError(f"Project with ID {note_data.project_id} does not exist")
        
        # Create the note
        note = await project_notes_repo.create_project_note(db, note_data, user_id)
        
        logger.info(f"Project note created successfully by user {user_id}: {note.title}")
        return note
        
    except Exception as e:
        logger.error(f"Error in create_project_note service: {e}")
        raise


async def get_project_note(db: AsyncSession, note_id: int) -> Optional[ProjectNotesReadWithRelations]:
    """
    Get a project note by ID with business logic
    
    Args:
        db: Database session
        note_id: Note ID
        
    Returns:
        Project note with relations or None if not found
    """
    try:
        note = await project_notes_repo.get_project_note_by_id(db, note_id)
        if not note:
            logger.warning(f"Project note not found: {note_id}")
            return None
        
        # Convert to response schema with relations
        # Note: This is a simplified version. In a real implementation,
        # you might want to fetch related data here
        return ProjectNotesReadWithRelations.model_validate(note)
        
    except Exception as e:
        logger.error(f"Error in get_project_note service: {e}")
        return None


async def get_project_notes_list(
    db: AsyncSession, 
    pagination: PaginationParams,
    query_params: Optional[Dict[str, Any]] = None
) -> ProjectNotesListResponse:
    """
    Get paginated list of project notes with filtering and search
    
    Args:
        db: Database session
        pagination: Pagination parameters
        query_params: Query parameters for filtering and search
        
    Returns:
        Paginated response with project notes
    """
    try:
        # Get paginated results
        result = await project_notes_repo.get_project_notes_paginated(db, pagination, query_params)
        
        logger.info(f"Retrieved {len(result.results)} project notes out of {result.meta.total} total")
        return result
        
    except Exception as e:
        logger.error(f"Error in get_project_notes_list service: {e}")
        raise


async def update_project_note(
    db: AsyncSession, 
    note_id: int, 
    note_data: ProjectNotesUpdate
) -> Optional[ProjectNotesReadWithRelations]:
    """
    Update a project note with business logic validation
    
    Args:
        db: Database session
        note_id: Note ID to update
        note_data: Update data
        
    Returns:
        Updated project note or None if not found
    """
    try:
        # Check if note exists
        existing_note = await project_notes_repo.get_project_note_by_id(db, note_id)
        if not existing_note:
            logger.warning(f"Project note not found for update: {note_id}")
            return None
        
        # Business logic: Validate update data
        if note_data.title is not None and len(note_data.title.strip()) == 0:
            raise ValueError("Note title cannot be empty")
        
        # Update the note
        updated_note = await project_notes_repo.update_project_note(db, note_id, note_data)
        if not updated_note:
            return None
        
        logger.info(f"Project note updated successfully: {updated_note.title} (ID: {note_id})")
        return ProjectNotesReadWithRelations.model_validate(updated_note)
        
    except Exception as e:
        logger.error(f"Error in update_project_note service: {e}")
        raise


async def delete_project_note(db: AsyncSession, note_id: int) -> bool:
    """
    Delete a project note with business logic validation
    
    Args:
        db: Database session
        note_id: Note ID to delete
        
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        # Check if note exists
        existing_note = await project_notes_repo.get_project_note_by_id(db, note_id)
        if not existing_note:
            logger.warning(f"Project note not found for deletion: {note_id}")
            return False
        
        # Business logic: Additional validation could go here
        # For example, check if user has permission to delete this note
        
        # Delete the note
        success = await project_notes_repo.delete_project_note(db, note_id)
        
        if success:
            logger.info(f"Project note deleted successfully: {existing_note.title} (ID: {note_id})")
        else:
            logger.error(f"Failed to delete project note: {note_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error in delete_project_note service: {e}")
        return False
