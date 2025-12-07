"""
Pydantic schemas for feature request operations.
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field

from app.models.feature_request import FeatureRequestStatus


class FeatureRequestBase(BaseModel):
    """Base fields for a feature request."""

    title: str = Field(..., min_length=3, max_length=500)
    description: str = Field(..., min_length=1)
    priority: Optional[int] = Field(
        default=None,
        ge=0,
        le=5,
        description="Priority rating from 0 to 5",
    )


class FeatureRequestCreate(FeatureRequestBase):
    """Payload for creating a feature request."""

    pass


class FeatureRequestUpdate(BaseModel):
    """Payload for updating feature request fields (admin)."""

    status: Optional[FeatureRequestStatus] = None
    priority: Optional[int] = Field(default=None, ge=0, le=5)
    rating: Optional[int] = Field(
        default=None,
        ge=0,
        description="Aggregate rating or votes",
    )


class FeatureRequestResponse(BaseModel):
    """Response schema for a single feature request."""

    id: int
    title: str
    description: str
    status: FeatureRequestStatus
    user_id: int
    priority: Optional[int]
    rating: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FeatureRequestListResponse(BaseModel):
    """Paginated list of feature requests."""

    items: List[FeatureRequestResponse]
    total: int
    limit: int
    offset: int


