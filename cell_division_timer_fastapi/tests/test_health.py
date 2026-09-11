"""Tests for application health and database connectivity."""

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    """Verify /health endpoint returns 200 OK and database connectivity."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert "app_name" in data
    assert "version" in data
    assert "database" in data
    assert data["database"]["connected"] is True
    assert "latency_ms" in data["database"]


def test_root_endpoint(client: TestClient):
    """Verify root GET / endpoint returns service discovery links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "documentation" in data
    assert data["documentation"] == "/docs"
