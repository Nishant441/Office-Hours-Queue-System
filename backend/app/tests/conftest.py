"""Pytest configuration and fixtures."""
import asyncio
import uuid
from typing import AsyncGenerator
from datetime import datetime, timezone, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.models.user import User
from app.models.course import Course, CourseStaff
from app.models.session import OfficeHoursSession
from app.models.enums import UserRole
from app.core.security import get_password_hash, create_access_token


# Test database URL (use separate test database)
TEST_DATABASE_URL = settings.DATABASE_URL_TEST or settings.DATABASE_URL.replace("office_hours", "office_hours_test")

# Create async engine for tests
test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session with automatic rollback."""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()
    
    # Drop tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database override."""
    async def override_get_db():
        yield db
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


# User fixtures
@pytest_asyncio.fixture
async def student_user(db: AsyncSession) -> User:
    """Create a test student user."""
    user = User(
        id=uuid.uuid4(),
        name="Test Student",
        email="student@test.com",
        password_hash=get_password_hash("password123"),
        role=UserRole.STUDENT,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def ta_user(db: AsyncSession) -> User:
    """Create a test TA user."""
    user = User(
        id=uuid.uuid4(),
        name="Test TA",
        email="ta@test.com",
        password_hash=get_password_hash("password123"),
        role=UserRole.TA,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db: AsyncSession) -> User:
    """Create a test admin user."""
    user = User(
        id=uuid.uuid4(),
        name="Test Admin",
        email="admin@test.com",
        password_hash=get_password_hash("password123"),
        role=UserRole.ADMIN,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# Token fixtures
@pytest.fixture
def student_token(student_user: User) -> str:
    """Create JWT token for student user."""
    return create_access_token(data={"user_id": str(student_user.id), "role": student_user.role.value})


@pytest.fixture
def ta_token(ta_user: User) -> str:
    """Create JWT token for TA user."""
    return create_access_token(data={"user_id": str(ta_user.id), "role": ta_user.role.value})


@pytest.fixture
def admin_token(admin_user: User) -> str:
    """Create JWT token for admin user."""
    return create_access_token(data={"user_id": str(admin_user.id), "role": admin_user.role.value})


# Course and session fixtures
@pytest_asyncio.fixture
async def sample_course(db: AsyncSession, admin_user: User) -> Course:
    """Create a test course."""
    course = Course(
        id=uuid.uuid4(),
        code="CS101",
        name="Introduction to Computer Science",
    )
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return course


@pytest_asyncio.fixture
async def ta_assigned_course(db: AsyncSession, sample_course: Course, ta_user: User) -> Course:
    """Assign TA to course."""
    assignment = CourseStaff(user_id=ta_user.id, course_id=sample_course.id)
    db.add(assignment)
    await db.commit()
    return sample_course


@pytest_asyncio.fixture
async def active_session(db: AsyncSession, ta_assigned_course: Course) -> OfficeHoursSession:
    """Create an active office hours session."""
    now = datetime.now(timezone.utc)
    session = OfficeHoursSession(
        id=uuid.uuid4(),
        course_id=ta_assigned_course.id,
        starts_at=now,
        ends_at=now + timedelta(hours=2),
        is_active=True,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session
