"""Seed script for demo data.

Run with: python -m app.scripts.seed_data
"""
import asyncio
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.models.course import Course, CourseStaff
from app.models.session import OfficeHoursSession
from app.models.enums import UserRole
from app.core.security import get_password_hash


async def seed_demo_data():
    """Seed database with demo data for testing."""
    async with AsyncSessionLocal() as db:
        print("🌱 Seeding demo data...")
        
        # Create users
        admin = User(
            id=uuid.uuid4(),
            name="Admin User",
            email="admin@university.edu",
            password_hash=get_password_hash("admin123"),
            role=UserRole.ADMIN,
        )
        
        ta1 = User(
            id=uuid.uuid4(),
            name="Alice TA",
            email="alice.ta@university.edu",
            password_hash=get_password_hash("ta123"),
            role=UserRole.TA,
        )
        
        ta2 = User(
            id=uuid.uuid4(),
            name="Bob TA",
            email="bob.ta@university.edu",
            password_hash=get_password_hash("ta123"),
            role=UserRole.TA,
        )
        
        student1 = User(
            id=uuid.uuid4(),
            name="Charlie Student",
            email="charlie@university.edu",
            password_hash=get_password_hash("student123"),
            role=UserRole.STUDENT,
        )
        
        student2 = User(
            id=uuid.uuid4(),
            name="Diana Student",
            email="diana@university.edu",
            password_hash=get_password_hash("student123"),
            role=UserRole.STUDENT,
        )
        
        db.add_all([admin, ta1, ta2, student1, student2])
        await db.commit()
        print("Created 5 users (1 admin, 2 TAs, 2 students)")
        
        # Create courses
        cs101 = Course(
            id=uuid.uuid4(),
            code="CS101",
            name="Introduction to Computer Science",
        )
        
        cs201 = Course(
            id=uuid.uuid4(),
            code="CS201",
            name="Data Structures and Algorithms",
        )
        
        db.add_all([cs101, cs201])
        await db.commit()
        print("Created 2 courses (CS101, CS201)")
        
        # Assign TAs to courses
        assignments = [
            CourseStaff(user_id=ta1.id, course_id=cs101.id),
            CourseStaff(user_id=ta1.id, course_id=cs201.id),
            CourseStaff(user_id=ta2.id, course_id=cs201.id),
        ]
        db.add_all(assignments)
        await db.commit()
        print("Assigned TAs to courses")
        
        # Create active office hours sessions
        now = datetime.now(timezone.utc)
        
        session1 = OfficeHoursSession(
            id=uuid.uuid4(),
            course_id=cs101.id,
            starts_at=now,
            ends_at=now + timedelta(hours=2),
            is_active=True,
        )
        
        session2 = OfficeHoursSession(
            id=uuid.uuid4(),
            course_id=cs201.id,
            starts_at=now,
            ends_at=now + timedelta(hours=3),
            is_active=True,
        )
        
        db.add_all([session1, session2])
        await db.commit()
        print("Created 2 active office hours sessions")
        
        print("\n🎉 Demo data seeded successfully!")
        print("\n📝 Login credentials:")
        print("  Admin:    admin@university.edu / admin123")
        print("  TA:       alice.ta@university.edu / ta123")
        print("  Student:  charlie@university.edu / student123")
        print(f"\n🎟️  Session IDs:")
        print(f"  CS101: {session1.id}")
        print(f"  CS201: {session2.id}")


if __name__ == "__main__":
    asyncio.run(seed_demo_data())
