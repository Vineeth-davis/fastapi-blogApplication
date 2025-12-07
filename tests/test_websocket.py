"""
Tests for WebSocket chat/comments functionality.
"""

import pytest
import json
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.models.blog import Blog, BlogStatus
from app.models.comment import Comment
from app.main import app
from sqlalchemy import select

@pytest.mark.websocket
class TestWebSocketComments:
    """Test WebSocket comment functionality."""

    @pytest.mark.asyncio
    async def test_websocket_connection(self, db_session, auth_headers: dict, approved_blog: Blog):
        """Test WebSocket connection to blog chat."""
        from app.database import get_db
        
        # Override get_db dependency - need async generator
        async def override_get_db():
            yield db_session
        
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            # Create TestClient (synchronous, but supports WebSockets)
            test_client = TestClient(app)
            
            # Get access token - auth_headers is async, so we need to await it
            # Actually, fixtures are auto-awaited by pytest, so this should work
            token = auth_headers["Authorization"].split(" ")[1]

            # Connect via WebSocket
            with test_client.websocket_connect(
                f"/api/blogs/{approved_blog.id}/ws?token={token}"
            ) as websocket:
                # Connection should be successful
                assert websocket is not None
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_websocket_unauthorized(self, db_session, approved_blog: Blog):
        """Test WebSocket connection without authentication."""
        from app.database import get_db
        
        # Override get_db dependency
        async def override_get_db():
            yield db_session
        
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            test_client = TestClient(app)
            
            # WebSocket connection without token should fail
            with pytest.raises(Exception):  # WebSocket connection should fail
                with test_client.websocket_connect(
                    f"/api/blogs/{approved_blog.id}/ws"
                ) as websocket:
                    pass
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_websocket_send_message(self, db_session, auth_headers: dict, approved_blog: Blog):
        """Test sending a message via WebSocket."""
        from app.database import get_db
        
        # Override get_db dependency
        async def override_get_db():
            yield db_session
        
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            test_client = TestClient(app)
            token = auth_headers["Authorization"].split(" ")[1]

            with test_client.websocket_connect(
                f"/api/blogs/{approved_blog.id}/ws?token={token}"
            ) as websocket:
                # Send a message
                message = {
                    "type": "comment",
                    "content": "This is a test comment",
                }
                websocket.send_json(message)

                # Should receive the message back (broadcast)
                received = websocket.receive_json()
                assert received["type"] == "comment"
                assert received["content"] == "This is a test comment"
                assert "user_id" in received
                assert "created_at" in received
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_websocket_broadcast(self, db_session, auth_headers: dict, admin_headers: dict, approved_blog: Blog):
        """Test that messages are broadcast to all connected clients."""
        from app.database import get_db
        
        # Override get_db dependency
        async def override_get_db():
            yield db_session
        
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            test_client = TestClient(app)
            token1 = auth_headers["Authorization"].split(" ")[1]
            token2 = admin_headers["Authorization"].split(" ")[1]

            # Connect two clients
            with test_client.websocket_connect(
                f"/api/blogs/{approved_blog.id}/ws?token={token1}"
            ) as ws1:
                with test_client.websocket_connect(
                    f"/api/blogs/{approved_blog.id}/ws?token={token2}"
                ) as ws2:
                    # Send message from client 1
                    message = {
                        "type": "comment",
                        "content": "Broadcast test message",
                    }
                    ws1.send_json(message)

                    # Both clients should receive the message
                    # Client 1 receives its own message
                    msg1 = ws1.receive_json()
                    assert msg1["content"] == "Broadcast test message"

                    # Client 2 receives the broadcast
                    msg2 = ws2.receive_json()
                    assert msg2["content"] == "Broadcast test message"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_websocket_invalid_blog(self, db_session, auth_headers: dict):
        """Test WebSocket connection to non-existent blog."""
        from app.database import get_db
        
        # Override get_db dependency
        async def override_get_db():
            yield db_session
        
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            test_client = TestClient(app)
            token = auth_headers["Authorization"].split(" ")[1]

            # Should fail to connect to non-existent blog
            with pytest.raises(Exception):  # Should fail
                with test_client.websocket_connect(
                    f"/api/blogs/99999/ws?token={token}"
                ) as websocket:
                    pass
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_websocket_comment_persistence(self, db_session, auth_headers: dict, approved_blog: Blog):
        """Test that comments are persisted to database."""
        from app.database import get_db
        
        # Override get_db dependency
        app.dependency_overrides[get_db] = lambda: db_session
        
        try:
            test_client = TestClient(app)
            token = auth_headers["Authorization"].split(" ")[1]

            with test_client.websocket_connect(
                f"/api/blogs/{approved_blog.id}/ws?token={token}"
            ) as websocket:
                # Send a comment
                message = {
                    "type": "comment",
                    "content": "Persistent comment",
                }
                websocket.send_json(message)

                # Receive the broadcast (to ensure processing is complete)
                websocket.receive_json()

            # Verify comment was saved to database
            result = await db_session.execute(
                select(Comment).where(Comment.blog_id == approved_blog.id)
            )
            comments = result.scalars().all()
            assert len(comments) > 0
            assert any(c.content == "Persistent comment" for c in comments)
        finally:
            app.dependency_overrides.clear()

