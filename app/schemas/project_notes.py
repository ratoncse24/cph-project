from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

from app.utils.pagination import PaginatedResponse


class ProjectNotesCreate(BaseModel):
    project_id: int = Field(..., description="Project ID")
    title: str = Field(..., min_length=1, max_length=255, description="Note title")
    description: Optional[str] = Field(None, description="Note description")


class ProjectNotesUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Note title")
    description: Optional[str] = Field(None, description="Note description")


class ProjectNotesRead(BaseModel):
    id: int
    project_id: int
    title: str
    description: Optional[str] = None
    added_by_user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ProjectNotesReadWithRelations(BaseModel):
    id: int
    project_id: int
    title: str
    description: Optional[str] = None
    added_by_user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    project_name: Optional[str] = None
    added_by_username: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# Response schema for paginated project notes list
ProjectNotesListResponse = PaginatedResponse[ProjectNotesReadWithRelations] 