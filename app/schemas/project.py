from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional
from datetime import datetime, date


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    username: str = Field(..., min_length=1, max_length=100, description="Project-specific username")
    password: str = Field(..., min_length=6, description="Project password (will be published as event)")
    client_id: int = Field(..., description="Client ID")
    deadline: Optional[date] = Field(None, description="Project deadline")
    status: str = Field(default="active", max_length=50, description="Project status")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status"""
        valid_statuses = ["active", "inactive", "archive", "completed"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v


class ProjectRead(BaseModel):
    id: int
    name: str
    username: str
    client_id: int
    deadline: Optional[date] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    
    # Include client information
    client_name: Optional[str] = None
    client_email: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProjectUpdate(BaseModel):
    """Schema for updating project information"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    username: Optional[str] = Field(None, min_length=1, max_length=100)
    password: Optional[str] = Field(None, min_length=6, description="Project password (will be published as event)")
    client_id: Optional[int] = Field(None, description="Client ID")
    deadline: Optional[date] = Field(None, description="Project deadline")
    status: Optional[str] = Field(None, max_length=50)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate status if provided"""
        if v is None:
            return v
        valid_statuses = ["active", "inactive", "archive", "completed"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v 