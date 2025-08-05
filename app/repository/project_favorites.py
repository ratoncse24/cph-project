from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from typing import Optional, List
import logging

from app.models.project_favorites import ProjectFavorites
from app.models.user import User
from app.models.project import Project
from app.models.role import Role
from app.schemas.project_favorites import ProjectFavoritesCreate, ProjectFavoritesReadWithRelations, ProjectFavoritesListResponse

logger = logging.getLogger(__name__)


async def create_favorite(db: AsyncSession, favorite_data: ProjectFavoritesCreate, user_id: int) -> ProjectFavorites:
    """Create a new favorite"""
    try:
        favorite = ProjectFavorites(
            user_id=user_id,
            favoritable_type=favorite_data.favoritable_type.value,
            favoritable_id=favorite_data.favoritable_id
        )
        db.add(favorite)
        await db.commit()
        await db.refresh(favorite)
        
        logger.info(f"Created favorite: {favorite.favoritable_type} {favorite.favoritable_id} for user {user_id}")
        return favorite
        
    except Exception as e:
        logger.error(f"Error creating favorite: {e}")
        await db.rollback()
        raise


async def get_favorite_by_id(db: AsyncSession, favorite_id: int) -> Optional[ProjectFavorites]:
    """Get favorite by ID"""
    try:
        result = await db.execute(
            select(ProjectFavorites).where(ProjectFavorites.id == favorite_id)
        )
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error fetching favorite by ID {favorite_id}: {e}")
        return None


async def delete_favorite_by_id(db: AsyncSession, favorite_id: int, user_id: int) -> bool:
    """Delete a favorite by ID"""
    try:
        result = await db.execute(
            select(ProjectFavorites).where(
                and_(
                    ProjectFavorites.id == favorite_id,
                    ProjectFavorites.user_id == user_id
                )
            )
        )
        favorite = result.scalar_one_or_none()
        
        if not favorite:
            logger.warning(f"Favorite not found for deletion: id={favorite_id}, user_id={user_id}")
            return False
        
        await db.delete(favorite)
        await db.commit()
        
        logger.info(f"Favorite deleted successfully: {favorite.favoritable_type} {favorite.favoritable_id} for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting favorite: {e}")
        await db.rollback()
        return False


async def delete_favorite(db: AsyncSession, user_id: int, favoritable_type: str, favoritable_id: int) -> bool:
    """Delete a favorite (legacy method)"""
    try:
        result = await db.execute(
            select(ProjectFavorites).where(
                and_(
                    ProjectFavorites.user_id == user_id,
                    ProjectFavorites.favoritable_type == favoritable_type,
                    ProjectFavorites.favoritable_id == favoritable_id
                )
            )
        )
        favorite = result.scalar_one_or_none()
        
        if not favorite:
            logger.warning(f"Favorite not found for deletion: user_id={user_id}, type={favoritable_type}, id={favoritable_id}")
            return False
        
        await db.delete(favorite)
        await db.commit()
        
        logger.info(f"Favorite deleted successfully: {favorite.favoritable_type} {favorite.favoritable_id} for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting favorite: {e}")
        await db.rollback()
        return False


async def get_favorites_by_user(db: AsyncSession, user_id: int) -> ProjectFavoritesListResponse:
    """Get all favorites for a specific user"""
    try:
        # Build query with joins for related data
        query = select(
            ProjectFavorites,
            User.username.label('user_username'),
            User.name.label('user_name'),
            Project.name.label('project_name'),
            Role.name.label('role_name')
        ).join(
            User, ProjectFavorites.user_id == User.id
        ).outerjoin(
            Project, and_(
                ProjectFavorites.favoritable_type == 'Project',
                ProjectFavorites.favoritable_id == Project.id
            )
        ).outerjoin(
            Role, and_(
                ProjectFavorites.favoritable_type == 'Role',
                ProjectFavorites.favoritable_id == Role.id
            )
        ).where(ProjectFavorites.user_id == user_id)
        
        result = await db.execute(query)
        favorites = result.all()
        
        # Convert to response schema
        results = []
        for favorite in favorites:
            favorite_dict = {
                'id': favorite.ProjectFavorites.id,
                'user_id': favorite.ProjectFavorites.user_id,
                'favoritable_type': favorite.ProjectFavorites.favoritable_type,
                'favoritable_id': favorite.ProjectFavorites.favoritable_id,
                'favorited_at': favorite.ProjectFavorites.favorited_at,
                'user_username': favorite.user_username,
                'user_name': favorite.user_name,
                'project_name': favorite.project_name if favorite.ProjectFavorites.favoritable_type == 'Project' else None,
                'role_name': favorite.role_name if favorite.ProjectFavorites.favoritable_type == 'Role' else None
            }
            results.append(ProjectFavoritesReadWithRelations(**favorite_dict))
        
        return ProjectFavoritesListResponse(results=results, total=len(results))
        
    except Exception as e:
        logger.error(f"Error fetching favorites for user {user_id}: {e}")
        return ProjectFavoritesListResponse(results=[], total=0)


async def check_favorite_exists(db: AsyncSession, user_id: int, favoritable_type: str, favoritable_id: int) -> bool:
    """Check if a favorite exists"""
    try:
        result = await db.execute(
            select(ProjectFavorites).where(
                and_(
                    ProjectFavorites.user_id == user_id,
                    ProjectFavorites.favoritable_type == favoritable_type,
                    ProjectFavorites.favoritable_id == favoritable_id
                )
            )
        )
        return result.scalar_one_or_none() is not None
    except Exception as e:
        logger.error(f"Error checking favorite existence: {e}")
        return False


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