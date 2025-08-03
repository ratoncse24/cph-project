from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from typing import Optional, List
import datetime
import logging

from app.models.client import Client
from app.schemas.client import ClientCreate, ClientUpdate, ClientRead

logger = logging.getLogger(__name__)


async def get_client_by_email(db: AsyncSession, email: str) -> Optional[Client]:
    """Get client by email"""
    result = await db.execute(select(Client).where(Client.email == email))
    return result.scalar_one_or_none()


async def create_client(db: AsyncSession, client_data: ClientCreate) -> Client:
    """Create a new client"""
    client_dict = client_data.model_dump()
    client = Client(**client_dict)
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return client


async def get_all_clients(db: AsyncSession, status: Optional[str] = None) -> List[Client]:
    """Get all clients with optional status filter, ordered by ID descending (newest first)"""
    query = select(Client).where(Client.deleted_at.is_(None))
    
    if status:
        query = query.where(Client.status == status)
    
    # Order by ID descending (newest first)
    query = query.order_by(Client.id.desc())
    
    result = await db.execute(query)
    return result.scalars().all()


async def get_client_by_id(db: AsyncSession, client_id: int) -> Optional[Client]:
    """Get client by ID"""
    try:
        result = await db.execute(
            select(Client).where(Client.id == client_id)
        )
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error fetching client by ID {client_id}: {e}")
        return None


async def update_client(db: AsyncSession, client_id: int, client_data: dict) -> Optional[Client]:
    """Update client information"""
    try:
        # Get existing client
        result = await db.execute(
            select(Client).where(Client.id == client_id)
        )
        client = result.scalar_one_or_none()
        
        if not client:
            logger.warning(f"Client not found for update: {client_id}")
            return None
        
        # Update fields
        for field, value in client_data.items():
            if hasattr(client, field) and value is not None:
                setattr(client, field, value)
        
        # Update timestamp
        client.updated_at = datetime.datetime.utcnow()
        
        await db.commit()
        await db.refresh(client)
        
        logger.info(f"Client updated successfully: {client.name} (ID: {client_id})")
        return client
        
    except Exception as e:
        logger.error(f"Error updating client {client_id}: {e}")
        await db.rollback()
        return None


async def soft_delete_client(db: AsyncSession, client_id: int) -> bool:
    """Soft delete client by setting deleted_at timestamp"""
    try:
        result = await db.execute(
            select(Client).where(Client.id == client_id)
        )
        client = result.scalar_one_or_none()
        
        if not client:
            logger.warning(f"Client not found for deletion: {client_id}")
            return False
        
        # Soft delete
        client.deleted_at = datetime.datetime.utcnow()
        client.status = "deleted"
        
        await db.commit()
        
        logger.info(f"Client soft deleted successfully: {client.name} (ID: {client_id})")
        return True
        
    except Exception as e:
        logger.error(f"Error soft deleting client {client_id}: {e}")
        await db.rollback()
        return False 