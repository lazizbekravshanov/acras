"""Report generation and retrieval endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.report import Report
from app.schemas.report import ReportListResponse, ReportResponse

router = APIRouter()


@router.get("", response_model=ReportListResponse)
async def list_reports(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    incident_id: uuid.UUID | None = None,
):
    """List reports with optional filtering."""
    query = select(Report)
    count_query = select(func.count(Report.id))

    if incident_id:
        query = query.where(Report.incident_id == incident_id)
        count_query = count_query.where(Report.incident_id == incident_id)

    total = (await db.execute(count_query)).scalar_one()
    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size).order_by(Report.created_at.desc()))
    reports = result.scalars().all()

    return ReportListResponse(
        items=[ReportResponse.model_validate(r) for r in reports],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(report_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get a single report by ID."""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return ReportResponse.model_validate(report)
