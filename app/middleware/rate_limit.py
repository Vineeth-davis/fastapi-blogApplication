from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi import status
from fastapi.responses import JSONResponse
from app.config import settings
from app.logging_config import get_logger


logger = get_logger(__name__)

# Create limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"] if settings.RATE_LIMIT_ENABLED else [],
)

# Rate limit exceeded handler
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom handler for rate limit exceeded.

    Args:
        request: The request that exceeded the rate limit
        exc: RateLimitExceeded exception

    Returns:
        Response with rate limit error
    """

    logger.warning(
        f"Rate limit exceeded for {get_remote_address(request)}: {request.url.path}"
    )

    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": f"Rate limit exceeded: {exc.detail}. Please try again later."
        },
        headers={"Retry-After": str(exc.retry_after) if hasattr(exc, "retry_after") else "60"},
    )

