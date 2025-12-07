"""
JWT and password hashing utilities.
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token (typically user_id, email, role)
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    # Convert 'sub' (subject/user_id) to string as required by JWT spec
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: Data to encode in the token (typically user_id)

    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    # Convert 'sub' (subject/user_id) to string as required by JWT spec
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string
        token_type: Expected token type ("access" or "refresh")

    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        # Verify token type
        if payload.get("type") != token_type:
            return None

        return payload
    except JWTError as e:
        # Log the error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"JWT decode error: {type(e).__name__}: {e}")
        return None
    except Exception as e:
        # Catch any other errors
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error verifying token: {type(e).__name__}: {e}")
        return None

