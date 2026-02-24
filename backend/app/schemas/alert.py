"""Pydantic schemas for alert endpoints."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class AlertConfigCreate(BaseModel):
    """Schema for creating an alert configuration."""

    name: str = Field(..., max_length=255)
    channel: Literal["webhook", "email", "sms", "websocket", "push"]
    recipient: str
    min_severity: Literal["minor", "moderate", "severe", "critical"] = "moderate"
    incident_types: list[str] = Field(default_factory=lambda: ["crash"])
    interstates: list[str] | None = None
    is_active: bool = True
    cooldown_minutes: int = Field(5, ge=1)


class AlertConfigUpdate(BaseModel):
    """Schema for updating an alert configuration."""

    name: str | None = Field(None, max_length=255)
    channel: Literal["webhook", "email", "sms", "websocket", "push"] | None = None
    recipient: str | None = None
    min_severity: Literal["minor", "moderate", "severe", "critical"] | None = None
    incident_types: list[str] | None = None
    interstates: list[str] | None = None
    is_active: bool | None = None
    cooldown_minutes: int | None = Field(None, ge=1)


class AlertConfigResponse(BaseModel):
    """Schema for alert config API responses."""

    id: uuid.UUID
    name: str
    channel: str
    recipient: str
    min_severity: str
    incident_types: list[str]
    interstates: list[str] | None = None
    is_active: bool
    cooldown_minutes: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AlertResponse(BaseModel):
    """Schema for alert history API responses."""

    id: uuid.UUID
    incident_id: uuid.UUID
    channel: str
    recipient: str
    status: str
    payload: dict
    sent_at: datetime | None = None
    error_message: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertListResponse(BaseModel):
    """Paginated list of alerts."""

    items: list[AlertResponse]
    total: int
    page: int
    page_size: int
