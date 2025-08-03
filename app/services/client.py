from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.client import ClientCreate, ClientUpdate, ClientRead, ClientListResponse
from app.repository import client as client_repository
from app.core.logger import logger


async def create_client_service(db: AsyncSession, client_data: ClientCreate) -> ClientRead:
    """
    Create a new client with business logic validation
    
    Args:
        db: Database session
        client_data: Client creation data
        
    Returns:
        Created client data
        
    Raises:
        ValueError: If email already exists
    """
    # Check if client with same email already exists
    existing_client = await client_repository.get_client_by_email(db, client_data.email)
    if existing_client:
        raise ValueError(f"Client with email {client_data.email} already exists")
    
    # Create client in database
    new_client = await client_repository.create_client(db, client_data)
    
    logger.info(f"Client created successfully: {new_client.name} (ID: {new_client.id})")
    return ClientRead.model_validate(new_client)


async def get_clients_list_service(db: AsyncSession, status: Optional[str] = None) -> ClientListResponse:
    """
    Get list of clients with optional status filtering
    
    Args:
        db: Database session
        status: Optional status filter
        
    Returns:
        List of clients with total count
    """
    # Get clients from repository
    clients = await client_repository.get_all_clients(db, status)
    
    # Convert to response schema
    client_list = [ClientRead.model_validate(client) for client in clients]
    
    logger.info(f"Retrieved {len(client_list)} clients" + (f" with status '{status}'" if status else ""))
    
    return ClientListResponse(
        clients=client_list,
        total=len(client_list)
    )


async def update_client_service(db: AsyncSession, client_id: int, client_data: ClientUpdate) -> Optional[ClientRead]:
    """
    Update client information with business logic validation
    
    Args:
        db: Database session
        client_id: Client ID to update
        client_data: Client update data
        
    Returns:
        Updated client data or None if not found
        
    Raises:
        ValueError: If email already exists for another client
    """
    # Check if client exists
    existing_client = await client_repository.get_client_by_id(db, client_id)
    if not existing_client:
        logger.warning(f"Client not found for update: {client_id}")
        return None
    
    # If email is being updated, check if it's already used by another client
    if client_data.email and client_data.email != existing_client.email:
        email_exists = await client_repository.get_client_by_email(db, client_data.email)
        if email_exists:
            raise ValueError(f"Client with email {client_data.email} already exists")
    
    # Prepare update data (only non-None values)
    update_data = {}
    for field, value in client_data.model_dump().items():
        if value is not None:
            update_data[field] = value
    
    # Update client in database
    updated_client = await client_repository.update_client(db, client_id, update_data)
    
    if updated_client:
        logger.info(f"Client updated successfully: {updated_client.name} (ID: {client_id})")
        return ClientRead.model_validate(updated_client)
    
    return None


async def get_client_by_id_service(db: AsyncSession, client_id: int) -> Optional[ClientRead]:
    """
    Get client by ID
    
    Args:
        db: Database session
        client_id: Client ID
        
    Returns:
        Client data or None if not found
    """
    client = await client_repository.get_client_by_id(db, client_id)
    
    if client:
        return ClientRead.model_validate(client)
    
    return None 