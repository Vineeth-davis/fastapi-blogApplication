from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.auth.dependencies import get_current_active_user
from app.auth.utils import verify_token
from app.auth.rbac import require_approver
from app.blogs.schemas import BlogCreate, BlogUpdate, BlogResponse, BlogListResponse
from app.blogs.service import (
    list_approved_blogs,
    create_blog,
    get_blog_by_id,
    get_blog_for_view,
    update_blog,
    soft_delete_blog,
    approve_blog,
    reject_blog,
)
from app.database import get_db
from app.models.user import User, UserRole


router = APIRouter(prefix="/api/blogs", tags=["blogs"])


@router.get("/", response_model=BlogListResponse)
async def list_blogs(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    List approved blogs with pagination.

    Public endpoint: only approved, non-deleted blogs are returned.
    """
    items, total = await list_approved_blogs(db, limit=limit, offset=offset)
    return BlogListResponse(items=items, total=total, limit=limit, offset=offset)


@router.post(
    "/",
    response_model=BlogResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_blog_endpoint(
    payload: BlogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new blog post.

    - Authenticated user required.
    - New blogs are created with status `pending`.
    """
    blog = await create_blog(db, current_user=current_user, data=payload)
    return blog


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Optional dependency that returns User if authenticated, None otherwise."""
    if credentials is None:
        return None
    try:
        token = credentials.credentials
        payload = verify_token(token, token_type="access")
        if payload is None:
            return None
        
        user_id_raw = payload.get("sub")
        if user_id_raw is None:
            return None
        
        try:
            user_id = int(user_id_raw)
        except (ValueError, TypeError):
            return None
        
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        return user if user and user.is_active else None
    except:
        return None


@router.get("/{blog_id}", response_model=BlogResponse)
async def get_blog_endpoint(
    blog_id: int,
    db: AsyncSession = Depends(get_db),
    # Optional: authenticated user gets broader visibility
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Get blog details.

    - Public can see approved blogs.
    - Authors can see their own pending/rejected blogs.
    - Admins can see all blogs.
    """
    blog = await get_blog_for_view(db, blog_id, current_user)
    if blog is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")

    return blog


@router.put("/{blog_id}", response_model=BlogResponse)
async def update_blog_endpoint(
    blog_id: int,
    payload: BlogUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update a blog.

    - Author can edit only if blog is not approved.
    - Admin can edit any blog.
    """
    blog = await get_blog_by_id(db, blog_id)
    if blog is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")

    updated = await update_blog(db, blog, data=payload, current_user=current_user)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to update this blog",
        )

    return updated


@router.delete("/{blog_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_blog_endpoint(
    blog_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Soft delete a blog.

    - Author or admin can delete.
    - Deletion sets `deleted_at` instead of removing the record.
    """
    blog = await get_blog_by_id(db, blog_id)
    if blog is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")

    allowed = await soft_delete_blog(db, blog, current_user=current_user)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to delete this blog",
        )

    return


@router.post("/{blog_id}/approve", response_model=BlogResponse)
async def approve_blog_endpoint(
    blog_id: int,
    db: AsyncSession = Depends(get_db),
    approver: User = Depends(require_approver),
):
    """
    Approve a blog.

    - Only admins or L1 approvers can approve.
    - Once approved, the blog becomes publicly visible.
    """
    blog = await get_blog_by_id(db, blog_id)
    if blog is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")

    if blog.status == blog.status.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Blog is already approved",
        )

    approved = await approve_blog(db, blog, approver=approver)
    return approved


@router.post("/{blog_id}/reject", response_model=BlogResponse)
async def reject_blog_endpoint(
    blog_id: int,
    db: AsyncSession = Depends(get_db),
    approver: User = Depends(require_approver),
):
    """
    Reject a blog.

    - Only admins or L1 approvers can reject.
    """
    blog = await get_blog_by_id(db, blog_id)
    if blog is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")

    if blog.status == blog.status.REJECTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Blog is already rejected",
        )

    rejected = await reject_blog(db, blog, approver=approver)
    return rejected



