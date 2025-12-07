from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class DraftSave(BaseModel):
    """Schema for saving draft blog data."""

    title: Optional[str] = Field(default=None, max_length=500)
    content: Optional[str] = Field(default=None)
    images: Optional[List[str]] = Field(default=None, description="List of image URLs")


class DraftResponse(BaseModel):
    """Schema for draft response."""

    title: Optional[str] = None
    content: Optional[str] = None
    images: Optional[List[str]] = None
    saved_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True

