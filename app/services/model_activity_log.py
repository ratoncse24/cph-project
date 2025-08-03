from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.repository import model_activity_log as model_activity_log_crud
from app.schemas.model_activity_log import (
    ModelActivityLogCreate,
    ModelActivityLogUpdate,
    ModelActivityLogRead,
    ModelActivityLogListRead,
    ModelActivityLogMarkRead,
    ModelActivityLogSearchParams,
    ModelActivityLogListResponse
)
from app.utils.pagination import PaginationParams, PaginationHandler, PaginationMeta
from app.core.logger import logger


async def create_activity_log(
    db: AsyncSession,
    model_id: int,
    title: str,
    description: str,
    action_type: str,
    performed_by: int,
    project: Optional[str] = None,
    role: Optional[str] = None
) -> None:
    """
    Create an activity log entry for model updates
    
    Args:
        db: Database session
        model_id: ID of the model
        title: Activity title
        description: Activity description
        action_type: Type of action performed
        performed_by: ID of the user who performed the action
        project: Optional project name
        role: Optional role in the activity
    """
    try:
        activity_log_data = ModelActivityLogCreate(
            model_id=model_id,
            title=title,
            description=description,
            action_type=action_type,
            performed_by=performed_by,
            project=project,
            role=role
        )
        
        await model_activity_log_crud.create_activity_log(db, activity_log_data)
        logger.info(f"Created activity log for model {model_id}: {title}")
        
    except Exception as e:
        logger.error(f"Failed to create activity log for model {model_id}: {e}")
        # Don't raise the exception to avoid breaking the main update flow

async def get_activity_log_by_id(
    db: AsyncSession,
    activity_log_id: int
) -> ModelActivityLogRead:
    """Get activity log by ID"""
    try:
        logger.debug(f"Fetching activity log: {activity_log_id}")
        
        activity_log = await model_activity_log_crud.get_activity_log_by_id(db, activity_log_id)
        
        if not activity_log:
            logger.warning(f"Activity log not found: {activity_log_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity log not found"
            )
        
        # Convert to response schema
        activity_log_response = ModelActivityLogRead.model_validate(activity_log)
        
        logger.info(f"✅ Successfully retrieved activity log {activity_log_id}")
        return activity_log_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching activity log {activity_log_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve activity log: {str(e)}"
        )


async def update_activity_log(
    db: AsyncSession,
    activity_log_id: int,
    activity_log_data: ModelActivityLogUpdate
) -> ModelActivityLogRead:
    """Update an activity log entry"""
    try:
        logger.info(f"Updating activity log: {activity_log_id}")
        
        activity_log = await model_activity_log_crud.update_activity_log(db, activity_log_id, activity_log_data)
        
        if not activity_log:
            logger.warning(f"Activity log not found for update: {activity_log_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity log not found"
            )
        
        # Convert to response schema
        activity_log_response = ModelActivityLogRead.model_validate(activity_log)
        
        logger.info(f"✅ Successfully updated activity log {activity_log_id}")
        return activity_log_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating activity log {activity_log_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update activity log: {str(e)}"
        )


async def delete_activity_log(
    db: AsyncSession,
    activity_log_id: int
) -> bool:
    """Delete an activity log entry"""
    try:
        logger.info(f"Deleting activity log: {activity_log_id}")
        
        success = await model_activity_log_crud.delete_activity_log(db, activity_log_id)
        
        if not success:
            logger.warning(f"Activity log not found for deletion: {activity_log_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity log not found"
            )
        
        logger.info(f"✅ Successfully deleted activity log {activity_log_id}")
        return success
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting activity log {activity_log_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete activity log: {str(e)}"
        )


async def mark_activity_logs_as_read(
    db: AsyncSession,
    mark_read_data: ModelActivityLogMarkRead
) -> dict:
    """Mark activity logs as read"""
    try:
        logger.info(f"Marking activity logs as read: {mark_read_data.log_ids}")
        
        updated_count = await model_activity_log_crud.mark_activity_logs_as_read(db, mark_read_data.log_ids)
        
        result = {
            "message": f"Successfully marked {updated_count} activity log(s) as read",
            "updated_count": updated_count
        }
        
        logger.info(f"✅ Successfully marked {updated_count} activity logs as read")
        return result
        
    except Exception as e:
        logger.error(f"Error marking activity logs as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark activity logs as read: {str(e)}"
        )


async def get_activity_logs_paginated(
    db: AsyncSession,
    pagination: PaginationParams,
    search_params:  Optional[dict] = None
) -> ModelActivityLogListResponse:
    """Get paginated list of activity logs with search and filtering"""
    try:
        logger.info(f"Fetching paginated activity logs (page: {pagination.page}, size: {pagination.size})")
        
        result = await model_activity_log_crud.get_activity_logs_paginated(db, pagination, search_params)
        
        logger.info(f"Found {len(result.results)} activity logs")
        return result
        
    except Exception as e:
        logger.error(f"Error fetching paginated activity logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve activity logs: {str(e)}"
        )


async def get_activity_logs_by_model(
    db: AsyncSession,
    model_id: int,
    pagination: PaginationParams
) -> ModelActivityLogListResponse:
    """Get activity logs for a specific model"""
    try:
        logger.info(f"Fetching activity logs for model: {model_id} (page: {pagination.page}, size: {pagination.size})")
        
        result = await model_activity_log_crud.get_activity_logs_by_model(db, model_id, pagination)
        
        logger.info(f"Found {len(result.results)} activity logs for model {model_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error fetching activity logs for model {model_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve activity logs for model: {str(e)}"
        )


async def get_unread_count(db: AsyncSession) -> dict:
    """Get count of unread activity logs"""
    try:
        logger.debug("Fetching unread activity logs count")
        
        count = await model_activity_log_crud.get_unread_count(db)
        result = {"unread_count": count}
        
        logger.info(f"Found {count} unread activity logs")
        return result
        
    except Exception as e:
        logger.error(f"Error fetching unread count: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get unread count: {str(e)}"
        ) 