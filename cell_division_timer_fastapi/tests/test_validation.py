"""Tests for API payload validation rules and error response formatting."""

from fastapi.testclient import TestClient


def test_validation_negative_cell_cycle(client: TestClient, sample_cell):
    """Ensure negative cell cycle duration triggers 422 Unprocessable Entity."""
    payload = {
        "cell_id": sample_cell.id,
        "experimental_batch": "BATCH-01",
        "replicate": 1,
        "experimental_condition": "Control",
        "medium": "Standard",
        "temperature_celsius": 30.0,
        "generation": 1,
        "division_start_time": "2024-03-01T10:00:00Z",
        "division_end_time": "2024-03-01T10:30:00Z",
        "cell_cycle_duration_hours": -2.5,  # Invalid!
    }
    response = client.post("/api/v1/divisions", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "VALIDATION_ERROR" in data.get("code", "")


def test_validation_end_before_start_timestamp(client: TestClient, sample_cell):
    """Ensure reversed division timestamps trigger 422 validation failure."""
    payload = {
        "cell_id": sample_cell.id,
        "experimental_batch": "BATCH-01",
        "replicate": 1,
        "experimental_condition": "Control",
        "medium": "Standard",
        "temperature_celsius": 30.0,
        "generation": 1,
        "division_start_time": "2024-03-01T10:30:00Z",
        "division_end_time": "2024-03-01T10:00:00Z",  # 30 min before start!
        "cell_cycle_duration_hours": 2.0,
    }
    response = client.post("/api/v1/divisions", json=payload)
    assert response.status_code == 422


def test_validation_extreme_temperature(client: TestClient, sample_cell):
    """Ensure impossible incubation temperatures trigger 422 validation."""
    payload = {
        "cell_id": sample_cell.id,
        "experimental_batch": "BATCH-01",
        "replicate": 1,
        "experimental_condition": "Control",
        "medium": "Standard",
        "temperature_celsius": 250.0,  # Far above biological threshold
        "generation": 1,
        "division_start_time": "2024-03-01T10:00:00Z",
        "division_end_time": "2024-03-01T10:30:00Z",
        "cell_cycle_duration_hours": 2.0,
    }
    response = client.post("/api/v1/divisions", json=payload)
    assert response.status_code == 422


def test_validation_empty_cell_fields(client: TestClient):
    """Ensure whitespace/empty cell creation payload fails with 422."""
    payload = {
        "id": "   ",  # Invalid empty ID
        "name": "",
        "organism": "Yeast",
        "cell_type": "Budding",
    }
    response = client.post("/api/v1/cells", json=payload)
    assert response.status_code == 422
