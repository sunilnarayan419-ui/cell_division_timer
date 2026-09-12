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


def test_create_division_rejects_mismatched_override_without_reason(client, sample_cell):
    """duration_override_minutes without duration_override_reason must be rejected."""
    payload = {
        "cell_id": sample_cell.id,
        "experimental_batch": "BATCH-OVR-01",
        "replicate": 1,
        "experimental_condition": "Control",
        "medium": "Standard",
        "temperature_celsius": 30.0,
        "generation": 1,
        "division_start_time": "2024-03-01T10:00:00Z",
        "division_end_time": "2024-03-01T10:30:00Z",
        "cell_cycle_duration_hours": 2.0,
        "duration_override_minutes": 100.0,  # no reason supplied -> invalid
    }
    response = client.post("/api/v1/divisions", json=payload)
    assert response.status_code == 422


def test_create_division_with_documented_duration_override(client, sample_cell):
    """A duration override with a documented reason is accepted and stored explicitly,
    while the calculated value (from the timestamps) remains visible and unchanged."""
    payload = {
        "cell_id": sample_cell.id,
        "experimental_batch": "BATCH-OVR-02",
        "replicate": 1,
        "experimental_condition": "Control",
        "medium": "Standard",
        "temperature_celsius": 30.0,
        "generation": 1,
        "division_start_time": "2024-03-01T10:00:00Z",
        "division_end_time": "2024-03-01T10:30:00Z",  # implies 30 minutes
        "cell_cycle_duration_hours": 2.0,
        "duration_override_minutes": 45.0,
        "duration_override_reason": "Manual correction for microscope stage-clock drift (+15 min).",
    }
    response = client.post("/api/v1/divisions", json=payload)
    assert response.status_code == 201
    data = response.json()

    # The official/stored value reflects the documented override...
    assert data["division_duration_minutes"] == 45.0
    assert data["duration_override_minutes"] == 45.0
    assert "clock drift" in data["duration_override_reason"]
    # ...but the raw calculation from the timestamps is still surfaced, so the
    # override is never silent.
    assert data["calculated_duration_minutes"] == 30.0


def test_create_division_without_override_matches_calculated(client, sample_cell):
    """Without an override, the stored value must exactly equal the calculated one."""
    payload = {
        "cell_id": sample_cell.id,
        "experimental_batch": "BATCH-OVR-03",
        "replicate": 1,
        "experimental_condition": "Control",
        "medium": "Standard",
        "temperature_celsius": 30.0,
        "generation": 1,
        "division_start_time": "2024-03-01T10:00:00Z",
        "division_end_time": "2024-03-01T10:30:00Z",
        "cell_cycle_duration_hours": 2.0,
    }
    response = client.post("/api/v1/divisions", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["division_duration_minutes"] == data["calculated_duration_minutes"] == 30.0
    assert data["growth_rate"] == data["calculated_growth_rate"]
    assert data["duration_override_minutes"] is None
    assert data["growth_rate_override"] is None


def test_update_partial_timestamp_rejects_invalid_merged_state(client, sample_cell):
    """Regression test: PATCHing only division_start_time to a value that would
    put it AFTER the existing division_end_time must be rejected (422), by
    validating the merged final record rather than the isolated PATCH fields.
    """
    create_res = client.post(
        "/api/v1/divisions",
        json={
            "cell_id": sample_cell.id,
            "experimental_batch": "BATCH-MERGE-01",
            "replicate": 1,
            "experimental_condition": "Control",
            "medium": "Standard",
            "temperature_celsius": 30.0,
            "generation": 1,
            "division_start_time": "2024-03-01T10:00:00Z",
            "division_end_time": "2024-03-01T10:30:00Z",
            "cell_cycle_duration_hours": 2.0,
        },
    )
    div_id = create_res.json()["id"]

    # Existing record: start=10:00, end=10:30. Only moving start to 11:00
    # (after the existing end) must fail rather than silently producing an
    # inverted record.
    update_res = client.put(
        f"/api/v1/divisions/{div_id}",
        json={"division_start_time": "2024-03-01T11:00:00Z"},
    )
    assert update_res.status_code == 422

    # The original record must be untouched by the rejected update.
    get_res = client.get(f"/api/v1/divisions/{div_id}")
    assert get_res.json()["division_duration_minutes"] == 30.0


def test_update_partial_end_time_rejects_invalid_merged_state(client, sample_cell):
    """Symmetric regression test: PATCHing only division_end_time earlier than
    the existing division_start_time must also be rejected."""
    create_res = client.post(
        "/api/v1/divisions",
        json={
            "cell_id": sample_cell.id,
            "experimental_batch": "BATCH-MERGE-02",
            "replicate": 1,
            "experimental_condition": "Control",
            "medium": "Standard",
            "temperature_celsius": 30.0,
            "generation": 1,
            "division_start_time": "2024-03-01T10:00:00Z",
            "division_end_time": "2024-03-01T10:30:00Z",
            "cell_cycle_duration_hours": 2.0,
        },
    )
    div_id = create_res.json()["id"]

    update_res = client.put(
        f"/api/v1/divisions/{div_id}",
        json={"division_end_time": "2024-03-01T09:00:00Z"},
    )
    assert update_res.status_code == 422


def test_update_valid_merged_timestamp_shift_recomputes_duration(client, sample_cell):
    """A valid partial update (shifting only start_time, still before the
    existing end_time) must succeed AND recompute the stored duration from
    the merged final state."""
    create_res = client.post(
        "/api/v1/divisions",
        json={
            "cell_id": sample_cell.id,
            "experimental_batch": "BATCH-MERGE-03",
            "replicate": 1,
            "experimental_condition": "Control",
            "medium": "Standard",
            "temperature_celsius": 30.0,
            "generation": 1,
            "division_start_time": "2024-03-01T10:00:00Z",
            "division_end_time": "2024-03-01T10:30:00Z",  # 30 min
            "cell_cycle_duration_hours": 2.0,
        },
    )
    div_id = create_res.json()["id"]

    update_res = client.put(
        f"/api/v1/divisions/{div_id}",
        json={"division_start_time": "2024-03-01T10:10:00Z"},  # now 20 min
    )
    assert update_res.status_code == 200
    assert update_res.json()["division_duration_minutes"] == 20.0
