"""Analytics endpoints — heatmaps, trends, predictions, summaries."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.camera import Camera
from app.models.incident import Incident
from app.schemas.analytics import (
    HeatmapPoint,
    HeatmapResponse,
    RiskScoreResponse,
    SummaryResponse,
    TrendDataPoint,
    TrendResponse,
)
from app.services.analytics_engine import AnalyticsEngine

router = APIRouter()

_analytics = AnalyticsEngine()


@router.get("/summary", response_model=SummaryResponse)
async def get_summary(db: AsyncSession = Depends(get_db)):
    """Get dashboard summary metrics."""
    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_ago = now - timedelta(days=30)

    active_cameras = (
        await db.execute(select(func.count(Camera.id)).where(Camera.status == "active"))
    ).scalar_one()

    active_incidents = (
        await db.execute(
            select(func.count(Incident.id)).where(
                Incident.status.in_(["detected", "confirmed", "responding", "clearing"])
            )
        )
    ).scalar_one()

    incidents_today = (
        await db.execute(
            select(func.count(Incident.id)).where(Incident.detected_at >= today_start)
        )
    ).scalar_one()

    incidents_this_week = (
        await db.execute(
            select(func.count(Incident.id)).where(Incident.detected_at >= week_start)
        )
    ).scalar_one()

    # Avg detection-to-confirmation time (last 30 days)
    avg_detection_time = (
        await db.execute(
            select(
                func.avg(
                    extract("epoch", Incident.confirmed_at) - extract("epoch", Incident.detected_at)
                )
            ).where(
                Incident.confirmed_at.is_not(None),
                Incident.detected_at >= month_ago,
            )
        )
    ).scalar_one()

    # Avg resolution time in minutes (last 30 days)
    avg_resolution_time = (
        await db.execute(
            select(
                func.avg(
                    (extract("epoch", Incident.resolved_at) - extract("epoch", Incident.detected_at)) / 60.0
                )
            ).where(
                Incident.resolved_at.is_not(None),
                Incident.detected_at >= month_ago,
            )
        )
    ).scalar_one()

    # False positive rate (last 30 days)
    total_30d = (
        await db.execute(
            select(func.count(Incident.id)).where(Incident.detected_at >= month_ago)
        )
    ).scalar_one()

    fp_30d = (
        await db.execute(
            select(func.count(Incident.id)).where(
                Incident.detected_at >= month_ago,
                Incident.status == "false_positive",
            )
        )
    ).scalar_one()

    fp_rate = round(fp_30d / total_30d, 3) if total_30d > 0 else None

    # Top severity in last 7 days
    top_severity_row = (
        await db.execute(
            select(Incident.severity, func.count(Incident.id).label("cnt"))
            .where(Incident.detected_at >= week_start)
            .group_by(Incident.severity)
            .order_by(func.count(Incident.id).desc())
            .limit(1)
        )
    ).first()

    return SummaryResponse(
        active_cameras=active_cameras,
        active_incidents=active_incidents,
        incidents_today=incidents_today,
        incidents_this_week=incidents_this_week,
        avg_detection_time_seconds=round(avg_detection_time, 1) if avg_detection_time else None,
        avg_resolution_time_minutes=round(avg_resolution_time, 1) if avg_resolution_time else None,
        false_positive_rate=fp_rate,
        top_severity=top_severity_row.severity if top_severity_row else None,
    )


@router.get("/heatmap", response_model=HeatmapResponse)
async def get_heatmap(
    db: AsyncSession = Depends(get_db),
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    severity: str | None = None,
):
    """Get crash heatmap data for geographic visualization."""
    now = datetime.now(UTC)
    if not start_date:
        start_date = now - timedelta(days=30)
    if not end_date:
        end_date = now

    # Round coordinates to ~0.5 mile buckets for spatial clustering
    lat_bucket = func.round(Incident.latitude * 100) / 100  # ~0.7 mile buckets
    lon_bucket = func.round(Incident.longitude * 100) / 100

    query = select(
        lat_bucket.label("latitude"),
        lon_bucket.label("longitude"),
        func.count(Incident.id).label("incident_count"),
    ).where(
        Incident.detected_at >= start_date,
        Incident.detected_at <= end_date,
    ).group_by(
        lat_bucket, lon_bucket
    )

    if severity:
        query = query.where(Incident.severity == severity)

    result = await db.execute(query)
    rows = result.all()

    max_count = max((r.incident_count for r in rows), default=1)
    points = [
        HeatmapPoint(
            latitude=float(r.latitude),
            longitude=float(r.longitude),
            intensity=r.incident_count / max_count,
            incident_count=r.incident_count,
        )
        for r in rows
    ]

    total = sum(r.incident_count for r in rows)

    return HeatmapResponse(
        points=points,
        total_incidents=total,
        period_start=start_date,
        period_end=end_date,
    )


@router.get("/trends", response_model=TrendResponse)
async def get_trends(
    db: AsyncSession = Depends(get_db),
    period: str = Query("daily", pattern="^(hourly|daily|weekly)$"),
    days: int = Query(30, ge=1, le=365),
):
    """Get incident trend data for time-series charts."""
    now = datetime.now(UTC)
    start = now - timedelta(days=days)

    if period == "hourly":
        trunc_func = func.date_trunc("hour", Incident.detected_at)
    elif period == "weekly":
        trunc_func = func.date_trunc("week", Incident.detected_at)
    else:
        trunc_func = func.date_trunc("day", Incident.detected_at)

    query = (
        select(
            trunc_func.label("period"),
            func.count(Incident.id).label("count"),
        )
        .where(Incident.detected_at >= start)
        .group_by("period")
        .order_by("period")
    )

    result = await db.execute(query)
    rows = result.all()

    data = [TrendDataPoint(timestamp=r.period, count=r.count) for r in rows]
    total = sum(r.count for r in rows)

    return TrendResponse(period=period, data=data, total=total)


@router.get("/risk", response_model=RiskScoreResponse)
async def get_risk_score(
    db: AsyncSession = Depends(get_db),
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
):
    """Get risk assessment for a specific location based on historical data."""
    now = datetime.now(UTC)
    thirty_days_ago = now - timedelta(days=30)

    # Count incidents within ~1 mile radius (~0.015 degrees) in last 30 days
    nearby_count = (
        await db.execute(
            select(func.count(Incident.id)).where(
                Incident.detected_at >= thirty_days_ago,
                func.abs(Incident.latitude - lat) < 0.015,
                func.abs(Incident.longitude - lon) < 0.015,
            )
        )
    ).scalar_one()

    # Fetch weather for context if available
    weather_condition = None
    try:
        from app.services.weather_service import get_weather
        weather = await get_weather(lat, lon)
        if weather:
            weather_condition = weather.get("condition")
    except Exception:
        pass

    risk_score, risk_level, factors = _analytics.compute_risk_score(
        historical_count=nearby_count,
        hour=now.hour,
        weather_condition=weather_condition,
    )

    return RiskScoreResponse(
        latitude=lat,
        longitude=lon,
        risk_score=risk_score,
        risk_level=risk_level,
        factors=factors,
        historical_incidents_30d=nearby_count,
        prediction_confidence=0.7 + min(nearby_count / 100, 0.25),
    )
