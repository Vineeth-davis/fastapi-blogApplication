"""
Authentication routes for registration, login, and token management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User, UserRole
from app.auth.schemas import (
    UserRegister,
    UserLogin,
    TokenResponse,
    UserResponse,
    RefreshTokenRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from app.auth.utils import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.auth.dependencies import get_current_active_user

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        Created user object

    Raises:
        HTTPException: If email or username already exists
    """
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Check if username already exists
    result = await db.execute(select(User).where(User.username == user_data.username))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Create new user
    hashed_password = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        role=UserRole.USER,  # Default role
        is_active=True,
    )

    db.add(new_user)
    await db.flush()  # Flush to get the ID without committing
    await db.refresh(new_user)
    # Note: get_db() will commit automatically when the function returns

    return new_user


@router.post("/login", response_model=TokenResponse)
async def login(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """
    Login user and return JWT tokens.

    Args:
        user_data: User login credentials
        db: Database session

    Returns:
        Access and refresh tokens

    Raises:
        HTTPException: If credentials are invalid or user is inactive
    """
    # Get user by email
    result = await db.execute(select(User).where(User.email == user_data.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Verify password
    if not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    # Create tokens
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email, "role": user.role.value}
    )
    refresh_token = create_refresh_token(data={"sub": user.id})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/login/form", response_model=TokenResponse)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    Login endpoint compatible with OAuth2 password flow (for Swagger UI).

    Uses username field for email.

    Args:
        form_data: OAuth2 form data
        db: Database session

    Returns:
        Access and refresh tokens
    """
    # OAuth2PasswordRequestForm uses 'username' field, but we use email
    user_data = UserLogin(email=form_data.username, password=form_data.password)
    return await login(user_data, db)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token using refresh token.

    Args:
        token_data: Refresh token
        db: Database session

    Returns:
        New access and refresh tokens

    Raises:
        HTTPException: If refresh token is invalid
    """
    # Verify refresh token
    payload = verify_token(token_data.refresh_token, token_type="refresh")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Create new tokens
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email, "role": user.role.value}
    )
    refresh_token = create_refresh_token(data={"sub": user.id})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get current authenticated user information.

    Args:
        current_user: Current authenticated user

    Returns:
        User information
    """
    return current_user


@router.post("/password-reset/request", status_code=status.HTTP_200_OK)
async def request_password_reset(
    reset_data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Request password reset (sends reset token via email).

    Note: In a real application, this would send an email with a reset link.
    For this implementation, we'll just return a success message.

    Args:
        reset_data: Email for password reset
        db: Database session

    Returns:
        Success message
    """
    # Check if user exists
    result = await db.execute(select(User).where(User.email == reset_data.email))
    user = result.scalar_one_or_none()

    if user:
        # In production, generate a reset token and send email
        # For now, just return success to prevent email enumeration
        pass

    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/password-reset/confirm", status_code=status.HTTP_200_OK)
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
):
    """
    Confirm password reset with token.

    Note: In a real application, the token would be validated against stored reset tokens.
    For this implementation, we decode the token to get user_id.

    Args:
        reset_data: Reset token and new password
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If token is invalid
    """
    # Verify token (in production, this would be a separate reset token)
    payload = verify_token(reset_data.token, token_type="refresh")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token",
        )

    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update password
    user.hashed_password = hash_password(reset_data.new_password)
    await db.commit()

    return {"message": "Password reset successfully"}

