from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectRead
from app.schemas.user import UserRead
from app.services import project as project_service
from app.utils.pagination import PaginationParams
from app.db.session import get_db
from app.dependencies.authorization import require_roles
from app.core.roles import UserRole
from app.utils.response_formatter import ResponseFormatter
from app.core.logger import logger

router = APIRouter()


@router.post("/projects")
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Create a new project (Admin only)
    
    Args:
        project_data: Project creation data
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Created project data
    """
    try:
        logger.info(f"Admin {current_user.username} creating new project: {project_data.name}")
        
        # Service handles business logic and database operations
        new_project = await project_service.create_project_service(db, project_data)
        
        response_data = ResponseFormatter.success_response(
            data=new_project,
            message="Project created successfully"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=201)
        
    except ValueError as e:
        logger.warning(f"Validation error creating project: {e}")
        response_data = ResponseFormatter.error_response(
            message=str(e)
        )
        return JSONResponse(content=response_data.to_dict(), status_code=400)
        
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        response_data = ResponseFormatter.error_response(
            message="Internal server error"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=500)


@router.get("/projects")
async def get_projects_list(
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=20, ge=1, le=100, description="Results per page"),
    status: str = Query(default=None, description="Filter by project status"),
    search: str = Query(default=None, description="Search in project name, username, or client name"),
    client_id: int = Query(default=None, description="Filter by client ID"),
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Get paginated list of projects (Admin only)
    
    Clean API layer - separates pagination from filtering logic
    
    Args:
        page: Page number (starts from 1)
        size: Number of results per page (max 100)
        status: Optional status filter
        search: Optional search term for filtering projects
        client_id: Optional client ID filter
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Standardized API response with paginated list of projects
    """
    logger.info(f"Admin {current_user.username} requesting projects list - page: {page}, size: {size}")
    
    # Separate pagination parameters from query filters
    pagination = PaginationParams(page=page, size=size)
    
    # Build query parameters dict for filtering
    query_params = {}
    if status:
        query_params['status'] = status
    if search:
        query_params['search'] = search
    if client_id:
        query_params['client_id'] = client_id
    
    # Repository handles query building and delegates pagination
    result = await project_service.get_projects_list_service(db, pagination, status, search, client_id)
    
    logger.info(f"Returned {len(result.results)} projects out of {result.meta.total} total")
    response_data = ResponseFormatter.success_response(data=result)
    return JSONResponse(content=response_data.to_dict(), status_code=200)


@router.get("/projects/{project_id}")
async def get_project_by_id(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Get project by ID (Admin only)
    
    Args:
        project_id: Project ID
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Project data
    """
    try:
        logger.info(f"Admin {current_user.username} requesting project ID: {project_id}")
        
        # Service handles business logic and database operations
        project = await project_service.get_project_by_id_service(db, project_id)
        
        if not project:
            response_data = ResponseFormatter.error_response(
                message="Project not found"
            )
            return JSONResponse(content=response_data.to_dict(), status_code=404)
        
        response_data = ResponseFormatter.success_response(
            data=project,
            message="Project retrieved successfully"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=200)
        
    except Exception as e:
        logger.error(f"Error retrieving project {project_id}: {e}")
        response_data = ResponseFormatter.error_response(
            message="Internal server error"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=500)


@router.put("/projects/{project_id}")
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Update project information (Admin only)
    
    Args:
        project_id: Project ID to update
        project_data: Project update data
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Updated project data
    """
    try:
        logger.info(f"Admin {current_user.username} updating project ID: {project_id}")
        
        # Service handles business logic and database operations
        updated_project = await project_service.update_project_service(db, project_id, project_data)
        
        if not updated_project:
            response_data = ResponseFormatter.error_response(
                message="Project not found"
            )
            return JSONResponse(content=response_data.to_dict(), status_code=404)
        
        response_data = ResponseFormatter.success_response(
            data=updated_project,
            message="Project updated successfully"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=200)
        
    except ValueError as e:
        logger.warning(f"Validation error updating project {project_id}: {e}")
        response_data = ResponseFormatter.error_response(
            message=str(e)
        )
        return JSONResponse(content=response_data.to_dict(), status_code=400)
        
    except Exception as e:
        logger.error(f"Error updating project {project_id}: {e}")
        response_data = ResponseFormatter.error_response(
            message="Internal server error"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=500)


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Soft delete project (Admin only)
    
    Args:
        project_id: Project ID to delete
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Success message
    """
    try:
        logger.info(f"Admin {current_user.username} deleting project ID: {project_id}")
        
        # Service handles business logic and database operations
        success = await project_service.delete_project_service(db, project_id)
        
        if not success:
            response_data = ResponseFormatter.error_response(
                message="Project not found"
            )
            return JSONResponse(content=response_data.to_dict(), status_code=404)
        
        response_data = ResponseFormatter.success_response(
            data={"project_id": project_id},
            message="Project deleted successfully"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=200)
        
    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {e}")
        response_data = ResponseFormatter.error_response(
            message="Internal server error"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=500) 