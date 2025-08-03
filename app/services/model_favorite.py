from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_

from app.repository import model_favorite as model_favorite_repository
from app.models.model_favorite import ModelFavorite
from app.models.model import Model
from app.schemas.model_favorite import ModelFavoriteCreate
from app.utils.pagination import PaginationParams, PaginationHandler, PaginatedResponse
from app.core.exceptions import NotFoundException, ConflictException


async def add_to_favorites(db: AsyncSession, user_id: int, favorite_data: ModelFavoriteCreate) -> Dict[str, Any]:
    """Add a model to user's favorites"""
    # Check if already favorited (active record)
    existing_favorite = await model_favorite_repository.get_model_favorite_by_user_and_model(db, user_id, favorite_data.model_id)
    if existing_favorite:
        raise ConflictException("Model is already in favorites")

    # Check if there's a soft-deleted record to restore
    soft_deleted_favorite = await model_favorite_repository.get_soft_deleted_favorite(db, user_id, favorite_data.model_id)
    was_restored = soft_deleted_favorite is not None

    # Create favorite (will restore soft-deleted record if exists)
    favorite = await model_favorite_repository.create_model_favorite(db, user_id, favorite_data.model_id)
    
    return {
        "id": favorite.id,
        "user_id": favorite.user_id,
        "model_id": favorite.model_id,
        "created_at": favorite.created_at,
        "message": "Model restored to favorites successfully" if was_restored else "Model added to favorites successfully"
    }


async def remove_from_favorites_by_id(db: AsyncSession,  user_id: int, favorite_id: int) -> Dict[str, Any]:
    """Remove a specific favorite by its ID"""
    # Check if favorite exists and belongs to user
    favorite = await model_favorite_repository.get_model_favorite_by_id(db, favorite_id)
    if not favorite:
        raise NotFoundException("Favorite not found")
    
    if favorite.user_id != user_id:
        raise NotFoundException("You can only remove your own favorites")

    # Delete favorite
    success = await model_favorite_repository.delete_model_favorite_by_id(db, favorite_id)
    if not success:
        raise NotFoundException("Failed to remove favorite")

    return {
        "message": "Favorite removed successfully"
    }

async def get_user_favorites_paginated(
    db: AsyncSession, 
    user_id: int, 
    pagination: PaginationParams,
) -> PaginatedResponse:
    """Get user's favorites with pagination"""
    return await model_favorite_repository.get_user_favorites_paginated(
        db, user_id, pagination
    )