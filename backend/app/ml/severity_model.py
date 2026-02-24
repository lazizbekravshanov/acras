"""Severity scoring model — rule-based with upgrade path to ML.

Computes incident severity from detection features.
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SeverityInput:
    """Input features for severity scoring."""

    crash_probability: float
    vehicle_count: int
    vehicle_types: list[str]
    optical_flow_magnitude: float
    motion_anomaly_score: float
    lane_impact: str | None
    hour_of_day: int
    has_fire: bool = False
    has_smoke: bool = False
    has_debris: bool = False


@dataclass
class SeverityOutput:
    """Severity scoring result."""

    score: float  # 0.0 to 1.0
    level: str  # minor, moderate, severe, critical
    factors: list[str]


class SeverityModel:
    """Rule-based severity scoring with configurable weights."""

    def __init__(self):
        self._weights = {
            "crash_probability": 0.30,
            "vehicle_count": 0.20,
            "heavy_vehicles": 0.10,
            "motion_anomaly": 0.15,
            "lane_blockage": 0.10,
            "hazards": 0.15,
        }

    def predict(self, features: SeverityInput) -> SeverityOutput:
        """Compute severity score from input features."""
        score = 0.0
        factors = []

        # Crash probability (30%)
        score += features.crash_probability * self._weights["crash_probability"]

        # Vehicle count (20%)
        vc_factor = min(features.vehicle_count / 8.0, 1.0)
        score += vc_factor * self._weights["vehicle_count"]
        if features.vehicle_count >= 3:
            factors.append(f"multi_vehicle ({features.vehicle_count})")

        # Heavy vehicles (10%)
        heavy = sum(1 for v in features.vehicle_types if v in ("truck", "bus"))
        if heavy > 0:
            score += (heavy / max(len(features.vehicle_types), 1)) * self._weights["heavy_vehicles"]
            factors.append(f"heavy_vehicles ({heavy})")

        # Motion anomaly (15%)
        score += features.motion_anomaly_score * self._weights["motion_anomaly"]
        if features.motion_anomaly_score > 0.7:
            factors.append("high_motion_anomaly")

        # Lane blockage (10%)
        lane_scores = {
            "right_shoulder": 0.1,
            "left_shoulder": 0.15,
            "lane_1": 0.4,
            "lane_2": 0.4,
            "lanes_1_2": 0.7,
            "all_lanes": 1.0,
        }
        if features.lane_impact:
            lane_factor = lane_scores.get(features.lane_impact, 0.3)
            score += lane_factor * self._weights["lane_blockage"]
            factors.append(f"lane_impact: {features.lane_impact}")

        # Hazards (15%)
        hazard_score = 0.0
        if features.has_fire:
            hazard_score = 1.0
            factors.append("fire_detected")
        elif features.has_smoke:
            hazard_score = 0.7
            factors.append("smoke_detected")
        elif features.has_debris:
            hazard_score = 0.4
            factors.append("debris_detected")
        score += hazard_score * self._weights["hazards"]

        # Time-of-day modifier (rush hour = slower response = worse outcome)
        if 7 <= features.hour_of_day <= 9 or 16 <= features.hour_of_day <= 18:
            score *= 1.1
            factors.append("rush_hour")
        elif 22 <= features.hour_of_day or features.hour_of_day <= 5:
            score *= 1.05
            factors.append("nighttime")

        score = min(score, 1.0)

        # Map to level
        if score < 0.25:
            level = "minor"
        elif score < 0.5:
            level = "moderate"
        elif score < 0.75:
            level = "severe"
        else:
            level = "critical"

        return SeverityOutput(score=round(score, 3), level=level, factors=factors)
