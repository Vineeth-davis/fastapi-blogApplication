from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.logging_config import setup_logging, get_logger
from app.database import init_db, close_db
from app.auth.routes import router as auth_router
from app.auth.role_routes import router as role_router
from app.blogs.routes import router as blogs_router
from app.blogs.websocket import router as blogs_ws_router
from app.feature_requests.routes import router as feature_requests_router
from app.notifications.routes import router as notifications_router
from app.session.routes import router as session_router
from app.middleware.audit import AuditMiddleware
from app.middleware.security import SecurityHeadersMiddleware, HTTPSRedirectMiddleware
from app.middleware.rate_limit import limiter, rate_limit_handler
from slowapi.errors import RateLimitExceeded

# Setup logging first
setup_logging()
logger = get_logger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="A production-ready FastAPI backend for a blog platform",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# Configure CORS (must be first middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTPS redirect (before other middleware)
if settings.ENVIRONMENT == "production" and settings.SSL_ENABLED:
    app.add_middleware(HTTPSRedirectMiddleware)

# Security headers
app.add_middleware(SecurityHeadersMiddleware)

# Add audit logging middleware
app.add_middleware(AuditMiddleware)

# Include routers
app.include_router(auth_router)
app.include_router(role_router)
app.include_router(blogs_router)
app.include_router(blogs_ws_router)
app.include_router(feature_requests_router)
app.include_router(notifications_router)
app.include_router(session_router)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")



@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Shutting down application")
    await close_db()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

