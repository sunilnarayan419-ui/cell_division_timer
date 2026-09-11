"""Service layer for Cell/Sample business operations."""

from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.cell import Cell
from app.repositories.cell_repository import CellRepository
from app.schemas.cell import CellCreate, CellResponse, CellUpdate
from app.utils.pagination import PaginatedResponse, PaginationParams


class CellService:
    """Business logic for Cell lines and samples."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CellRepository(db)

    def get_cell(self, cell_id: str) -> Cell:
        """Retrieve a cell sample by its unique ID.

        Raises:
            HTTPException: 404 if cell does not exist.
        """
        cell = self.repo.get_by_id(cell_id)
        if not cell:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cell sample with ID '{cell_id}' was not found",
            )
        return cell

    def get_cell_response(self, cell_id: str) -> CellResponse:
        """Retrieve a cell and attach its division count."""
        cell = self.get_cell(cell_id)
        count = self.repo.get_division_count(cell_id)
        resp = CellResponse.model_validate(cell)
        resp.division_count = count
        return resp

    def list_cells(
        self,
        pagination: PaginationParams,
        organism: Optional[str] = None,
        cell_type: Optional[str] = None,
        search: Optional[str] = None,
    ) -> PaginatedResponse[CellResponse]:
        """List cells with optional filtering and pagination."""
        rows, total = self.repo.get_with_filters(
            offset=pagination.offset,
            limit=pagination.limit,
            organism=organism,
            cell_type=cell_type,
            search=search,
        )

        items = []
        for cell, count in rows:
            c_resp = CellResponse.model_validate(cell)
            c_resp.division_count = count
            items.append(c_resp)

        return PaginatedResponse.create(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    def create_cell(self, data: CellCreate) -> CellResponse:
        """Register a new cell line or sample.

        Raises:
            HTTPException: 409 if a cell with this ID already exists.
        """
        if self.repo.exists(data.id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A cell sample with ID '{data.id}' already exists",
            )

        cell = Cell(
            id=data.id,
            name=data.name,
            organism=data.organism,
            cell_type=data.cell_type,
            passage_number=data.passage_number,
            source_line=data.source_line,
            description=data.description,
        )
        created = self.repo.create(cell)
        resp = CellResponse.model_validate(created)
        resp.division_count = 0
        return resp

    def update_cell(self, cell_id: str, data: CellUpdate) -> CellResponse:
        """Update metadata for an existing cell sample."""
        cell = self.get_cell(cell_id)

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(cell, key, value)

        updated = self.repo.update(cell)
        count = self.repo.get_division_count(cell_id)
        resp = CellResponse.model_validate(updated)
        resp.division_count = count
        return resp

    def delete_cell(self, cell_id: str) -> None:
        """Delete an existing cell sample and its cascaded observations."""
        cell = self.get_cell(cell_id)
        self.repo.delete(cell)
