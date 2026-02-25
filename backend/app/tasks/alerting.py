"""Celery tasks for alert dispatching."""

import asyncio
import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.alerting.dispatch_alerts")
def dispatch_alerts(incident_data: dict, report_summary: str | None = None) -> list[dict]:
    """Dispatch alerts for an incident to all matching configurations."""
    return _run_async(_dispatch_alerts_async(incident_data, report_summary))


async def _dispatch_alerts_async(incident_data: dict, report_summary: str | None) -> list[dict]:
    """Async implementation of alert dispatching."""
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.config import settings
    from app.models.alert import Alert, AlertConfig
    from app.services.alert_dispatcher import AlertDispatcher

    dispatcher = AlertDispatcher()
    results = []

    engine = create_async_engine(settings.async_database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as db:
            # Fetch active alert configs
            configs = (
                await db.execute(select(AlertConfig).where(AlertConfig.is_active.is_(True)))
            ).scalars().all()

            for config in configs:
                config_dict = {
                    "channel": config.channel,
                    "recipient": config.recipient,
                    "min_severity": config.min_severity,
                    "incident_types": config.incident_types,
                    "interstates": config.interstates,
                    "cooldown_minutes": config.cooldown_minutes,
                }

                if not dispatcher.should_alert(config_dict, incident_data):
                    continue

                result = await dispatcher.dispatch(incident_data, config_dict, report_summary)
                results.append(result)

                # Persist alert record
                alert = Alert(
                    incident_id=incident_data["id"],
                    channel=result["channel"],
                    recipient=result["recipient"],
                    status=result["status"],
                    payload=result["payload"],
                    sent_at=result.get("sent_at"),
                    error_message=result.get("error_message"),
                )
                db.add(alert)

            await db.commit()

        logger.info(
            "Dispatched %d alerts for incident %s",
            len(results),
            incident_data.get("id"),
        )
    finally:
        await dispatcher.close()
        await engine.dispose()

    return results


def _run_async(coro):
    """Helper to run async code from a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
