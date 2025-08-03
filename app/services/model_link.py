from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from app.repository import model_link as model_link_crud
from app.repository import model as model_crud
from app.schemas.model_link import (
    ModelLinkCreate, ModelLinkUpdate, ModelLinkRead, ModelLinkPublicRead
)
from app.utils.pagination import PaginationParams, PaginatedResponse
from app.core.logger import logger


async def create_model_link(
    db: AsyncSession,
    model_link_data: ModelLinkCreate,
    created_by_user_id: int
) -> Optional[ModelLinkRead]:
    """Create a new model link with validation"""
    try:
        # Validate that all model IDs exist
        # for model_id in model_link_data.model_ids:
        #     model = await model_crud.get_model_by_id(db, model_id)
        #     if not model:
        #         raise ValueError(f"Model with ID {model_id} does not exist")
        #     if model.deleted_at is not None:
        #         raise ValueError(f"Model with ID {model_id} is deleted")
        
        # Create the model link
        model_link = await model_link_crud.create_model_link(
            db=db,
            model_link_data=model_link_data,
            created_by_user_id=created_by_user_id
        )
        
        if not model_link:
            raise ValueError("Failed to create model link")
        
        # Convert to response schema
        return model_link_to_dict(model_link)
        
    except ValueError as e:
        logger.warning(f"Model link creation failed - validation error: {e}")
        raise e
    except Exception as e:
        logger.error(f"Model link creation failed - unexpected error: {e}")
        raise ValueError("Failed to create model link")


async def get_model_link_by_id(
    db: AsyncSession,
    model_link_id: int
) -> Optional[Dict[str, Any]]:
    """Get model link by ID"""
    try:
        model_link = await model_link_crud.get_model_link_by_id(db, model_link_id)
        if not model_link:
            return None
        
        return model_link_to_dict(model_link)
        
    except Exception as e:
        logger.error(f"Error getting model link by ID {model_link_id}: {e}")
        return None


async def get_model_link_by_short_code(
    db: AsyncSession,
    short_code: str
) -> Optional[Dict[str, Any]]:
    """Get model link by short code"""
    try:
        model_link = await model_link_crud.get_model_link_by_short_code(db, short_code)
        if not model_link:
            return None
        
        return model_link_to_dict(model_link)
        
    except Exception as e:
        logger.error(f"Error getting model link by short code {short_code}: {e}")
        return None


async def delete_model_link(
    db: AsyncSession,
    model_link_id: int
) -> bool:
    """Delete a model link"""
    try:
        # Check if model link exists
        existing_link = await model_link_crud.get_model_link_by_id(db, model_link_id)
        if not existing_link:
            raise ValueError(f"Model link with ID {model_link_id} does not exist")
        
        success = await model_link_crud.delete_model_link(db, model_link_id)
        if not success:
            raise ValueError("Failed to delete model link")
        
        return True
        
    except ValueError as e:
        logger.warning(f"Model link deletion failed - validation error: {e}")
        raise e
    except Exception as e:
        logger.error(f"Model link deletion failed - unexpected error: {e}")
        raise ValueError("Failed to delete model link")


async def get_model_links_paginated(
    db: AsyncSession,
    pagination: PaginationParams,
    created_by_user_id: Optional[int] = None,
    status: Optional[str] = None
) -> PaginatedResponse:
    """Get paginated list of model links"""
    try:
        return await model_link_crud.get_model_links_paginated(
            db=db,
            pagination=pagination,
            created_by_user_id=created_by_user_id,
            status=status
        )
        
    except Exception as e:
        logger.error(f"Error getting paginated model links: {e}")
        from app.utils.pagination import PaginationHandler
        # Return empty paginated response
        meta = PaginationHandler.create_meta(pagination.page, pagination.size, 0)
        return PaginatedResponse(results=[], meta=meta)


async def get_public_model_link_data(
    db: AsyncSession,
    short_code: str
) -> Optional[ModelLinkPublicRead]:
    """Get public model link data for sharing"""
    try:
        # Get the model link
        model_link = await model_link_crud.get_model_link_by_short_code(db, short_code)
        if not model_link:
            return None
        
        # Get model data based on data_to_share configuration
        models_data = await model_link_crud.get_models_for_public_link(db, model_link)
        
        return ModelLinkPublicRead(
            short_code=model_link.short_code,
            data_to_share=model_link.data_to_share,
            models=models_data
        )
        
    except Exception as e:
        logger.error(f"Error getting public model link data for {short_code}: {e}")
        return None


def model_link_to_dict(model_link) -> Dict[str, Any]:
    """Convert model link to dictionary"""
    return {
        'id': model_link.id,
        'short_code': model_link.short_code,
        'created_by_user_id': model_link.created_by_user_id,
        'data_to_share': model_link.data_to_share,
        'status': model_link.status,
        'created_at': model_link.created_at,
        'updated_at': model_link.updated_at,
        'deleted_at': model_link.deleted_at
    } 