#!/usr/bin/env python3
"""
Wait for database to be ready before starting the application.

This script checks if the database is reachable and ready to accept connections.
"""

import asyncio
import sys
import os
from urllib.parse import urlparse

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import asyncpg
except ImportError as e:
    print(f"Error importing asyncpg: {e}")
    sys.exit(1)


async def check_database():
    """Check if database is ready."""
    max_attempts = 30
    attempt = 0
    
    # Get DATABASE_URL from environment variable first (Docker sets this)
    # Fall back to .env file via settings if not in environment
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        # Try to load from settings (reads from .env file)
        try:
            from app.config import settings
            db_url = settings.DATABASE_URL
            print("  Note: Using DATABASE_URL from .env file (environment variable not set)")
        except Exception as e:
            print(f"  Error loading settings: {e}")
            sys.exit(1)
    else:
        print("  Note: Using DATABASE_URL from environment variable")
    
    # Debug: Print the actual DATABASE_URL being used
    print(f"DEBUG: DATABASE_URL: {db_url}")
    
    # Handle passwords with special characters (like @) BEFORE processing scheme
    # If the URL has multiple @ symbols, the password likely contains @
    from urllib.parse import quote_plus
    
    # Count @ symbols - should be exactly 1 (separating auth from host)
    at_count = db_url.count('@')
    if at_count > 1:
        # Password contains @ - need to URL-encode it
        # Extract the scheme and find where credentials end
        scheme_end = db_url.find("://") + 3
        # Find the last @ (this should be the auth/host separator)
        last_at = db_url.rfind('@')
        # Everything before last @ is auth, after is host+path
        auth_part = db_url[scheme_end:last_at]
        host_part = db_url[last_at+1:]
        
        if ':' in auth_part:
            user, password = auth_part.split(':', 1)
            # URL-encode the password
            encoded_password = quote_plus(password, safe='')
            # Reconstruct URL
            scheme = db_url[:scheme_end]
            db_url = f"{scheme}{user}:{encoded_password}@{host_part}"
            print(f"  Note: URL-encoded password with special characters (@ -> %40)")
            print(f"  DEBUG: Fixed URL (password masked): {db_url.replace(encoded_password, '****')}")
    
    # Handle asyncpg connection string (postgresql+asyncpg://...)
    # Do this AFTER password encoding to avoid breaking the URL structure
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    elif db_url.startswith("postgresql://"):
        pass
    else:
        # SQLite doesn't need waiting
        print("Using SQLite, no need to wait for database")
        return True
    
    # Parse connection string
    parsed = urlparse(db_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
    user = parsed.username or "postgres"
    password = parsed.password or ""
    database = parsed.path.lstrip("/") or "postgres"
    
    print(f"Waiting for database at {host}:{port} (database: {database}, user: {user})...")
    
    # Check if hostname is resolvable (for debugging)
    if host == "db":
        print("  Note: Using Docker service name 'db' - ensure containers are on the same network")
        # Try to resolve the hostname first
        try:
            import socket
            socket.gethostbyname(host)
            print(f"  ✓ Hostname '{host}' is resolvable")
        except socket.gaierror:
            print(f"  ✗ Hostname '{host}' cannot be resolved - this will cause connection failures")
            print(f"    Make sure:")
            print(f"    1. Database service is running: docker-compose ps")
            print(f"    2. Containers are on the same network")
            print(f"    3. DATABASE_URL uses 'db' as hostname (not 'localhost')")
    
    while attempt < max_attempts:
        try:
            # Try to connect
            conn = await asyncpg.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                timeout=2
            )
            await conn.close()
            print(f"✓ Database is ready!")
            return True
        except (asyncpg.exceptions.InvalidPasswordError, asyncpg.exceptions.PostgresError) as e:
            # Database is reachable but credentials are wrong
            print(f"✗ Database connection error: {e}")
            return False
        except (OSError, asyncio.TimeoutError, Exception) as e:
            attempt += 1
            error_msg = str(e)
            if "Name or service not known" in error_msg or "getaddrinfo failed" in error_msg:
                print(f"  Attempt {attempt}/{max_attempts}: DNS resolution failed for '{host}'")
                print(f"    This usually means:")
                print(f"    - Database service is not running")
                print(f"    - Containers are not on the same Docker network")
                print(f"    - DATABASE_URL hostname is incorrect (should be 'db' in Docker)")
            else:
                print(f"  Attempt {attempt}/{max_attempts}: Database not ready ({error_msg[:50]}...)")
            
            if attempt < max_attempts:
                await asyncio.sleep(2)
            else:
                print(f"✗ Failed to connect to database after {max_attempts} attempts")
                print(f"  Final error: {e}")
                print(f"  DATABASE_URL: {db_url}")
                return False
    
    return False


async def main():
    """Main function."""
    # Small delay to ensure Docker network is initialized
    print("Initializing database connection check...")
    await asyncio.sleep(1)
    
    success = await check_database()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())

