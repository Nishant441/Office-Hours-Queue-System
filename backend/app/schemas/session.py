"""Pydantic schemas for office hours sessions."""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class SessionCreate(BaseModel):
    """Schema for creating an office hours session."""
    course_id: uuid.UUID
    starts_at: datetime
    ends_at: datetime
    
    @field_validator('ends_at')
    @classmethod
    def validate_end_time(cls, v: datetime, info) -> datetime:
        """Ensure end time is after start time."""
        if 'starts_at' in info.data and v <= info.data['starts_at']:
            raise ValueError('ends_at must be after starts_at')
        return v


class SessionResponse(BaseModel):
    """Office hours session response schema."""
    id: uuid.UUID
    course_id: uuid.UUID
    starts_at: datetime
    ends_at: datetime
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class SessionStats(BaseModel):
    """Session statistics response schema."""
    count_open: int
    count_claimed: int
    count_in_progress: int
    count_resolved: int
    count_cancelled: int
    avg_wait_time_seconds: float | None
    median_wait_time_seconds: float | None
    avg_time_to_resolve_seconds: float | None
