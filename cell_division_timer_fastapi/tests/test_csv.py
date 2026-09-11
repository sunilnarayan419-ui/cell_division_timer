"""Tests for CSV import and export endpoints."""

import io
from fastapi.testclient import TestClient


def test_csv_export_and_import(client: TestClient, sample_cell):
    """Test full cycle of exporting to CSV and re-importing."""
    # 1. Create a division record
    client.post(
        "/api/v1/divisions",
        json={
            "cell_id": sample_cell.id,
            "experimental_batch": "BATCH-CSV-1",
            "replicate": 1,
            "experimental_condition": "Standard",
            "medium": "Broth",
            "temperature_celsius": 30.0,
            "generation": 1,
            "division_start_time": "2024-03-01T10:00:00Z",
            "division_end_time": "2024-03-01T10:25:00Z",
            "cell_cycle_duration_hours": 2.2,
        },
    )

    # 2. Export CSV
    export_res = client.get("/api/v1/data/export/csv")
    assert export_res.status_code == 200
    assert "text/csv" in export_res.headers["content-type"]
    csv_text = export_res.text
    assert "record_id" in csv_text
    assert sample_cell.id in csv_text

    # 3. Import CSV with a brand new cell
    new_csv_content = (
        "cell_id,organism,cell_type,experimental_batch,replicate,experimental_condition,medium,"
        "temperature_celsius,generation,division_start_time,division_end_time,cell_cycle_duration_hours,notes\n"
        "CELL-AUTO-01,Test Auto Organism,Auto Type,BATCH-IMP-01,1,Nutrient Test,Agar,37.0,1,"
        "2024-03-01T12:00:00Z,2024-03-01T12:30:00Z,1.5,Imported via CSV test\n"
    )

    file_tuple = ("dataset.csv", io.BytesIO(new_csv_content.encode("utf-8")), "text/csv")
    import_res = client.post("/api/v1/data/import/csv", files={"file": file_tuple})
    assert import_res.status_code == 200
    import_data = import_res.json()
    assert import_data["success"] is True
    assert import_data["imported_count"] == 1
    assert import_data["errors_count"] == 0

    # Verify auto-created cell exists
    cell_res = client.get("/api/v1/cells/CELL-AUTO-01")
    assert cell_res.status_code == 200
    assert cell_res.json()["name"] == "Auto-imported CELL-AUTO-01"
