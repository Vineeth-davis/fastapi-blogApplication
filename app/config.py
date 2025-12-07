"""
Application configuration using Pydantic Settings.

Loads configuration from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Blog Platform API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./blog.db"

    # JWT
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    # Store as string to avoid JSON parsing issues, parse to list via validator
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    CORS_CREDENTIALS: bool = True
    FRONTEND_URL: str = "http://localhost:3000"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from comma-separated string or list."""
        if isinstance(v, list):
            # If already a list, join it back to string (will be parsed again)
            return ",".join(v)
        if isinstance(v, str):
            # Clean up the string: remove newlines, extra spaces
            cleaned = v.replace("\n", " ").replace("\r", " ").strip()
            return cleaned if cleaned else "http://localhost:3000,http://localhost:5173"
        return "http://localhost:3000,http://localhost:5173"

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # 'json' or 'text'

    # Redis (Optional)
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = False

    # File Upload
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    UPLOAD_DIR: str = "./uploads"

    # SSL/HTTPS
    SSL_ENABLED: bool = False
    SSL_CERT_PATH: str = ""
    SSL_KEY_PATH: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        # Environment variables take precedence over .env file
        env_ignore_empty=True,
    )

    def get_cors_origins(self) -> List[str]:
        """Get CORS_ORIGINS as a list (parsed from comma-separated string)."""
        if isinstance(self.CORS_ORIGINS, str):
            origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
            return origins if origins else ["http://localhost:3000", "http://localhost:5173"]
        # Fallback (should not happen)
        return ["http://localhost:3000", "http://localhost:5173"]


# Global settings instance
settings = Settings()

