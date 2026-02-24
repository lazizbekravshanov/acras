"""Pydantic schemas for analytics endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class HeatmapPoint(BaseModel):
    """A single point on the crash heatmap."""

    latitude: float
    longitude: float
    intensity: float = Field(..., ge=0, le=1)
    incident_count: int


class HeatmapResponse(BaseModel):
    """Crash heatmap data."""

    points: list[HeatmapPoint]
    total_incidents: int
    period_start: datetime
    period_end: datetime


class TrendDataPoint(BaseModel):
    """A single data point in a trend series."""

    timestamp: datetime
    count: int
    severity_breakdown: dict[str, int] = {}


class TrendResponse(BaseModel):
    """Trend data for charts."""

    period: str
    data: list[TrendDataPoint]
    total: int


class RiskScoreResponse(BaseModel):
    """Risk assessment for a location."""

    latitude: float
    longitude: float
    risk_score: float = Field(..., ge=0, le=1)
    risk_level: str  # low, medium, high, critical
    factors: list[str]
    historical_incidents_30d: int
    prediction_confidence: float


class SummaryResponse(BaseModel):
    """Dashboard summary metrics."""

    active_cameras: int
    active_incidents: int
    incidents_today: int
    incidents_this_week: int
    avg_detection_time_seconds: float | None = None
    avg_resolution_time_minutes: float | None = None
    false_positive_rate: float | None = None
    top_severity: str | None = None
