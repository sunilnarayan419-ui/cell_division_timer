"""Tests for API versioning middleware, header-based routing, and v2-beta endpoints."""

import pytest
from fastapi.testclient import TestClient


def test_root_endpoint_versioning_metadata(client: TestClient) -> None:
    """Verify root endpoint exposes v1 and v2-beta version directories."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "versions" in data
    assert "v1" in data["versions"]
    assert "v2-beta" in data["versions"]
    assert data["versions"]["v1"]["status"] == "stable"
    assert data["versions"]["v2-beta"]["status"] == "beta"
    assert "versioning" in data
    assert data["versioning"]["default_version"] == "v1"


def test_v1_path_headers(client: TestClient) -> None:
    """Verify /api/v1 endpoints return stable lifecycle headers."""
    response = client.get("/api/v1/divisions")
    assert response.status_code == 200
    assert response.headers.get("x-api-version") == "v1"
    assert response.headers.get("x-api-lifecycle") == "stable"
    assert "X-API-Version" in response.headers.get("vary", "")


def test_v2_path_headers(client: TestClient) -> None:
    """Verify /api/v2 endpoints return beta lifecycle headers and warning."""
    response = client.get("/api/v2/beta/status")
    assert response.status_code == 200
    assert response.headers.get("x-api-version") == "v2-beta"
    assert response.headers.get("x-api-lifecycle") == "beta"
    assert "v2-beta is an active preview" in response.headers.get("x-api-warning", "")

    data = response.json()
    assert data["status"] == "beta"
    assert "version" in data
    assert len(data["features"]) > 0


def test_unversioned_path_defaults_to_v1(client: TestClient) -> None:
    """Verify unversioned /api/divisions routes transparently to v1 when header is absent."""
    response = client.get("/api/divisions")
    assert response.status_code == 200
    assert response.headers.get("x-api-version") == "v1"
    assert response.headers.get("x-api-lifecycle") == "stable"


def test_unversioned_path_header_routing_to_v2(client: TestClient) -> None:
    """Verify unversioned /api/divisions routes to v2 when X-API-Version: 2 is supplied."""
    response = client.get("/api/divisions", headers={"X-API-Version": "2"})
    assert response.status_code == 200
    assert response.headers.get("x-api-version") == "v2-beta"
    assert response.headers.get("x-api-lifecycle") == "beta"

    # Verify v2 subphase fields exist in items
    data = response.json()
    assert "items" in data
    if len(data["items"]) > 0:
        first_item = data["items"][0]
        assert "mitotic_subphases" in first_item
        assert "checkpoint_delay_index" in first_item
        assert "arrest_probability_score" in first_item


def test_unversioned_path_vendor_mime_routing_to_v2(client: TestClient) -> None:
    """Verify content-negotiated vendor MIME routes to v2."""
    response = client.get(
        "/api/divisions",
        headers={"Accept": "application/vnd.celldivision.v2+json"},
    )
    assert response.status_code == 200
    assert response.headers.get("x-api-version") == "v2-beta"
    assert response.headers.get("x-api-lifecycle") == "beta"


def test_unsupported_api_version_rejection(client: TestClient) -> None:
    """Verify requesting an unsupported API version returns 400 Bad Request."""
    response = client.get("/api/divisions", headers={"X-API-Version": "99"})
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "UNSUPPORTED_API_VERSION"
    assert "99" in data["detail"]
    assert "v1" in data["supported_versions"]
    assert "v2-beta" in data["supported_versions"]


def test_v2_batch_analyze_endpoint(client: TestClient) -> None:
    """Verify v2 beta batch kinetic analysis capability."""
    payload = {
        "batch_name": "BATCH-TEST-V2",
        "observations": [
            {
                "cell_id": "CELL-SC-001",
                "temperature_celsius": 30.0,
                "division_duration_minutes": 25.0,
                "cell_cycle_duration_hours": 2.0,
                "experimental_condition": "Control",
            },
            {
                "cell_id": "CELL-SC-001",
                "temperature_celsius": 35.0,
                "division_duration_minutes": 30.0,
                "cell_cycle_duration_hours": 1.7,
                "experimental_condition": "Thermal Shift",
            },
        ],
    }

    response = client.post("/api/v2/divisions/batch-analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["batch_name"] == "BATCH-TEST-V2"
    assert data["total_processed"] == 2
    assert data["mean_division_minutes"] == 27.5
    assert data["arrhenius_q10_estimate"] is not None
    assert data["arrhenius_q10_estimate"] > 0


def test_v2_predictive_thermal_kinetics(client: TestClient) -> None:
    """Verify v2 Arrhenius Q10 temperature modeling."""
    response = client.get(
        "/api/v2/analytics/predictive-kinetics?ref_temp=30.0&elevated_temp=35.0"
    )
    assert response.status_code == 200
    data = response.json()
    assert "q10_temperature_coefficient" in data
    assert "activation_energy_kj_mol" in data
    assert "biological_interpretation" in data
    assert data["q10_temperature_coefficient"] > 0


def test_v2_mitotic_phase_distribution(client: TestClient) -> None:
    """Verify v2 mitotic subphase population distribution endpoint."""
    response = client.get("/api/v2/analytics/mitotic-phases")
    assert response.status_code == 200
    data = response.json()
    assert "mean_prophase_minutes" in data
    assert "mean_metaphase_minutes" in data
    assert "mean_anaphase_minutes" in data
    assert "mean_telophase_minutes" in data
    assert "mean_total_mitosis_minutes" in data
