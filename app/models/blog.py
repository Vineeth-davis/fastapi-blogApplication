"""
Blog model for blogs.
"""

from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class BlogStatus(PyEnum):
    """Blog status enumeration."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Blog(Base):
    """Blog model representing blogs."""

    __tablename__ = "blogs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    content = Column(Text, nullable=False)  # Markdown or rich text content
    status = Column(Enum(BlogStatus), default=BlogStatus.PENDING, nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    images = Column(JSON, nullable=True)  # Array of image URLs/paths
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)  # For soft deletes

    # Relationships
    author = relationship("User", back_populates="blogs")
    comments = relationship("Comment", back_populates="blog", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Blog(id={self.id}, title={self.title[:50]}, status={self.status.value})>"

