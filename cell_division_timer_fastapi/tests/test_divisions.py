"""Tests for Cell Division Records CRUD, filters, and biological kinetics."""

from datetime import datetime, timezone
from fastapi.testclient import TestClient


def test_create_division_automated_metrics(client: TestClient, sample_cell):
    """Test creating a division record with automated duration and growth rate calculation."""
    payload = {
        "cell_id": sample_cell.id,
        "experimental_batch": "BATCH-TEST-01",
        "replicate": 1,
        "experimental_condition": "Control",
        "medium": "YPD Broth",
        "temperature_celsius": 30.0,
        "generation": 1,
        "division_start_time": "2024-03-01T10:00:00Z",
        "division_end_time": "2024-03-01T10:30:00Z",  # 30 minutes duration
        "cell_cycle_duration_hours": 2.0,  # growth rate = ln(2)/2.0 = ~0.3466
        "notes": "Healthy division",
    }

    response = client.post("/api/v1/divisions", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["id"] is not None
    assert data["division_duration_minutes"] == 30.0
    assert abs(data["growth_rate"] - 0.3466) < 0.001
    assert data["is_outlier"] is False
    assert data["quality_flag"] == "PASS"
    assert data["organism"] == sample_cell.organism


def test_create_division_nonexistent_cell_fails(client: TestClient):
    """Test creating division with nonexistent parent cell returns 404."""
    payload = {
        "cell_id": "CELL-DOES-NOT-EXIST",
        "experimental_batch": "BATCH-01",
        "replicate": 1,
        "experimental_condition": "Control",
        "medium": "Standard",
        "temperature_celsius": 37.0,
        "generation": 1,
        "division_start_time": "2024-03-01T10:00:00Z",
        "division_end_time": "2024-03-01T10:30:00Z",
        "cell_cycle_duration_hours": 1.0,
    }
    response = client.post("/api/v1/divisions", json=payload)
    assert response.status_code == 404
    assert "does not exist" in response.json()["detail"]


def test_get_and_update_division(client: TestClient, sample_cell):
    """Test retrieving and modifying a division record."""
    create_res = client.post(
        "/api/v1/divisions",
        json={
            "cell_id": sample_cell.id,
            "experimental_batch": "BATCH-02",
            "replicate": 1,
            "experimental_condition": "Nutrient Shock",
            "medium": "Minimal Media",
            "temperature_celsius": 30.0,
            "generation": 2,
            "division_start_time": "2024-03-01T12:00:00Z",
            "division_end_time": "2024-03-01T12:25:00Z",
            "cell_cycle_duration_hours": 3.0,
        },
    )
    div_id = create_res.json()["id"]

    # Retrieve
    get_res = client.get(f"/api/v1/divisions/{div_id}")
    assert get_res.status_code == 200
    assert get_res.json()["experimental_condition"] == "Nutrient Shock"

    # Update
    update_res = client.put(
        f"/api/v1/divisions/{div_id}",
        json={"notes": "Updated note", "cell_cycle_duration_hours": 4.0},
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["notes"] == "Updated note"
    # Growth rate should be recomputed: ln(2)/4.0 = ~0.1733
    assert abs(updated_data["growth_rate"] - 0.1733) < 0.001


def test_delete_division(client: TestClient, sample_cell):
    """Test deleting division record."""
    create_res = client.post(
        "/api/v1/divisions",
        json={
            "cell_id": sample_cell.id,
            "experimental_batch": "BATCH-DEL",
            "replicate": 1,
            "experimental_condition": "Control",
            "medium": "Standard",
            "temperature_celsius": 30.0,
            "generation": 1,
            "division_start_time": "2024-03-01T08:00:00Z",
            "division_end_time": "2024-03-01T08:20:00Z",
            "cell_cycle_duration_hours": 2.0,
        },
    )
    div_id = create_res.json()["id"]

    del_res = client.delete(f"/api/v1/divisions/{div_id}")
    assert del_res.status_code == 204

    get_res = client.get(f"/api/v1/divisions/{div_id}")
    assert get_res.status_code == 404


def test_filtering_and_sorting(client: TestClient, sample_cell):
    """Test complex filtering (temperature, batch, condition) and sorting."""
    # Insert multiple records
    records = [
        ("BATCH-X", "Control", 30.0, 1, 25.0, 2.0),
        ("BATCH-X", "Heat Stress", 37.0, 2, 35.0, 2.8),
        ("BATCH-Y", "Control", 30.0, 3, 22.0, 1.8),
    ]
    for batch, cond, temp, gen, div_m, cyc_h in records:
        client.post(
            "/api/v1/divisions",
            json={
                "cell_id": sample_cell.id,
                "experimental_batch": batch,
                "replicate": 1,
                "experimental_condition": cond,
                "medium": "Standard",
                "temperature_celsius": temp,
                "generation": gen,
                "division_start_time": "2024-03-01T10:00:00Z",
                "division_end_time": f"2024-03-01T10:{int(div_m):02d}:00Z",
                "cell_cycle_duration_hours": cyc_h,
            },
        )

    # Filter by min_temp=35.0
    res = client.get("/api/v1/divisions?min_temp=35.0")
    assert res.status_code == 200
    data = res.json()
    assert all(r["temperature_celsius"] >= 35.0 for r in data["items"])

    # Filter by batch=BATCH-X and sort by generation desc
    res2 = client.get("/api/v1/divisions?batch=BATCH-X&sort_by=generation&sort_order=desc")
    assert res2.status_code == 200
    items2 = res2.json()["items"]
    assert len(items2) >= 2
    assert items2[0]["generation"] >= items2[1]["generation"]
