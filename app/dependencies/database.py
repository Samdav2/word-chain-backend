"""Database dependencies."""

from typing import Annotated, AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import async_session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session for a request."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


# Type alias for cleaner endpoint signatures
DbSession = Annotated[AsyncSession, Depends(get_db)]
