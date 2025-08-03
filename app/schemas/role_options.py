from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List
from datetime import datetime


class RoleOptionsCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Role option name")
    option_type: str = Field(default="category", max_length=50, description="Type of option (category, harif_color, etc.)")
    status: str = Field(default="active", max_length=50, description="Role option status")

    @field_validator("option_type")
    @classmethod
    def validate_option_type(cls, v: str) -> str:
        """Validate option type"""
        valid_types = ["category", "harif_color", "other"]
        if v not in valid_types:
            raise ValueError(f"Option type must be one of: {', '.join(valid_types)}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status"""
        valid_statuses = ["active", "inactive", "deleted"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v


class RoleOptionsRead(BaseModel):
    id: int
    name: str
    option_type: str
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RoleOptionsUpdate(BaseModel):
    """Schema for updating role options information"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    option_type: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, max_length=50)

    @field_validator("option_type")
    @classmethod
    def validate_option_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate option type if provided"""
        if v is None:
            return v
        valid_types = ["category", "harif_color", "other"]
        if v not in valid_types:
            raise ValueError(f"Option type must be one of: {', '.join(valid_types)}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate status if provided"""
        if v is None:
            return v
        valid_statuses = ["active", "inactive", "deleted"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v


class RoleOptionsListResponse(BaseModel):
    """Response schema for role options list"""
    role_options: List[RoleOptionsRead]
    total: int
    status: str = "success" 