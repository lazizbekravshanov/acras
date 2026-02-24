"""Incident tracking service — state machine, deduplication, confidence aggregation.

Manages the lifecycle of detected incidents from initial detection through resolution.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field

from app.services.detection_engine import DetectionResult

logger = logging.getLogger(__name__)

# State transition map: current_state -> allowed next states
VALID_TRANSITIONS = {
    "detected": {"confirmed", "false_positive", "resolved"},
    "confirmed": {"responding", "clearing", "resolved", "false_positive"},
    "responding": {"clearing", "resolved"},
    "clearing": {"resolved"},
    "resolved": set(),
    "false_positive": set(),
}

# Auto-resolve timeout by severity (minutes)
AUTO_RESOLVE_TIMEOUT = {
    "minor": 15,
    "moderate": 30,
    "severe": 60,
    "critical": 120,
}


@dataclass
class TrackedIncident:
    """In-memory representation of an active incident being tracked."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    camera_id: str = ""
    incident_type: str = "unknown"
    severity: str = "minor"
    severity_score: float = 0.0
    confidence: float = 0.0
    status: str = "detected"
    latitude: float = 0.0
    longitude: float = 0.0
    interstate: str = ""
    direction: str | None = None
    vehicle_count: int = 0
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    confirmed_at: datetime | None = None
    resolved_at: datetime | None = None
    last_update: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    # Rolling window of detection confidences
    confidence_history: list[float] = field(default_factory=list)
    consecutive_detections: int = 0
    consecutive_non_detections: int = 0


