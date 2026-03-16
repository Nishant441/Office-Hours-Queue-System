"""Tickets API router."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.models.ticket import Ticket
from app.models.course import CourseStaff
from app.models.user import User
from app.models.enums import UserRole, TicketStatus
from app.schemas.ticket import (
    TicketCreate,
    TicketResponse,
    TicketCreateResponse,
    DuplicateTicketResult,
)
from app.services.ticket_service import TicketService
from app.ai.duplicate_finder import find_duplicates

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("/", response_model=TicketCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    ticket_data: TicketCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role([UserRole.STUDENT]))],
) -> TicketCreateResponse:
    ticket, duplicates = await TicketService.create_ticket(
        db=db,
        session_id=ticket_data.session_id,
        student=current_user,
        title=ticket_data.title,
        description=ticket_data.description,
        topic_tag=ticket_data.topic_tag,
    )

    return TicketCreateResponse(
        ticket=TicketResponse.model_validate(ticket),
        possible_duplicates=duplicates,
    )


@router.get("/sessions/{session_id}/tickets", response_model=list[TicketResponse])
async def list_session_tickets(
    session_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role([UserRole.STUDENT, UserRole.TA, UserRole.ADMIN]))],
    status_filter: TicketStatus | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[Ticket]:
    """
    - STUDENT: can only see their own tickets in this session
    - TA/ADMIN: can see all tickets in this session
    """
    query = select(Ticket).where(Ticket.session_id == session_id)

    if current_user.role == UserRole.STUDENT:
        query = query.where(Ticket.student_id == current_user.id)

    if status_filter:
        query = query.where(Ticket.status == status_filter)

    query = query.order_by(Ticket.created_at.asc()).limit(limit).offset(offset)

    result = await db.execute(query)
    tickets = result.scalars().all()
    return list(tickets)


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Ticket:
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    if current_user.role == UserRole.STUDENT:
        if ticket.student_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only view your own tickets")

    elif current_user.role == UserRole.TA:
        result = await db.execute(
            select(CourseStaff).where(
                CourseStaff.user_id == current_user.id,
                CourseStaff.course_id == ticket.course_id,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view tickets from your assigned courses",
            )

    return ticket


@router.post("/{ticket_id}/claim", response_model=TicketResponse)
async def claim_ticket(
    ticket_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role([UserRole.TA]))],
) -> Ticket:
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()

    if ticket:
        result = await db.execute(
            select(CourseStaff).where(
                CourseStaff.user_id == current_user.id,
                CourseStaff.course_id == ticket.course_id,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only claim tickets from your assigned courses",
            )

    return await TicketService.claim_ticket(db, ticket_id, current_user)


@router.post("/{ticket_id}/start", response_model=TicketResponse)
async def start_ticket(
    ticket_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role([UserRole.TA]))],
) -> Ticket:
    return await TicketService.start_ticket(db, ticket_id, current_user)


@router.post("/{ticket_id}/resolve", response_model=TicketResponse)
async def resolve_ticket(
    ticket_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role([UserRole.TA]))],
) -> Ticket:
    return await TicketService.resolve_ticket(db, ticket_id, current_user)


@router.post("/{ticket_id}/cancel", response_model=TicketResponse)
async def cancel_ticket(
    ticket_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role([UserRole.STUDENT]))],
) -> Ticket:
    return await TicketService.cancel_ticket(db, ticket_id, current_user)


@router.get("/{ticket_id}/duplicates", response_model=list[DuplicateTicketResult])
async def get_ticket_duplicates(
    ticket_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    top_k: int = Query(5, ge=1, le=20),
    threshold: float | None = Query(None, ge=0.0, le=1.0),
) -> list[DuplicateTicketResult]:
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    if current_user.role == UserRole.STUDENT:
        if ticket.student_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view duplicates for your own tickets",
            )
    elif current_user.role == UserRole.TA:
        result = await db.execute(
            select(CourseStaff).where(
                CourseStaff.user_id == current_user.id,
                CourseStaff.course_id == ticket.course_id,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view duplicates from your assigned courses",
            )

    return await find_duplicates(db, ticket_id, current_user, top_k, threshold)
