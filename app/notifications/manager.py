"""
In-memory notifications manager for Server-Sent Events (SSE).

Admins can subscribe to an SSE stream to receive real-time notifications
when new blogs are submitted with status `pending`.
"""

import asyncio
import json
from typing import AsyncIterator, Dict
from uuid import uuid4

from app.models.blog import Blog


class NotificationsManager:
    """
    Manages SSE connections and broadcasts notifications.
    """

    def __init__(self) -> None:
        # client_id -> asyncio.Queue[str]
        self._clients: Dict[str, asyncio.Queue[str]] = {}

    async def connect(self) -> AsyncIterator[str]:
        """
        Register a new SSE client and yield messages as they arrive.

        Yields already-formatted SSE lines (including 'data: ...\\n\\n').
        """
        client_id = str(uuid4())
        queue: asyncio.Queue[str] = asyncio.Queue()
        self._clients[client_id] = queue

        try:
            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connected'})}\n\n"
            
            while True:
                # Use timeout to prevent hanging
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {message}\n\n"
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield f": heartbeat\n\n"
        finally:
            # Remove client on disconnect
            self._clients.pop(client_id, None)

    async def notify_new_pending_blog(self, blog: Blog) -> None:
        """
        Broadcast a new pending blog notification to all connected clients.
        """
        if not self._clients:
            # No clients connected, nothing to do
            return

        payload = {
            "type": "new_pending_blog",
            "blog_id": blog.id,
            "title": blog.title,
            "author_id": blog.author_id,
        }
        message = json.dumps(payload)

        # Fan out to all clients
        # Use put_nowait to avoid blocking if queue is full (shouldn't happen with unbounded queue)
        for client_id, queue in self._clients.items():
            try:
                queue.put_nowait(message)
            except Exception:
                # If put_nowait fails (unlikely), try await put
                await queue.put(message)


# Singleton manager instance
notifications_manager = NotificationsManager()


