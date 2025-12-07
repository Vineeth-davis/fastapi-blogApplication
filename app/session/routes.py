from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import get_current_active_user
from app.database import get_db
from app.models.user import User
from app.session.schemas import DraftSave, DraftResponse
from app.session.service import save_draft, get_draft

router = APIRouter(prefix="/api/session", tags=["session"])


@router.get("/draft", response_model=DraftResponse)
async def get_draft_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get saved draft for blog submission.

    - Authenticated user required.
    - Returns draft data if exists and not expired.
    - Returns empty draft if no draft exists.
    """
    session = await get_draft(db, current_user)

    if session is None or not session.draft_data:
        # Return empty draft
        return DraftResponse()

    draft_data = session.draft_data or {}
    return DraftResponse(
        title=draft_data.get("title"),
        content=draft_data.get("content"),
        images=draft_data.get("images"),
        saved_at=session.updated_at,
        expires_at=session.expires_at,
    )


@router.post("/draft", response_model=DraftResponse, status_code=status.HTTP_200_OK)
async def save_draft_endpoint(
    draft_data: DraftSave,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Save draft for blog submission.

    - Authenticated user required.
    - Saves draft data (title, content, images) for the current user.
    - Updates existing draft or creates new one.
    - Draft expires after 30 days.
    """
    session = await save_draft(db, current_user, draft_data)

    draft_json = session.draft_data or {}
    return DraftResponse(
        title=draft_json.get("title"),
        content=draft_json.get("content"),
        images=draft_json.get("images"),
        saved_at=session.updated_at,
        expires_at=session.expires_at,
    )

