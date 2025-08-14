from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.fact_sheets import FactSheetCreate, FactSheetUpdate, FactSheetRead, FactSheetStatusUpdate
from app.repository import fact_sheets as fact_sheets_repository
from app.core.logger import logger


async def create_fact_sheet_service(db: AsyncSession, fact_sheet_data: FactSheetCreate) -> FactSheetRead:
    """
    Create a new fact sheet with business logic validation
    
    Args:
        db: Database session
        fact_sheet_data: Fact sheet creation data
        
    Returns:
        Created fact sheet data
        
    Raises:
        ValueError: If project doesn't exist, client doesn't exist, or fact sheet already exists
    """
    # Check if project exists
    project_exists = await fact_sheets_repository.check_project_exists(db, fact_sheet_data.project_id)
    if not project_exists:
        raise ValueError(f"Project with ID {fact_sheet_data.project_id} does not exist")
    
    # Check if client exists
    client_exists = await fact_sheets_repository.check_client_exists(db, fact_sheet_data.client_id)
    if not client_exists:
        raise ValueError(f"Client with ID {fact_sheet_data.client_id} does not exist")
    
    # Check if fact sheet already exists for this project
    fact_sheet_exists = await fact_sheets_repository.check_fact_sheet_exists(db, fact_sheet_data.project_id)
    if fact_sheet_exists:
        raise ValueError(f"Fact sheet already exists for project {fact_sheet_data.project_id}")
    
    # Create fact sheet in database
    new_fact_sheet = await fact_sheets_repository.create_fact_sheet(db, fact_sheet_data)
    
    logger.info(f"Fact sheet created successfully for project {new_fact_sheet.project_id}")
    return _convert_to_fact_sheet_read(new_fact_sheet)


async def get_fact_sheet_by_project_id_service(db: AsyncSession, project_id: int) -> Optional[FactSheetRead]:
    """
    Get fact sheet by project ID
    
    Args:
        db: Database session
        project_id: Project ID
        
    Returns:
        Fact sheet data or None if not found
    """
    fact_sheet = await fact_sheets_repository.get_fact_sheet_by_project_id(db, project_id)
    
    if fact_sheet:
        return _convert_to_fact_sheet_read(fact_sheet)
    
    return None


async def update_fact_sheet_service(
    db: AsyncSession, 
    project_id: int, 
    fact_sheet_data: FactSheetUpdate,
    current_user_role: str
) -> Optional[FactSheetRead]:
    """
    Update fact sheet information with role-based validation
    
    Args:
        db: Database session
        project_id: Project ID
        fact_sheet_data: Fact sheet update data
        current_user_role: Current user's role (admin or project)
        
    Returns:
        Updated fact sheet data or None if not found
        
    Raises:
        ValueError: If project role tries to update approved fact sheet or admin tries to update content
    """
    # Get existing fact sheet
    existing_fact_sheet = await fact_sheets_repository.get_fact_sheet_by_project_id(db, project_id)
    if not existing_fact_sheet:
        logger.warning(f"Fact sheet not found for project: {project_id}")
        return None
    
    # Role-based validation
    if current_user_role == "project":
        # Project role can only update content if fact sheet is not approved
        if existing_fact_sheet.status == "approved":
            raise ValueError("Cannot update fact sheet content after approval")
        
        # Project role cannot update status
        if fact_sheet_data.status is not None:
            raise ValueError("Project role cannot update fact sheet status")
    
    elif current_user_role == "admin":
        # Admin can only update status, not content
        content_fields = [
            'client_reference', 'cph_casting_reference', 'project_name', 'director',
            'deadline_date', 'ppm_date', 'project_description', 'shooting_date',
            'location', 'total_hours', 'time_range_start', 'time_range_end',
            'budget_details', 'terms', 'total_project_price', 'rights_buy_outs', 'conditions'
        ]
        
        for field in content_fields:
            if getattr(fact_sheet_data, field) is not None:
                raise ValueError(f"Admin role cannot update fact sheet content field: {field}")
    
    # Prepare update data (only non-None values)
    update_data = {}
    for field, value in fact_sheet_data.model_dump().items():
        if value is not None:
            update_data[field] = value
    
    # Update fact sheet in database
    updated_fact_sheet = await fact_sheets_repository.update_fact_sheet(db, project_id, update_data)
    
    if updated_fact_sheet:
        logger.info(f"Fact sheet updated successfully for project {project_id} by {current_user_role} role")
        return _convert_to_fact_sheet_read(updated_fact_sheet)
    
    return None


