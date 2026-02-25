"""Incident query and management endpoints."""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthDep, get_db
from app.models.incident import Incident
from app.schemas.incident import IncidentCreate, IncidentListResponse, IncidentResponse, IncidentUpdate

router = APIRouter()


def _incident_to_response(incident: Incident) -> IncidentResponse:
    return IncidentResponse.model_validate(incident)


@router.get("", response_model=IncidentListResponse)
async def list_incidents(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: str | None = None,
    severity: str | None = None,
    incident_type: str | None = None,
    camera_id: uuid.UUID | None = None,
    interstate: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
):
    """List incidents with filtering and pagination."""
    query = select(Incident)
    count_query = select(func.count(Incident.id))

    filters = []
    if status:
        filters.append(Incident.status == status)
    if severity:
        filters.append(Incident.severity == severity)
    if incident_type:
        filters.append(Incident.incident_type == incident_type)
    if camera_id:
        filters.append(Incident.camera_id == camera_id)
    if interstate:
        filters.append(Incident.interstate == interstate)
    if start_date:
        filters.append(Incident.detected_at >= start_date)
    if end_date:
        filters.append(Incident.detected_at <= end_date)

    for f in filters:
        query = query.where(f)
        count_query = count_query.where(f)

    total = (await db.execute(count_query)).scalar_one()
    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size).order_by(Incident.detected_at.desc()))
    incidents = result.scalars().all()

    return IncidentListResponse(
        items=[_incident_to_response(i) for i in incidents],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get a single incident by ID."""
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return _incident_to_response(incident)


@router.post("", response_model=IncidentResponse, status_code=201, dependencies=[AuthDep])
async def create_incident(data: IncidentCreate, db: AsyncSession = Depends(get_db)):
    """Create a new incident (primarily used by the detection pipeline)."""
    incident = Incident(
        camera_id=data.camera_id,
        incident_type=data.incident_type,
        severity=data.severity,
        severity_score=data.severity_score,
        confidence=data.confidence,
        latitude=data.latitude,
        longitude=data.longitude,
        interstate=data.interstate,
        direction=data.direction,
        lane_impact=data.lane_impact,
        vehicle_count=data.vehicle_count,
        thumbnail_url=data.thumbnail_url,
        weather_conditions=data.weather_conditions,
        detection_frames=data.detection_frames,
        metadata_=data.metadata,
    )
    db.add(incident)
    await db.commit()
    await db.refresh(incident)
    return _incident_to_response(incident)


@router.patch("/{incident_id}", response_model=IncidentResponse, dependencies=[AuthDep])
async def update_incident(incident_id: uuid.UUID, data: IncidentUpdate, db: AsyncSession = Depends(get_db)):
    """Update an incident (status changes, manual overrides)."""
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    update_data = data.model_dump(exclude_unset=True)

    # Validate status transitions
    if "status" in update_data:
        from app.services.incident_tracker import VALID_TRANSITIONS

        new_status = update_data["status"]
        allowed = VALID_TRANSITIONS.get(incident.status, set())
        if new_status != incident.status and new_status not in allowed:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid status transition: {incident.status} -> {new_status}",
            )
        if new_status == "confirmed" and incident.confirmed_at is None:
            incident.confirmed_at = datetime.now(UTC)
        elif new_status == "resolved" and incident.resolved_at is None:
            incident.resolved_at = datetime.now(UTC)

    # Explicit field allowlist for setattr
    updatable_fields = {"status", "severity", "severity_score", "confidence", "lane_impact", "vehicle_count"}
    for key, value in update_data.items():
        if key in updatable_fields:
            setattr(incident, key, value)

    await db.commit()
    await db.refresh(incident)
    return _incident_to_response(incident)
