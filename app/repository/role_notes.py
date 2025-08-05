from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, and_
from typing import Optional
import datetime
import logging

from app.models.role_notes import RoleNotes
from app.models.project import Project
from app.models.role import Role
from app.models.user import User
from app.schemas.role_notes import RoleNotesCreate, RoleNotesUpdate, RoleNotesReadWithRelations, RoleNotesListResponse
from app.utils.pagination import PaginationParams, PaginationHandler

logger = logging.getLogger(__name__)


async def create_role_note(db: AsyncSession, note_data: RoleNotesCreate, user_id: int) -> RoleNotes:
    """Create a new role note"""
    try:
        note = RoleNotes(
            project_id=note_data.project_id,
            role_id=note_data.role_id,
            title=note_data.title,
            description=note_data.description,
            added_by_user_id=user_id
        )
        db.add(note)
        await db.commit()
        await db.refresh(note)
        
        logger.info(f"Created role note: {note.title} (ID: {note.id})")
        return note
        
    except Exception as e:
        logger.error(f"Error creating role note: {e}")
        await db.rollback()
        raise


async def get_role_note_by_id(db: AsyncSession, note_id: int) -> Optional[RoleNotes]:
    """Get role note by ID"""
    try:
        result = await db.execute(
            select(RoleNotes).where(RoleNotes.id == note_id)
        )
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error fetching role note by ID {note_id}: {e}")
        return None


async def get_role_note_with_relations(db: AsyncSession, note_id: int) -> Optional[RoleNotesReadWithRelations]:
    """Get role note by ID with related data"""
    try:
        result = await db.execute(
            select(
                RoleNotes,
                Project.name.label('project_name'),
                Role.name.label('role_name'),
                User.username.label('added_by_username'),
                User.name.label('added_by_name'),
                User.profile_picture_url.label('added_by_profile_picture_url')
            ).join(
                Project, RoleNotes.project_id == Project.id
            ).join(
                Role, RoleNotes.role_id == Role.id
            ).join(
                User, RoleNotes.added_by_user_id == User.id
            ).where(RoleNotes.id == note_id)
        )
        return result.first()
    except Exception as e:
        logger.error(f"Error fetching role note with relations by ID {note_id}: {e}")
        return None


async def get_role_notes_paginated(
    db: AsyncSession, 
    pagination: PaginationParams,
    query_params: Optional[dict] = None
) -> RoleNotesListResponse:
    """
    Get paginated list of role notes with optional filters
    
    Args:
        db: Database session
        pagination: Pure pagination parameters (page, size)
        query_params: Dict of query parameters for filtering (search, project_id, role_id, etc.)
        
    Returns:
        RoleNotesListResponse with paginated notes and metadata
    """
    # Build the base query with joins for related data
    query = select(
        RoleNotes,
        Project.name.label('project_name'),
        Role.name.label('role_name'),
        User.username.label('added_by_username'),
        User.name.label('added_by_name'),
        User.profile_picture_url.label('added_by_profile_picture_url')
    ).join(
        Project, RoleNotes.project_id == Project.id
    ).join(
        Role, RoleNotes.role_id == Role.id
    ).join(
        User, RoleNotes.added_by_user_id == User.id
    )
    
    # Apply business logic filters from query_params
    if query_params:
        # Handle search parameter
        if query_params.get('search'):
            search_term = f"%{query_params['search']}%"
            search_conditions = [
                RoleNotes.title.ilike(search_term),
                RoleNotes.description.ilike(search_term),
                Project.name.ilike(search_term),
                Role.name.ilike(search_term)
            ]
            query = query.where(or_(*search_conditions))
        
        # Handle project_id filter
        if query_params.get('project_id'):
            query = query.where(RoleNotes.project_id == query_params['project_id'])
        
        # Handle role_id filter
        if query_params.get('role_id'):
            query = query.where(RoleNotes.role_id == query_params['role_id'])
        
        # Handle added_by_user_id filter
        if query_params.get('added_by_user_id'):
            query = query.where(RoleNotes.added_by_user_id == query_params['added_by_user_id'])
    
    # Delegate pagination to the utility
    return await PaginationHandler.paginate_query(
        db=db,
        query=query,
        pagination=pagination,
        response_schema=RoleNotesReadWithRelations
    )


async def update_role_note(db: AsyncSession, note_id: int, note_data: RoleNotesUpdate) -> Optional[RoleNotes]:
    """Update role note"""
    try:
        # Get existing note
        result = await db.execute(
            select(RoleNotes).where(RoleNotes.id == note_id)
        )
        note = result.scalar_one_or_none()
        
        if not note:
            logger.warning(f"Role note not found for update: {note_id}")
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
        
        logger.info(f"Role note updated successfully: {note.title} (ID: {note_id})")
        return note
        
    except Exception as e:
        logger.error(f"Error updating role note {note_id}: {e}")
        await db.rollback()
        return None


async def delete_role_note(db: AsyncSession, note_id: int) -> bool:
    """Delete role note"""
    try:
        result = await db.execute(
            select(RoleNotes).where(RoleNotes.id == note_id)
        )
        note = result.scalar_one_or_none()
        
        if not note:
            logger.warning(f"Role note not found for deletion: {note_id}")
            return False
        
        await db.delete(note)
        await db.commit()
        
        logger.info(f"Role note deleted successfully: {note.title} (ID: {note_id})")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting role note {note_id}: {e}")
        await db.rollback()
        return False


async def get_notes_by_role_id(db: AsyncSession, role_id: int) -> list[RoleNotes]:
    """Get all notes for a specific role"""
    try:
        result = await db.execute(
            select(RoleNotes).where(RoleNotes.role_id == role_id)
        )
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error fetching notes for role {role_id}: {e}")
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


async def check_role_exists(db: AsyncSession, role_id: int) -> bool:
    """Check if role exists"""
    try:
        result = await db.execute(
            select(Role).where(Role.id == role_id)
        )
        return result.scalar_one_or_none() is not None
    except Exception as e:
        logger.error(f"Error checking role existence {role_id}: {e}")
        return False 