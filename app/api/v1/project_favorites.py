from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.project_favorites import ProjectFavoritesCreate, ProjectFavoritesRead
from app.schemas.user import UserRead
from app.services import project_favorites as project_favorites_service
from app.db.session import get_db
from app.dependencies.authorization import require_roles
from app.core.roles import UserRole
from app.utils.response_formatter import ResponseFormatter
from app.core.logger import logger


router = APIRouter()


@router.post("/project-favorites", status_code=status.HTTP_201_CREATED)
async def create_favorite(
    favorite_data: ProjectFavoritesCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Create a new favorite (Admin only)
    
    Args:
        favorite_data: Favorite creation data
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Standardized API response with created favorite
    """
    logger.info(f"Admin {current_user.username} creating favorite for {favorite_data.favoritable_type.value} {favorite_data.favoritable_id}")
    
    try:
        favorite = await project_favorites_service.create_favorite(db, favorite_data, current_user.id)
        
        response_data = ResponseFormatter.success_response(
            data=ProjectFavoritesRead.model_validate(favorite),
            message="Favorite created successfully"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_201_CREATED)
        
    except ValueError as e:
        logger.warning(f"Validation error creating favorite: {e}")
        response_data = ResponseFormatter.error_response(
            message=str(e)
        )
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error creating favorite: {e}")
        response_data = ResponseFormatter.error_response(
            message="Failed to create favorite"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/project-favorites")
async def get_favorites_list(
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Get all favorites for the current user (Admin only)
    
    Args:
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Standardized API response with list of favorites
    """
    logger.info(f"Admin {current_user.username} requesting favorites list")
    
    try:
        # Service handles business logic and delegates to repository
        result = await project_favorites_service.get_favorites_list(db, current_user.id)
        
        logger.info(f"Returned {len(result.results)} favorites for user {current_user.id}")
        response_data = ResponseFormatter.success_response(data=result)
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error retrieving favorites list: {e}")
        response_data = ResponseFormatter.error_response(
            message="Failed to retrieve favorites list"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/project-favorites/{favorite_id}")
async def get_favorite_by_id(
    favorite_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Get a specific favorite by ID (Admin only)
    
    Args:
        favorite_id: Favorite ID
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Standardized API response with favorite details
    """
    logger.info(f"Admin {current_user.username} requesting favorite {favorite_id}")
    
    try:
        favorite = await project_favorites_service.get_favorite_by_id(db, favorite_id, current_user.id)
        
        if not favorite:
            response_data = ResponseFormatter.error_response(
                message="Favorite not found"
            )
            return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_404_NOT_FOUND)
        
        response_data = ResponseFormatter.success_response(data=favorite)
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error retrieving favorite {favorite_id}: {e}")
        response_data = ResponseFormatter.error_response(
            message="Failed to retrieve favorite"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.delete("/project-favorites/{favorite_id}")
async def delete_favorite_by_id(
    favorite_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Delete a favorite by ID (Admin only)
    
    Args:
        favorite_id: ID of the favorite to delete
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Standardized API response
    """
    logger.info(f"Admin {current_user.username} deleting favorite: {favorite_id}")
    
    try:
        success = await project_favorites_service.delete_favorite_by_id(db, favorite_id, current_user.id)
        
        if not success:
            response_data = ResponseFormatter.error_response(
                message="Favorite not found"
            )
            return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_404_NOT_FOUND)
        
        response_data = ResponseFormatter.success_response(
            message="Favorite deleted successfully"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error deleting favorite: {e}")
        response_data = ResponseFormatter.error_response(
            message="Failed to delete favorite"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.delete("/project-favorites/{favoritable_type}/{favoritable_id}")
async def delete_favorite(
    favoritable_type: str,
    favoritable_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Delete a favorite (Admin only) - Legacy endpoint
    
    Args:
        favoritable_type: Type of favorited item (Project or Role)
        favoritable_id: ID of the favorited item
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Standardized API response
    """
    logger.info(f"Admin {current_user.username} deleting favorite: {favoritable_type} {favoritable_id}")
    
    try:
        success = await project_favorites_service.delete_favorite(db, current_user.id, favoritable_type, favoritable_id)
        
        if not success:
            response_data = ResponseFormatter.error_response(
                message="Favorite not found"
            )
            return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_404_NOT_FOUND)
        
        response_data = ResponseFormatter.success_response(
            message="Favorite deleted successfully"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error deleting favorite: {e}")
        response_data = ResponseFormatter.error_response(
            message="Failed to delete favorite"
        )
        return JSONResponse(content=response_data.to_dict(), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) 