"""Duplicate ticket detection using pgvector similarity search."""
import uuid

from sqlalchemy import select, and_, or_, Text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import cast

from app.models.ticket import Ticket, TicketEmbedding
from app.models.user import User
from app.models.enums import UserRole, TicketStatus
from app.schemas.ticket import DuplicateTicketResult
from app.core.config import settings


async def find_duplicates(
    db: AsyncSession,
    ticket_id: uuid.UUID,
    current_user: User,
    top_k: int = 5,
    threshold: float | None = None,
) -> list[DuplicateTicketResult]:
    """Find duplicate tickets using vector similarity search.
    
    Implements privacy rules:
    - Students can see: their own tickets + anonymized resolved tickets
    - TAs can see: all tickets from assigned courses
    - Admins can see: all tickets
    
    Args:
        db: Database session
        ticket_id: Target ticket ID to find duplicates for
        current_user: Current authenticated user
        top_k: Number of similar tickets to return (default: 5)
        threshold: Similarity threshold (default: from settings)
        
    Returns:
        List of similar tickets with similarity scores
    """
    if threshold is None:
        threshold = settings.DUPLICATE_SIMILARITY_THRESHOLD
    
    result = await db.execute(
        select(Ticket, TicketEmbedding)
        .join(TicketEmbedding, Ticket.id == TicketEmbedding.ticket_id)
        .where(Ticket.id == ticket_id)
    )
    row = result.one_or_none()
    
    if row is None:
        return []
    
    target_ticket, target_embedding = row
    
    privacy_conditions = []
    
    if current_user.role == UserRole.STUDENT:
        privacy_conditions.append(
            or_(
                Ticket.student_id == current_user.id,
                Ticket.status == TicketStatus.RESOLVED,
            )
        )
    elif current_user.role == UserRole.TA:
        privacy_conditions.append(Ticket.course_id == target_ticket.course_id)
        
    query = (
        select(
            Ticket,
            (1 - (TicketEmbedding.embedding.cosine_distance(target_embedding.embedding) / 2)).label('similarity')
        )
        .join(TicketEmbedding, Ticket.id == TicketEmbedding.ticket_id)
        .where(
            and_(
                Ticket.course_id == target_ticket.course_id,  
                Ticket.id != ticket_id,  
                *privacy_conditions,
            )
        )
        .order_by(TicketEmbedding.embedding.cosine_distance(target_embedding.embedding))
        .limit(top_k)
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    duplicates = []
    for ticket, similarity in rows:
        if similarity < threshold:
            continue

        if current_user.role == UserRole.STUDENT and ticket.student_id != current_user.id:
            student_id = None
        else:
            student_id = ticket.student_id

        duplicates.append(
            DuplicateTicketResult(
                ticket_id=ticket.id,
                title=ticket.title,
                status=ticket.status.value,
                similarity=round(float(similarity), 4),
                student_id=student_id,
                created_at=ticket.created_at,
            )
        )
    
    return duplicates
