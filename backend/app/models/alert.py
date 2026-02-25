"""Alert and alert configuration models."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Alert(Base, UUIDPrimaryKeyMixin):
    """A sent alert for an incident."""

    __tablename__ = "alerts"

    incident_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)  # webhook, email, sms, websocket, push
    recipient: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    incident = relationship("Incident", back_populates="alerts")

    __table_args__ = (
        Index("idx_alerts_incident", "incident_id"),
        Index("idx_alerts_status", "status"),
    )


class AlertConfig(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Configuration for alert routing rules."""

    __tablename__ = "alert_configs"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    recipient: Mapped[str] = mapped_column(Text, nullable=False)
    min_severity: Mapped[str] = mapped_column(String(20), nullable=False, default="moderate")
    incident_types: Mapped[list] = mapped_column(ARRAY(Text), default=lambda: ["crash"])
    interstates: Mapped[list | None] = mapped_column(ARRAY(Text))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    cooldown_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
