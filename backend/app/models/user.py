"""User model."""
import uuid
from datetime import datetime

from sqlalchemy import String, Enum as SQLEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import UserRole


class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole, name="user_role"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    
    # Relationships
    course_staffs: Mapped[list["CourseStaff"]] = relationship(
        "CourseStaff", back_populates="user", foreign_keys="CourseStaff.user_id"
    )
    tickets_created: Mapped[list["Ticket"]] = relationship(
        "Ticket", back_populates="student", foreign_keys="Ticket.student_id"
    )
    tickets_assigned: Mapped[list["Ticket"]] = relationship(
        "Ticket", back_populates="assigned_ta", foreign_keys="Ticket.assigned_ta_id"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
