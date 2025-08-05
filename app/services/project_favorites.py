from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.project_favorites import ProjectFavoritesCreate, ProjectFavoritesReadWithRelations, ProjectFavoritesListResponse
from app.repository import project_favorites as project_favorites_repo
from app.core.logger import logger


async def create_favorite(db: AsyncSession, favorite_data: ProjectFavoritesCreate, user_id: int):
    """
    Create a new favorite with business logic validation
    
    Args:
        db: Database session
        favorite_data: Favorite creation data
        user_id: ID of the user creating the favorite
        
    Returns:
        Created favorite
        
    Raises:
        ValueError: If project/role doesn't exist or validation fails
    """
    try:
        # Business logic: Check if the item to be favorited exists
        if favorite_data.favoritable_type.value == "Project":
            item_exists = await project_favorites_repo.check_project_exists(db, favorite_data.favoritable_id)
            if not item_exists:
                raise ValueError(f"Project with ID {favorite_data.favoritable_id} does not exist")
        elif favorite_data.favoritable_type.value == "Role":
            item_exists = await project_favorites_repo.check_role_exists(db, favorite_data.favoritable_id)
            if not item_exists:
                raise ValueError(f"Role with ID {favorite_data.favoritable_id} does not exist")
        
        # Business logic: Check if favorite already exists
        favorite_exists = await project_favorites_repo.check_favorite_exists(
            db, user_id, favorite_data.favoritable_type.value, favorite_data.favoritable_id
        )
        if favorite_exists:
            raise ValueError(f"Favorite already exists for {favorite_data.favoritable_type.value} {favorite_data.favoritable_id}")
        
        # Create the favorite
        favorite = await project_favorites_repo.create_favorite(db, favorite_data, user_id)
        
        logger.info(f"Favorite created successfully by user {user_id}: {favorite.favoritable_type} {favorite.favoritable_id}")
        return favorite
        
    except Exception as e:
        logger.error(f"Error in create_favorite service: {e}")
        raise


async def get_favorite_by_id(db: AsyncSession, favorite_id: int, user_id: int) -> Optional[ProjectFavoritesReadWithRelations]:
    """
    Get a favorite by ID with business logic validation
    
    Args:
        db: Database session
        favorite_id: Favorite ID
        user_id: ID of the user (for authorization)
        
    Returns:
        Favorite with relations or None if not found
    """
    try:
        favorite = await project_favorites_repo.get_favorite_by_id(db, favorite_id)
        if not favorite:
            logger.warning(f"Favorite not found: {favorite_id}")
            return None
        
        # Check if the favorite belongs to the user
        if favorite.user_id != user_id:
            logger.warning(f"Favorite {favorite_id} does not belong to user {user_id}")
            return None
        
        # Convert to response schema with relations
        return ProjectFavoritesReadWithRelations.model_validate(favorite)
        
    except Exception as e:
        logger.error(f"Error in get_favorite_by_id service: {e}")
        return None


async def delete_favorite_by_id(db: AsyncSession, favorite_id: int, user_id: int) -> bool:
    """
    Delete a favorite by ID with business logic validation
    
    Args:
        db: Database session
        favorite_id: ID of the favorite to delete
        user_id: ID of the user (for authorization)
        
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        # Check if favorite exists and belongs to the user
        favorite = await project_favorites_repo.get_favorite_by_id(db, favorite_id)
        if not favorite:
            logger.warning(f"Favorite not found for deletion: id={favorite_id}")
            return False
        
        if favorite.user_id != user_id:
            logger.warning(f"Favorite {favorite_id} does not belong to user {user_id}")
            return False
        
        # Delete the favorite
        success = await project_favorites_repo.delete_favorite_by_id(db, favorite_id, user_id)
        
        if success:
            logger.info(f"Favorite deleted successfully: {favorite.favoritable_type} {favorite.favoritable_id} for user {user_id}")
        else:
            logger.error(f"Failed to delete favorite: {favorite_id} for user {user_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error in delete_favorite_by_id service: {e}")
        return False


async def delete_favorite(db: AsyncSession, user_id: int, favoritable_type: str, favoritable_id: int) -> bool:
    """
    Delete a favorite with business logic validation (legacy method)
    
    Args:
        db: Database session
        user_id: ID of the user
        favoritable_type: Type of favorited item (Project or Role)
        favoritable_id: ID of the favorited item
        
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        # Check if favorite exists
        favorite_exists = await project_favorites_repo.check_favorite_exists(db, user_id, favoritable_type, favoritable_id)
        if not favorite_exists:
            logger.warning(f"Favorite not found for deletion: user_id={user_id}, type={favoritable_type}, id={favoritable_id}")
            return False
        
        # Delete the favorite
        success = await project_favorites_repo.delete_favorite(db, user_id, favoritable_type, favoritable_id)
        
        if success:
            logger.info(f"Favorite deleted successfully: {favoritable_type} {favoritable_id} for user {user_id}")
        else:
            logger.error(f"Failed to delete favorite: {favoritable_type} {favoritable_id} for user {user_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error in delete_favorite service: {e}")
        return False


async def get_favorites_list(db: AsyncSession, user_id: int) -> ProjectFavoritesListResponse:
    """
    Get all favorites for a specific user
    
    Args:
        db: Database session
        user_id: ID of the user
        
    Returns:
        List of favorites with related data
    """
    try:
        result = await project_favorites_repo.get_favorites_by_user(db, user_id)
        
        logger.info(f"Retrieved {len(result.results)} favorites for user {user_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error in get_favorites_list service: {e}")
        raise 