"""
Feature Request model for user-submitted feature requests.
"""

from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from app.database import Base


class FeatureRequestStatus(PyEnum):
    """Feature request status enumeration."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class FeatureRequest(Base):
    """Feature Request model representing user-submitted feature requests."""

    __tablename__ = "feature_requests"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=False)
    status = Column(Enum(FeatureRequestStatus), default=FeatureRequestStatus.PENDING, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    priority = Column(Integer, default=0, nullable=True)  # Priority rating (0-5 or similar)
    rating = Column(Integer, default=0, nullable=True)  # User rating/votes
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="feature_requests")

    def __repr__(self) -> str:
        return f"<FeatureRequest(id={self.id}, title={self.title[:50]}, status={self.status.value})>"

