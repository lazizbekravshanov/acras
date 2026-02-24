"""Alert configuration and history endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthDep, get_db
from app.models.alert import Alert, AlertConfig
from app.schemas.alert import (
    AlertConfigCreate,
    AlertConfigResponse,
    AlertConfigUpdate,
    AlertListResponse,
    AlertResponse,
)

router = APIRouter()


@router.post("/configs", response_model=AlertConfigResponse, status_code=201, dependencies=[AuthDep])
async def create_alert_config(data: AlertConfigCreate, db: AsyncSession = Depends(get_db)):
    """Create a new alert configuration rule."""
    config = AlertConfig(
        name=data.name,
        channel=data.channel,
        recipient=data.recipient,
        min_severity=data.min_severity,
        incident_types=data.incident_types,
        interstates=data.interstates,
        is_active=data.is_active,
        cooldown_minutes=data.cooldown_minutes,
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return AlertConfigResponse.model_validate(config)


@router.get("/configs", response_model=list[AlertConfigResponse])
async def list_alert_configs(db: AsyncSession = Depends(get_db)):
    """List all alert configurations."""
    result = await db.execute(select(AlertConfig).order_by(AlertConfig.created_at.desc()))
    configs = result.scalars().all()
    return [AlertConfigResponse.model_validate(c) for c in configs]


@router.patch("/configs/{config_id}", response_model=AlertConfigResponse, dependencies=[AuthDep])
async def update_alert_config(
    config_id: uuid.UUID, data: AlertConfigUpdate, db: AsyncSession = Depends(get_db)
):
    """Update an alert configuration."""
    result = await db.execute(select(AlertConfig).where(AlertConfig.id == config_id))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Alert config not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(config, key, value)

    await db.commit()
    await db.refresh(config)
    return AlertConfigResponse.model_validate(config)


@router.delete("/configs/{config_id}", status_code=204, dependencies=[AuthDep])
async def delete_alert_config(config_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Delete an alert configuration."""
    result = await db.execute(select(AlertConfig).where(AlertConfig.id == config_id))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Alert config not found")
    await db.delete(config)
    await db.commit()


@router.get("/history", response_model=AlertListResponse)
async def list_alerts(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    incident_id: uuid.UUID | None = None,
    status: str | None = None,
):
    """List alert delivery history."""
    query = select(Alert)
    count_query = select(func.count(Alert.id))

    if incident_id:
        query = query.where(Alert.incident_id == incident_id)
        count_query = count_query.where(Alert.incident_id == incident_id)
    if status:
        query = query.where(Alert.status == status)
        count_query = count_query.where(Alert.status == status)

    total = (await db.execute(count_query)).scalar_one()
    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size).order_by(Alert.created_at.desc()))
    alerts = result.scalars().all()

    return AlertListResponse(
        items=[AlertResponse.model_validate(a) for a in alerts],
        total=total,
        page=page,
        page_size=page_size,
    )
