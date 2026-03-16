"""Courses API router."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.models.course import Course, CourseStaff
from app.models.user import User
from app.models.enums import UserRole
from app.schemas.course import CourseCreate, CourseResponse

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("/", response_model=list[CourseResponse])
async def list_courses(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[Course]:
    """
    Admin/Student: all courses
    TA: only assigned courses
    """
    if current_user.role == UserRole.TA:
        result = await db.execute(
            select(Course)
            .options(selectinload(Course.staff).selectinload(CourseStaff.user))
            .join(CourseStaff, CourseStaff.course_id == Course.id)
            .where(CourseStaff.user_id == current_user.id)
        )
        return list(result.scalars().all())

    result = await db.execute(
        select(Course)
        .options(selectinload(Course.staff).selectinload(CourseStaff.user))
    )
    return list(result.scalars().all())


@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    course_data: CourseCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role([UserRole.ADMIN]))],
) -> Course:

    result = await db.execute(select(Course).where(Course.code == course_data.code))
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Course with code '{course_data.code}' already exists",
        )

    course = Course(code=course_data.code, name=course_data.name)
    db.add(course)
    await db.commit()
    await db.refresh(course)

    return CourseResponse(
        id=course.id,
        code=course.code,
        name=course.name,
        created_at=course.created_at,
        staff=[]
    )


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role([UserRole.ADMIN]))],
):
    """Delete a course and all associated data."""
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
        
    await db.delete(course)
    await db.commit()


@router.post("/{course_id}/staff/{user_id}", status_code=status.HTTP_201_CREATED)
async def assign_staff_to_course(
    course_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role([UserRole.ADMIN]))],
) -> dict:
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role != UserRole.TA:
        raise HTTPException(status_code=400, detail="User must have TA role")

    result = await db.execute(
        select(CourseStaff).where(
            CourseStaff.user_id == user_id,
            CourseStaff.course_id == course_id,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="TA already assigned to this course")

    assignment = CourseStaff(user_id=user_id, course_id=course_id)
    db.add(assignment)
    await db.commit()

    return {"message": f"TA {user.name} assigned to course {course.code}"}


@router.delete("/{course_id}/staff/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_staff_from_course(
    course_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role([UserRole.ADMIN]))],
):
    """Remove a TA from a course."""
    result = await db.execute(
        select(CourseStaff).where(
            CourseStaff.user_id == user_id,
            CourseStaff.course_id == course_id,
        )
    )
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="TA assignment not found for this course",
        )

    from app.models.ticket import Ticket
    from app.models.enums import TicketStatus
    from sqlalchemy import update

    await db.execute(
        update(Ticket)
        .where(
            Ticket.course_id == course_id,
            Ticket.assigned_ta_id == user_id,
            Ticket.status.in_([TicketStatus.CLAIMED, TicketStatus.IN_PROGRESS]),
        )
        .values(
            status=TicketStatus.OPEN,
            assigned_ta_id=None,
            claimed_at=None,
            started_at=None,
        )
    )

    await db.delete(assignment)
    await db.commit()
