from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator
from typing import Optional, List
from datetime import datetime
import re


class ClientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Client name")
    phone: Optional[str] = Field(None, max_length=20, description="Client phone number")
    email: EmailStr = Field(..., description="Client email address")
    address: Optional[str] = Field(None, description="Client address")
    status: str = Field(default="active", max_length=50, description="Client status")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format if provided"""
        if v is None:
            return v
        
        # Basic phone validation
        cleaned_phone = re.sub(r'[^\d+\(\)\-\s]', '', v)
        if len(cleaned_phone) < 10:
            raise ValueError("Phone number must be at least 10 digits")
        
        return cleaned_phone


class ClientRead(BaseModel):
    id: int
    name: str
    phone: Optional[str] = None
    email: EmailStr
    address: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ClientUpdate(BaseModel):
    """Schema for updating client information"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = Field(None, description="Client email address")
    address: Optional[str] = Field(None, description="Client address")
    status: Optional[str] = Field(None, max_length=50)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format if provided"""
        if v is None:
            return v
        
        # Basic phone validation
        cleaned_phone = re.sub(r'[^\d+\(\)\-\s]', '', v)
        if len(cleaned_phone) < 10:
            raise ValueError("Phone number must be at least 10 digits")
        
        return cleaned_phone


class ClientListResponse(BaseModel):
    """Response schema for client list"""
    clients: List[ClientRead]
    total: int
    status: str = "success" 