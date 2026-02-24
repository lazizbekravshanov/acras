"""Analytics engine — historical analysis, trends, and prediction.

Provides heatmap data, temporal patterns, severity trends, and risk scoring.
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.camera import Camera
from app.models.incident import Incident

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """Computes analytics and predictions from historical incident data."""

    async def get_summary_stats(self, db: AsyncSession) -> dict:
        """Get high-level summary statistics for the dashboard."""
        now = datetime.now(timezone.utc)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        active_cameras = (await db.execute(
            select(func.count(Camera.id)).where(Camera.status == "active")
        )).scalar_one()

        active_incidents = (await db.execute(
            select(func.count(Incident.id)).where(
                Incident.status.in_(["detected", "confirmed", "responding", "clearing"])
            )
        )).scalar_one()

        today_count = (await db.execute(
            select(func.count(Incident.id)).where(Incident.detected_at >= today)
        )).scalar_one()

        week_count = (await db.execute(
            select(func.count(Incident.id)).where(Incident.detected_at >= week_ago)
        )).scalar_one()

        # False positive rate (last 30 days)
        total_30d = (await db.execute(
            select(func.count(Incident.id)).where(Incident.detected_at >= month_ago)
        )).scalar_one()

        fp_30d = (await db.execute(
            select(func.count(Incident.id)).where(
                Incident.detected_at >= month_ago,
                Incident.status == "false_positive",
            )
        )).scalar_one()

        fp_rate = fp_30d / total_30d if total_30d > 0 else None

        return {
            "active_cameras": active_cameras,
            "active_incidents": active_incidents,
            "incidents_today": today_count,
            "incidents_this_week": week_count,
            "false_positive_rate": round(fp_rate, 3) if fp_rate is not None else None,
        }

    async def get_hourly_pattern(self, db: AsyncSession, days: int = 30) -> list[dict]:
        """Get incident count by hour of day for the last N days."""
        start = datetime.now(timezone.utc) - timedelta(days=days)

        result = await db.execute(
            select(
                func.extract("hour", Incident.detected_at).label("hour"),
                func.count(Incident.id).label("count"),
            )
            .where(Incident.detected_at >= start)
            .group_by("hour")
            .order_by("hour")
        )

        return [{"hour": int(r.hour), "count": r.count} for r in result.all()]

    async def get_severity_distribution(self, db: AsyncSession, days: int = 30) -> dict[str, int]:
        """Get severity breakdown for the last N days."""
        start = datetime.now(timezone.utc) - timedelta(days=days)

        result = await db.execute(
            select(Incident.severity, func.count(Incident.id).label("count"))
            .where(Incident.detected_at >= start)
            .group_by(Incident.severity)
        )

        return {r.severity: r.count for r in result.all()}

    async def get_top_locations(self, db: AsyncSession, limit: int = 10) -> list[dict]:
        """Get top incident locations ranked by frequency."""
        start = datetime.now(timezone.utc) - timedelta(days=30)

        result = await db.execute(
            select(
                Incident.interstate,
                Incident.direction,
                Incident.latitude,
                Incident.longitude,
                func.count(Incident.id).label("count"),
            )
            .where(Incident.detected_at >= start)
            .group_by(Incident.interstate, Incident.direction, Incident.latitude, Incident.longitude)
            .order_by(func.count(Incident.id).desc())
            .limit(limit)
        )

        return [
            {
                "interstate": r.interstate,
                "direction": r.direction,
                "latitude": r.latitude,
                "longitude": r.longitude,
                "incident_count": r.count,
            }
            for r in result.all()
        ]

    def compute_risk_score(
        self,
        historical_count: int,
        hour: int,
        weather_condition: str | None = None,
    ) -> tuple[float, str, list[str]]:
        """Compute a risk score for a location based on historical data and current conditions."""
        score = 0.0
        factors = []

        # Historical density (40% weight)
        hist_factor = min(historical_count / 20.0, 1.0)
        score += hist_factor * 0.4
        if historical_count > 5:
            factors.append(f"high_incident_density ({historical_count} in 30d)")

        # Time of day (30% weight)
        time_risk = 0.0
        if 7 <= hour <= 9 or 16 <= hour <= 18:
            time_risk = 0.8
            factors.append("rush_hour")
        elif 22 <= hour or hour <= 5:
            time_risk = 0.6
            factors.append("nighttime")
        elif 11 <= hour <= 13:
            time_risk = 0.4
            factors.append("midday")
        score += time_risk * 0.3

        # Weather (30% weight)
        weather_risk = 0.0
        if weather_condition:
            wc = weather_condition.lower()
            if "rain" in wc or "storm" in wc:
                weather_risk = 0.7
                factors.append("wet_conditions")
            elif "snow" in wc or "ice" in wc:
                weather_risk = 0.9
                factors.append("winter_conditions")
            elif "fog" in wc:
                weather_risk = 0.6
                factors.append("reduced_visibility")
        score += weather_risk * 0.3

        score = min(score, 1.0)

        if score < 0.25:
            level = "low"
        elif score < 0.5:
            level = "medium"
        elif score < 0.75:
            level = "high"
        else:
            level = "critical"

        return round(score, 3), level, factors
