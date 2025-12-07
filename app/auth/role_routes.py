from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.database import get_db
from app.models.user import User, UserRole
from app.auth.dependencies import get_current_active_user
from app.auth.rbac import require_admin
from app.auth.schemas import UserResponse

router = APIRouter(prefix="/api/auth/roles", tags=["role-management"])


class UpdateRoleRequest(BaseModel):
    """Schema for updating user role."""

    user_id: int
    new_role: UserRole


class UpdateRoleResponse(BaseModel):
    """Schema for role update response."""

    message: str
    user: UserResponse


@router.post("/update", response_model=UpdateRoleResponse, dependencies=[Depends(require_admin)])
async def update_user_role(
    role_data: UpdateRoleRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a user's role (admin only).

    Args:
        role_data: User ID and new role
        current_user: Current admin user
        db: Database session

    Returns:
        Updated user information

    Raises:
        HTTPException: If user not found or invalid role
    """
    # Prevent self-demotion (admin cannot remove their own admin role)
    if role_data.user_id == current_user.id and role_data.new_role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove your own admin role",
        )

    # Get target user
    result = await db.execute(select(User).where(User.id == role_data.user_id))
    target_user = result.scalar_one_or_none()

    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update role
    old_role = target_user.role
    target_user.role = role_data.new_role
    await db.commit()
    await db.refresh(target_user)

    return UpdateRoleResponse(
        message=f"User role updated from {old_role.value} to {role_data.new_role.value}",
        user=target_user,
    )


@router.get("/users", response_model=list[UserResponse], dependencies=[Depends(require_admin)])
async def list_all_users(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    List all users (admin only).

    Args:
        current_user: Current admin user
        db: Database session

    Returns:
        List of all users
    """
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users


@router.get("/users/{user_id}", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get user by ID (admin only).

    Args:
        user_id: User ID
        current_user: Current admin user
        db: Database session

    Returns:
        User information

    Raises:
        HTTPException: If user not found
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user

