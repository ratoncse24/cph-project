from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, and_
from typing import Optional
import datetime
import logging

from app.models.project_notes import ProjectNotes
from app.models.project import Project
from app.models.user import User
from app.schemas.project_notes import ProjectNotesCreate, ProjectNotesUpdate, ProjectNotesReadWithRelations, ProjectNotesListResponse
from app.utils.pagination import PaginationParams, PaginationHandler

logger = logging.getLogger(__name__)


async def create_project_note(db: AsyncSession, note_data: ProjectNotesCreate, user_id: int) -> ProjectNotes:
    """Create a new project note"""
    try:
        note = ProjectNotes(
            project_id=note_data.project_id,
            title=note_data.title,
            description=note_data.description,
            added_by_user_id=user_id
        )
        db.add(note)
        await db.commit()
        await db.refresh(note)
        
        logger.info(f"Created project note: {note.title} (ID: {note.id})")
        return note
        
    except Exception as e:
        logger.error(f"Error creating project note: {e}")
        await db.rollback()
        raise


async def get_project_note_by_id(db: AsyncSession, note_id: int) -> Optional[ProjectNotes]:
    """Get project note by ID"""
    try:
        result = await db.execute(
            select(ProjectNotes).where(ProjectNotes.id == note_id)
        )
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error fetching project note by ID {note_id}: {e}")
        return None


async def get_project_note_with_relations(db: AsyncSession, note_id: int) -> Optional[ProjectNotes]:
    """Get project note by ID with related data"""
    try:
        from sqlalchemy.orm import selectinload
        
        result = await db.execute(
            select(ProjectNotes)
            .options(
                selectinload(ProjectNotes.project),
                selectinload(ProjectNotes.added_by_user)
            )
            .where(ProjectNotes.id == note_id)
        )
        note = result.scalar_one_or_none()
        
        if note:
            # Add related data to the note object
            if hasattr(note, 'project') and note.project:
                try:
                    note.project_name = getattr(note.project, 'name', None)
                except Exception as e:
                    logger.warning(f"Error accessing project name: {e}")
                    note.project_name = None
            if hasattr(note, 'added_by_user') and note.added_by_user:
                try:
                    note.added_by_username = getattr(note.added_by_user, 'username', None)
                    note.added_by_name = getattr(note.added_by_user, 'name', None)
                    note.added_by_profile_picture_url = getattr(note.added_by_user, 'profile_picture_url', None)
                except Exception as e:
                    logger.warning(f"Error accessing user attributes: {e}")
                    note.added_by_username = None
                    note.added_by_name = None
                    note.added_by_profile_picture_url = None
        
        return note
    except Exception as e:
        logger.error(f"Error fetching project note with relations by ID {note_id}: {e}")
        return None


async def get_project_notes_paginated(
    db: AsyncSession, 
    pagination: PaginationParams,
    query_params: Optional[dict] = None
) -> ProjectNotesListResponse:
    """
    Get paginated list of project notes with optional filters
    
    Args:
        db: Database session
        pagination: Pure pagination parameters (page, size)
        query_params: Dict of query parameters for filtering (search, project_id, etc.)
        
    Returns:
        ProjectNotesListResponse with paginated notes and metadata
    """
    from sqlalchemy.orm import selectinload
    
    # Build the base query with relationships loaded
    query = select(ProjectNotes).options(
        selectinload(ProjectNotes.project),
        selectinload(ProjectNotes.added_by_user)
    )
    
    # Apply business logic filters from query_params
    if query_params:
        # Handle search parameter
        if query_params.get('search'):
            search_term = f"%{query_params['search']}%"
            search_conditions = [
                ProjectNotes.title.ilike(search_term),
                ProjectNotes.description.ilike(search_term)
            ]
            query = query.where(or_(*search_conditions))
        
        # Handle project_id filter
        if query_params.get('project_id'):
            query = query.where(ProjectNotes.project_id == query_params['project_id'])
        
        # Handle added_by_user_id filter
        if query_params.get('added_by_user_id'):
            query = query.where(ProjectNotes.added_by_user_id == query_params['added_by_user_id'])
    
    # Delegate pagination to the utility
    result = await PaginationHandler.paginate_query(
        db=db,
        query=query,
        pagination=pagination,
        response_schema=ProjectNotesReadWithRelations
    )
    
    # Add related data to each note result
    for note_result in result.results:
        if hasattr(note_result, 'project') and note_result.project:
            try:
                note_result.project_name = getattr(note_result.project, 'name', None)
            except Exception as e:
                logger.warning(f"Error accessing project name: {e}")
                note_result.project_name = None
        if hasattr(note_result, 'added_by_user') and note_result.added_by_user:
            try:
                note_result.added_by_username = getattr(note_result.added_by_user, 'username', None)
                note_result.added_by_name = getattr(note_result.added_by_user, 'name', None)
                note_result.added_by_profile_picture_url = getattr(note_result.added_by_user, 'profile_picture_url', None)
            except Exception as e:
                logger.warning(f"Error accessing user attributes: {e}")
                note_result.added_by_username = None
                note_result.added_by_name = None
                note_result.added_by_profile_picture_url = None
    
    return result


async def update_project_note(db: AsyncSession, note_id: int, note_data: ProjectNotesUpdate) -> Optional[ProjectNotes]:
    """Update project note"""
    try:
        # Get existing note
        result = await db.execute(
            select(ProjectNotes).where(ProjectNotes.id == note_id)
        )
        note = result.scalar_one_or_none()
        
        if not note:
            logger.warning(f"Project note not found for update: {note_id}")
            return None
        
        # Update fields
        update_data = note_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(note, field):
                setattr(note, field, value)
        
        # Update timestamp
        note.updated_at = datetime.datetime.utcnow()
        
        await db.commit()
        await db.refresh(note)
        
        logger.info(f"Project note updated successfully: {note.title} (ID: {note_id})")
        return note
        
    except Exception as e:
        logger.error(f"Error updating project note {note_id}: {e}")
        await db.rollback()
        return None


async def delete_project_note(db: AsyncSession, note_id: int) -> bool:
    """Delete project note"""
    try:
        result = await db.execute(
            select(ProjectNotes).where(ProjectNotes.id == note_id)
        )
        note = result.scalar_one_or_none()
        
        if not note:
            logger.warning(f"Project note not found for deletion: {note_id}")
            return False
        
        await db.delete(note)
        await db.commit()
        
        logger.info(f"Project note deleted successfully: {note.title} (ID: {note_id})")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting project note {note_id}: {e}")
        await db.rollback()
        return False


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