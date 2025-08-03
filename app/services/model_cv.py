from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.repository import model_cv as model_cv_crud
from app.schemas.model_cv import ModelCVCreate, ModelCVUpdate, ModelCVRead, ModelCVRead
from app.utils.pagination import PaginationParams, PaginatedResponse
from app.core.logger import logger


async def create_model_cv(
    db: AsyncSession,
    cv_data: ModelCVCreate
) -> Optional[ModelCVRead]:
    """
    Create a new model CV with business logic validation
    
    Args:
        db: Database session
        cv_data: CV creation data
        
    Returns:
        Created ModelCVRead object or None if creation fails
    """
    try:
        logger.info(f"Creating model CV for model {cv_data.model_id}")
        
        # Create the CV using repository
        cv = await model_cv_crud.create_model_cv(db, cv_data)
        
        if not cv:
            logger.warning(f"Failed to create model CV for model {cv_data.model_id}")
            return None
        
        # Convert to response schema
        cv_response = ModelCVRead.model_validate(cv)
        
        logger.info(f"✅ Successfully created model CV {cv.id} for model {cv_data.model_id}")
        return cv_response
        
    except Exception as e:
        logger.error(f"Error creating model CV: {e}")
        raise Exception("Model CV creation failed")


async def get_model_cvs_paginated(
    db: AsyncSession,
    model_id: int,
    pagination: PaginationParams
) -> PaginatedResponse[ModelCVRead]:
    """
    Get paginated list of CVs for a specific model with model information
    
    Args:
        db: Database session
        model_id: Model ID
        pagination: Pagination parameters
        
    Returns:
        PaginatedResponse with ModelCVRead objects
    """
    try:
        logger.info(f"Fetching paginated CVs for model: {model_id} (page: {pagination.page}, size: {pagination.size})")
        
        result = await model_cv_crud.get_model_cvs_paginated(db, model_id, pagination)
        
        logger.info(f"Found {len(result.results)} CVs for model {model_id} (page {pagination.page})")
        return result
        
    except Exception as e:
        logger.error(f"Error fetching paginated CVs for model {model_id}: {e}")
        raise Exception("Failed to fetch model CVs")


async def get_model_cv_by_id(
    db: AsyncSession,
    cv_id: int
) -> Optional[ModelCVRead]:
    """
    Get a specific model CV by ID
    
    Args:
        db: Database session
        cv_id: CV ID
        
    Returns:
        ModelCVRead object or None if not found
    """
    try:
        logger.debug(f"Fetching model CV: {cv_id}")
        
        cv = await model_cv_crud.get_model_cv_by_id(db, cv_id)
        
        if not cv:
            logger.warning(f"Model CV not found: {cv_id}")
            return None
        
        # Convert to response schema
        cv_response = ModelCVRead.model_validate(cv)
        
        logger.debug(f"Found model CV: {cv_id}")
        return cv_response
        
    except Exception as e:
        logger.error(f"Error fetching model CV {cv_id}: {e}")
        raise Exception("Failed to fetch model CV")


async def get_model_cv_with_model(
    db: AsyncSession,
    cv_id: int
) -> Optional[ModelCVRead]:
    """
    Get a model CV with model information
    
    Args:
        db: Database session
        cv_id: CV ID
        
    Returns:
        ModelCVRead object or None if not found
    """
    try:
        logger.debug(f"Fetching model CV with model info: {cv_id}")
        
        result = await model_cv_crud.get_model_cv_with_model(db, cv_id)
        
        if not result:
            logger.warning(f"Model CV with model not found: {cv_id}")
            return None
        
        cv, model = result
        
        # Create response with model information
        cv_response = ModelCVRead(
            id=cv.id,
            model_id=cv.model_id,
            title=cv.title,
            role=cv.role,
            date=cv.date,
            casting_category=cv.casting_category,
            note=cv.note,
            status=cv.status,
            created_at=cv.created_at,
            updated_at=cv.updated_at,
            deleted_at=cv.deleted_at
        )
        
        logger.debug(f"Found model CV with model: {cv_id}")
        return cv_response
        
    except Exception as e:
        logger.error(f"Error fetching model CV with model {cv_id}: {e}")
        raise Exception("Failed to fetch model CV with model")


async def update_model_cv(
    db: AsyncSession,
    cv_id: int,
    cv_data: ModelCVUpdate
) -> Optional[ModelCVRead]:
    """
    Update a model CV with business logic validation
    
    Args:
        db: Database session
        cv_id: CV ID to update
        cv_data: Update data
        
    Returns:
        Updated ModelCVRead object or None if not found
    """
    try:
        logger.info(f"Updating model CV: {cv_id}")
        
        # Update the CV using repository
        cv = await model_cv_crud.update_model_cv(db, cv_id, cv_data)
        
        if not cv:
            logger.warning(f"Failed to update model CV: {cv_id}")
            return None
        
        # Convert to response schema
        cv_response = ModelCVRead.model_validate(cv)
        
        logger.info(f"✅ Successfully updated model CV: {cv_id}")
        return cv_response
        
    except Exception as e:
        logger.error(f"Error updating model CV {cv_id}: {e}")
        raise Exception("Model CV update failed")


async def delete_model_cv(
    db: AsyncSession,
    cv_id: int
) -> bool:
    """
    Delete a model CV with business logic validation
    
    Args:
        db: Database session
        cv_id: CV ID to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Deleting model CV: {cv_id}")
        
        # Delete the CV using repository
        success = await model_cv_crud.delete_model_cv(db, cv_id)
        
        if not success:
            logger.warning(f"Failed to delete model CV: {cv_id}")
            return False
        
        logger.info(f"✅ Successfully deleted model CV: {cv_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting model CV {cv_id}: {e}")
        raise Exception("Model CV deletion failed")


async def get_cvs_by_model(
    db: AsyncSession,
    model_id: int
) -> List[ModelCVRead]:
    """
    Get all CVs for a specific model
    
    Args:
        db: Database session
        model_id: Model ID
        
    Returns:
        List of ModelCVRead objects
    """
    try:
        logger.debug(f"Fetching CVs for model: {model_id}")
        
        cvs = await model_cv_crud.get_cvs_by_model(db, model_id)
        
        # Convert to response schema
        cv_responses = [ModelCVRead.model_validate(cv) for cv in cvs]
        
        logger.debug(f"Found {len(cv_responses)} CVs for model {model_id}")
        return cv_responses
        
    except Exception as e:
        logger.error(f"Error fetching CVs for model {model_id}: {e}")
        raise Exception("Failed to fetch model CVs") 