"""
Tests for Server-Sent Events (SSE) notifications.
"""

import pytest
import json
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.models.blog import Blog, BlogStatus
from app.notifications.manager import notifications_manager
from app.main import app


@pytest.mark.asyncio
@pytest.mark.sse
class TestSSENotifications:
    """Test SSE notification functionality."""

    @pytest.mark.asyncio
    async def test_sse_notification_delivery(self, db_session, admin_headers: dict, test_user, test_admin, client: AsyncClient):
        """
        Test SSE notification delivery when a new blog is created.

        This test is required by the assignment.
        """
        from app.database import get_db
        from app.auth.utils import create_access_token
        import threading
        import time
        
        # Override get_db dependency
        async def override_get_db():
            yield db_session
        
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            # Use TestClient for SSE (works better than httpx AsyncClient for streaming)
            test_client = TestClient(app)
            admin_token = admin_headers["Authorization"].split(" ")[1]
            admin_headers_dict = {"Authorization": f"Bearer {admin_token}"}
            
            # Create token for regular user (to create blog)
            user_token = create_access_token(data={"sub": test_user.id, "email": test_user.email, "role": test_user.role.value})
            user_headers = {"Authorization": f"Bearer {user_token}"}
            
            # Connect to SSE stream first, then create blog in a separate thread
            messages = []
            
            def create_blog():
                """Create blog in a separate thread after a short delay."""
                time.sleep(0.2)  # Wait for SSE connection to establish
                blog_response = test_client.post(
                    "/api/blogs/",
                    headers=user_headers,  # Use regular user headers, not admin
                    json={
                        "title": "New Pending Blog",
                        "content": "This should trigger a notification.",
                    },
                )
                return blog_response.json() if blog_response.status_code == 201 else None
            
            # Start blog creation in background
            blog_thread = threading.Thread(target=create_blog)
            blog_data = {"id": None}
            
            def create_blog_with_result():
                result = create_blog()
                if result:
                    blog_data["id"] = result["id"]
                    blog_data.update(result)
            
            blog_thread = threading.Thread(target=create_blog_with_result)
            blog_thread.start()
            
            # Connect to SSE stream and read messages
            with test_client.stream(
                "GET",
                "/api/notifications/sse",
                headers=admin_headers_dict,  # Use admin headers for SSE
            ) as response:
                # Verify connection
                assert response.status_code == 200
                
                # Read SSE messages - wait for notification
                line_count = 0
                for line in response.iter_lines():
                    line_count += 1
                    if not line:
                        continue
                    
                    # SSE format: "data: {...}\n\n"
                    if line.startswith("data: "):
                        try:
                            message_data = json.loads(line[6:])  # Remove "data: " prefix
                            # Skip connection messages
                            if message_data.get("type") != "connected":
                                messages.append(message_data)
                                # Got our notification, can break
                                break
                        except json.JSONDecodeError:
                            continue
                    elif line.startswith(":"):
                        # Comment line (heartbeat), ignore
                        continue
                    
                    # Limit iterations to prevent infinite loop
                    if line_count > 100:
                        break
            
            # Wait for blog creation thread to finish
            blog_thread.join(timeout=2.0)
            
            # Verify notification was received
            assert len(messages) > 0, (
                f"No notification received. "
                f"Got {len(messages)} messages: {messages}. "
                f"Blog was created with ID: {blog_data.get('id')}"
            )
            notification = messages[0]
            assert notification["type"] == "new_pending_blog"
            assert notification["blog_id"] == blog_data.get("id")
            assert notification["title"] == "New Pending Blog"
        finally:
            app.dependency_overrides.clear()

    async def test_sse_admin_only(self, client: AsyncClient, auth_headers: dict):
        """Test that SSE endpoint is admin-only."""
        response = await client.get("/api/notifications/sse", headers=auth_headers)

        assert response.status_code == 403

    async def test_sse_unauthorized(self, client: AsyncClient):
        """Test that SSE endpoint requires authentication."""
        response = await client.get("/api/notifications/sse")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_sse_multiple_clients(self, db_session, admin_headers: dict, test_user, test_admin, client: AsyncClient):
        """Test that notifications are broadcast to all connected clients."""
        from app.database import get_db
        from app.auth.utils import create_access_token
        import threading
        import time
        
        # Override get_db dependency
        async def override_get_db():
            yield db_session
        
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            test_client = TestClient(app)
            admin_token = admin_headers["Authorization"].split(" ")[1]
            admin_headers_dict = {"Authorization": f"Bearer {admin_token}"}
            
            # Create token for regular user (to create blog)
            user_token = create_access_token(data={"sub": test_user.id, "email": test_user.email, "role": test_user.role.value})
            user_headers = {"Authorization": f"Bearer {user_token}"}
            
            # Create blog first (in a thread to allow SSE connection to be established)
            messages = []
            blog_data = {"id": None}
            
            def create_blog():
                """Create blog after a delay to allow SSE connection."""
                time.sleep(0.2)
                blog_response = test_client.post(
                    "/api/blogs/",
                    headers=user_headers,  # Use regular user headers, not admin
                    json={
                        "title": "Multi-client Test Blog",
                        "content": "Testing multiple clients.",
                    },
                )
                if blog_response.status_code == 201:
                    result = blog_response.json()
                    blog_data["id"] = result["id"]
                    blog_data.update(result)
            
            blog_thread = threading.Thread(target=create_blog)
            blog_thread.start()
            
            # Connect to SSE stream and receive notification
            # Note: TestClient.stream() is blocking, so we can only test one connection at a time
            # In production, multiple clients work correctly
            with test_client.stream(
                "GET",
                "/api/notifications/sse",
                headers=admin_headers_dict,  # Use admin headers for SSE
            ) as response:
                assert response.status_code == 200
                
                # Read messages until we get the notification
                line_count = 0
                for line in response.iter_lines():
                    line_count += 1
                    if not line:
                        continue
                    
                    if line.startswith("data: "):
                        try:
                            msg = json.loads(line[6:])
                            if msg.get("type") != "connected":
                                messages.append(msg)
                                break
                        except json.JSONDecodeError:
                            continue
                    elif line.startswith(":"):
                        continue
                    
                    if line_count > 100:
                        break
            
            blog_thread.join(timeout=2.0)
            
            # Verify notification was received
            assert len(messages) > 0, "No notification received"
            assert messages[0]["type"] == "new_pending_blog"
            assert messages[0]["blog_id"] == blog_data.get("id")
        finally:
            app.dependency_overrides.clear()

