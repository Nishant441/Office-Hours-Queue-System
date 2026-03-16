"""Initial schema with pgvector extension

Revision ID: 001_initial
Revises:
Create Date: 2026-01-29 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create ENUM types (idempotent) + reuse them without recreating
    op.execute(
        """
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
        CREATE TYPE user_role AS ENUM ('STUDENT', 'TA', 'ADMIN');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ticket_status') THEN
        CREATE TYPE ticket_status AS ENUM ('OPEN', 'CLAIMED', 'IN_PROGRESS', 'RESOLVED', 'CANCELLED');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ticket_event_type') THEN
        CREATE TYPE ticket_event_type AS ENUM ('CREATED', 'CLAIMED', 'STARTED', 'RESOLVED', 'CANCELLED', 'UPDATED');
    END IF;
END$$;
"""
    )

    user_role_enum = postgresql.ENUM(
        "STUDENT", "TA", "ADMIN", name="user_role", create_type=False
    )
    ticket_status_enum = postgresql.ENUM(
        "OPEN", "CLAIMED", "IN_PROGRESS", "RESOLVED", "CANCELLED",
        name="ticket_status",
        create_type=False,
    )
    ticket_event_type_enum = postgresql.ENUM(
        "CREATED", "CLAIMED", "STARTED", "RESOLVED", "CANCELLED", "UPDATED",
        name="ticket_event_type",
        create_type=False,
    )

    # Create users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", user_role_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # Create courses table
    op.create_table(
        "courses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_courses_code", "courses", ["code"], unique=True)

    # Create course_staff table
    op.create_table(
        "course_staff",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id"), primary_key=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_unique_constraint("uq_user_course", "course_staff", ["user_id", "course_id"])

    # Create office_hours_sessions table
    op.create_table(
        "office_hours_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_sessions_starts_at", "office_hours_sessions", ["starts_at"])

    # Create tickets table
    op.create_table(
        "tickets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("office_hours_sessions.id"), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("assigned_ta_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("topic_tag", sa.String(100), nullable=True),
        sa.Column("status", ticket_status_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_tickets_status", "tickets", ["status"])
    op.create_index("ix_tickets_created_at", "tickets", ["created_at"])

    # Create ticket_events table
    op.create_table(
        "ticket_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("event_type", ticket_event_type_enum, nullable=False),
        sa.Column("from_status", ticket_status_enum, nullable=True),
        sa.Column("to_status", ticket_status_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ticket_events_ticket_id", "ticket_events", ["ticket_id"])

    # Create ticket_embeddings table with pgvector
    op.create_table(
        "ticket_embeddings",
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tickets.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("embedding", postgresql.ARRAY(sa.Float), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Convert embedding column to vector type
    op.execute(
        "ALTER TABLE ticket_embeddings ALTER COLUMN embedding TYPE vector(384) USING embedding::vector(384)"
    )

    # Create IVFFlat index for ANN search
    op.execute(
        """
CREATE INDEX idx_ticket_embeddings_vector
ON ticket_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100)
"""
    )


def downgrade() -> None:
    op.drop_index("idx_ticket_embeddings_vector", table_name="ticket_embeddings")
    op.drop_table("ticket_embeddings")

    op.drop_index("ix_ticket_events_ticket_id", table_name="ticket_events")
    op.drop_table("ticket_events")

    op.drop_index("ix_tickets_created_at", table_name="tickets")
    op.drop_index("ix_tickets_status", table_name="tickets")
    op.drop_table("tickets")

    op.drop_index("ix_sessions_starts_at", table_name="office_hours_sessions")
    op.drop_table("office_hours_sessions")

    op.drop_table("course_staff")

    op.drop_index("ix_courses_code", table_name="courses")
    op.drop_table("courses")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    # Drop enum types and extension
    op.execute("DROP TYPE IF EXISTS ticket_event_type")
    op.execute("DROP TYPE IF EXISTS ticket_status")
    op.execute("DROP TYPE IF EXISTS user_role")
    op.execute("DROP EXTENSION IF EXISTS vector")
