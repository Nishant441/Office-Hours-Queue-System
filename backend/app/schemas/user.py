"""Pydantic schemas for user data."""
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Base user schema."""
    name: str
    email: EmailStr
    role: str


class UserResponse(UserBase):
    """User response schema."""
    id: uuid.UUID
    created_at: datetime
    
    class Config:
        from_attributes = True
