"""
Role-Based Access Control (RBAC) dependencies and utilities.

Provides decorators and dependencies to restrict endpoints based on user roles.
"""

from typing import List
from fastapi import Depends, HTTPException, status
from app.models.user import User, UserRole

# Direct import - no circular dependency since dependencies.py doesn't import rbac
from app.auth.dependencies import get_current_active_user


def require_role(allowed_roles: List[UserRole]):
    """
    Create a dependency that requires the user to have one of the specified roles.

    Args:
        allowed_roles: List of allowed roles

    Returns:
        Dependency function that checks user role

    Example:
        @router.get("/admin-only")
        async def admin_endpoint(user: User = Depends(require_role([UserRole.ADMIN]))):
            ...
    """
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[role.value for role in allowed_roles]}",
            )
        return current_user

    return role_checker


def require_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Dependency that requires the user to be an admin.

    Args:
        current_user: Current authenticated user

    Returns:
        User object if admin

    Raises:
        HTTPException: If user is not an admin
    """
    # Ensure current_user is actually a User object, not a function
    if not isinstance(current_user, User):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Dependency resolution error",
        )
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin role required.",
        )
    return current_user


def require_approver(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Dependency that requires the user to be an admin or L1 approver.

    Args:
        current_user: Current authenticated user

    Returns:
        User object if admin or approver

    Raises:
        HTTPException: If user is not an admin or approver
    """
    # Ensure current_user is actually a User object, not a function
    if not isinstance(current_user, User):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Dependency resolution error",
        )
    if current_user.role not in [UserRole.ADMIN, UserRole.L1_APPROVER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin or L1 Approver role required.",
        )
    return current_user


def has_role(user: User, role: UserRole) -> bool:
    """
    Check if a user has a specific role.

    Args:
        user: User object
        role: Role to check

    Returns:
        True if user has the role, False otherwise
    """
    return user.role == role


def has_any_role(user: User, roles: List[UserRole]) -> bool:
    """
    Check if a user has any of the specified roles.

    Args:
        user: User object
        roles: List of roles to check

    Returns:
        True if user has any of the roles, False otherwise
    """
    return user.role in roles


def is_admin(user: User) -> bool:
    """
    Check if a user is an admin.

    Args:
        user: User object

    Returns:
        True if user is admin, False otherwise
    """
    return user.role == UserRole.ADMIN


def is_approver(user: User) -> bool:
    """
    Check if a user is an admin or L1 approver.

    Args:
        user: User object

    Returns:
        True if user is admin or approver, False otherwise
    """
    return user.role in [UserRole.ADMIN, UserRole.L1_APPROVER]

