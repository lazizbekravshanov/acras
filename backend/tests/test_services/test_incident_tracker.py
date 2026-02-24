"""Tests for the incident tracking service."""

import pytest
from datetime import datetime, timezone

from app.services.incident_tracker import IncidentTracker, TrackedIncident
from app.services.detection_engine import DetectionResult


@pytest.fixture
def tracker():
    return IncidentTracker()


@pytest.fixture
def crash_detection():
    return DetectionResult(
        camera_id="cam-001",
        timestamp=1700000000.0,
        vehicles=[{"class": "car", "confidence": 0.9, "bbox": [100, 100, 200, 200]}],
        vehicle_count=2,
        optical_flow_magnitude=3.5,
        motion_anomaly_score=0.6,
        crash_probability=0.85,
        incident_type="crash",
        severity_score=0.65,
        severity_level="severe",
        is_incident=True,
        inference_time_ms=15.2,
    )


@pytest.fixture
def normal_detection():
    return DetectionResult(
        camera_id="cam-001",
        timestamp=1700000001.0,
        vehicles=[{"class": "car", "confidence": 0.9, "bbox": [100, 100, 200, 200]}],
        vehicle_count=3,
        optical_flow_magnitude=1.0,
        motion_anomaly_score=0.1,
        crash_probability=0.05,
        incident_type=None,
        severity_score=0.1,
        severity_level="minor",
        is_incident=False,
        inference_time_ms=12.0,
    )


def test_new_incident_created(tracker, crash_detection):
    """A crash detection should create a new tracked incident."""
    incident = tracker.process_detection(
        crash_detection,
        camera_lat=29.1234,
        camera_lon=-81.0567,
        camera_interstate="I-95",
        camera_direction="NB",
    )

    assert incident is not None
    assert incident.incident_type == "crash"
    assert incident.severity == "severe"
    assert incident.status == "detected"
    assert incident.confidence == 0.85
    assert len(tracker.active_incidents) == 1


def test_duplicate_detection_updates_existing(tracker, crash_detection):
    """Same camera + same type within 5 minutes = same incident."""
    incident1 = tracker.process_detection(
        crash_detection,
        camera_lat=29.1234,
        camera_lon=-81.0567,
        camera_interstate="I-95",
    )

    incident2 = tracker.process_detection(
        crash_detection,
        camera_lat=29.1234,
        camera_lon=-81.0567,
        camera_interstate="I-95",
    )

    assert incident1.id == incident2.id
    assert len(tracker.active_incidents) == 1
    assert incident2.consecutive_detections == 2


def test_auto_confirm_after_consecutive_detections(tracker, crash_detection):
    """3+ consecutive detections with high confidence should auto-confirm."""
    for _ in range(3):
        incident = tracker.process_detection(
            crash_detection,
            camera_lat=29.1234,
            camera_lon=-81.0567,
            camera_interstate="I-95",
        )

    assert incident.status == "confirmed"
    assert incident.confirmed_at is not None


def test_no_incident_on_normal_traffic(tracker, normal_detection):
    """Normal traffic should not create an incident."""
    result = tracker.process_detection(
        normal_detection,
        camera_lat=29.1234,
        camera_lon=-81.0567,
        camera_interstate="I-95",
    )

    assert result is None
    assert len(tracker.active_incidents) == 0


def test_distance_calculation():
    """Test approximate distance calculation."""
    tracker = IncidentTracker()
    # ~1 mile apart
    dist = tracker._approx_distance_miles(29.0, -81.0, 29.015, -81.0)
    assert 0.9 < dist < 1.2
