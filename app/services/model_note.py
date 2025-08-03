from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.repository import model_note as model_note_crud
from app.schemas.model_note import ModelNoteCreate, ModelNoteUpdate, ModelNoteRead, ModelNoteWithUser
from app.utils.pagination import PaginationParams, PaginatedResponse
from app.core.logger import logger


async def create_model_note(
    db: AsyncSession,
    note_data: ModelNoteCreate
) -> Optional[ModelNoteRead]:
    """
    Create a new model note with business logic validation
    
    Args:
        db: Database session
        note_data: Note creation data
        
    Returns:
        Created ModelNoteRead object or None if creation fails
    """
    try:
        logger.info(f"Creating model note for model {note_data.model_id} by user {note_data.added_by_user_id}")
        
        # Create the note using repository
        note = await model_note_crud.create_model_note(db, note_data)
        
        if not note:
            logger.warning(f"Failed to create model note for model {note_data.model_id}")
            return None
        
        # Convert to response schema
        note_response = ModelNoteRead.model_validate(note)
        
        logger.info(f"✅ Successfully created model note {note.id} for model {note_data.model_id}")
        return note_response
        
    except Exception as e:
        logger.error(f"Error creating model note: {e}")
        raise Exception("Model note creation failed")


async def get_model_notes_paginated(
    db: AsyncSession,
    model_id: int,
    pagination: PaginationParams
) -> PaginatedResponse[ModelNoteWithUser]:
    """
    Get paginated list of notes for a specific model with user information
    
    Args:
        db: Database session
        model_id: Model ID
        pagination: Pagination parameters
        
    Returns:
        PaginatedResponse with ModelNoteWithUser objects
    """
    try:
        logger.debug(f"Fetching paginated notes for model: {model_id} (page: {pagination.page}, size: {pagination.size})")
        
        result = await model_note_crud.get_model_notes_paginated(db, model_id, pagination)
        
        logger.debug(f"Found {len(result.results)} notes for model {model_id} (page {pagination.page})")
        return result
        
    except Exception as e:
        logger.error(f"Error fetching paginated notes for model {model_id}: {e}")
        raise Exception("Failed to fetch model notes")


async def get_model_note_by_id(
    db: AsyncSession,
    note_id: int
) -> Optional[ModelNoteRead]:
    """
    Get a specific model note by ID
    
    Args:
        db: Database session
        note_id: Note ID
        
    Returns:
        ModelNoteRead object or None if not found
    """
    try:
        logger.debug(f"Fetching model note: {note_id}")
        
        note = await model_note_crud.get_model_note_by_id(db, note_id)
        
        if not note:
            logger.warning(f"Model note not found: {note_id}")
            return None
        
        # Convert to response schema
        note_response = ModelNoteRead.model_validate(note)
        
        logger.debug(f"Found model note: {note_id}")
        return note_response
        
    except Exception as e:
        logger.error(f"Error fetching model note {note_id}: {e}")
        raise Exception("Failed to fetch model note")


async def get_model_note_with_user(
    db: AsyncSession,
    note_id: int
) -> Optional[ModelNoteWithUser]:
    """
    Get a model note with user information who added it
    
    Args:
        db: Database session
        note_id: Note ID
        
    Returns:
        ModelNoteWithUser object or None if not found
    """
    try:
        logger.debug(f"Fetching model note with user info: {note_id}")
        
        result = await model_note_crud.get_model_note_with_user(db, note_id)
        
        if not result:
            logger.warning(f"Model note with user not found: {note_id}")
            return None
        
        note, user = result
        
        # Create response with user information
        note_response = ModelNoteWithUser(
            id=note.id,
            model_id=note.model_id,
            title=note.title,
            description=note.description,
            added_by_user_id=note.added_by_user_id,
            added_by_username=user.username if user else None,
            created_at=note.created_at,
            updated_at=note.updated_at,
            deleted_at=note.deleted_at
        )
        
        logger.debug(f"Found model note with user: {note_id}")
        return note_response
        
    except Exception as e:
        logger.error(f"Error fetching model note with user {note_id}: {e}")
        raise Exception("Failed to fetch model note with user")


async def update_model_note(
    db: AsyncSession,
    note_id: int,
    note_data: ModelNoteUpdate
) -> Optional[ModelNoteRead]:
    """
    Update a model note with business logic validation
    
    Args:
        db: Database session
        note_id: Note ID to update
        note_data: Update data
        
    Returns:
        Updated ModelNoteRead object or None if not found
    """
    try:
        logger.info(f"Updating model note: {note_id}")
        
        # Update the note using repository
        note = await model_note_crud.update_model_note(db, note_id, note_data)
        
        if not note:
            logger.warning(f"Failed to update model note: {note_id}")
            return None
        
        # Convert to response schema
        note_response = ModelNoteRead.model_validate(note)
        
        logger.info(f"✅ Successfully updated model note: {note_id}")
        return note_response
        
    except Exception as e:
        logger.error(f"Error updating model note {note_id}: {e}")
        raise Exception("Model note update failed")


async def delete_model_note(
    db: AsyncSession,
    note_id: int
) -> bool:
    """
    Delete a model note with business logic validation
    
    Args:
        db: Database session
        note_id: Note ID to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Deleting model note: {note_id}")
        
        # Delete the note using repository
        success = await model_note_crud.delete_model_note(db, note_id)
        
        if success:
            logger.info(f"✅ Successfully deleted model note: {note_id}")
        else:
            logger.warning(f"Failed to delete model note: {note_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error deleting model note {note_id}: {e}")
        raise Exception("Model note deletion failed")
