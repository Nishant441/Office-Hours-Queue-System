"""Tests for authentication endpoints."""
import pytest
from httpx import AsyncClient

from app.models.user import User


class TestRegister:
    """Tests for user registration."""
    
    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "name": "New User",
                "email": "newuser@test.com",
                "password": "securepassword123",
                "role": "STUDENT",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert data["name"] == "New User"
        assert data["role"] == "STUDENT"
        assert "id" in data
        assert "password" not in data
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, student_user: User):
        """Test registration with existing email returns conflict."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "name": "Another User",
                "email": student_user.email,
                "password": "password123",
            },
        )
        
        assert response.status_code == 409
        assert "already registered" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email format."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "name": "Test User",
                "email": "not-an-email",
                "password": "password123",
            },
        )
        
        assert response.status_code == 422  # Validation error


class TestLogin:
    """Tests for user login."""
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, student_user: User):
        """Test successful login returns JWT token."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "student@test.com",
                "password": "password123",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_invalid_password(self, client: AsyncClient, student_user: User):
        """Test login with wrong password returns unauthorized."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "student@test.com",
                "password": "wrongpassword",
            },
        )
        
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent email."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@test.com",
                "password": "password123",
            },
        )
        
        assert response.status_code == 401


class TestProtectedEndpoints:
    """Tests for protected endpoint access."""
    
    @pytest.mark.asyncio
    async def test_access_without_token(self, client: AsyncClient):
        """Test accessing protected endpoint without token."""
        response = await client.get("/api/v1/courses/")
        assert response.status_code == 403  # No credentials provided
    
    @pytest.mark.asyncio
    async def test_access_with_valid_token(self, client: AsyncClient, student_token: str):
        """Test accessing protected endpoint with valid token."""
        response = await client.get(
            "/api/v1/courses/",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_access_with_invalid_token(self, client: AsyncClient):
        """Test accessing protected endpoint with invalid token."""
        response = await client.get(
            "/api/v1/courses/",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401
