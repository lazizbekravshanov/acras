"""Celery tasks for report generation and analytics snapshots."""

import logging

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
    logger.info("Generating analytics snapshot")
    # This would aggregate recent data and store as an AnalyticsSnapshot
    return {"status": "completed", "snapshot_type": "hourly"}
