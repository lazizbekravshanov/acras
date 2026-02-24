"""Celery tasks for alert dispatching."""

import asyncio
import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.alerting.dispatch_alerts")
def dispatch_alerts(incident_data: dict, report_summary: str | None = None) -> list[dict]:
    """Dispatch alerts for an incident to all matching configurations."""
    from app.services.alert_dispatcher import AlertDispatcher

    dispatcher = AlertDispatcher()

    # In a real implementation, we'd fetch active AlertConfigs from the DB
    # For now, this demonstrates the pattern
    results = []
    logger.info("Alert dispatch triggered for incident %s", incident_data.get("id"))

    return results


def _run_async(coro):
    """Helper to run async code from a sync Celery task."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)
