"""
Feature requests endpoints.

Per assignment:
- GET  /api/feature-requests/         : User - list feature requests
- POST /api/feature-requests/         : User - submit feature request
- PATCH /api/feature-requests/{id}    : Admin - update feature request status
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.auth.rbac import require_admin
from app.database import get_db
from app.feature_requests.schemas import (
    FeatureRequestCreate,
    FeatureRequestUpdate,
    FeatureRequestResponse,
    FeatureRequestListResponse,
)
from app.models.feature_request import FeatureRequest, FeatureRequestStatus
from app.models.user import User


router = APIRouter(prefix="/api/feature-requests", tags=["feature-requests"])


@router.get("/", response_model=FeatureRequestListResponse)
async def list_feature_requests(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status_filter: Optional[FeatureRequestStatus] = Query(
        default=None, alias="status"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List feature requests.

    - Regular users see only their own requests.
    - Admins see all requests.
    - Optional filter by status.
    """
    query = select(FeatureRequest)

    if not current_user.role.name.lower() == "admin":
        query = query.where(FeatureRequest.user_id == current_user.id)

    if status_filter is not None:
        query = query.where(FeatureRequest.status == status_filter)

    total_query = select(func.count()).select_from(query.subquery())

    query = query.order_by(FeatureRequest.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    items = result.scalars().all()

    total_result = await db.execute(total_query)
    total = int(total_result.scalar_one())

    return FeatureRequestListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/",
    response_model=FeatureRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_feature_request(
    payload: FeatureRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Submit a feature request.

    - User creates with status `pending`.
    """
    fr = FeatureRequest(
        title=payload.title,
        description=payload.description,
        status=FeatureRequestStatus.PENDING,
        user_id=current_user.id,
        priority=payload.priority if payload.priority is not None else 0,
    )
    db.add(fr)
    await db.flush()
    await db.refresh(fr)
    return fr


@router.patch(
    "/{feature_request_id}",
    response_model=FeatureRequestResponse,
)
async def update_feature_request(
    feature_request_id: int,
    payload: FeatureRequestUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    Update feature request status (admin only).

    - Allowed status values: pending / accepted / declined.
    - Admin can also adjust priority and rating.
    """
    result = await db.execute(
        select(FeatureRequest).where(FeatureRequest.id == feature_request_id)
    )
    fr = result.scalar_one_or_none()
    if fr is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feature request not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(fr, field, value)

    await db.flush()
    await db.refresh(fr)
    return fr


