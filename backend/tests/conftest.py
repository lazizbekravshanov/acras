"""Shared test fixtures for ACRAS backend tests."""

import asyncio
import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def app():
    """Create a test FastAPI application."""
    return create_app()


@pytest.fixture
def client(app):
    """Create a synchronous test client."""
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def api_key():
    """Return the test API key."""
    return "dev-secret-key-change-in-production"


@pytest.fixture
def auth_headers(api_key):
    """Return headers with API key."""
    return {"X-API-Key": api_key}


@pytest.fixture
def sample_camera_data():
    """Return sample camera creation data."""
    return {
        "name": "Test Camera I-95 NB",
        "description": "Test camera for unit tests",
        "stream_url": "https://example.com/stream.mjpeg",
        "stream_type": "mjpeg",
        "latitude": 29.1234,
        "longitude": -81.0567,
        "state_code": "FL",
        "interstate": "I-95",
        "direction": "NB",
        "mile_marker": 142.3,
        "source_agency": "FDOT",
        "metadata": {},
    }


@pytest.fixture
def sample_incident_data():
    """Return sample incident creation data."""
    return {
        "camera_id": str(uuid.uuid4()),
        "incident_type": "crash",
        "severity": "moderate",
        "severity_score": 0.45,
        "confidence": 0.85,
        "latitude": 29.1234,
        "longitude": -81.0567,
        "interstate": "I-95",
        "direction": "NB",
        "lane_impact": "lane_1",
        "vehicle_count": 2,
        "metadata": {},
    }
