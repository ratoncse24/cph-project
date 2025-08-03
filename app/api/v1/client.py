from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.client import ClientCreate, ClientUpdate, ClientRead, ClientListResponse
from app.schemas.user import UserRead
from app.services import client as client_service
from app.db.session import get_db
from app.dependencies.authorization import require_roles
from app.core.roles import UserRole
from app.utils.response_formatter import ResponseFormatter
from app.core.logger import logger

router = APIRouter()


@router.post("/clients")
async def create_client(
    client_data: ClientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Create a new client (Admin only)
    
    Args:
        client_data: Client creation data
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Created client data
    """
    try:
        logger.info(f"Admin {current_user.username} creating new client: {client_data.name}")
        
        # Service handles business logic and database operations
        new_client = await client_service.create_client_service(db, client_data)
        
        response_data = ResponseFormatter.success_response(
            data=new_client,
            message="Client created successfully"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=201)
        
    except ValueError as e:
        logger.warning(f"Validation error creating client: {e}")
        response_data = ResponseFormatter.error_response(
            message=str(e)
        )
        return JSONResponse(content=response_data.to_dict(), status_code=400)
        
    except Exception as e:
        logger.error(f"Error creating client: {e}")
        response_data = ResponseFormatter.error_response(
            message="Internal server error"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=500)


@router.get("/clients")
async def get_clients_list(
    status: str = Query(default=None, description="Filter by client status"),
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Get list of clients with optional status filtering (Admin only)
    
    Args:
        status: Optional status filter
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        List of clients with total count
    """
    try:
        logger.info(f"Admin {current_user.username} requesting clients list" + (f" with status '{status}'" if status else ""))
        
        # Service handles business logic and database operations
        clients_response = await client_service.get_clients_list_service(db, status)
        
        response_data = ResponseFormatter.success_response(
            data=clients_response,
            message=f"Retrieved {clients_response.total} clients"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=200)
        
    except Exception as e:
        logger.error(f"Error retrieving clients list: {e}")
        response_data = ResponseFormatter.error_response(
            message="Internal server error"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=500)


@router.put("/clients/{client_id}")
async def update_client(
    client_id: int,
    client_data: ClientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Update client information (Admin only)
    
    Args:
        client_id: Client ID to update
        client_data: Client update data
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Updated client data
    """
    try:
        logger.info(f"Admin {current_user.username} updating client ID: {client_id}")
        
        # Service handles business logic and database operations
        updated_client = await client_service.update_client_service(db, client_id, client_data)
        
        if not updated_client:
            response_data = ResponseFormatter.error_response(
                message="Client not found"
            )
            return JSONResponse(content=response_data.to_dict(), status_code=404)
        
        response_data = ResponseFormatter.success_response(
            data=updated_client,
            message="Client updated successfully"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=200)
        
    except ValueError as e:
        logger.warning(f"Validation error updating client {client_id}: {e}")
        response_data = ResponseFormatter.error_response(
            message=str(e)
        )
        return JSONResponse(content=response_data.to_dict(), status_code=400)
        
    except Exception as e:
        logger.error(f"Error updating client {client_id}: {e}")
        response_data = ResponseFormatter.error_response(
            message="Internal server error"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=500) 