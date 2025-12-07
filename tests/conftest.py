"""
Pytest configuration and shared fixtures.
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models.user import User, UserRole
from app.models.blog import Blog, BlogStatus
from app.auth.utils import hash_password


# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session with rollback.

    Creates tables, yields a session, then drops tables after test.
    """
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test client with database override.

    Overrides the get_db dependency to use the test database session.
    """
    async def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """
    Create a test user with default role.

    Returns:
        User: Test user instance
    """
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=hash_password("testpassword123"),
        role=UserRole.USER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_admin(db_session: AsyncSession) -> User:
    """
    Create a test admin user.

    Returns:
        User: Test admin user instance
    """
    admin = User(
        email="admin@example.com",
        username="admin",
        hashed_password=hash_password("adminpassword123"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest.fixture
async def test_approver(db_session: AsyncSession) -> User:
    """
    Create a test L1 approver user.

    Returns:
        User: Test approver user instance
    """
    approver = User(
        email="approver@example.com",
        username="approver",
        hashed_password=hash_password("approverpassword123"),
        role=UserRole.L1_APPROVER,
        is_active=True,
    )
    db_session.add(approver)
    await db_session.commit()
    await db_session.refresh(approver)
    return approver


@pytest.fixture
async def auth_headers(client: AsyncClient, test_user: User) -> dict:
    """
    Get authentication headers for test user.

    Returns:
        dict: Headers with Authorization token
    """
    response = await client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 200
    token_data = response.json()
    return {"Authorization": f"Bearer {token_data['access_token']}"}


@pytest.fixture
async def admin_headers(client: AsyncClient, test_admin: User) -> dict:
    """
    Get authentication headers for admin user.

    Returns:
        dict: Headers with Authorization token
    """
    response = await client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "adminpassword123"},
    )
    assert response.status_code == 200
    token_data = response.json()
    return {"Authorization": f"Bearer {token_data['access_token']}"}


@pytest.fixture
async def test_blog(db_session: AsyncSession, test_user: User) -> Blog:
    """
    Create a test blog post.

    Returns:
        Blog: Test blog instance
    """
    blog = Blog(
        title="Test Blog Post",
        content="This is a test blog post content.",
        status=BlogStatus.PENDING,
        author_id=test_user.id,
    )
    db_session.add(blog)
    await db_session.commit()
    await db_session.refresh(blog)
    return blog


@pytest.fixture
async def approved_blog(db_session: AsyncSession, test_user: User) -> Blog:
    """
    Create an approved test blog post.

    Returns:
        Blog: Approved test blog instance
    """
    blog = Blog(
        title="Approved Blog Post",
        content="This is an approved blog post content.",
        status=BlogStatus.APPROVED,
        author_id=test_user.id,
    )
    db_session.add(blog)
    await db_session.commit()
    await db_session.refresh(blog)
    return blog

