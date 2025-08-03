from fastapi import APIRouter, Depends,Query
from fastapi.responses import JSONResponse
from app.schemas.user import (UserRead)

from app.repository.user import (get_users_paginated)
from app.db.session import get_db

from app.dependencies.authorization import require_roles
from app.core.roles import UserRole
from app.utils.pagination import PaginationParams
from app.utils.response_formatter import ResponseFormatter
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logger import logger


router = APIRouter()


@router.get("/users")
async def get_users_list(
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=20, ge=1, le=100, description="results per page"),
    search: str = Query(default=None, description="Search term for username, email, or role"),
    role: str = Query(default=None, description="Filter by role"),
    status: str = Query(default=None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Get paginated list of users (Admin only)
    
    Clean API layer - separates pagination from filtering logic
    
    Args:
        page: Page number (starts from 1)
        size: Number of results per page (max 100)
        search: Optional search term for filtering users
        role: Optional role filter
        status: Optional status filter
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Standardized API response with paginated list of users
    """
    logger.info(f"Admin {current_user.username} requesting users list - page: {page}, size: {size}")
    
    # Separate pagination parameters from query filters
    pagination = PaginationParams(page=page, size=size)
    
    # Build query parameters dict for filtering
    query_params = {}
    if search:
        query_params['search'] = search
    if role:
        query_params['role'] = role
    if status:
        query_params['status'] = status
    
    # Repository handles query building and delegates pagination
    result = await get_users_paginated(db, pagination, query_params)
    
    logger.info(f"Returned {len(result.results)} users out of {result.meta.total} total")
    response_data = ResponseFormatter.success_response(data=result)
    return JSONResponse(content=response_data.to_dict(), status_code=200)
