"""Pydantic schemas for incident endpoints."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class IncidentCreate(BaseModel):
    """Schema for creating an incident (internal, from detection pipeline)."""

    camera_id: uuid.UUID
    incident_type: Literal["crash", "stall", "debris", "fire", "wrong_way", "pedestrian", "weather_hazard", "unknown"]
    severity: Literal["minor", "moderate", "severe", "critical"]
    severity_score: float = Field(..., ge=0, le=1)
    confidence: float = Field(..., ge=0, le=1)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    interstate: str
    direction: str | None = None
    lane_impact: str | None = None
    vehicle_count: int | None = None
    thumbnail_url: str | None = None
    weather_conditions: dict | None = None
    detection_frames: list = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class IncidentUpdate(BaseModel):
    """Schema for updating an incident."""

    status: Literal["detected", "confirmed", "responding", "clearing", "resolved", "false_positive"] | None = None
    severity: Literal["minor", "moderate", "severe", "critical"] | None = None
    severity_score: float | None = Field(None, ge=0, le=1)
    confidence: float | None = Field(None, ge=0, le=1)
    lane_impact: str | None = None
    vehicle_count: int | None = None


class IncidentResponse(BaseModel):
    """Schema for incident API responses."""

    id: uuid.UUID
    camera_id: uuid.UUID
    incident_type: str
    severity: str
    severity_score: float
    confidence: float
    status: str
    latitude: float
    longitude: float
    interstate: str
    direction: str | None = None
    lane_impact: str | None = None
    vehicle_count: int | None = None
    detected_at: datetime
    confirmed_at: datetime | None = None
    resolved_at: datetime | None = None
    thumbnail_url: str | None = None
    weather_conditions: dict | None = None
    detection_frames: list = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IncidentListResponse(BaseModel):
    """Paginated list of incidents."""

    items: list[IncidentResponse]
    total: int
    page: int
    page_size: int
