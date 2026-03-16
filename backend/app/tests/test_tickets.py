"""Tests for ticket workflow and permissions."""
import uuid

import pytest
from httpx import AsyncClient

from app.models.user import User
from app.models.session import OfficeHoursSession


class TestTicketCreation:
    """Tests for creating tickets."""
    
    @pytest.mark.asyncio
    async def test_create_ticket_success(
        self,
        client: AsyncClient,
        student_token: str,
        active_session: OfficeHoursSession,
    ):
        """Test student can create a ticket for active session."""
        response = await client.post(
            "/api/v1/tickets/",
            json={
                "session_id": str(active_session.id),
                "title": "Need help with recursion",
                "description": "I don't understand how recursion works in tree traversal",
                "topic_tag": "algorithms",
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "ticket" in data
        assert "possible_duplicates" in data
        assert data["ticket"]["title"] == "Need help with recursion"
        assert data["ticket"]["status"] == "OPEN"
        assert isinstance(data["possible_duplicates"], list)
    



class TestTicketStateTransitions:
    """Tests for ticket state machine transitions."""
    
    @pytest.mark.asyncio
    async def test_claim_ticket_success(
        self,
        client: AsyncClient,
        student_token: str,
        ta_token: str,
        active_session: OfficeHoursSession,
    ):
        """Test TA can claim an open ticket."""
        # Student creates ticket
        response = await client.post(
            "/api/v1/tickets/",
            json={
                "session_id": str(active_session.id),
                "title": "Help needed",
                "description": "Description",
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )
        ticket_id = response.json()["ticket"]["id"]
        
        # TA claims ticket
        response = await client.post(
            f"/api/v1/tickets/{ticket_id}/claim",
            headers={"Authorization": f"Bearer {ta_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CLAIMED"
        assert data["claimed_at"] is not None
        assert data["assigned_ta_id"] is not None
    
    @pytest.mark.asyncio
    async def test_start_ticket_success(
        self,
        client: AsyncClient,
        student_token: str,
        ta_token: str,
        active_session: OfficeHoursSession,
    ):
        """Test TA can start a claimed ticket."""
        # Create and claim ticket
        response = await client.post(
            "/api/v1/tickets/",
            json={
                "session_id": str(active_session.id),
                "title": "Help needed",
                "description": "Description",
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )
        ticket_id = response.json()["ticket"]["id"]
        
        await client.post(
            f"/api/v1/tickets/{ticket_id}/claim",
            headers={"Authorization": f"Bearer {ta_token}"},
        )
        
        # Start ticket
        response = await client.post(
            f"/api/v1/tickets/{ticket_id}/start",
            headers={"Authorization": f"Bearer {ta_token}"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "IN_PROGRESS"
    
    @pytest.mark.asyncio
    async def test_resolve_ticket_success(
        self,
        client: AsyncClient,
        student_token: str,
        ta_token: str,
        active_session: OfficeHoursSession,
    ):
        """Test complete ticket lifecycle: OPEN -> CLAIMED -> IN_PROGRESS -> RESOLVED."""
        # Create ticket
        response = await client.post(
            "/api/v1/tickets/",
            json={
                "session_id": str(active_session.id),
                "title": "Help needed",
                "description": "Description",
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )
        ticket_id = response.json()["ticket"]["id"]
        
        # Claim
        await client.post(
            f"/api/v1/tickets/{ticket_id}/claim",
            headers={"Authorization": f"Bearer {ta_token}"},
        )
        
        # Start
        await client.post(
            f"/api/v1/tickets/{ticket_id}/start",
            headers={"Authorization": f"Bearer {ta_token}"},
        )
        
        # Resolve
        response = await client.post(
            f"/api/v1/tickets/{ticket_id}/resolve",
            headers={"Authorization": f"Bearer {ta_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "RESOLVED"
        assert data["resolved_at"] is not None
    
    @pytest.mark.asyncio
    async def test_cancel_ticket_success(
        self,
        client: AsyncClient,
        student_token: str,
        active_session: OfficeHoursSession,
    ):
        """Test student can cancel their own OPEN ticket."""
        # Create ticket
        response = await client.post(
            "/api/v1/tickets/",
            json={
                "session_id": str(active_session.id),
                "title": "Help needed",
                "description": "Description",
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )
        ticket_id = response.json()["ticket"]["id"]
        
        # Cancel
        response = await client.post(
            f"/api/v1/tickets/{ticket_id}/cancel",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "CANCELLED"
    
    @pytest.mark.asyncio
    async def test_cannot_cancel_claimed_ticket(
        self,
        client: AsyncClient,
        student_token: str,
        ta_token: str,
        active_session: OfficeHoursSession,
    ):
        """Test student cannot cancel a ticket that has been claimed."""
        # Create and claim ticket
        response = await client.post(
            "/api/v1/tickets/",
            json={
                "session_id": str(active_session.id),
                "title": "Help needed",
                "description": "Description",
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )
        ticket_id = response.json()["ticket"]["id"]
        
        await client.post(
            f"/api/v1/tickets/{ticket_id}/claim",
            headers={"Authorization": f"Bearer {ta_token}"},
        )
        
        # Try to cancel
        response = await client.post(
            f"/api/v1/tickets/{ticket_id}/cancel",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == 400
        assert "OPEN" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_invalid_state_transition(
        self,
        client: AsyncClient,
        student_token: str,
        ta_token: str,
        active_session: OfficeHoursSession,
    ):
        """Test invalid state transitions are rejected."""
        # Create ticket (OPEN)
        response = await client.post(
            "/api/v1/tickets/",
            json={
                "session_id": str(active_session.id),
                "title": "Help needed",
                "description": "Description",
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )
        ticket_id = response.json()["ticket"]["id"]
        
        # Try to start without claiming first (OPEN -> IN_PROGRESS is invalid)
        response = await client.post(
            f"/api/v1/tickets/{ticket_id}/start",
            headers={"Authorization": f"Bearer {ta_token}"},
        )
        assert response.status_code == 400
        assert "CLAIMED" in response.json()["detail"]


class TestPermissions:
    """Tests for permission checks and IDOR prevention."""
    
    @pytest.mark.asyncio
    async def test_student_cannot_claim_ticket(
        self,
        client: AsyncClient,
        student_token: str,
        active_session: OfficeHoursSession,
    ):
        """Test students cannot claim tickets."""
        # Create ticket
        response = await client.post(
            "/api/v1/tickets/",
            json={
                "session_id": str(active_session.id),
                "title": "Help needed",
                "description": "Description",
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )
        ticket_id = response.json()["ticket"]["id"]
        
        # Try to claim with student token
        response = await client.post(
            f"/api/v1/tickets/{ticket_id}/claim",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_student_cannot_view_other_tickets(
        self,
        client: AsyncClient,
        db,
        student_token: str,
        active_session: OfficeHoursSession,
    ):
        """Test students can only view their own tickets (IDOR prevention)."""
        # Create another student
        from app.models.user import User
        from app.models.enums import UserRole
        from app.core.security import get_password_hash, create_access_token
        
        other_student = User(
            id=uuid.uuid4(),
            name="Other Student",
            email="other@test.com",
            password_hash=get_password_hash("password123"),
            role=UserRole.STUDENT,
        )
        db.add(other_student)
        await db.commit()
        await db.refresh(other_student)
        
        other_token = create_access_token(
            data={"user_id": str(other_student.id), "role": other_student.role.value}
        )
        
        # Other student creates a ticket
        response = await client.post(
            "/api/v1/tickets/",
            json={
                "session_id": str(active_session.id),
                "title": "Private ticket",
                "description": "Description",
            },
            headers={"Authorization": f"Bearer {other_token}"},
        )
        ticket_id = response.json()["ticket"]["id"]
        
        # Original student tries to view it
        response = await client.get(
            f"/api/v1/tickets/{ticket_id}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == 403
