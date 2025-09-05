"""
Async Database Configuration for HMO Analyser
Provides async SQLAlchemy session management for high-performance operations
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os
from typing import AsyncGenerator

# Get your existing database URL and convert to async format
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://username:password@localhost/hmo_analyser")

# Convert sync postgres URL to async
if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
elif DATABASE_URL.startswith("postgres://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://")
else:
    # If already async format, use as is
    ASYNC_DATABASE_URL = DATABASE_URL

print(f"🔗 Async database URL: {ASYNC_DATABASE_URL}")

# Create async engine with optimized settings
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    pool_size=20,  # Number of connections to maintain
    max_overflow=30,  # Additional connections beyond pool_size
    pool_timeout=30,  # Seconds to wait for connection
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_pre_ping=True,  # Verify connections before use
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Keep objects accessible after commit
    autoflush=True,
    autocommit=False
)

# Async dependency for FastAPI
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for async database sessions
    Usage: db: AsyncSession = Depends(get_async_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Test connection function
async def test_async_connection():
    """Test the async database connection"""
    try:
        async with AsyncSessionLocal() as session:
            # Simple query to test connection
            result = await session.execute("SELECT 1")
            value = result.scalar()
            if value == 1:
                print("✅ Async database connection successful!")
                return True
            else:
                print("❌ Async database connection test failed")
                return False
    except Exception as e:
        print(f"❌ Async database connection error: {e}")
        return False

# Cleanup function for graceful shutdown
async def close_async_db():
    """Close the async database engine"""
    await async_engine.dispose()
    print("🧹 Async database connections closed")

if __name__ == "__main__":
    # Test the async database connection
    import asyncio
    
    async def main():
        print("🧪 Testing async database connection...")
        success = await test_async_connection()
        await close_async_db()
        return success
    
    result = asyncio.run(main())
    if result:
        print("🎉 Async database setup is ready!")
    else:
        print("❌ Please check your database configuration")