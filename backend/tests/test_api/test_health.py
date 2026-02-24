"""Tests for health check endpoints."""


def test_health_endpoint(client):
    """Health endpoint should return healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_openapi_docs(client):
    """OpenAPI docs should be accessible."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["info"]["title"] == "ACRAS — AI Crash Report Automation System"
    assert "/api/v1/cameras" in data["paths"]
