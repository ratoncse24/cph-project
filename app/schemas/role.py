from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

from app.utils.pagination import PaginatedResponse


class RoleCreate(BaseModel):
    project_id: int = Field(..., description="Project ID")
    name: str = Field(..., min_length=1, max_length=255, description="Role name")
    gender: Optional[str] = Field(None, max_length=50, description="Gender")
    ethnicity: Optional[str] = Field(None, max_length=100, description="Ethnicity")
    language: Optional[str] = Field(None, max_length=100, description="Language")
    native_language: Optional[str] = Field(None, max_length=100, description="Native language")
    age_from: Optional[int] = Field(None, ge=0, le=150, description="Minimum age")
    age_to: Optional[int] = Field(None, ge=0, le=150, description="Maximum age")
    height_from: Optional[float] = Field(None, ge=0, le=300, description="Minimum height in cm")
    height_to: Optional[float] = Field(None, ge=0, le=300, description="Maximum height in cm")
    tags: Optional[List[str]] = Field(None, description="Tags")
    category: Optional[str] = Field(None, max_length=100, description="Category")
    hair_color: Optional[str] = Field(None, max_length=50, description="Hair color")
    status: Optional[str] = Field("active", max_length=50, description="Status")


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Role name")
    gender: Optional[str] = Field(None, max_length=50, description="Gender")
    ethnicity: Optional[str] = Field(None, max_length=100, description="Ethnicity")
    language: Optional[str] = Field(None, max_length=100, description="Language")
    native_language: Optional[str] = Field(None, max_length=100, description="Native language")
    age_from: Optional[int] = Field(None, ge=0, le=150, description="Minimum age")
    age_to: Optional[int] = Field(None, ge=0, le=150, description="Maximum age")
    height_from: Optional[float] = Field(None, ge=0, le=300, description="Minimum height in cm")
    height_to: Optional[float] = Field(None, ge=0, le=300, description="Maximum height in cm")
    tags: Optional[List[str]] = Field(None, description="Tags")
    category: Optional[str] = Field(None, max_length=100, description="Category")
    hair_color: Optional[str] = Field(None, max_length=50, description="Hair color")
    status: Optional[str] = Field(None, max_length=50, description="Status")


class RoleRead(BaseModel):
    id: int
    project_id: int
    name: str
    gender: Optional[str] = None
    ethnicity: Optional[str] = None
    language: Optional[str] = None
    native_language: Optional[str] = None
    age_from: Optional[int] = None
    age_to: Optional[int] = None
    height_from: Optional[float] = None
    height_to: Optional[float] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    hair_color: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RoleReadWithRelations(BaseModel):
    id: int
    project_id: int
    name: str
    gender: Optional[str] = None
    ethnicity: Optional[str] = None
    language: Optional[str] = None
    native_language: Optional[str] = None
    age_from: Optional[int] = None
    age_to: Optional[int] = None
    height_from: Optional[float] = None
    height_to: Optional[float] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    hair_color: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    project_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# Response schema for paginated roles list
RoleListResponse = PaginatedResponse[RoleReadWithRelations] 