"""
Script to seed the database with initial users for each role.

Usage:
    python scripts/seed_users.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.auth.utils import hash_password
from sqlalchemy import select


async def create_user_if_not_exists(
    email: str,
    username: str,
    password: str,
    role: UserRole,
    is_active: bool = True,
) -> User:
    """Create a user if it doesn't already exist."""
    async with AsyncSessionLocal() as session:
        # Check if user already exists
        result = await session.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"⚠️  User {email} already exists, skipping...")
            return existing_user
        
        # Create new user
        hashed_password = hash_password(password)
        new_user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            role=role,
            is_active=is_active,
        )
        
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        
        print(f"✅ Created {role.value}: {username} ({email})")
        return new_user


async def seed_users():
    """Seed the database with initial users."""
    print("🌱 Seeding users...")
    print("-" * 50)
    
    # Admin user
    await create_user_if_not_exists(
        email="admin@example.com",
        username="admin",
        password="admin@1",
        role=UserRole.ADMIN,
    )
    
    # L1 Approver user
    await create_user_if_not_exists(
        email="approver@example.com",
        username="approver",
        password="approver@1",
        role=UserRole.L1_APPROVER,
    )
    
    # Regular users (user1, user2, user3, user4, user5)
    for i in range(1, 6):
        await create_user_if_not_exists(
            email=f"user{i}@example.com",
            username=f"user{i}",
            password=f"user{i}@1",
            role=UserRole.USER,
        )
    
    print("-" * 50)
    print("✅ User seeding completed!")
    print("\n📋 Created users:")
    print("   Admin: admin / admin@1")
    print("   L1 Approver: approver / approver@1")
    for i in range(1, 6):
        print(f"   User {i}: user{i} / user{i}@1")


if __name__ == "__main__":
    asyncio.run(seed_users())

