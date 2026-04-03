"""Office hours session model."""
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class OfficeHoursSession(Base):
    """Office hours session model."""
    
    __tablename__ = "office_hours_sessions"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id"), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(nullable=False)
    ends_at: Mapped[datetime] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    
    course: Mapped["Course"] = relationship("Course", back_populates="sessions")
    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="session")
    
    def __repr__(self) -> str:
        return f"<OfficeHoursSession(id={self.id}, course_id={self.course_id}, is_active={self.is_active})>"
