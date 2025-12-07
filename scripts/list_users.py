"""List all users in the database."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import select


async def list_users():
    """List all users."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        if not users:
            print("No users found in database.")
            return
        
        print("\n📋 Users in database:")
        print("-" * 60)
        for user in users:
            print(f"  {user.username:15} ({user.email:25}) - {user.role.value}")
        print("-" * 60)
        print(f"\nTotal: {len(users)} users")


if __name__ == "__main__":
    asyncio.run(list_users())

