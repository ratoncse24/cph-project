from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.project_notes import ProjectNotesCreate, ProjectNotesUpdate, ProjectNotesReadWithRelations
from app.schemas.user import UserRead
from app.services import project_notes as project_notes_service
from app.db.session import get_db
from app.dependencies.authorization import require_roles
from app.core.roles import UserRole
from app.utils.pagination import PaginationParams
from app.utils.response_formatter import ResponseFormatter
from app.core.logger import logger


router = APIRouter()


@router.post("/project-notes", status_code=status.HTTP_201_CREATED)
async def create_project_note(
    note_data: ProjectNotesCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Create a new project note (Admin only)
    
    Args:
        note_data: Project note creation data
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Standardized API response with created project note
    """
    logger.info(f"Admin {current_user.username} creating project note for project {note_data.project_id}")
    
    try:
        note = await project_notes_service.create_project_note(db, note_data, current_user.id)
        
        response_data = ResponseFormatter.success_response(
            data=note,
            message="Project note created successfully"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_201_CREATED)
        
    except ValueError as e:
        logger.warning(f"Validation error creating project note: {e}")
        response_data = ResponseFormatter.error_response(
            message=str(e)
        )
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error creating project note: {e}")
        response_data = ResponseFormatter.error_response(
            message="Failed to create project note"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/project-notes")
async def get_project_notes_list(
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=20, ge=1, le=100, description="Results per page"),
    search: str = Query(default=None, description="Search term for title, description, or project name"),
    project_id: int = Query(default=None, description="Filter by project ID"),
    added_by_user_id: int = Query(default=None, description="Filter by user who added the note"),
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Get paginated list of project notes with filtering and search (Admin only)
    
    Args:
        page: Page number (starts from 1)
        size: Number of results per page (max 100)
        search: Optional search term for filtering notes
        project_id: Optional project ID filter
        added_by_user_id: Optional user ID filter
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Standardized API response with paginated list of project notes
    """
    logger.info(f"Admin {current_user.username} requesting project notes list - page: {page}, size: {size}")
    
    # Separate pagination parameters from query filters
    pagination = PaginationParams(page=page, size=size)
    
    # Build query parameters dict for filtering
    query_params = {}
    if search:
        query_params['search'] = search
    if project_id:
        query_params['project_id'] = project_id
    if added_by_user_id:
        query_params['added_by_user_id'] = added_by_user_id
    
    try:
        # Service handles business logic and delegates to repository
        result = await project_notes_service.get_project_notes_list(db, pagination, query_params)
        
        logger.info(f"Returned {len(result.results)} project notes out of {result.meta.total} total")
        response_data = ResponseFormatter.success_response(data=result)
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error retrieving project notes list: {e}")
        response_data = ResponseFormatter.error_response(
            message="Failed to retrieve project notes list"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/project-notes/{note_id}")
async def get_project_note(
    note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Get a specific project note by ID (Admin only)
    
    Args:
        note_id: Project note ID
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Standardized API response with project note details
    """
    logger.info(f"Admin {current_user.username} requesting project note {note_id}")
    
    try:
        note = await project_notes_service.get_project_note(db, note_id)
        
        if not note:
            response_data = ResponseFormatter.error_response(
                message="Project note not found"
            )
            return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_404_NOT_FOUND)
        
        response_data = ResponseFormatter.success_response(data=note)
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error retrieving project note {note_id}: {e}")
        response_data = ResponseFormatter.error_response(
            message="Failed to retrieve project note"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.put("/project-notes/{note_id}")
async def update_project_note(
    note_id: int,
    note_data: ProjectNotesUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Update a project note (Admin only)
    
    Args:
        note_id: Project note ID
        note_data: Project note update data
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Standardized API response with updated project note
    """
    logger.info(f"Admin {current_user.username} updating project note {note_id}")
    
    try:
        updated_note = await project_notes_service.update_project_note(db, note_id, note_data)
        
        if not updated_note:
            response_data = ResponseFormatter.error_response(
                message="Project note not found"
            )
            return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_404_NOT_FOUND)
        
        response_data = ResponseFormatter.success_response(
            data=updated_note,
            message="Project note updated successfully"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_200_OK)
        
    except ValueError as e:
        logger.warning(f"Validation error updating project note: {e}")
        response_data = ResponseFormatter.error_response(
            message=str(e)
        )
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error updating project note {note_id}: {e}")
        response_data = ResponseFormatter.error_response(
            message="Failed to update project note"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.delete("/project-notes/{note_id}")
async def delete_project_note(
    note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Delete a project note (Admin only)
    
    Args:
        note_id: Project note ID
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Standardized API response
    """
    logger.info(f"Admin {current_user.username} deleting project note {note_id}")
    
    try:
        success = await project_notes_service.delete_project_note(db, note_id)
        
        if not success:
            response_data = ResponseFormatter.error_response(
                message="Project note not found"
            )
            return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_404_NOT_FOUND)
        
        response_data = ResponseFormatter.success_response(
            data = {},
            message="Project note deleted successfully"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error deleting project note {note_id}: {e}")
        response_data = ResponseFormatter.error_response(
            message="Failed to delete project note"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
