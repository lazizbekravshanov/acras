"""Pydantic schemas for camera endpoints."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class CameraBase(BaseModel):
    """Shared camera fields."""

    name: str = Field(..., max_length=255)
    description: str | None = None
    stream_url: str
    stream_type: Literal["rtsp", "mjpeg", "hls", "http_image"]
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    state_code: str = Field(..., min_length=2, max_length=2)
    interstate: str = Field(..., max_length=20)
    direction: str | None = Field(None, max_length=20)
    mile_marker: float | None = None
    source_agency: str | None = Field(None, max_length=255)
    metadata_: dict = Field(default_factory=dict, alias="metadata")


class CameraCreate(CameraBase):
    """Schema for creating a camera."""
    pass


class CameraUpdate(BaseModel):
    """Schema for updating a camera (all fields optional)."""

    name: str | None = Field(None, max_length=255)
    description: str | None = None
    stream_url: str | None = None
    stream_type: Literal["rtsp", "mjpeg", "hls", "http_image"] | None = None
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    state_code: str | None = Field(None, min_length=2, max_length=2)
    interstate: str | None = Field(None, max_length=20)
    direction: str | None = Field(None, max_length=20)
    mile_marker: float | None = None
    status: Literal["active", "inactive", "error", "maintenance"] | None = None
    source_agency: str | None = Field(None, max_length=255)
    metadata_: dict | None = Field(None, alias="metadata")


class CameraResponse(CameraBase):
    """Schema for camera API responses."""

    id: uuid.UUID
    status: str
    last_frame_at: datetime | None = None
    fps_actual: float | None = None
    resolution_width: int | None = None
    resolution_height: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class CameraListResponse(BaseModel):
    """Paginated list of cameras."""

    items: list[CameraResponse]
    total: int
    page: int
    page_size: int


class CameraBulkImport(BaseModel):
    """Bulk import cameras from JSON."""

    cameras: list[CameraCreate]


class CameraHealthResponse(BaseModel):
    """Camera health status."""

    camera_id: uuid.UUID
    status: str
    fps: float | None = None
    latency_ms: float | None = None
    error_message: str | None = None
    checked_at: datetime

    model_config = {"from_attributes": True}
