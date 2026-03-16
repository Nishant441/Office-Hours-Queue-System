"""Pydantic schemas for tickets."""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class TicketCreate(BaseModel):
    """Schema for creating a ticket."""
    session_id: uuid.UUID
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    topic_tag: str | None = Field(None, max_length=100)


class TicketResponse(BaseModel):
    """Ticket response schema."""
    id: uuid.UUID
    session_id: uuid.UUID
    course_id: uuid.UUID
    student_id: uuid.UUID
    assigned_ta_id: uuid.UUID | None
    title: str
    description: str
    topic_tag: str | None
    status: str
    created_at: datetime
    claimed_at: datetime | None
    started_at: datetime | None
    resolved_at: datetime | None
    cancelled_at: datetime | None
    
    class Config:
        from_attributes = True


class DuplicateTicketResult(BaseModel):
    """Duplicate ticket result with similarity score."""
    ticket_id: uuid.UUID
    title: str
    status: str
    similarity: float
    student_id: uuid.UUID | None = None  
    created_at: datetime


class TicketCreateResponse(BaseModel):
    """Response when creating a ticket, includes duplicates."""
    ticket: TicketResponse
    possible_duplicates: list[DuplicateTicketResult]


class TicketUpdate(BaseModel):
    """Schema for updating ticket title/description (OPEN tickets only)."""
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = Field(None, min_length=1)
    topic_tag: str | None = Field(None, max_length=100)
