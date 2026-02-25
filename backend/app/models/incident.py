"""Incident model — detected traffic events."""

import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import DateTime, Double, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

INCIDENT_TYPES = ("crash", "stall", "debris", "fire", "wrong_way", "pedestrian", "weather_hazard", "unknown")
SEVERITY_LEVELS = ("minor", "moderate", "severe", "critical")
INCIDENT_STATUSES = ("detected", "confirmed", "responding", "clearing", "resolved", "false_positive")


class Incident(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A detected traffic incident."""

    __tablename__ = "incidents"

    camera_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cameras.id"), nullable=False)
    incident_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    severity_score: Mapped[float] = mapped_column(Double, nullable=False)
    confidence: Mapped[float] = mapped_column(Double, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="detected")
    location: Mapped[str] = mapped_column(Geography("POINT", srid=4326), nullable=False)
    latitude: Mapped[float] = mapped_column(Double, nullable=False)
    longitude: Mapped[float] = mapped_column(Double, nullable=False)
    interstate: Mapped[str] = mapped_column(String(20), nullable=False)
    direction: Mapped[str | None] = mapped_column(String(20))
    lane_impact: Mapped[str | None] = mapped_column(String(50))
    vehicle_count: Mapped[int | None] = mapped_column(Integer)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    detection_frames: Mapped[list] = mapped_column(JSONB, default=list)
    thumbnail_url: Mapped[str | None] = mapped_column(Text)
    weather_conditions: Mapped[dict | None] = mapped_column(JSONB)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)

    # Relationships
    camera = relationship("Camera", back_populates="incidents")
    reports = relationship("Report", back_populates="incident", lazy="selectin")
    alerts = relationship("Alert", back_populates="incident", lazy="noload")

    __table_args__ = (
        Index("idx_incidents_camera", "camera_id"),
        Index("idx_incidents_status", "status"),
        Index("idx_incidents_severity", "severity"),
        Index("idx_incidents_detected_at", "detected_at"),
        Index("idx_incidents_location", "location", postgresql_using="gist"),
        Index("idx_incidents_type", "incident_type"),
    )
