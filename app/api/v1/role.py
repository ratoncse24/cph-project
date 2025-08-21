from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.role import RoleCreate, RoleUpdate, RoleReadWithRelations
from app.schemas.user import UserRead
from app.services import role as role_service
from app.db.session import get_db
from app.dependencies.authorization import require_roles
from app.core.roles import UserRole
from app.utils.pagination import PaginationParams
from app.utils.response_formatter import ResponseFormatter
from app.core.logger import logger


router = APIRouter()


@router.post("/roles", status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Create a new role (Admin only)
    
    Args:
        role_data: Role creation data
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Standardized API response with created role
    """
    logger.info(f"Admin {current_user.username} creating role for project {role_data.project_id}")
    
    try:
        role = await role_service.create_role(db, role_data)
        
        response_data = ResponseFormatter.success_response(
            data=RoleReadWithRelations.model_validate(role),
            message="Role created successfully"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_201_CREATED)
        
    except ValueError as e:
        logger.warning(f"Validation error creating role: {e}")
        response_data = ResponseFormatter.error_response(
            message=str(e)
        )
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error creating role: {e}")
        response_data = ResponseFormatter.error_response(
            message="Failed to create role"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/roles")
async def get_roles_list(
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=20, ge=1, le=100, description="Results per page"),
    search: str = Query(default=None, description="Search term for name, gender, ethnicity, language, category, hair_color, or project name"),
    project_id: int = Query(default=None, description="Filter by project ID"),
    status: str = Query(default=None, description="Filter by status"),
    gender: str = Query(default=None, description="Filter by gender"),
    category: str = Query(default=None, description="Filter by category"),
    age_from: int = Query(default=None, ge=0, le=150, description="Filter by minimum age"),
    age_to: int = Query(default=None, ge=0, le=150, description="Filter by maximum age"),
    height_from: float = Query(default=None, ge=0, le=300, description="Filter by minimum height (cm)"),
    height_to: float = Query(default=None, ge=0, le=300, description="Filter by maximum height (cm)"),
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(require_roles([UserRole.ADMIN, UserRole.PROJECT]))
):
    """
    Get paginated list of roles with filtering and search
    
    PROJECT role users can only see roles for their own project.
    ADMIN role users can see roles for any project.
    
    Args:
        page: Page number (starts from 1)
        size: Number of results per page (max 100)
        search: Optional search term for filtering roles
        project_id: Optional project ID filter (ignored for PROJECT role users)
        status: Optional status filter
        gender: Optional gender filter
        category: Optional category filter
        age_from: Optional minimum age filter
        age_to: Optional maximum age filter
        height_from: Optional minimum height filter (cm)
        height_to: Optional maximum height filter (cm)
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Standardized API response with paginated list of roles
    """
    logger.info(f"User {current_user.username} requesting roles list - page: {page}, size: {size}")
    
    # Separate pagination parameters from query filters
    pagination = PaginationParams(page=page, size=size)
    
    # Build query parameters dict for filtering
    query_params = {}
    if search:
        query_params['search'] = search
    if project_id:
        query_params['project_id'] = project_id
    if status:
        query_params['status'] = status
    if gender:
        query_params['gender'] = gender
    if category:
        query_params['category'] = category
    if age_from is not None:
        query_params['age_from'] = age_from
    if age_to is not None:
        query_params['age_to'] = age_to
    if height_from is not None:
        query_params['height_from'] = height_from
    if height_to is not None:
        query_params['height_to'] = height_to
    
    try:
        # Service handles business logic and delegates to repository with role-based access control
        result = await role_service.get_roles_list(
            db, 
            pagination, 
            query_params,
            current_user.role_name,
            current_user.username
        )
        
        logger.info(f"Returned {len(result.results)} roles out of {result.meta.total} total")
        response_data = ResponseFormatter.success_response(data=result)
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error retrieving roles list: {e}")
        response_data = ResponseFormatter.error_response(
            message="Failed to retrieve roles list"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/roles/{role_id}")
async def get_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Get a specific role by ID (Admin only)
    
    Args:
        role_id: Role ID
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Standardized API response with role details
    """
    logger.info(f"Admin {current_user.username} requesting role {role_id}")
    
    try:
        role = await role_service.get_role(db, role_id)
        
        if not role:
            response_data = ResponseFormatter.error_response(
                message="Role not found"
            )
            return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_404_NOT_FOUND)
        
        response_data = ResponseFormatter.success_response(data=role)
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error retrieving role {role_id}: {e}")
        response_data = ResponseFormatter.error_response(
            message="Failed to retrieve role"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.put("/roles/{role_id}")
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Update a role (Admin only)
    
    Args:
        role_id: Role ID
        role_data: Role update data
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Standardized API response with updated role
    """
    logger.info(f"Admin {current_user.username} updating role {role_id}")
    
    try:
        updated_role = await role_service.update_role(db, role_id, role_data)
        
        if not updated_role:
            response_data = ResponseFormatter.error_response(
                message="Role not found"
            )
            return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_404_NOT_FOUND)
        
        response_data = ResponseFormatter.success_response(
            data=updated_role,
            message="Role updated successfully"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_200_OK)
        
    except ValueError as e:
        logger.warning(f"Validation error updating role: {e}")
        response_data = ResponseFormatter.error_response(
            message=str(e)
        )
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error updating role {role_id}: {e}")
        response_data = ResponseFormatter.error_response(
            message="Failed to update role"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.delete("/roles/{role_id}")
async def delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Delete a role (Admin only)
    
    Args:
        role_id: Role ID
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Standardized API response
    """
    logger.info(f"Admin {current_user.username} deleting role {role_id}")
    
    try:
        success = await role_service.delete_role(db, role_id)
        
        if not success:
            response_data = ResponseFormatter.error_response(
                message="Role not found"
            )
            return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_404_NOT_FOUND)
        
        response_data = ResponseFormatter.success_response(
            message="Role deleted successfully"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error deleting role {role_id}: {e}")
        response_data = ResponseFormatter.error_response(
            message="Failed to delete role"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


 