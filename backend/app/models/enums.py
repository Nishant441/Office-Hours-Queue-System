"""Enums for database models."""
import enum


class UserRole(str, enum.Enum):
    """User role enumeration."""
    STUDENT = "STUDENT"
    TA = "TA"
    ADMIN = "ADMIN"


class TicketStatus(str, enum.Enum):
    """Ticket status enumeration."""
    OPEN = "OPEN"
    CLAIMED = "CLAIMED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CANCELLED = "CANCELLED"


class TicketEventType(str, enum.Enum):
    """Ticket event type enumeration."""
    CREATED = "CREATED"
    CLAIMED = "CLAIMED"
    STARTED = "STARTED"
    RESOLVED = "RESOLVED"
    CANCELLED = "CANCELLED"
    UPDATED = "UPDATED"
