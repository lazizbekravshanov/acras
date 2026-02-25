"""FastAPI application factory for ACRAS."""

import logging
import sys

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.config import settings
from app.core.events import lifespan
from app.core.exceptions import register_exception_handlers


def configure_logging() -> None:
    """Set up structured logging."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    if settings.LOG_FORMAT == "json":
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(log_level),
        )
    else:
        log_fmt = "%(asctime)s %(levelname)s %(name)s: %(message)s"
        logging.basicConfig(level=log_level, stream=sys.stdout, format=log_fmt)


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    configure_logging()

    app = FastAPI(
        title="ACRAS — AI Crash Report Automation System",
        description="Real-time traffic incident detection, reporting, and analytics.",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-API-Key", "Authorization"],
    )

    # Exception handlers
    register_exception_handlers(app)

    # Routers
    app.include_router(v1_router)

    # Health check endpoints
    @app.get("/health", tags=["system"])
    async def health():
        return {"status": "healthy"}

    @app.get("/ready", tags=["system"])
    async def ready():
        from sqlalchemy import text

        from app.core import events

        checks = {"database": False, "redis": False}
        try:
            if events.async_session_factory:
                async with events.async_session_factory() as session:
                    await session.execute(text("SELECT 1"))
                    checks["database"] = True
        except Exception:
            pass
        try:
            if events.redis_client:
                await events.redis_client.ping()
                checks["redis"] = True
        except Exception:
            pass

        all_ready = all(checks.values())
        return {"status": "ready" if all_ready else "degraded", "checks": checks}

    return app


app = create_app()
