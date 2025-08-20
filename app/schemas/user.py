from pydantic import BaseModel, EmailStr, ConfigDict, field_validator, Field
from typing import Optional, List
from datetime import datetime
import re

from app.utils.pagination import PaginatedResponse


class UserEventData(BaseModel):
    """Schema for user event data from external services"""
    user_id: int = Field(..., description="User ID")
    name: Optional[str] = Field(..., description="Name")
    username: str = Field(..., description="Username")
    email: Optional[EmailStr] = Field(None, description="User email")
    phone: Optional[str] = Field(None, description="User phone number")
    role_name: str = Field(..., description="User role")
    profile_picture_url: Optional[str] = Field(None, description="Profile picture URL")
    temporary_profile_picture_url: Optional[str] = Field(None, description="Temporary profile picture URL")
    temporary_profile_picture_expires_at: Optional[datetime] = None
    status: str = Field(..., description="User status")
    token_version: Optional[int] = Field(None, description="Token version for JWT invalidation")
    member_of: Optional[str] = Field(None, description="Organization/group membership (ignored by our service)")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    created_by_system: Optional[bool] = Field(None, description="Whether created by system")
    
    class Config:
        extra = "allow"  # Allow additional fields that we might not process


class UserUpdatedEventData(UserEventData):
    """Schema for user updated event data with additional fields"""
    updated_by_system: Optional[bool] = Field(None, description="Whether updated by system")
    updated_by: Optional[str] = Field(None, description="Who updated the user")
    updated_fields: Optional[List[str]] = Field(None, description="List of updated fields")
    self_update: Optional[bool] = Field(None, description="Whether this is a self-update")


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100, description="Unique username")
    email: Optional[EmailStr] = Field(None, description="User's email address (optional)")
    phone: Optional[str] = Field(None, max_length=20, description="User's phone number")
    role_name: str = Field(..., max_length=20, description="User role")
    profile_picture_url: Optional[str] = Field(None, description="Profile picture URL")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        plain_username_pattern = r'^[a-zA-Z0-9_-]+$'
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'

        if re.match(plain_username_pattern, v) or re.match(email_pattern, v):
            return v
        raise ValueError('Username must be either a valid email or contain only letters, numbers, underscores, and hyphens')

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format if provided"""
        if v is None:
            return v
        
        # Basic phone validation - you can make this more sophisticated
        cleaned_phone = re.sub(r'[^\d+\(\)\-\s]', '', v)
        if len(cleaned_phone) < 10:
            raise ValueError("Phone number must be at least 10 digits")
        
        return cleaned_phone


class UserRead(BaseModel):
    id: int
    username: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role_name: str
    profile_picture_url: Optional[str] = None
    temporary_profile_picture_url: Optional[str] = None
    temporary_profile_picture_expires_at: Optional[datetime] = None
    status: str
    token_version: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    username: str = Field(..., description="Username for login")
    password: str = Field(..., description="User password")


class Token(BaseModel):
    """Legacy token response for backward compatibility"""
    access_token: str
    token_type: str = "bearer"


class TokenPair(BaseModel):
    """Enhanced token response with refresh token"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: Optional[int] = Field(default=None, description="Access token expiration in seconds")


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh"""
    refresh_token: str = Field(..., description="Valid refresh token")


class TokenValidationResponse(BaseModel):
    """Response for token validation"""
    valid: bool
    user_id: Optional[int] = None
    expires_at: Optional[str] = None
    token_type: Optional[str] = None


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[EmailStr] = Field(None, description="User's email address (optional)")
    phone: Optional[str] = Field(None, max_length=20)
    role_name: Optional[str] = Field(None, max_length=20)
    profile_picture_url: Optional[str] = None
    status: Optional[str] = Field(None, max_length=20)
    token_version: Optional[int] = Field(None, description="Token version for JWT invalidation")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        """Validate username format if provided"""
        if v is None:
            return v
            
        cleaned_username = v.strip()
        if len(cleaned_username) < 3:
            raise ValueError("Username must be at least 3 characters long")

        return cleaned_username


# Response schema for paginated user list
UserListResponse = PaginatedResponse[UserRead]
