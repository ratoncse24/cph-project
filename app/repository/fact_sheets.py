from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import Optional
import datetime
import logging

from app.models.fact_sheets import FactSheet
from app.models.project import Project
from app.models.client import Client
from app.models.user import User
from app.schemas.fact_sheets import FactSheetCreate, FactSheetUpdate
from app.core.logger import logger


async def create_fact_sheet(db: AsyncSession, fact_sheet_data: FactSheetCreate) -> FactSheet:
    """Create a new fact sheet"""
    try:
        fact_sheet_dict = fact_sheet_data.model_dump()
        fact_sheet = FactSheet(**fact_sheet_dict)
        db.add(fact_sheet)
        await db.commit()
        await db.refresh(fact_sheet)
        
        # Load relationships
        result = await db.execute(
            select(FactSheet)
            .options(
                selectinload(FactSheet.project),
                selectinload(FactSheet.client),
                selectinload(FactSheet.approved_by)
            )
            .where(FactSheet.project_id == fact_sheet.project_id)
        )
        fact_sheet_with_relations = result.scalar_one()
        
        logger.info(f"Fact sheet created for project {fact_sheet.project_id}")
        return fact_sheet_with_relations
        
    except Exception as e:
        logger.error(f"Error creating fact sheet: {e}")
        await db.rollback()
        raise


async def get_fact_sheet_by_project_id(db: AsyncSession, project_id: int) -> Optional[FactSheet]:
    """Get fact sheet by project ID with all relationships"""
    try:
        result = await db.execute(
            select(FactSheet)
            .options(
                selectinload(FactSheet.project),
                selectinload(FactSheet.client),
                selectinload(FactSheet.approved_by)
            )
            .where(FactSheet.project_id == project_id)
        )
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error fetching fact sheet for project {project_id}: {e}")
        return None


async def update_fact_sheet(db: AsyncSession, project_id: int, fact_sheet_data: dict) -> Optional[FactSheet]:
    """Update fact sheet information"""
    try:
        # Get existing fact sheet
        result = await db.execute(
            select(FactSheet).where(FactSheet.project_id == project_id)
        )
        fact_sheet = result.scalar_one_or_none()
        
        if not fact_sheet:
            logger.warning(f"Fact sheet not found for project: {project_id}")
            return None
        
        # Update fields
        for field, value in fact_sheet_data.items():
            if hasattr(fact_sheet, field) and value is not None:
                setattr(fact_sheet, field, value)
        
        # Update timestamp
        fact_sheet.updated_at = datetime.datetime.utcnow()
        
        await db.commit()
        await db.refresh(fact_sheet)
        
        # Load relationships
        result = await db.execute(
            select(FactSheet)
            .options(
                selectinload(FactSheet.project),
                selectinload(FactSheet.client),
                selectinload(FactSheet.approved_by)
            )
            .where(FactSheet.project_id == project_id)
        )
        fact_sheet_with_relations = result.scalar_one()
        
        logger.info(f"Fact sheet updated for project {project_id}")
        return fact_sheet_with_relations
        
    except Exception as e:
        logger.error(f"Error updating fact sheet for project {project_id}: {e}")
        await db.rollback()
        return None


async def approve_fact_sheet(db: AsyncSession, project_id: int, approved_by_id: int) -> Optional[FactSheet]:
    """Approve fact sheet (admin only)"""
    try:
        # Get existing fact sheet
        result = await db.execute(
            select(FactSheet).where(FactSheet.project_id == project_id)
        )
        fact_sheet = result.scalar_one_or_none()
        
        if not fact_sheet:
            logger.warning(f"Fact sheet not found for project: {project_id}")
            return None
        
        # Update approval fields
        fact_sheet.status = "approved"
        fact_sheet.approved_at = datetime.datetime.utcnow()
        fact_sheet.approved_by_id = approved_by_id
        fact_sheet.updated_at = datetime.datetime.utcnow()
        
        await db.commit()
        await db.refresh(fact_sheet)
        
        # Load relationships
        result = await db.execute(
            select(FactSheet)
            .options(
                selectinload(FactSheet.project),
                selectinload(FactSheet.client),
                selectinload(FactSheet.approved_by)
            )
            .where(FactSheet.project_id == project_id)
        )
        fact_sheet_with_relations = result.scalar_one()
        
        logger.info(f"Fact sheet approved for project {project_id} by user {approved_by_id}")
        return fact_sheet_with_relations
        
    except Exception as e:
        logger.error(f"Error approving fact sheet for project {project_id}: {e}")
        await db.rollback()
        return None


async def check_fact_sheet_exists(db: AsyncSession, project_id: int) -> bool:
    """Check if fact sheet exists for project"""
    try:
        result = await db.execute(
            select(FactSheet).where(FactSheet.project_id == project_id)
        )
        return result.scalar_one_or_none() is not None
    except Exception as e:
        logger.error(f"Error checking fact sheet existence for project {project_id}: {e}")
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


async def check_client_exists(db: AsyncSession, client_id: int) -> bool:
    """Check if client exists"""
    try:
        result = await db.execute(
            select(Client).where(Client.id == client_id)
        )
        return result.scalar_one_or_none() is not None
    except Exception as e:
        logger.error(f"Error checking client existence {client_id}: {e}")
        return False


async def check_user_exists(db: AsyncSession, user_id: int) -> bool:
    """Check if user exists"""
    try:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none() is not None
    except Exception as e:
        logger.error(f"Error checking user existence {user_id}: {e}")
        return False 