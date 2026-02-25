"""Application lifecycle events — startup and shutdown hooks."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

logger = logging.getLogger(__name__)

# Global references set during startup
engine = None
async_session_factory: async_sessionmaker[AsyncSession] | None = None
redis_client: aioredis.Redis | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown."""
    global engine, async_session_factory, redis_client

    # Startup
    logger.info("Starting ACRAS backend...")

    engine = create_async_engine(settings.async_database_url, echo=False, pool_size=20, max_overflow=10)
    async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

    logger.info("Database and Redis connections established.")

    yield

    # Shutdown
    logger.info("Shutting down ACRAS backend...")
    if redis_client:
        await redis_client.close()
    if engine:
        await engine.dispose()
    logger.info("Shutdown complete.")
