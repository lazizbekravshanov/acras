"""Tests for the severity scoring model."""

import pytest

from app.ml.severity_model import SeverityInput, SeverityModel, SeverityOutput


@pytest.fixture
def model():
    return SeverityModel()


def test_minor_incident(model):
    """Low crash probability + 1 car should be minor."""
    result = model.predict(SeverityInput(
        crash_probability=0.1,
        vehicle_count=1,
        vehicle_types=["car"],
        optical_flow_magnitude=1.0,
        motion_anomaly_score=0.1,
        lane_impact="right_shoulder",
        hour_of_day=14,
    ))
    assert result.level == "minor"
    assert result.score < 0.25


def test_critical_incident(model):
    """High crash prob + fire + many vehicles = critical."""
    result = model.predict(SeverityInput(
        crash_probability=0.95,
        vehicle_count=6,
        vehicle_types=["car", "truck", "car", "bus", "car", "car"],
        optical_flow_magnitude=5.0,
        motion_anomaly_score=0.9,
        lane_impact="all_lanes",
        hour_of_day=17,
        has_fire=True,
    ))
    assert result.level == "critical"
    assert result.score > 0.75


def test_severity_output_has_factors(model):
    """Output should include contributing factor descriptions."""
    result = model.predict(SeverityInput(
        crash_probability=0.8,
        vehicle_count=4,
        vehicle_types=["car", "truck", "car", "car"],
        optical_flow_magnitude=4.0,
        motion_anomaly_score=0.8,
        lane_impact="lanes_1_2",
        hour_of_day=8,
    ))
    assert isinstance(result.factors, list)
    assert len(result.factors) > 0
    assert any("rush_hour" in f for f in result.factors)


def test_severity_score_bounds(model):
    """Severity score should always be between 0 and 1."""
    # Test with extreme values
    result = model.predict(SeverityInput(
        crash_probability=1.0,
        vehicle_count=20,
        vehicle_types=["truck"] * 20,
        optical_flow_magnitude=10.0,
        motion_anomaly_score=1.0,
        lane_impact="all_lanes",
        hour_of_day=17,
        has_fire=True,
        has_smoke=True,
        has_debris=True,
    ))
    assert 0 <= result.score <= 1.0
