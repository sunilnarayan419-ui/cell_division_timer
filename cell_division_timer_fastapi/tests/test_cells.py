"""Tests for Cell sample management REST endpoints."""

from fastapi.testclient import TestClient


def test_create_cell_success(client: TestClient):
    """Test successful cell registration."""
    payload = {
        "id": "CELL-NEW-01",
        "name": "E. coli MG1655",
        "organism": "Escherichia coli",
        "cell_type": "Rod bacterium",
        "passage_number": 2,
        "source_line": "ATCC 47076",
        "description": "Standard bacterial test sample",
    }
    response = client.post("/api/v1/cells", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "CELL-NEW-01"
    assert data["name"] == "E. coli MG1655"
    assert data["division_count"] == 0


def test_create_duplicate_cell_conflict(client: TestClient, sample_cell):
    """Test registering a cell with existing ID returns 409 Conflict."""
    payload = {
        "id": sample_cell.id,
        "name": "Duplicate Cell",
        "organism": "Test Organism",
        "cell_type": "Test Type",
    }
    response = client.post("/api/v1/cells", json=payload)
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_get_cell_by_id(client: TestClient, sample_cell):
    """Test retrieving existing cell."""
    response = client.get(f"/api/v1/cells/{sample_cell.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_cell.id
    assert data["name"] == sample_cell.name


def test_get_nonexistent_cell(client: TestClient):
    """Test fetching nonexistent cell returns 404."""
    response = client.get("/api/v1/cells/NONEXISTENT-999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_update_cell(client: TestClient, sample_cell):
    """Test modifying cell metadata."""
    update_payload = {"name": "Updated Yeast Name", "passage_number": 5}
    response = client.put(f"/api/v1/cells/{sample_cell.id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Yeast Name"
    assert data["passage_number"] == 5


def test_delete_cell(client: TestClient, sample_cell):
    """Test deleting cell sample."""
    response = client.delete(f"/api/v1/cells/{sample_cell.id}")
    assert response.status_code == 204

    # Verify deletion
    get_res = client.get(f"/api/v1/cells/{sample_cell.id}")
    assert get_res.status_code == 404


def test_list_cells_pagination_and_filtering(client: TestClient):
    """Test paginated and filtered listing of cell samples."""
    # Seed 3 cells
    cells = [
        {"id": "CELL-A", "name": "Line A", "organism": "Yeast Alpha", "cell_type": "Budding"},
        {"id": "CELL-B", "name": "Line B", "organism": "Bacteria Beta", "cell_type": "Rod"},
        {"id": "CELL-C", "name": "Line C", "organism": "Yeast Gamma", "cell_type": "Fission"},
    ]
    for c in cells:
        client.post("/api/v1/cells", json=c)

    # Filter by organism "Yeast"
    res = client.get("/api/v1/cells?organism=Yeast&page=1&page_size=10")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 2
    assert all("Yeast" in item["organism"] for item in data["items"])
