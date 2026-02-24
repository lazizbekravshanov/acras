"""Aggregated v1 API router."""

from fastapi import APIRouter

from app.api.v1 import alerts, analytics, cameras, incidents, reports, websocket

router = APIRouter(prefix="/api/v1")

router.include_router(cameras.router, prefix="/cameras", tags=["cameras"])
router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
router.include_router(reports.router, prefix="/reports", tags=["reports"])
router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
router.include_router(websocket.router, tags=["websocket"])
