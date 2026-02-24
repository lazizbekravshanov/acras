"""Celery application configuration."""

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "acras",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.processing",
        "app.tasks.reporting",
        "app.tasks.alerting",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Rate limiting
    task_default_rate_limit="100/m",
    # Result expiry
    result_expires=3600,
)

# Periodic tasks
celery_app.conf.beat_schedule = {
    "check-auto-resolve": {
        "task": "app.tasks.processing.check_auto_resolve",
        "schedule": 60.0,  # Every minute
    },
    "camera-health-check": {
        "task": "app.tasks.processing.camera_health_check",
        "schedule": 300.0,  # Every 5 minutes
    },
    "generate-analytics-snapshot": {
        "task": "app.tasks.reporting.generate_analytics_snapshot",
        "schedule": crontab(minute=0),  # Every hour
    },
}
