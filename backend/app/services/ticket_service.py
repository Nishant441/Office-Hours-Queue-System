"""Ticket service with business logic and state machine."""
import uuid
from datetime import datetime, timedelta, timezone
from collections import defaultdict

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ticket import Ticket, TicketEvent, TicketEmbedding
from app.models.session import OfficeHoursSession
from app.models.user import User
from app.models.enums import TicketStatus, TicketEventType
from app.ai.embeddings import get_embedding_provider
from app.ai.duplicate_finder import find_duplicates
from app.schemas.ticket import DuplicateTicketResult
from app.core.websocket import manager


# State machine: valid transitions
VALID_TRANSITIONS = {
    TicketStatus.OPEN: [TicketStatus.CLAIMED, TicketStatus.CANCELLED],
    TicketStatus.CLAIMED: [TicketStatus.IN_PROGRESS],
    TicketStatus.IN_PROGRESS: [TicketStatus.RESOLVED],
}




class TicketService:
    """Business logic for ticket operations."""
    
    @staticmethod
    def _get_utcnow() -> datetime:
        """Get current UTC time as naive datetime."""
        return datetime.now(timezone.utc).replace(tzinfo=None)

    @staticmethod
    async def _broadcast_ticket_update(ticket: Ticket):
        """Broadcast ticket update to all session clients."""
        await manager.broadcast(
            ticket.session_id,
            {"type": "TICKET_UPDATED", "ticket_id": str(ticket.id), "status": ticket.status.value},
        )


    
    @staticmethod
    async def create_ticket(
        db: AsyncSession,
        session_id: uuid.UUID,
        student: User,
        title: str,
        description: str,
        topic_tag: str | None = None,
    ) -> tuple[Ticket, list[DuplicateTicketResult]]:
        """Create a new ticket with embedding and duplicate detection.
        
        Args:
            db: Database session
            session_id: Office hours session ID
            student: Student creating the ticket
            title: Ticket title
            description: Ticket description
            topic_tag: Optional topic tag
            
        Returns:
            Tuple of (created ticket, list of duplicate tickets)
            
        Raises:
            HTTPException: If session not found, inactive, or rate limit exceeded
        """

        
        # Verify session exists and is active
        result = await db.execute(
            select(OfficeHoursSession).where(OfficeHoursSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Office hours session not found",
            )
        
        if not session.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create ticket for inactive session",
            )
        
        # Create ticket
        ticket = Ticket(
            session_id=session_id,
            course_id=session.course_id,
            student_id=student.id,
            title=title,
            description=description,
            topic_tag=topic_tag,
            status=TicketStatus.OPEN,
        )
        db.add(ticket)
        await db.flush()  
        
        # Generate embedding
        embedding_provider = get_embedding_provider()
        embedding_vector = embedding_provider.encode_ticket(title, description, topic_tag)
        
        ticket_embedding = TicketEmbedding(
            ticket_id=ticket.id,
            embedding=embedding_vector,
        )
        db.add(ticket_embedding)
        
        # Log creation event
        event = TicketEvent(
            ticket_id=ticket.id,
            actor_user_id=student.id,
            event_type=TicketEventType.CREATED,
            from_status=None,
            to_status=TicketStatus.OPEN,
        )
        db.add(event)
        
        await db.commit()
        await db.refresh(ticket)
        
        # Broadcast update
        await TicketService._broadcast_ticket_update(ticket)
        
        # Find duplicates
        duplicates = await find_duplicates(db, ticket.id, student, top_k=5)
        
        return ticket, duplicates
    
    @staticmethod
    async def claim_ticket(
        db: AsyncSession,
        ticket_id: uuid.UUID,
        ta: User,
    ) -> Ticket:
        """TA claims an open ticket.
        
        Args:
            db: Database session
            ticket_id: Ticket ID to claim
            ta: TA user claiming the ticket
            
        Returns:
            Updated ticket
            
        Raises:
            HTTPException: If ticket not found or invalid state transition
        """
        result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
        ticket = result.scalar_one_or_none()
        
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found",
            )
        
        # Validate state transition
        if ticket.status != TicketStatus.OPEN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot claim ticket with status {ticket.status.value}. Must be OPEN.",
            )
        
        # Update ticket
        now = TicketService._get_utcnow()
        ticket.status = TicketStatus.CLAIMED
        ticket.assigned_ta_id = ta.id
        ticket.claimed_at = now
        
        # Log event
        event = TicketEvent(
            ticket_id=ticket_id,
            actor_user_id=ta.id,
            event_type=TicketEventType.CLAIMED,
            from_status=TicketStatus.OPEN,
            to_status=TicketStatus.CLAIMED,
        )
        db.add(event)
        
        await db.commit()
        await db.refresh(ticket)
        
        # Broadcast update
        await TicketService._broadcast_ticket_update(ticket)
        
        return ticket
    
    @staticmethod
    async def start_ticket(
        db: AsyncSession,
        ticket_id: uuid.UUID,
        ta: User,
    ) -> Ticket:
        """TA starts working on a claimed ticket.
        
        Args:
            db: Database session
            ticket_id: Ticket ID to start
            ta: TA user starting the ticket
            
        Returns:
            Updated ticket
        """
        result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
        ticket = result.scalar_one_or_none()
        
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found",
            )
        
        if ticket.status != TicketStatus.CLAIMED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot start ticket with status {ticket.status.value}. Must be CLAIMED.",
            )
        
        if ticket.assigned_ta_id != ta.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the assigned TA can start this ticket",
            )
        
        # Update ticket
        now = TicketService._get_utcnow()
        ticket.status = TicketStatus.IN_PROGRESS
        ticket.started_at = now
        
        # Log event
        event = TicketEvent(
            ticket_id=ticket_id,
            actor_user_id=ta.id,
            event_type=TicketEventType.STARTED,
            from_status=TicketStatus.CLAIMED,
            to_status=TicketStatus.IN_PROGRESS,
        )
        db.add(event)
        
        await db.commit()
        await db.refresh(ticket)
        
        # Broadcast update
        await TicketService._broadcast_ticket_update(ticket)
        
        return ticket
    
    @staticmethod
    async def resolve_ticket(
        db: AsyncSession,
        ticket_id: uuid.UUID,
        ta: User,
    ) -> Ticket:
        """TA resolves an in-progress ticket.
        
        Args:
            db: Database session
            ticket_id: Ticket ID to resolve
            ta: TA user resolving the ticket
            
        Returns:
            Updated ticket
        """
        result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
        ticket = result.scalar_one_or_none()
        
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found",
            )
        
        if ticket.status != TicketStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot resolve ticket with status {ticket.status.value}. Must be IN_PROGRESS.",
            )
        
        if ticket.assigned_ta_id != ta.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the assigned TA can resolve this ticket",
            )
        
        # Update ticket
        now = TicketService._get_utcnow()
        ticket.status = TicketStatus.RESOLVED
        ticket.resolved_at = now
        
        # Log event
        event = TicketEvent(
            ticket_id=ticket_id,
            actor_user_id=ta.id,
            event_type=TicketEventType.RESOLVED,
            from_status=TicketStatus.IN_PROGRESS,
            to_status=TicketStatus.RESOLVED,
        )
        db.add(event)
        
        await db.commit()
        await db.refresh(ticket)
        
        # Broadcast update
        await TicketService._broadcast_ticket_update(ticket)
        
        return ticket
    
    @staticmethod
    async def cancel_ticket(
        db: AsyncSession,
        ticket_id: uuid.UUID,
        student: User,
    ) -> Ticket:
        """Student cancels their own open ticket.
        
        Args:
            db: Database session
            ticket_id: Ticket ID to cancel
            student: Student user canceling the ticket
            
        Returns:
            Updated ticket
        """
        result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
        ticket = result.scalar_one_or_none()
        
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found",
            )
        
        if ticket.student_id != student.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only cancel your own tickets",
            )
        
        if ticket.status != TicketStatus.OPEN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel ticket with status {ticket.status.value}. Can only cancel OPEN tickets.",
            )
        
        # Update ticket
        now = TicketService._get_utcnow()
        ticket.status = TicketStatus.CANCELLED
        ticket.cancelled_at = now
        
        # Log event
        event = TicketEvent(
            ticket_id=ticket_id,
            actor_user_id=student.id,
            event_type=TicketEventType.CANCELLED,
            from_status=TicketStatus.OPEN,
            to_status=TicketStatus.CANCELLED,
        )
        db.add(event)
        
        await db.commit()
        await db.refresh(ticket)
        
        # Broadcast update
        await TicketService._broadcast_ticket_update(ticket)
        
        return ticket
