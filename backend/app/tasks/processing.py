"""Celery tasks for frame processing and incident tracking."""

import logging

import cv2
import numpy as np

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

# Lazy-initialized singletons
_detection_engine = None
_incident_tracker = None


def _get_detection_engine():
    global _detection_engine
    if _detection_engine is None:
        from app.services.detection_engine import DetectionEngine
        _detection_engine = DetectionEngine()
    return _detection_engine


def _get_incident_tracker():
    global _incident_tracker
    if _incident_tracker is None:
        from app.services.incident_tracker import IncidentTracker
        _incident_tracker = IncidentTracker()
    return _incident_tracker


@celery_app.task(name="app.tasks.processing.process_frame")
def process_frame(camera_id: str, frame_bytes: bytes, camera_info: dict) -> dict | None:
    """Process a single frame through the detection pipeline.

    Args:
        camera_id: Camera identifier
        frame_bytes: JPEG-encoded frame bytes
        camera_info: Dict with camera metadata (lat, lon, interstate, direction)

    Returns:
        Detection result dict, or None if no incident
    """
    engine = _get_detection_engine()
    tracker = _get_incident_tracker()

    # Decode frame
    nparr = np.frombuffer(frame_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None:
        logger.error("Failed to decode frame for camera %s", camera_id)
        return None

    # Run detection pipeline
    result = engine.process_frame(camera_id, frame)

    # Track incident
    incident = tracker.process_detection(
        result,
        camera_lat=camera_info.get("latitude", 0.0),
        camera_lon=camera_info.get("longitude", 0.0),
        camera_interstate=camera_info.get("interstate", ""),
        camera_direction=camera_info.get("direction"),
    )

    if incident:
        return {
            "incident_id": incident.id,
            "camera_id": camera_id,
            "incident_type": incident.incident_type,
            "severity": incident.severity,
            "severity_score": incident.severity_score,
            "confidence": incident.confidence,
            "status": incident.status,
            "latitude": incident.latitude,
            "longitude": incident.longitude,
            "interstate": incident.interstate,
            "vehicle_count": incident.vehicle_count,
            "inference_time_ms": result.inference_time_ms,
        }

    return None


@celery_app.task(name="app.tasks.processing.check_auto_resolve")
def check_auto_resolve() -> int:
    """Periodic task: check for incidents that should be auto-resolved."""
    tracker = _get_incident_tracker()
    resolved = tracker.check_auto_resolve()
    if resolved:
        logger.info("Auto-resolved %d incidents", len(resolved))
    return len(resolved)


@celery_app.task(name="app.tasks.processing.camera_health_check")
def camera_health_check() -> dict:
    """Periodic task: check camera stream health."""
    # This would check each active stream's status
    # For now, return a placeholder
    logger.info("Camera health check completed")
    return {"checked": 0, "healthy": 0, "degraded": 0, "offline": 0}
