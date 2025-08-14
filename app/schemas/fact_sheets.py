from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional
from datetime import datetime, date, time
from decimal import Decimal


class FactSheetCreate(BaseModel):
    """Schema for creating fact sheet (auto-created with project)"""
    project_id: int = Field(..., description="Project ID")
    client_id: int = Field(..., description="Client ID")
    client_reference: Optional[str] = Field(None, max_length=255)
    cph_casting_reference: Optional[str] = Field(None, max_length=255)
    project_name: Optional[str] = Field(None, max_length=255)
    director: Optional[str] = Field(None, max_length=255)
    deadline_date: Optional[date] = Field(None)
    ppm_date: Optional[date] = Field(None)
    project_description: Optional[str] = Field(None)
    shooting_date: Optional[date] = Field(None)
    location: Optional[str] = Field(None, max_length=255)
    total_hours: Optional[Decimal] = Field(None, ge=0, le=999.99)
    time_range_start: Optional[time] = Field(None)
    time_range_end: Optional[time] = Field(None)
    budget_details: Optional[str] = Field(None)
    terms: Optional[str] = Field(None)
    total_project_price: Optional[Decimal] = Field(None, ge=0, le=999999999999.99)
    rights_buy_outs: Optional[str] = Field(None)
    conditions: Optional[str] = Field(None)
    status: str = Field(default="pending", max_length=50)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status"""
        valid_statuses = ["pending", "approved"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v


class FactSheetRead(BaseModel):
    """Schema for reading fact sheet data"""
    project_id: int
    client_id: int
    client_reference: Optional[str] = None
    cph_casting_reference: Optional[str] = None
    project_name: Optional[str] = None
    director: Optional[str] = None
    deadline_date: Optional[date] = None
    ppm_date: Optional[date] = None
    project_description: Optional[str] = None
    shooting_date: Optional[date] = None
    location: Optional[str] = None
    total_hours: Optional[Decimal] = None
    time_range_start: Optional[time] = None
    time_range_end: Optional[time] = None
    budget_details: Optional[str] = None
    terms: Optional[str] = None
    total_project_price: Optional[Decimal] = None
    rights_buy_outs: Optional[str] = None
    conditions: Optional[str] = None
    status: str
    approved_at: Optional[datetime] = None
    approved_by_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Include related data
    project_name_from_project: Optional[str] = None
    client_name: Optional[str] = None
    approved_by_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class FactSheetUpdate(BaseModel):
    """Schema for updating fact sheet information"""
    client_reference: Optional[str] = Field(None, max_length=255)
    cph_casting_reference: Optional[str] = Field(None, max_length=255)
    project_name: Optional[str] = Field(None, max_length=255)
    director: Optional[str] = Field(None, max_length=255)
    deadline_date: Optional[date] = Field(None)
    ppm_date: Optional[date] = Field(None)
    project_description: Optional[str] = Field(None)
    shooting_date: Optional[date] = Field(None)
    location: Optional[str] = Field(None, max_length=255)
    total_hours: Optional[Decimal] = Field(None, ge=0, le=999.99)
    time_range_start: Optional[time] = Field(None)
    time_range_end: Optional[time] = Field(None)
    budget_details: Optional[str] = Field(None)
    terms: Optional[str] = Field(None)
    total_project_price: Optional[Decimal] = Field(None, ge=0, le=999999999999.99)
    rights_buy_outs: Optional[str] = Field(None)
    conditions: Optional[str] = Field(None)
    status: Optional[str] = Field(None, max_length=50)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate status if provided"""
        if v is None:
            return v
        valid_statuses = ["pending", "approved"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v


class FactSheetStatusUpdate(BaseModel):
    """Schema for updating only the status (admin only)"""
    status: str = Field(..., max_length=50)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status"""
        valid_statuses = ["pending", "approved"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v 