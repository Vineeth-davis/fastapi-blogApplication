"""
functions for blog CRUD operations
"""

from datetime import datetime
from typing import Optional, Tuple, List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.blog import Blog, BlogStatus
from app.models.user import User, UserRole
from app.blogs.schemas import BlogCreate, BlogUpdate
from app.notifications.manager import notifications_manager


async def list_approved_blogs(
    db: AsyncSession,
    limit: int,
    offset: int,
) -> Tuple[List[Blog], int]:
    """
    List approved, non-deleted blogs with pagination.
    """
    base_query = (
        select(Blog)
        .where(
            Blog.status == BlogStatus.APPROVED,
            Blog.deleted_at.is_(None),
        )
        .order_by(Blog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(base_query)
    items: List[Blog] = result.scalars().all()

    count_query = select(func.count()).select_from(
        select(Blog.id)
        .where(
            Blog.status == BlogStatus.APPROVED,
            Blog.deleted_at.is_(None),
        )
        .subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    return items, int(total)


async def create_blog(db: AsyncSession, current_user: User, data: BlogCreate) -> Blog:
    """
    Create a new blog as pending for the current user.
    """
    blog = Blog(
        title=data.title,
        content=data.content,
        images=data.images,
        status=BlogStatus.PENDING,
        author_id=current_user.id,
    )
    db.add(blog)
    await db.flush()
    await db.refresh(blog)
    await db.commit() 
    # Notify admins about new pending blog
    await notifications_manager.notify_new_pending_blog(blog)
    return blog


async def get_blog_by_id(db: AsyncSession, blog_id: int) -> Optional[Blog]:
    """
    Get a blog by id, excluding soft-deleted ones.
    """
    result = await db.execute(
        select(Blog).where(Blog.id == blog_id, Blog.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


def _can_view_blog(blog: Blog, user: Optional[User]) -> bool:
    """
    Determine if the given user can view the blog.

    - Public can see approved blogs
    - Authors, admins, and L1 approvers can see any non-deleted blog
    """
    if blog.status == BlogStatus.APPROVED:
        return True

    if user is None:
        return False

    if user.id == blog.author_id:
        return True

    if user.role in {UserRole.ADMIN, UserRole.L1_APPROVER}:
        return True

    return False


async def get_blog_for_view(
    db: AsyncSession,
    blog_id: int,
    current_user: Optional[User],
) -> Optional[Blog]:
    """
    Get a blog if the current user is allowed to view it.
    """
    blog = await get_blog_by_id(db, blog_id)
    if blog is None:
        return None

    if not _can_view_blog(blog, current_user):
        return None

    return blog


def _can_edit_blog(blog: Blog, user: User) -> bool:
    """
    Determine if the given user can edit the blog.

    - Admin can edit any blog
    - Author can edit only if the blog is not approved
    """
    if user.role == UserRole.ADMIN:
        return True

    if blog.author_id == user.id and blog.status != BlogStatus.APPROVED:
        return True

    return False


def _can_delete_blog(blog: Blog, user: User) -> bool:
    """
    Determine if the given user can delete the blog.

    - Admin can delete any blog
    - Author can delete their own blog
    """
    if user.role == UserRole.ADMIN:
        return True

    if blog.author_id == user.id:
        return True

    return False


async def update_blog(
    db: AsyncSession,
    blog: Blog,
    data: BlogUpdate,
    current_user: User,
) -> Optional[Blog]:
    """
    Update a blog if the current user is allowed to edit it.
    """
    if not _can_edit_blog(blog, current_user):
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(blog, field, value)

    blog.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(blog)
    return blog


async def soft_delete_blog(
    db: AsyncSession,
    blog: Blog,
    current_user: User,
) -> bool:
    """
    Soft-delete a blog (set deleted_at) if the current user is allowed.
    """
    if not _can_delete_blog(blog, current_user):
        return False

    blog.deleted_at = datetime.utcnow()
    await db.flush()
    return True


async def approve_blog(
    db: AsyncSession,
    blog: Blog,
    approver: User,
) -> Blog:
    """
    Approve a blog.

    Admins and L1 approvers are expected to be enforced at the route level.
    """
    blog.status = BlogStatus.APPROVED
    blog.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(blog)
    return blog


async def reject_blog(
    db: AsyncSession,
    blog: Blog,
    approver: User,
) -> Blog:
    """
    Reject a blog.

    Admins and L1 approvers are expected to be enforced at the route level.
    """
    blog.status = BlogStatus.REJECTED
    blog.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(blog)
    return blog



