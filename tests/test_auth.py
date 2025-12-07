"""
Tests for authentication endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


@pytest.mark.asyncio
@pytest.mark.auth
class TestAuthentication:
    """Test authentication endpoints."""

    async def test_register_success(self, client: AsyncClient, db_session: AsyncSession):
        """Test successful user registration."""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "password123",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert data["role"] == UserRole.USER.value
        assert "hashed_password" not in data
        assert "password" not in data

    async def test_register_duplicate_email(self, client: AsyncClient, test_user: User):
        """Test registration with duplicate email."""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "username": "differentuser",
                "password": "password123",
            },
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    async def test_register_duplicate_username(self, client: AsyncClient, test_user: User):
        """Test registration with duplicate username."""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "different@example.com",
                "username": "testuser",
                "password": "password123",
            },
        )

        assert response.status_code == 400
        assert "username" in response.json()["detail"].lower()

    async def test_register_weak_password(self, client: AsyncClient):
        """Test registration with weak password."""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "user@example.com",
                "username": "user",
                "password": "short",  # Too short
            },
        )

        # Should fail validation (Pydantic will validate min length)
        assert response.status_code in [400, 422]

    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Test successful login."""
        response = await client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "testpassword123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient, test_user: User):
        """Test login with wrong password."""
        response = await client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "wrongpassword"},
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower() or "invalid" in response.json()["detail"].lower()

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user."""
        response = await client.post(
            "/api/auth/login",
            json={"email": "nonexistent@example.com", "password": "password123"},
        )

        assert response.status_code == 401

    async def test_get_current_user(self, client: AsyncClient, auth_headers: dict):
        """Test getting current user info."""
        response = await client.get("/api/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"

    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test getting current user without authentication."""
        response = await client.get("/api/auth/me")

        assert response.status_code == 401

    async def test_refresh_token(self, client: AsyncClient, test_user: User):
        """Test token refresh."""
        # First login
        login_response = await client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "testpassword123"},
        )
        assert login_response.status_code == 200
        refresh_token = login_response.json()["refresh_token"]

        # Refresh token
        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test refresh with invalid token."""
        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid_token"},
        )

        assert response.status_code == 401

