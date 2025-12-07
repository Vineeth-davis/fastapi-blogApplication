"""
Tests for blog CRUD operations and approval workflow.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.blog import Blog, BlogStatus
from app.models.user import User, UserRole


@pytest.mark.asyncio
@pytest.mark.blogs
class TestBlogCRUD:
    """Test blog CRUD operations."""

    async def test_create_blog(self, client: AsyncClient, auth_headers: dict):
        """
        Test creating a blog post (user).

        This test is required by the assignment.
        """
        response = await client.post(
            "/api/blogs/",
            headers=auth_headers,
            json={
                "title": "My First Blog Post",
                "content": "This is the content of my first blog post.",
                "images": ["https://example.com/image1.jpg"],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "My First Blog Post"
        assert data["content"] == "This is the content of my first blog post."
        assert data["status"] == BlogStatus.PENDING.value
        assert "author_id" in data
        assert "id" in data

    async def test_create_blog_admin(self, client: AsyncClient, admin_headers: dict):
        """
        Test creating a blog post (admin).

        This test is required by the assignment.
        """
        response = await client.post(
            "/api/blogs/",
            headers=admin_headers,
            json={
                "title": "Admin Blog Post",
                "content": "This is an admin blog post.",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Admin Blog Post"
        assert data["status"] == BlogStatus.PENDING.value

    async def test_create_blog_unauthorized(self, client: AsyncClient):
        """Test creating a blog without authentication."""
        response = await client.post(
            "/api/blogs/",
            json={
                "title": "Unauthorized Blog",
                "content": "This should fail.",
            },
        )

        assert response.status_code == 401

    async def test_list_blogs_public(self, client: AsyncClient, approved_blog: Blog):
        """Test listing approved blogs (public endpoint)."""
        response = await client.get("/api/blogs/")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) > 0
        # Only approved blogs should be visible
        for blog in data["items"]:
            assert blog["status"] == BlogStatus.APPROVED.value

    async def test_get_blog_by_id_public(self, client: AsyncClient, approved_blog: Blog):
        """Test getting a single approved blog (public)."""
        response = await client.get(f"/api/blogs/{approved_blog.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == approved_blog.id
        assert data["title"] == approved_blog.title

    async def test_get_pending_blog_public(self, client: AsyncClient, test_blog: Blog):
        """Test getting a pending blog (should not be visible to public)."""
        response = await client.get(f"/api/blogs/{test_blog.id}")

        assert response.status_code == 404

    async def test_get_own_pending_blog(self, client: AsyncClient, auth_headers: dict, test_blog: Blog):
        """Test getting own pending blog (author can see it)."""
        response = await client.get(f"/api/blogs/{test_blog.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_blog.id

    async def test_update_own_blog(self, client: AsyncClient, auth_headers: dict, test_blog: Blog):
        """Test updating own blog (if not approved)."""
        response = await client.put(
            f"/api/blogs/{test_blog.id}",
            headers=auth_headers,
            json={
                "title": "Updated Title",
                "content": "Updated content.",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["content"] == "Updated content."

    async def test_update_other_user_blog(self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
        """Test updating another user's blog (should fail)."""
        # Create another user and blog
        from app.models.user import User
        from app.auth.utils import hash_password

        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password=hash_password("password123"),
            role=UserRole.USER,
            is_active=True,
        )
        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)

        from app.models.blog import Blog, BlogStatus

        other_blog = Blog(
            title="Other User's Blog",
            content="Content",
            status=BlogStatus.PENDING,
            author_id=other_user.id,
        )
        db_session.add(other_blog)
        await db_session.commit()
        await db_session.refresh(other_blog)

        # Try to update
        response = await client.put(
            f"/api/blogs/{other_blog.id}",
            headers=auth_headers,
            json={"title": "Hacked Title"},
        )

        assert response.status_code == 403

    async def test_delete_own_blog(self, client: AsyncClient, auth_headers: dict, test_blog: Blog):
        """Test deleting own blog."""
        response = await client.delete(f"/api/blogs/{test_blog.id}", headers=auth_headers)

        assert response.status_code in [200, 204]  # Both are valid for DELETE

        # Verify it's soft deleted (not visible)
        get_response = await client.get(f"/api/blogs/{test_blog.id}", headers=auth_headers)
        assert get_response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.blogs
class TestBlogApproval:
    """Test blog approval workflow."""

    async def test_approve_blog_admin(self, client: AsyncClient, admin_headers: dict, test_blog: Blog):
        """Test admin approving a blog."""
        response = await client.post(
            f"/api/blogs/{test_blog.id}/approve",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == BlogStatus.APPROVED.value

    async def test_approve_blog_approver(self, client: AsyncClient, test_approver: User, test_blog: Blog):
        """Test L1 approver approving a blog."""
        # Login as approver
        login_response = await client.post(
            "/api/auth/login",
            json={"email": "approver@example.com", "password": "approverpassword123"},
        )
        approver_headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

        response = await client.post(
            f"/api/blogs/{test_blog.id}/approve",
            headers=approver_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == BlogStatus.APPROVED.value

    async def test_approve_blog_user(self, client: AsyncClient, auth_headers: dict, test_blog: Blog):
        """Test regular user trying to approve (should fail)."""
        response = await client.post(
            f"/api/blogs/{test_blog.id}/approve",
            headers=auth_headers,
        )

        assert response.status_code == 403

    async def test_reject_blog_admin(self, client: AsyncClient, admin_headers: dict, test_blog: Blog):
        """Test admin rejecting a blog."""
        response = await client.post(
            f"/api/blogs/{test_blog.id}/reject",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == BlogStatus.REJECTED.value

    async def test_reject_blog_user(self, client: AsyncClient, auth_headers: dict, test_blog: Blog):
        """Test regular user trying to reject (should fail)."""
        response = await client.post(
            f"/api/blogs/{test_blog.id}/reject",
            headers=auth_headers,
        )

        assert response.status_code == 403

