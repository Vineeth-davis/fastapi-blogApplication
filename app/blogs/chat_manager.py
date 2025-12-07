"""
WebSocket chat manager for blog comments.

Manages WebSocket connections per blog post and broadcasts messages
to all connected clients for a given blog.
"""

from typing import Dict, Set

from fastapi import WebSocket


class ChatManager:
    """
    In-memory chat manager.

    Stores active WebSocket connections per blog_id.
    """

    def __init__(self) -> None:
        # blog_id -> set of WebSockets
        self._connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, blog_id: int, websocket: WebSocket) -> None:
        """
        Register a WebSocket connection for a blog.
        """
        await websocket.accept()
        self._connections.setdefault(blog_id, set()).add(websocket)

    def disconnect(self, blog_id: int, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection for a blog.
        """
        if blog_id in self._connections:
            self._connections[blog_id].discard(websocket)
            if not self._connections[blog_id]:
                self._connections.pop(blog_id, None)

    async def broadcast(self, blog_id: int, message: str) -> None:
        """
        Broadcast a message to all WebSocket connections for a blog.
        """
        connections = self._connections.get(blog_id, set()).copy()
        for ws in connections:
            try:
                await ws.send_text(message)
            except Exception:
                # Best-effort cleanup on send failure
                self.disconnect(blog_id, ws)


chat_manager = ChatManager()


