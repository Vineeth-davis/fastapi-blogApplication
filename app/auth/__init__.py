"""
Authentication module for JWT-based authentication and authorization.
"""

# Import dependencies first (no circular dependency)
from app.auth.dependencies import get_current_user, get_current_active_user
from app.auth.utils import create_access_token, create_refresh_token, verify_token, hash_password, verify_password

# Import RBAC functions lazily to avoid circular imports
# These are imported where needed, so we don't need to import them here
# If you need them, import directly: from app.auth.rbac import require_admin

__all__ = [
    "get_current_user",
    "get_current_active_user",
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "hash_password",
    "verify_password",
    # RBAC functions should be imported directly from app.auth.rbac
    # "require_role",
    # "require_admin",
    # "require_approver",
    # "has_role",
    # "has_any_role",
    # "is_admin",
    # "is_approver",
]

