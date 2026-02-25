"""Dependency injection for API endpoints."""

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import events
from app.core.security import verify_api_key


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session."""
    if events.async_session_factory is None:
        raise RuntimeError("Database not initialized")
    async with events.async_session_factory() as session:
        yield session


async def get_redis():
    """Return the Redis client."""
    if events.redis_client is None:
        raise RuntimeError("Redis not initialized")
    return events.redis_client


# Shorthand dependency for authenticated endpoints
AuthDep = Depends(verify_api_key)
