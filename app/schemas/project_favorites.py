from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


class FavoritableType(str, Enum):
    """Enum for favoritable types"""
    PROJECT = "Project"
    ROLE = "Role"


class ProjectFavoritesCreate(BaseModel):
    favoritable_type: FavoritableType = Field(..., description="Type of item to favorite (Project or Role)")
    favoritable_id: int = Field(..., description="ID of the Project or Role to favorite")


class ProjectFavoritesRead(BaseModel):
    id: int
    user_id: int
    favoritable_type: str
    favoritable_id: int
    favorited_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ProjectFavoritesReadWithRelations(BaseModel):
    id: int
    user_id: int
    favoritable_type: str
    favoritable_id: int
    favorited_at: Optional[datetime] = None
    user_username: Optional[str] = None
    user_name: Optional[str] = None
    project_name: Optional[str] = None
    role_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProjectFavoritesListResponse(BaseModel):
    """Response schema for project favorites list"""
    results: List[ProjectFavoritesReadWithRelations] = Field(..., description="List of favorites")
    total: int = Field(..., description="Total number of favorites") 