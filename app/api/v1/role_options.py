from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.role_options import RoleOptionsCreate, RoleOptionsUpdate, RoleOptionsRead, RoleOptionsListResponse
from app.schemas.user import UserRead
from app.services import role_options as role_options_service
from app.db.session import get_db
from app.dependencies.authorization import require_roles
from app.core.roles import UserRole
from app.utils.response_formatter import ResponseFormatter
from app.core.logger import logger

router = APIRouter()


@router.post("/role-options")
async def create_role_option(
    role_option_data: RoleOptionsCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Create a new role option (Admin only)
    
    Args:
        role_option_data: Role option creation data
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Created role option data
    """
    try:
        logger.info(f"Admin {current_user.username} creating new role option: {role_option_data.name}")
        
        # Service handles business logic and database operations
        new_role_option = await role_options_service.create_role_option_service(db, role_option_data)
        
        response_data = ResponseFormatter.success_response(
            data=new_role_option,
            message="Role option created successfully"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=201)
        
    except ValueError as e:
        logger.warning(f"Validation error creating role option: {e}")
        response_data = ResponseFormatter.error_response(
            message=str(e)
        )
        return JSONResponse(content=response_data.to_dict(), status_code=400)
        
    except Exception as e:
        logger.error(f"Error creating role option: {e}")
        response_data = ResponseFormatter.error_response(
            message="Internal server error"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=500)


@router.get("/role-options")
async def get_role_options_list(
    status: str = Query(default=None, description="Filter by role option status"),
    option_type: str = Query(default=None, description="Filter by option type"),
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Get list of role options with optional status and option_type filtering (Admin only)
    
    Args:
        status: Optional status filter
        option_type: Optional option_type filter
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        List of role options with total count
    """
    try:
        filter_info = []
        if status:
            filter_info.append(f"status '{status}'")
        if option_type:
            filter_info.append(f"option_type '{option_type}'")
        
        filter_text = f" with {' and '.join(filter_info)}" if filter_info else ""
        logger.info(f"Admin {current_user.username} requesting role options list{filter_text}")
        
        # Service handles business logic and database operations
        role_options_response = await role_options_service.get_role_options_list_service(db, status, option_type)
        
        response_data = ResponseFormatter.success_response(
            data=role_options_response,
            message=f"Retrieved {role_options_response.total} role options"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=200)
        
    except Exception as e:
        logger.error(f"Error retrieving role options list: {e}")
        response_data = ResponseFormatter.error_response(
            message="Internal server error"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=500)


@router.put("/role-options/{role_option_id}")
async def update_role_option(
    role_option_id: int,
    role_option_data: RoleOptionsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Update role option information (Admin only)
    
    Args:
        role_option_id: Role option ID to update
        role_option_data: Role option update data
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Updated role option data
    """
    try:
        logger.info(f"Admin {current_user.username} updating role option ID: {role_option_id}")
        
        # Service handles business logic and database operations
        updated_role_option = await role_options_service.update_role_option_service(db, role_option_id, role_option_data)
        
        if not updated_role_option:
            response_data = ResponseFormatter.error_response(
                message="Role option not found"
            )
            return JSONResponse(content=response_data.to_dict(), status_code=404)
        
        response_data = ResponseFormatter.success_response(
            data=updated_role_option,
            message="Role option updated successfully"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=200)
        
    except ValueError as e:
        logger.warning(f"Validation error updating role option {role_option_id}: {e}")
        response_data = ResponseFormatter.error_response(
            message=str(e)
        )
        return JSONResponse(content=response_data.to_dict(), status_code=400)
        
    except Exception as e:
        logger.error(f"Error updating role option {role_option_id}: {e}")
        response_data = ResponseFormatter.error_response(
            message="Internal server error"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=500) 