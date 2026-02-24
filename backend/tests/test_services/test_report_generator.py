"""Tests for the report generator service."""

import pytest

from app.services.report_generator import ReportGenerator


@pytest.fixture
def generator():
    return ReportGenerator()


@pytest.fixture
def sample_incident():
    return {
        "id": "test-incident-001",
        "incident_type": "crash",
        "severity": "severe",
        "severity_score": 0.72,
        "confidence": 0.91,
        "latitude": 29.1234,
        "longitude": -81.0567,
        "interstate": "I-95",
        "direction": "NB",
        "mile_marker": 142.3,
        "state_code": "FL",
        "detected_at": "2025-01-15T15:42:00Z",
        "confirmed_at": "2025-01-15T15:42:30Z",
        "vehicle_count": 3,
        "lane_impact": "lanes_1_2",
    }


@pytest.fixture
def sample_weather():
    return {
        "condition": "rain",
        "temperature_f": 72,
        "visibility_miles": 3,
        "wind_speed_mph": 15,
        "road_condition": "wet",
    }


def test_structured_report_generation(generator, sample_incident, sample_weather):
    """Structured report should contain all required sections."""
    report = generator.generate_structured_report(sample_incident, sample_weather)

    assert "report_id" in report
    assert report["summary"]["type"] == "crash"
    assert report["summary"]["severity"] == "severe"
    assert report["summary"]["confidence"] == 0.91
    assert report["summary"]["location"]["interstate"] == "I-95"
    assert report["details"]["vehicle_count"] == 3
    assert report["weather"]["condition"] == "rain"
    assert "probable_cause_factors" in report["analysis"]


def test_narrative_generation(generator, sample_incident, sample_weather):
    """Narrative should be a non-empty string with key details."""
    structured = generator.generate_structured_report(sample_incident, sample_weather)
    narrative = generator.generate_narrative(structured)

    assert isinstance(narrative, str)
    assert len(narrative) > 50
    assert "I-95" in narrative
    assert "severe" in narrative.lower() or "SEVERE" in narrative


def test_severity_clearance_estimate(generator):
    """Clearance time estimates should scale with severity."""
    assert generator._estimate_clearance("minor") < generator._estimate_clearance("critical")


def test_lane_blockage_estimate(generator):
    """Blockage percentage should be 0 for no lane impact."""
    assert generator._estimate_blockage(None) == 0
    assert generator._estimate_blockage("all_lanes") == 100
    assert 0 < generator._estimate_blockage("lane_1") < 100


def test_weather_cause_inference(generator):
    """Rain weather should produce wet road and visibility factors."""
    incident = {"vehicle_count": 1}
    weather = {"condition": "rain", "visibility_miles": 2}
    causes = generator._infer_causes(incident, weather)
    assert "wet_road" in causes
    assert "reduced_visibility" in causes
