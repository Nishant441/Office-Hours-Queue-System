"""Pydantic schemas for courses."""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class CourseCreate(BaseModel):
    """Schema for creating a course."""
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=255)


from app.schemas.user import UserResponse


class CourseResponse(BaseModel):
    """Course response schema."""
    id: uuid.UUID
    code: str
    name: str
    created_at: datetime
    staff: list[UserResponse] = []
    
    @field_validator("staff", mode="before")
    @classmethod
    def flatten_staff(cls, v: list):
        """Flatten CourseStaff objects to Users."""
        if not v:
            return []
        if hasattr(v[0], "user"):
            return [item.user for item in v]
        return v

    class Config:
        from_attributes = True


class CourseStaffAssign(BaseModel):
    """Schema for assigning staff to a course."""
    user_id: uuid.UUID
    course_id: uuid.UUID
