"""
Audit logging middleware for role-based actions.

Logs important actions performed by users, especially role-based operations.
"""

import json
from datetime import datetime
from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.logging_config import get_logger
from app.auth.utils import verify_token

logger = get_logger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log role-based actions for audit trail.

    Logs requests to protected endpoints, especially those requiring
    admin or approver roles.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log audit information.

        Args:
            request: Incoming request
            call_next: Next middleware/endpoint handler

        Returns:
            Response from endpoint
        """
        # Extract user info from JWT token if available
        user_id = None
        user_role = None
        user_email = None

        # Try to extract user info from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = verify_token(token, token_type="access")
            if payload:
                user_id = payload.get("sub")
                user_role = payload.get("role")
                user_email = payload.get("email")

        # Log request
        start_time = datetime.utcnow()
        response = await call_next(request)
        process_time = (datetime.utcnow() - start_time).total_seconds()

        # Log audit information for important endpoints
        if self._should_log(request, response):
            audit_data = {
                "method": request.method,
                "path": str(request.url.path),
                "query_params": str(request.query_params),
                "user_id": user_id,
                "user_role": user_role,
                "user_email": user_email,
                "status_code": response.status_code,
                "process_time": process_time,
                "client_ip": request.client.host if request.client else None,
            }

            logger.info(
                "Audit log",
                extra={"audit": audit_data},
            )

        return response

    def _should_log(self, request: Request, response: Response) -> bool:
        """
        Determine if request should be logged for audit.

        Args:
            request: Incoming request
            response: Response from endpoint

        Returns:
            True if should log, False otherwise
        """
        # Log all admin/approver endpoints
        protected_paths = [
            "/api/blogs/",
            "/api/auth/roles/",
            "/api/feature-requests/",
            "/api/notifications/sse",
        ]

        # Log POST, PUT, DELETE, PATCH methods on protected paths
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            for path in protected_paths:
                if request.url.path.startswith(path):
                    return True

        # Log all admin role management endpoints
        if "/api/auth/roles/" in request.url.path:
            return True

        # Log approval/rejection actions
        if "/approve" in request.url.path or "/reject" in request.url.path:
            return True

        return False

