"""Analytics endpoints — heatmaps, trends, predictions, summaries."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
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

router = APIRouter()


@router.get("/summary", response_model=SummaryResponse)
async def get_summary(db: AsyncSession = Depends(get_db)):
    """Get dashboard summary metrics."""
    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())

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

    return SummaryResponse(
        active_cameras=active_cameras,
        active_incidents=active_incidents,
        incidents_today=incidents_today,
        incidents_this_week=incidents_this_week,
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

    query = select(
        Incident.latitude,
        Incident.longitude,
        func.count(Incident.id).label("incident_count"),
    ).where(
        Incident.detected_at >= start_date,
        Incident.detected_at <= end_date,
    ).group_by(
        Incident.latitude, Incident.longitude
    )

    if severity:
        query = query.where(Incident.severity == severity)

    result = await db.execute(query)
    rows = result.all()

    max_count = max((r.incident_count for r in rows), default=1)
    points = [
        HeatmapPoint(
            latitude=r.latitude,
            longitude=r.longitude,
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

    # Simple risk scoring based on incident density
    risk_score = min(1.0, nearby_count / 20.0)
    if risk_score < 0.25:
        risk_level = "low"
    elif risk_score < 0.5:
        risk_level = "medium"
    elif risk_score < 0.75:
        risk_level = "high"
    else:
        risk_level = "critical"

    factors = []
    if nearby_count > 0:
        factors.append(f"{nearby_count} incidents in last 30 days")
    now_hour = now.hour
    if 7 <= now_hour <= 9 or 16 <= now_hour <= 18:
        factors.append("rush_hour")
        risk_score = min(1.0, risk_score * 1.3)

    return RiskScoreResponse(
        latitude=lat,
        longitude=lon,
        risk_score=round(risk_score, 3),
        risk_level=risk_level,
        factors=factors,
        historical_incidents_30d=nearby_count,
        prediction_confidence=0.7,
    )
