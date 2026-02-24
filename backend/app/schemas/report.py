"""Pydantic schemas for report endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class ReportResponse(BaseModel):
    """Schema for report API responses."""

    id: uuid.UUID
    incident_id: uuid.UUID
    report_type: str
    structured_data: dict
    narrative: str
    pdf_url: str | None = None
    version: int
    generated_by: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportListResponse(BaseModel):
    """Paginated list of reports."""

    items: list[ReportResponse]
    total: int
    page: int
    page_size: int
