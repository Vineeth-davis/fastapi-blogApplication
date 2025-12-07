"""
Schemas for blog operations.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.blog import BlogStatus


class BlogBase(BaseModel):
    """Base fields for a blog."""

    title: str = Field(..., min_length=3, max_length=500)
    content: str = Field(..., min_length=1)
    images: Optional[List[str]] = Field(default=None, description="List of image URLs")


class BlogCreate(BlogBase):
    """Payload for creating a blog."""

    pass


class BlogUpdate(BaseModel):
    """Payload for updating a blog (partial update)."""

    title: Optional[str] = Field(default=None, min_length=3, max_length=500)
    content: Optional[str] = Field(default=None, min_length=1)
    images: Optional[List[str]] = Field(default=None, description="List of image URLs")


class BlogResponse(BaseModel):
    """Response schema for a single blog."""

    id: int
    title: str
    content: str
    images: Optional[List[str]]
    status: BlogStatus
    author_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BlogListResponse(BaseModel):
    """Paginated list of blogs."""

    items: List[BlogResponse]
    total: int
    limit: int
    offset: int