class IncidentTracker:
    """Tracks active incidents, handles dedup and state transitions."""

    def __init__(self):
        self._active: dict[str, TrackedIncident] = {}

    @property
    def active_incidents(self) -> list[TrackedIncident]:
        return list(self._active.values())

    def process_detection(
        self,
        result: DetectionResult,
        camera_lat: float,
        camera_lon: float,
        camera_interstate: str,
        camera_direction: str | None = None,
    ) -> TrackedIncident | None:
        """Process a detection result. Returns a new or updated incident, or None."""
        now = datetime.now(timezone.utc)

        if result.is_incident and result.incident_type:
            # Check for existing incident (deduplication)
            existing = self._find_duplicate(
                camera_id=result.camera_id,
                incident_type=result.incident_type,
                lat=camera_lat,
                lon=camera_lon,
                interstate=camera_interstate,
                direction=camera_direction,
                timestamp=now,
            )

            if existing:
                return self._update_existing(existing, result, now)
            else:
                return self._create_new(result, camera_lat, camera_lon, camera_interstate, camera_direction, now)
        else:
            # No incident detected — update tracking for active incidents on this camera
            self._record_non_detection(result.camera_id, now)
            return None

    def _find_duplicate(
        self,
        camera_id: str,
        incident_type: str,
        lat: float,
        lon: float,
        interstate: str,
        direction: str | None,
        timestamp: datetime,
    ) -> TrackedIncident | None:
        """Check if detection matches an existing active incident."""
        for incident in self._active.values():
            if incident.status in ("resolved", "false_positive"):
                continue

            # Same camera, same type, within 5 minutes
            if (
                incident.camera_id == camera_id
                and incident.incident_type == incident_type
                and (timestamp - incident.last_update) < timedelta(minutes=5)
            ):
                return incident

            # Nearby camera (within ~0.5 miles), same interstate + direction, within 2 minutes
            dist = self._approx_distance_miles(lat, lon, incident.latitude, incident.longitude)
            if (
                dist < 0.5
                and incident.interstate == interstate
                and incident.direction == direction
                and (timestamp - incident.last_update) < timedelta(minutes=2)
            ):
                return incident

        return None

    def _update_existing(
        self, incident: TrackedIncident, result: DetectionResult, now: datetime
    ) -> TrackedIncident:
        """Update an existing incident with a new detection."""
        incident.consecutive_detections += 1
        incident.consecutive_non_detections = 0
        incident.confidence_history.append(result.crash_probability)
        incident.last_update = now

        # Update severity if higher
        if result.severity_score > incident.severity_score:
            incident.severity_score = result.severity_score
            incident.severity = self._score_to_level(result.severity_score)

        # Update vehicle count to max observed
        if result.vehicle_count > incident.vehicle_count:
            incident.vehicle_count = result.vehicle_count

        # Rolling average confidence
        recent = incident.confidence_history[-10:]
        incident.confidence = sum(recent) / len(recent)

        # Auto-confirm: 3+ consecutive detections with avg confidence > 0.7
        if (
            incident.status == "detected"
            and incident.consecutive_detections >= 3
            and incident.confidence > 0.7
        ):
            incident.status = "confirmed"
            incident.confirmed_at = now
            logger.info("Incident %s auto-confirmed (confidence: %.2f)", incident.id, incident.confidence)

        return incident

    def _create_new(
        self,
        result: DetectionResult,
        lat: float,
        lon: float,
        interstate: str,
        direction: str | None,
        now: datetime,
    ) -> TrackedIncident:
        """Create a new tracked incident."""
        incident = TrackedIncident(
            camera_id=result.camera_id,
            incident_type=result.incident_type or "unknown",
            severity=result.severity_level,
            severity_score=result.severity_score,
            confidence=result.crash_probability,
            latitude=lat,
            longitude=lon,
            interstate=interstate,
            direction=direction,
            vehicle_count=result.vehicle_count,
            detected_at=now,
            last_update=now,
            confidence_history=[result.crash_probability],
            consecutive_detections=1,
        )
        self._active[incident.id] = incident
        logger.info(
            "New incident %s: %s on %s (confidence: %.2f)",
            incident.id, incident.incident_type, interstate, incident.confidence,
        )
        return incident

    def _record_non_detection(self, camera_id: str, now: datetime) -> None:
        """Record that no incident was detected from this camera."""
        for incident in list(self._active.values()):
            if incident.camera_id != camera_id:
                continue
            if incident.status in ("resolved", "false_positive"):
                continue

            incident.consecutive_non_detections += 1
            incident.consecutive_detections = 0

            # Mark as false positive if confidence drops quickly
            if (
                incident.status == "detected"
                and incident.consecutive_non_detections >= 10
                and incident.confidence < 0.3
            ):
                incident.status = "false_positive"
                incident.resolved_at = now
                logger.info("Incident %s marked as false positive", incident.id)

    def check_auto_resolve(self) -> list[TrackedIncident]:
        """Check for incidents that should be auto-resolved. Call periodically."""
        now = datetime.now(timezone.utc)
        resolved = []

        for incident in list(self._active.values()):
            if incident.status in ("resolved", "false_positive"):
                continue

            timeout_minutes = AUTO_RESOLVE_TIMEOUT.get(incident.severity, 30)
            if (now - incident.last_update) > timedelta(minutes=timeout_minutes):
                incident.status = "resolved"
                incident.resolved_at = now
                resolved.append(incident)
                logger.info("Incident %s auto-resolved (no activity for %dm)", incident.id, timeout_minutes)

        # Clean up resolved incidents from active tracking
        for inc in resolved:
            self._active.pop(inc.id, None)

        return resolved

    @staticmethod
    def _approx_distance_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Fast approximate distance in miles between two lat/lon points."""
        # 1 degree latitude ~= 69 miles, 1 degree longitude ~= 54.6 miles (at US latitudes)
        dlat = abs(lat1 - lat2) * 69.0
        dlon = abs(lon1 - lon2) * 54.6
        return (dlat**2 + dlon**2) ** 0.5

    @staticmethod
    def _score_to_level(score: float) -> str:
        if score < 0.25:
            return "minor"
        elif score < 0.5:
            return "moderate"
        elif score < 0.75:
            return "severe"
        return "critical"
