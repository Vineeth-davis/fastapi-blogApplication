"""
Service functions for session/draft management.
"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.session import Session
from app.models.user import User
from app.session.schemas import DraftSave


async def save_draft(
    db: AsyncSession,
    current_user: User,
    draft_data: DraftSave,
) -> Session:
    """
    Save or update draft blog data for the current user.

    Args:
        db: Database session
        current_user: Current authenticated user
        draft_data: Draft data to save

    Returns:
        Session object with saved draft
    """
    # Check if session exists for user
    result = await db.execute(
        select(Session).where(Session.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()

    # Prepare draft data as JSON
    draft_json = draft_data.model_dump(exclude_unset=True, exclude_none=True)

    if session:
        # Update existing session
        session.draft_data = draft_json
        session.updated_at = datetime.utcnow()
        # Extend expiry if needed (30 days from now)
        session.expires_at = datetime.utcnow() + timedelta(days=30)
    else:
        # Create new session
        session = Session(
            user_id=current_user.id,
            draft_data=draft_json,
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        db.add(session)

    await db.flush()
    await db.refresh(session)
    return session


async def get_draft(
    db: AsyncSession,
    current_user: User,
) -> Optional[Session]:
    """
    Retrieve draft blog data for the current user.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        Session object if draft exists and not expired, None otherwise
    """
    result = await db.execute(
        select(Session).where(Session.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()

    if session is None:
        return None

    # Check if expired
    if session.is_expired():
        # Optionally delete expired session
        await db.delete(session)
        await db.flush()
        return None

    return session

