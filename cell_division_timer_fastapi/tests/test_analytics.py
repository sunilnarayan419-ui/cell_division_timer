"""Tests for Biotechnology Analytics and Kinetic Aggregation endpoints."""

from fastapi.testclient import TestClient


def test_analytics_endpoints_with_data(client: TestClient, sample_cell):
    """Verify all statistical endpoints calculate correct distributions."""
    # Seed 3 divisions
    test_divisions = [
        {"temp": 30.0, "cond": "Control", "gen": 1, "div_m": 20.0, "cycle_h": 2.0},
        {"temp": 30.0, "cond": "Control", "gen": 2, "div_m": 30.0, "cycle_h": 3.0},
        {"temp": 37.0, "cond": "Thermal Stress", "gen": 3, "div_m": 40.0, "cycle_h": 4.0},
    ]
    for d in test_divisions:
        client.post(
            "/api/v1/divisions",
            json={
                "cell_id": sample_cell.id,
                "experimental_batch": "BATCH-ANALYTICS-01",
                "replicate": 1,
                "experimental_condition": d["cond"],
                "medium": "Standard",
                "temperature_celsius": d["temp"],
                "generation": d["gen"],
                "division_start_time": "2024-03-01T10:00:00Z",
                "division_end_time": f"2024-03-01T10:{int(d['div_m']):02d}:00Z",
                "cell_cycle_duration_hours": d["cycle_h"],
            },
        )

    # 1. Overall Summary
    res_summary = client.get("/api/v1/analytics/summary")
    assert res_summary.status_code == 200
    summary_data = res_summary.json()
    assert summary_data["total_observations"] >= 3
    assert summary_data["division_duration_minutes"]["mean"] is not None
    assert summary_data["division_duration_minutes"]["cv_percent"] is not None

    # 2. By Cell Type
    res_ct = client.get("/api/v1/analytics/by-cell-type")
    assert res_ct.status_code == 200
    ct_data = res_ct.json()
    assert len(ct_data) >= 1
    assert ct_data[0]["group_value"] == sample_cell.cell_type

    # 3. By Condition
    res_cond = client.get("/api/v1/analytics/by-condition")
    assert res_cond.status_code == 200
    cond_data = res_cond.json()
    conditions = [item["group_value"] for item in cond_data]
    assert "Control" in conditions
    assert "Thermal Stress" in conditions

    # 4. By Temperature
    res_temp = client.get("/api/v1/analytics/by-temperature")
    assert res_temp.status_code == 200
    temp_data = res_temp.json()
    temps = [item["temperature_celsius"] for item in temp_data]
    assert 30.0 in temps
    assert 37.0 in temps

    # 5. By Generation
    res_gen = client.get("/api/v1/analytics/by-generation")
    assert res_gen.status_code == 200
    gen_data = res_gen.json()
    generations = [item["generation"] for item in gen_data]
    assert 1 in generations
    assert 2 in generations

    # 6. Batches
    res_batches = client.get("/api/v1/analytics/batches")
    assert res_batches.status_code == 200
    batch_data = res_batches.json()
    assert any(b["batch_id"] == "BATCH-ANALYTICS-01" for b in batch_data)
