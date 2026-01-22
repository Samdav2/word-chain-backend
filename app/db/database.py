"""
Database configuration with support for SQLite (development) and PostgreSQL (production).

Features:
- Automatic database type detection from URL
- Connection pooling optimized for high concurrency (games require many simultaneous connections)
- Easy switching via DATABASE_URL environment variable

Usage:
    # SQLite (development)
    DATABASE_URL=sqlite+aiosqlite:///./data/wordchain.db

    # PostgreSQL (production)
    DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/wordchain_db
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool, QueuePool
from app.core.config import settings


def _create_engine():
    """
    Create the async database engine with appropriate settings.

    SQLite: Uses NullPool (no connection pooling needed for file-based DB)
    PostgreSQL: Uses QueuePool with configurable size for high concurrency
    """
    db_url = settings.database_url
    is_sqlite = db_url.startswith("sqlite")

    # Common engine arguments
    engine_args = {
        "echo": settings.debug,
        "future": True,
    }

    if is_sqlite:
        # SQLite configuration
        # - NullPool: Create fresh connections (SQLite handles this efficiently)
        # - check_same_thread: Required for async SQLite
        engine_args["poolclass"] = NullPool
        engine_args["connect_args"] = {"check_same_thread": False}
    else:
        # PostgreSQL configuration for high concurrency
        # - pool_size: Base number of persistent connections
        # - max_overflow: Additional connections allowed during peak load
        # - pool_timeout: Seconds to wait for a connection before error
        # - pool_recycle: Recycle connections after this many seconds (prevents stale connections)
        # - pool_pre_ping: Test connections before use (handles dropped connections)
        engine_args["pool_size"] = settings.db_pool_size
        engine_args["max_overflow"] = settings.db_max_overflow
        engine_args["pool_timeout"] = settings.db_pool_timeout
        engine_args["pool_recycle"] = 3600  # Recycle connections hourly
        engine_args["pool_pre_ping"] = True  # Verify connection health

    return create_async_engine(db_url, **engine_args)


# Create async engine
engine = _create_engine()

# Create async session factory
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def create_tables():
    """Create all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """Drop all database tables (use with caution!)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def get_async_session() -> AsyncSession:
    """Get an async database session."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


def get_database_info() -> dict:
    """Get information about the current database configuration."""
    db_url = settings.database_url
    is_sqlite = db_url.startswith("sqlite")

    return {
        "type": "sqlite" if is_sqlite else "postgresql",
        "pool_size": None if is_sqlite else settings.db_pool_size,
        "max_overflow": None if is_sqlite else settings.db_max_overflow,
        "is_production_ready": not is_sqlite,
    }
