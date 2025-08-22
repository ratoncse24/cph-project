from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.fact_sheets import FactSheetRead, FactSheetUpdate, FactSheetStatusUpdate
from app.schemas.user import UserRead
from app.services import fact_sheets as fact_sheets_service
from app.db.session import get_db
from app.dependencies.authorization import require_roles
from app.core.roles import UserRole
from app.utils.response_formatter import ResponseFormatter
from app.core.logger import logger

router = APIRouter()


@router.get("/fact-sheets/{project_id}")
async def get_fact_sheet_by_project_id(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(require_roles([UserRole.ADMIN, UserRole.PROJECT]))
):
    """
    Get fact sheet by project ID (Admin and Project roles)
    
    PROJECT role users can only access fact sheets for their own project.
    ADMIN role users can access any fact sheet.
    
    Args:
        project_id: Project ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Fact sheet data
    """
    try:
        logger.info(f"User {current_user.username} requesting fact sheet for project ID: {project_id}")
        
        # Service handles business logic and database operations with role-based access control
        fact_sheet = await fact_sheets_service.get_fact_sheet_by_project_id_service(
            db, 
            project_id, 
            current_user.role_name,
            current_user.username
        )
        
        if not fact_sheet:
            response_data = ResponseFormatter.error_response(
                message="Fact sheet not found"
            )
            return JSONResponse(content=response_data.to_dict(), status_code=404)
        
        response_data = ResponseFormatter.success_response(
            data=fact_sheet,
            message="Fact sheet retrieved successfully"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=200)
        
    except ValueError as e:
        logger.warning(f"Access denied for user {current_user.username} to fact sheet project {project_id}: {e}")
        response_data = ResponseFormatter.error_response(
            message=str(e)
        )
        return JSONResponse(content=response_data.to_dict(), status_code=403)
        
    except Exception as e:
        logger.error(f"Error retrieving fact sheet for project {project_id}: {e}")
        response_data = ResponseFormatter.error_response(
            message="Internal server error"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=500)


@router.put("/fact-sheets/{project_id}")
async def update_fact_sheet(
    project_id: int,
    fact_sheet_data: FactSheetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(require_roles([UserRole.ADMIN, UserRole.PROJECT]))
):
    """
    Update fact sheet information (Admin and Project roles with different permissions)
    
    PROJECT role users can only update fact sheets for their own project and cannot update approved fact sheets.
    ADMIN role users can update any fact sheet but can only modify status fields.
    
    Args:
        project_id: Project ID
        fact_sheet_data: Fact sheet update data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated fact sheet data
    """
    try:
        logger.info(f"User {current_user.username} updating fact sheet for project ID: {project_id}")
        
        # Service handles business logic and database operations with role-based validation and access control
        updated_fact_sheet = await fact_sheets_service.update_fact_sheet_service(
            db, project_id, fact_sheet_data, current_user.role_name, current_user.username, current_user.id
        )
        
        if not updated_fact_sheet:
            response_data = ResponseFormatter.error_response(
                message="Fact sheet not found"
            )
            return JSONResponse(content=response_data.to_dict(), status_code=404)
        
        response_data = ResponseFormatter.success_response(
            data=updated_fact_sheet,
            message="Fact sheet updated successfully"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=200)
        
    except ValueError as e:
        logger.warning(f"Validation error updating fact sheet for project {project_id}: {e}")
        response_data = ResponseFormatter.error_response(
            message=str(e)
        )
        return JSONResponse(content=response_data.to_dict(), status_code=400)
        
    except Exception as e:
        logger.error(f"Error updating fact sheet for project {project_id}: {e}")
        response_data = ResponseFormatter.error_response(
            message="Internal server error"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=500)
