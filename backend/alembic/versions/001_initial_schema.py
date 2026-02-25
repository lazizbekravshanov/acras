"""Initial schema — all tables for ACRAS.

Revision ID: 001
Revises: None
Create Date: 2025-01-15
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Cameras
    op.create_table(
        "cameras",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("stream_url", sa.Text, nullable=False),
        sa.Column("stream_type", sa.String(20), nullable=False),
        sa.Column("latitude", sa.Double, nullable=False),
        sa.Column("longitude", sa.Double, nullable=False),
        sa.Column("state_code", sa.String(2), nullable=False),
        sa.Column("interstate", sa.String(20), nullable=False),
        sa.Column("direction", sa.String(20)),
        sa.Column("mile_marker", sa.Double),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("last_frame_at", sa.DateTime(timezone=True)),
        sa.Column("fps_actual", sa.Double),
        sa.Column("resolution_width", sa.Integer),
        sa.Column("resolution_height", sa.Integer),
        sa.Column("source_agency", sa.String(255)),
        sa.Column("metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_cameras_status", "cameras", ["status"])
    op.create_index("idx_cameras_interstate", "cameras", ["interstate"])

    # Incidents
    op.create_table(
        "incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("camera_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cameras.id"), nullable=False),
        sa.Column("incident_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("severity_score", sa.Double, nullable=False),
        sa.Column("confidence", sa.Double, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="detected"),
        sa.Column("latitude", sa.Double, nullable=False),
        sa.Column("longitude", sa.Double, nullable=False),
        sa.Column("interstate", sa.String(20), nullable=False),
        sa.Column("direction", sa.String(20)),
        sa.Column("lane_impact", sa.String(50)),
        sa.Column("vehicle_count", sa.Integer),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True)),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("detection_frames", postgresql.JSONB, server_default="[]"),
        sa.Column("thumbnail_url", sa.Text),
        sa.Column("weather_conditions", postgresql.JSONB),
        sa.Column("metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_incidents_camera", "incidents", ["camera_id"])
    op.create_index("idx_incidents_status", "incidents", ["status"])
    op.create_index("idx_incidents_severity", "incidents", ["severity"])
    op.create_index("idx_incidents_detected_at", "incidents", ["detected_at"])
    op.create_index("idx_incidents_type", "incidents", ["incident_type"])

    # Reports
    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id"), nullable=False),
        sa.Column("report_type", sa.String(20), nullable=False),
        sa.Column("structured_data", postgresql.JSONB, nullable=False),
        sa.Column("narrative", sa.Text, nullable=False),
        sa.Column("pdf_url", sa.Text),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("generated_by", sa.String(50), nullable=False, server_default="system"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_reports_incident", "reports", ["incident_id"])

    # Alerts
    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id"), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("recipient", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("payload", postgresql.JSONB, nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("error_message", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_alerts_incident", "alerts", ["incident_id"])
    op.create_index("idx_alerts_status", "alerts", ["status"])

    # Alert configurations
    op.create_table(
        "alert_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("recipient", sa.Text, nullable=False),
        sa.Column("min_severity", sa.String(20), nullable=False, server_default="moderate"),
        sa.Column("incident_types", postgresql.ARRAY(sa.Text), server_default="{crash}"),
        sa.Column("interstates", postgresql.ARRAY(sa.Text)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("cooldown_minutes", sa.Integer, nullable=False, server_default="5"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Analytics snapshots
    op.create_table(
        "analytics_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("snapshot_type", sa.String(50), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data", postgresql.JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_analytics_type_period", "analytics_snapshots", ["snapshot_type", "period_start"])

    # Camera health log
    op.create_table(
        "camera_health_log",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("camera_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cameras.id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("fps", sa.Double),
        sa.Column("latency_ms", sa.Double),
        sa.Column("error_message", sa.Text),
        sa.Column("checked_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_camera_health_camera", "camera_health_log", ["camera_id", "checked_at"])


def downgrade() -> None:
    op.drop_table("camera_health_log")
    op.drop_table("analytics_snapshots")
    op.drop_table("alert_configs")
    op.drop_table("alerts")
    op.drop_table("reports")
    op.drop_table("incidents")
    op.drop_table("cameras")
