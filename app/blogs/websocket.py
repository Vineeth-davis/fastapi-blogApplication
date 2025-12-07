"""
WebSocket endpoint for real-time blog comments.

Endpoint (per assignment):
- WS /api/blogs/{id}/ws : Real-time chat/comments under each blog post,
  broadcast to all connected clients (no polling).
"""

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.auth.utils import verify_token
from app.database import get_db
from app.models.blog import Blog
from app.models.comment import Comment
from app.models.user import User
from app.blogs.chat_manager import chat_manager

router = APIRouter(tags=["blog-comments"])


async def _get_user_from_token(
    token: str,
    db: AsyncSession,
) -> Optional[User]:
    """
    Decode access token and return active user, or None if invalid.
    """
    payload = verify_token(token, token_type="access")
    if payload is None:
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        return None

    result = await db.execute(select(User).where(User.id == user_id_int))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        return None

    return user


@router.websocket("/api/blogs/{blog_id}/ws")
async def blog_comments_websocket(
    websocket: WebSocket,
    blog_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket endpoint for blog comments/chat.

    Auth:
    - Requires a valid JWT access token passed as a query parameter: ?token=...
    - Only authenticated, active users may connect.

    Behavior:
    - On connection, validates blog existence and user token.
    - On incoming "comment" messages, stores a Comment record and broadcasts
      the comment to all clients connected to this blog.
    """
    # Extract token from query params
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Validate user
    user = await _get_user_from_token(token, db)
    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Ensure blog exists (and is not soft-deleted)
    result = await db.execute(
        select(Blog).where(Blog.id == blog_id, Blog.deleted_at.is_(None))
    )
    blog = result.scalar_one_or_none()
    if blog is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await chat_manager.connect(blog_id, websocket)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                # Ignore invalid JSON
                continue

            msg_type = data.get("type")
            if msg_type == "comment":
                content = (data.get("content") or "").strip()
                if not content:
                    continue

                # Store comment in DB
                comment = Comment(
                    content=content,
                    blog_id=blog_id,
                    user_id=user.id,
                    created_at=datetime.utcnow(),
                )
                db.add(comment)
                await db.flush()
                await db.refresh(comment)

                # Broadcast comment to all clients for this blog
                outgoing = {
                    "type": "comment",
                    "blog_id": blog_id,
                    "comment_id": comment.id,
                    "content": comment.content,
                    "user_id": user.id,
                    "username": user.username,
                    "created_at": comment.created_at.isoformat() + "Z",
                }
                await chat_manager.broadcast(blog_id, json.dumps(outgoing))
            else:
                # for future chats - ignore for now
                continue
    except WebSocketDisconnect:
        chat_manager.disconnect(blog_id, websocket)
    except Exception:
        chat_manager.disconnect(blog_id, websocket)
        await websocket.close()


