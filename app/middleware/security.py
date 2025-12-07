"""
Security middleware for HTTPS enforcement and security headers.
"""

from typing import Callable
from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.

    Adds headers like:
    - Content-Security-Policy
    - X-Frame-Options
    - X-Content-Type-Options
    - X-XSS-Protection
    - Strict-Transport-Security (HSTS)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and add security headers.

        Args:
            request: Incoming request
            call_next: Next middleware/endpoint handler

        Returns:
            Response with security headers
        """
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy (adjust based on your needs)
        # Allow CDN resources for Swagger UI
        # For /docs endpoint, use more permissive CSP to allow Swagger UI to work
        if request.url.path == "/docs" or request.url.path.startswith("/docs/"):
            # More permissive CSP for Swagger UI
            csp = (
                "default-src 'self' https://cdn.jsdelivr.net https://fastapi.tiangolo.com; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https:; "
                "font-src 'self' data: https://cdn.jsdelivr.net; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            )
        else:
            # Standard CSP for other endpoints
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https:; "
                "font-src 'self' data: https://cdn.jsdelivr.net; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            )
        response.headers["Content-Security-Policy"] = csp

        # HSTS (only in production with HTTPS)
        if settings.ENVIRONMENT == "production" and settings.SSL_ENABLED:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce HTTPS in production.

    Redirects HTTP requests to HTTPS when SSL is enabled and in production.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and redirect to HTTPS if needed.

        Args:
            request: Incoming request
            call_next: Next middleware/endpoint handler

        Returns:
            Response (redirected to HTTPS if needed)
        """
        # Only enforce in production with SSL enabled
        if (
            settings.ENVIRONMENT == "production"
            and settings.SSL_ENABLED
            and request.url.scheme == "http"
        ):
            # Get the host from the request
            host = request.headers.get("host", request.url.hostname)
            https_url = request.url.replace(scheme="https", netloc=host)


            logger.warning(f"Redirecting HTTP to HTTPS: {request.url} -> {https_url}")
            return RedirectResponse(url=str(https_url), status_code=301)

        response = await call_next(request)
        return response

