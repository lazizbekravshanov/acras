"""Camera and camera health log models."""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Double, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Camera(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A traffic camera source."""

    __tablename__ = "cameras"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    stream_url: Mapped[str] = mapped_column(Text, nullable=False)
    stream_type: Mapped[str] = mapped_column(String(20), nullable=False)  # rtsp, mjpeg, hls, http_image
    latitude: Mapped[float] = mapped_column(Double, nullable=False)
    longitude: Mapped[float] = mapped_column(Double, nullable=False)
    state_code: Mapped[str] = mapped_column(String(2), nullable=False)
    interstate: Mapped[str] = mapped_column(String(20), nullable=False)
    direction: Mapped[str | None] = mapped_column(String(20))
    mile_marker: Mapped[float | None] = mapped_column(Double)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    last_frame_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fps_actual: Mapped[float | None] = mapped_column(Double)
    resolution_width: Mapped[int | None] = mapped_column(Integer)
    resolution_height: Mapped[int | None] = mapped_column(Integer)
    source_agency: Mapped[str | None] = mapped_column(String(255))
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)

    # Relationships
    incidents = relationship("Incident", back_populates="camera", lazy="selectin")
    health_logs = relationship("CameraHealthLog", back_populates="camera", lazy="noload")

    __table_args__ = (
        Index("idx_cameras_status", "status"),
        Index("idx_cameras_interstate", "interstate"),
    )


class CameraHealthLog(Base):
    """Periodic health check records for cameras."""

    __tablename__ = "camera_health_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    camera_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cameras.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    fps: Mapped[float | None] = mapped_column(Double)
    latency_ms: Mapped[float | None] = mapped_column(Double)
    error_message: Mapped[str | None] = mapped_column(Text)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    camera = relationship("Camera", back_populates="health_logs")

    __table_args__ = (
        Index("idx_camera_health_camera", "camera_id", "checked_at"),
    )
