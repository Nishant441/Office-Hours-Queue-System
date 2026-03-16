"""Office hours sessions API router."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.models.session import OfficeHoursSession
from app.models.ticket import Ticket
from app.models.course import Course, CourseStaff
from app.models.user import User
from app.models.enums import UserRole, TicketStatus
from app.schemas.session import SessionCreate, SessionResponse, SessionStats

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/active", response_model=SessionResponse | None)
async def get_active_session_for_course(
    course_id: Annotated[uuid.UUID, Query(...)],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> OfficeHoursSession | None:
    """
    Returns the active session for a course, if any.
    Any authenticated user can call this.
    """
    result = await db.execute(select(Course).where(Course.id == course_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Course not found")

    result = await db.execute(
        select(OfficeHoursSession)
        .where(
            OfficeHoursSession.course_id == course_id,
            OfficeHoursSession.is_active.is_(True),
        )
        .order_by(OfficeHoursSession.starts_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role([UserRole.TA, UserRole.ADMIN]))],
) -> OfficeHoursSession:
    result = await db.execute(select(Course).where(Course.id == session_data.course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if current_user.role == UserRole.TA:
        result = await db.execute(
            select(CourseStaff).where(
                CourseStaff.user_id == current_user.id,
                CourseStaff.course_id == session_data.course_id,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="You are not assigned to this course")

    session = OfficeHoursSession(
        course_id=session_data.course_id,
        starts_at=session_data.starts_at,
        ends_at=session_data.ends_at,
        is_active=True,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.post("/{session_id}/close", response_model=SessionResponse)
async def close_session(
    session_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role([UserRole.TA, UserRole.ADMIN]))],
) -> OfficeHoursSession:
    result = await db.execute(select(OfficeHoursSession).where(OfficeHoursSession.id == session_id))
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.is_active = False
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> OfficeHoursSession:
    result = await db.execute(select(OfficeHoursSession).where(OfficeHoursSession.id == session_id))
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session


@router.get("/{session_id}/stats", response_model=SessionStats)
async def get_session_stats(
    session_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role([UserRole.TA, UserRole.ADMIN]))],
) -> SessionStats:
    result = await db.execute(select(OfficeHoursSession).where(OfficeHoursSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await db.execute(
        select(Ticket.status, func.count(Ticket.id).label("count"))
        .where(Ticket.session_id == session_id)
        .group_by(Ticket.status)
    )
    status_counts = {row.status: row.count for row in result.all()}

    result = await db.execute(
        select(
            func.avg(func.extract("epoch", Ticket.claimed_at - Ticket.created_at)).label("avg_wait"),
            func.percentile_cont(0.5).within_group(
                func.extract("epoch", Ticket.claimed_at - Ticket.created_at)
            ).label("median_wait"),
        ).where(and_(Ticket.session_id == session_id, Ticket.claimed_at.isnot(None)))
    )
    wait_stats = result.one_or_none()

    result = await db.execute(
        select(func.avg(func.extract("epoch", Ticket.resolved_at - Ticket.created_at)).label("avg_resolve"))
        .where(and_(Ticket.session_id == session_id, Ticket.status == TicketStatus.RESOLVED))
    )
    resolve_stats = result.one_or_none()

    return SessionStats(
        count_open=status_counts.get(TicketStatus.OPEN, 0),
        count_claimed=status_counts.get(TicketStatus.CLAIMED, 0),
        count_in_progress=status_counts.get(TicketStatus.IN_PROGRESS, 0),
        count_resolved=status_counts.get(TicketStatus.RESOLVED, 0),
        count_cancelled=status_counts.get(TicketStatus.CANCELLED, 0),
        avg_wait_time_seconds=float(wait_stats.avg_wait) if wait_stats and wait_stats.avg_wait else None,
        median_wait_time_seconds=float(wait_stats.median_wait) if wait_stats and wait_stats.median_wait else None,
        avg_time_to_resolve_seconds=float(resolve_stats.avg_resolve) if resolve_stats and resolve_stats.avg_resolve else None,
    )
