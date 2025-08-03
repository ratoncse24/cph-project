from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.repository import model_relationship as model_relationship_crud
from app.schemas.model_relationship import ModelRelationshipCreate, ModelRelationshipUpdate, ModelRelationshipRead, ModelRelationshipWithModels
from app.core.logger import logger


async def create_model_relationship(
    db: AsyncSession,
    relationship_data: ModelRelationshipCreate
) -> Optional[ModelRelationshipRead]:
    """
    Create a new model relationship with business logic validation
    
    Args:
        db: Database session
        relationship_data: Relationship creation data
        
    Returns:
        Created ModelRelationshipRead object or None if creation fails
    """
    try:
        logger.info(f"Creating model relationship between models {relationship_data.model_id} and {relationship_data.linked_model_id}")
        
        # Validate that models are not the same
        if relationship_data.model_id == relationship_data.linked_model_id:
            logger.warning(f"Attempted to create relationship with same model: {relationship_data.model_id}")
            raise ValueError("Cannot create relationship with the same model")
        
        # Create the relationship using repository
        relationship = await model_relationship_crud.create_model_relationship(db, relationship_data)
        
        if not relationship:
            logger.warning(f"Failed to create model relationship between models {relationship_data.model_id} and {relationship_data.linked_model_id}")
            return None
        
        # Convert to response schema
        relationship_response = ModelRelationshipRead.model_validate(relationship)
        
        logger.info(f"✅ Successfully created model relationship {relationship.id} between models {relationship_data.model_id} and {relationship_data.linked_model_id}")
        return relationship_response
        
    except Exception as e:
        logger.error(f"Error creating model relationship: {e}")
        raise Exception("Model relationship creation failed")


async def get_model_relationships(
    db: AsyncSession,
    model_id: int
) -> List[ModelRelationshipWithModels]:
    """
    Get all relationships for a specific model with model information
    
    Args:
        db: Database session
        model_id: Model ID
        
    Returns:
        List of ModelRelationshipWithModels objects
    """
    try:
        logger.debug(f"Fetching relationships for model: {model_id}")
        
        relationships = await model_relationship_crud.get_model_relationships(db, model_id)
        
        logger.debug(f"Found {len(relationships)} relationships for model {model_id}")
        return relationships
        
    except Exception as e:
        logger.error(f"Error fetching relationships for model {model_id}: {e}")
        raise Exception("Failed to fetch model relationships")


async def get_model_relationship_by_id(
    db: AsyncSession,
    relationship_id: int
) -> Optional[ModelRelationshipRead]:
    """
    Get a specific model relationship by ID
    
    Args:
        db: Database session
        relationship_id: Relationship ID
        
    Returns:
        ModelRelationshipRead object or None if not found
    """
    try:
        logger.debug(f"Fetching model relationship: {relationship_id}")
        
        relationship = await model_relationship_crud.get_model_relationship_by_id(db, relationship_id)
        
        if not relationship:
            logger.warning(f"Model relationship not found: {relationship_id}")
            return None
        
        # Convert to response schema
        relationship_response = ModelRelationshipRead.model_validate(relationship)
        
        logger.debug(f"Found model relationship: {relationship_id}")
        return relationship_response
        
    except Exception as e:
        logger.error(f"Error fetching model relationship {relationship_id}: {e}")
        raise Exception("Failed to fetch model relationship")


async def get_model_relationship_with_models(
    db: AsyncSession,
    relationship_id: int
) -> Optional[ModelRelationshipWithModels]:
    """
    Get a model relationship with model information
    
    Args:
        db: Database session
        relationship_id: Relationship ID
        
    Returns:
        ModelRelationshipWithModels object or None if not found
    """
    try:
        logger.debug(f"Fetching model relationship with models: {relationship_id}")
        
        result = await model_relationship_crud.get_model_relationship_with_models(db, relationship_id)
        
        if not result:
            logger.warning(f"Model relationship with models not found: {relationship_id}")
            return None
        
        relationship, model, linked_model = result
        
        # Create response with model information
        relationship_response = ModelRelationshipWithModels(
            id=relationship.id,
            model_id=relationship.model_id,
            linked_model_id=relationship.linked_model_id,
            relation_type=relationship.relation_type,
            status=relationship.status,
            model_first_name=model.first_name if model else None,
            model_last_name=model.last_name if model else None,
            model_email=model.email if model else None,
            linked_model_first_name=linked_model.first_name if linked_model else None,
            linked_model_last_name=linked_model.last_name if linked_model else None,
            linked_model_email=linked_model.email if linked_model else None,
            created_at=relationship.created_at,
            updated_at=relationship.updated_at,
            deleted_at=relationship.deleted_at
        )
        
        logger.debug(f"Found model relationship with models: {relationship_id}")
        return relationship_response
        
    except Exception as e:
        logger.error(f"Error fetching model relationship with models {relationship_id}: {e}")
        raise Exception("Failed to fetch model relationship with models")


async def update_model_relationship(
    db: AsyncSession,
    relationship_id: int,
    relationship_data: ModelRelationshipUpdate
) -> Optional[ModelRelationshipRead]:
    """
    Update a model relationship with business logic validation
    
    Args:
        db: Database session
        relationship_id: Relationship ID to update
        relationship_data: Update data
        
    Returns:
        Updated ModelRelationshipRead object or None if not found
    """
    try:
        logger.info(f"Updating model relationship: {relationship_id}")
        
        # Update the relationship using repository
        relationship = await model_relationship_crud.update_model_relationship(db, relationship_id, relationship_data)
        
        if not relationship:
            logger.warning(f"Failed to update model relationship: {relationship_id}")
            return None
        
        # Convert to response schema
        relationship_response = ModelRelationshipRead.model_validate(relationship)
        
        logger.info(f"✅ Successfully updated model relationship: {relationship_id}")
        return relationship_response
        
    except Exception as e:
        logger.error(f"Error updating model relationship {relationship_id}: {e}")
        raise Exception("Model relationship update failed")


async def delete_model_relationship(
    db: AsyncSession,
    relationship_id: int
) -> bool:
    """
    Delete a model relationship with business logic validation
    
    Args:
        db: Database session
        relationship_id: Relationship ID to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Deleting model relationship: {relationship_id}")
        
        # Delete the relationship using repository
        success = await model_relationship_crud.delete_model_relationship(db, relationship_id)
        
        if not success:
            logger.warning(f"Failed to delete model relationship: {relationship_id}")
            return False
        
        logger.info(f"✅ Successfully deleted model relationship: {relationship_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting model relationship {relationship_id}: {e}")
        raise Exception("Model relationship deletion failed")


async def get_relationships_by_model(
    db: AsyncSession,
    model_id: int
) -> List[ModelRelationshipRead]:
    """
    Get all relationships for a specific model
    
    Args:
        db: Database session
        model_id: Model ID
        
    Returns:
        List of ModelRelationshipRead objects
    """
    try:
        logger.debug(f"Fetching relationships for model: {model_id}")
        
        relationships = await model_relationship_crud.get_relationships_by_model(db, model_id)
        
        # Convert to response schema
        relationship_responses = [ModelRelationshipRead.model_validate(rel) for rel in relationships]
        
        logger.debug(f"Found {len(relationship_responses)} relationships for model {model_id}")
        return relationship_responses
        
    except Exception as e:
        logger.error(f"Error fetching relationships for model {model_id}: {e}")
        raise Exception("Failed to fetch model relationships") 