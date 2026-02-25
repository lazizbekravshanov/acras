"""Celery tasks for report generation and analytics snapshots."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.reporting.generate_report")
def generate_report(incident_data: dict, weather_data: dict | None = None) -> dict:
    """Generate a structured + narrative report for an incident."""
    from app.services.report_generator import ReportGenerator

    generator = ReportGenerator()
    structured = generator.generate_structured_report(incident_data, weather_data)
    narrative = generator.generate_narrative(structured)

    return {
        "structured_data": structured,
        "narrative": narrative,
        "incident_id": incident_data["id"],
    }


@celery_app.task(name="app.tasks.reporting.generate_analytics_snapshot")
def generate_analytics_snapshot() -> dict:
    """Periodic task: generate hourly analytics snapshot."""
    return _run_async(_generate_snapshot())


async def _generate_snapshot() -> dict:
    """Async implementation of analytics snapshot generation."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.config import settings
    from app.models.analytics import AnalyticsSnapshot
    from app.services.analytics_engine import AnalyticsEngine

    engine_db = create_async_engine(settings.async_database_url, echo=False)
    async_session = async_sessionmaker(engine_db, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as db:
            analytics = AnalyticsEngine()

            summary = await analytics.get_summary_stats(db)
            severity_dist = await analytics.get_severity_distribution(db)
            hourly_pattern = await analytics.get_hourly_pattern(db)
            top_locations = await analytics.get_top_locations(db, limit=10)

            now = datetime.now(UTC)
            period_start = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
            period_end = now.replace(minute=0, second=0, microsecond=0)

            snapshot = AnalyticsSnapshot(
                snapshot_type="hourly",
                period_start=period_start,
                period_end=period_end,
                data={
                    "summary": summary,
                    "severity_distribution": severity_dist,
                    "hourly_pattern": hourly_pattern,
                    "top_locations": top_locations,
                },
            )
            db.add(snapshot)
            await db.commit()

            logger.info("Generated analytics snapshot for %s - %s", period_start, period_end)
            return {"status": "completed", "snapshot_type": "hourly", "period_start": str(period_start)}
    finally:
        await engine_db.dispose()


def _run_async(coro):
    """Helper to run async code from a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
