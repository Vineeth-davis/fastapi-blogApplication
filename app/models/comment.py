"""
Comment model for blog post comments.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class Comment(Base):
    """Comment model representing comments on blog posts."""

    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    blog_id = Column(Integer, ForeignKey("blogs.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)  # For soft deletes

    # Relationships
    blog = relationship("Blog", back_populates="comments")
    user = relationship("User", back_populates="comments")

    def __repr__(self) -> str:
        return f"<Comment(id={self.id}, blog_id={self.blog_id}, user_id={self.user_id})>"

