from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import require_admin
from app.database import get_db
from app.models.user import User
from app.notifications.manager import notifications_manager

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("/sse")
async def notifications_sse(
    _: User = Depends(require_admin),
    __: AsyncSession = Depends(get_db),
):
    """
    SSE stream for new pending blogs.

    - Admin-only endpoint.
    - Yields an event whenever a new blog is created with status `pending`.
    """

    async def event_generator():
        async for message in notifications_manager.connect():
            yield message

    return StreamingResponse(event_generator(), media_type="text/event-stream")


