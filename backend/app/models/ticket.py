"""Ticket, TicketEvent, and TicketEmbedding models."""
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, Enum as SQLEnum, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.db.base import Base
from app.models.enums import TicketStatus, TicketEventType


class Ticket(Base):
    """Ticket model for student help requests."""
    
    __tablename__ = "tickets"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("office_hours_sessions.id"), nullable=False)
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    assigned_ta_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    topic_tag: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    status: Mapped[TicketStatus] = mapped_column(
        SQLEnum(TicketStatus, name="ticket_status"),
        default=TicketStatus.OPEN,
        nullable=False,
        index=True
    )
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False, index=True)
    claimed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(nullable=True)
    
    # Relationships
    student: Mapped["User"] = relationship(
        "User", back_populates="tickets_created", foreign_keys=[student_id]
    )
    assigned_ta: Mapped["User"] = relationship(
        "User", back_populates="tickets_assigned", foreign_keys=[assigned_ta_id]
    )
    session: Mapped["OfficeHoursSession"] = relationship(
        "OfficeHoursSession", back_populates="tickets"
    )
    course: Mapped["Course"] = relationship("Course", back_populates="tickets")
    events: Mapped[list["TicketEvent"]] = relationship(
        "TicketEvent", back_populates="ticket", cascade="all, delete-orphan"
    )
    embedding: Mapped["TicketEmbedding"] = relationship(
        "TicketEmbedding", back_populates="ticket", uselist=False, cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Ticket(id={self.id}, title={self.title[:30]}, status={self.status})>"


class TicketEvent(Base):
    """Audit log for ticket state transitions."""
    
    __tablename__ = "ticket_events"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    event_type: Mapped[TicketEventType] = mapped_column(
        SQLEnum(TicketEventType, name="ticket_event_type"), nullable=False
    )
    from_status: Mapped[TicketStatus | None] = mapped_column(
        SQLEnum(TicketStatus, name="ticket_status"), nullable=True
    )
    to_status: Mapped[TicketStatus] = mapped_column(
        SQLEnum(TicketStatus, name="ticket_status"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="events")
    actor: Mapped["User"] = relationship("User")
    
    def __repr__(self) -> str:
        return f"<TicketEvent(id={self.id}, ticket_id={self.ticket_id}, event_type={self.event_type})>"


class TicketEmbedding(Base):
    """Vector embeddings for ticket similarity search using pgvector."""
    
    __tablename__ = "ticket_embeddings"
    
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), primary_key=True
    )
    embedding: Mapped[Vector] = mapped_column(Vector(384), nullable=False)  
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    
    
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="embedding")
    
    def __repr__(self) -> str:
        return f"<TicketEmbedding(ticket_id={self.ticket_id})>"
