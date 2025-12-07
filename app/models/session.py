"""
Session model for storing draft blog posts.
"""

from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Session(Base):
    """Session model for storing draft blog post data."""

    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, unique=True)
    draft_data = Column(JSON, nullable=True)  # Store draft blog data (title, content, images, etc.)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="sessions")

    def __init__(self, *args, **kwargs):
        """Initialize session with default expiry (30 days)."""
        super().__init__(*args, **kwargs)
        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(days=30)

    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.utcnow() > self.expires_at

    def __repr__(self) -> str:
        return f"<Session(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"