async def approve_fact_sheet_service(
    db: AsyncSession, 
    project_id: int, 
    approved_by_id: int
) -> Optional[FactSheetRead]:
    """
    Approve fact sheet (admin only)
    
    Args:
        db: Database session
        project_id: Project ID
        approved_by_id: ID of the admin user approving the fact sheet
        
    Returns:
        Approved fact sheet data or None if not found
        
    Raises:
        ValueError: If user doesn't exist
    """
    # Check if user exists
    user_exists = await fact_sheets_repository.check_user_exists(db, approved_by_id)
    if not user_exists:
        raise ValueError(f"User with ID {approved_by_id} does not exist")
    
    # Approve fact sheet
    approved_fact_sheet = await fact_sheets_repository.approve_fact_sheet(db, project_id, approved_by_id)
    
    if approved_fact_sheet:
        logger.info(f"Fact sheet approved successfully for project {project_id} by user {approved_by_id}")
        return _convert_to_fact_sheet_read(approved_fact_sheet)
    
    return None


def _convert_to_fact_sheet_read(fact_sheet) -> FactSheetRead:
    """Convert fact sheet model to FactSheetRead schema with related information"""
    # Safely extract related information
    project_name_from_project = None
    client_name = None
    approved_by_name = None
    
    # Check if project relationship is loaded and accessible
    if hasattr(fact_sheet, 'project') and fact_sheet.project is not None:
        try:
            project_name_from_project = fact_sheet.project.name
        except Exception:
            project_name_from_project = None
    
    # Check if client relationship is loaded and accessible
    if hasattr(fact_sheet, 'client') and fact_sheet.client is not None:
        try:
            client_name = fact_sheet.client.name
        except Exception:
            client_name = None
    
    # Check if approved_by relationship is loaded and accessible
    if hasattr(fact_sheet, 'approved_by') and fact_sheet.approved_by is not None:
        try:
            approved_by_name = fact_sheet.approved_by.name
        except Exception:
            approved_by_name = None
    
    fact_sheet_dict = {
        "project_id": fact_sheet.project_id,
        "client_id": fact_sheet.client_id,
        "client_reference": fact_sheet.client_reference,
        "cph_casting_reference": fact_sheet.cph_casting_reference,
        "project_name": fact_sheet.project_name,
        "director": fact_sheet.director,
        "deadline_date": fact_sheet.deadline_date,
        "ppm_date": fact_sheet.ppm_date,
        "project_description": fact_sheet.project_description,
        "shooting_date": fact_sheet.shooting_date,
        "location": fact_sheet.location,
        "total_hours": fact_sheet.total_hours,
        "time_range_start": fact_sheet.time_range_start,
        "time_range_end": fact_sheet.time_range_end,
        "budget_details": fact_sheet.budget_details,
        "terms": fact_sheet.terms,
        "total_project_price": fact_sheet.total_project_price,
        "rights_buy_outs": fact_sheet.rights_buy_outs,
        "conditions": fact_sheet.conditions,
        "status": fact_sheet.status,
        "approved_at": fact_sheet.approved_at,
        "approved_by_id": fact_sheet.approved_by_id,
        "created_at": fact_sheet.created_at,
        "updated_at": fact_sheet.updated_at,
        "project_name_from_project": project_name_from_project,
        "client_name": client_name,
        "approved_by_name": approved_by_name
    }
    return FactSheetRead(**fact_sheet_dict) 