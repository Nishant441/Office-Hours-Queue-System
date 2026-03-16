"""Users API router (admin helpers)."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.user import User
from app.models.enums import UserRole
from app.schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserResponse])
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role([UserRole.ADMIN]))],
    role: UserRole | None = Query(None, description="Filter by role, e.g. TA"),
) -> list[User]:
    """Admin-only list users, optionally filtered by role."""
    query = select(User)
    if role:
        query = query.where(User.role == role)

    query = query.order_by(User.name.asc())
    result = await db.execute(query)
    return list(result.scalars().all())
