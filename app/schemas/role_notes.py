from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

from app.utils.pagination import PaginatedResponse


class RoleNotesCreate(BaseModel):
    project_id: int = Field(..., description="Project ID")
    role_id: int = Field(..., description="Role ID")
    title: str = Field(..., min_length=1, max_length=255, description="Note title")
    description: Optional[str] = Field(None, description="Note description")


class RoleNotesUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Note title")
    description: Optional[str] = Field(None, description="Note description")


class RoleNotesRead(BaseModel):
    id: int
    project_id: int
    role_id: int
    title: str
    description: Optional[str] = None
    added_by_user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RoleNotesReadWithRelations(BaseModel):
    id: int
    project_id: int
    role_id: int
    title: str
    description: Optional[str] = None
    added_by_user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    project_name: Optional[str] = None
    role_name: Optional[str] = None
    added_by_username: Optional[str] = None
    added_by_name: Optional[str] = None
    added_by_profile_picture_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# Response schema for paginated role notes list
RoleNotesListResponse = PaginatedResponse[RoleNotesReadWithRelations] 