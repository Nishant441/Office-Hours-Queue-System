"""Course and CourseStaff models."""
import uuid
from datetime import datetime

from sqlalchemy import String, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Course(Base):
    """Course model."""
    
    __tablename__ = "courses"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    
    staff: Mapped[list["CourseStaff"]] = relationship("CourseStaff", back_populates="course", cascade="all, delete-orphan")
    sessions: Mapped[list["OfficeHoursSession"]] = relationship(
        "OfficeHoursSession", back_populates="course", cascade="all, delete-orphan"
    )
    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="course", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Course(id={self.id}, code={self.code}, name={self.name})>"


class CourseStaff(Base):
    """Association table for course staff assignments."""
    
    __tablename__ = "course_staff"
    
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id"), primary_key=True)
    assigned_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    
    user: Mapped["User"] = relationship("User", back_populates="course_staffs")
    course: Mapped["Course"] = relationship("Course", back_populates="staff")
    
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_user_course"),
    )
    
    def __repr__(self) -> str:
        return f"<CourseStaff(user_id={self.user_id}, course_id={self.course_id})>"
