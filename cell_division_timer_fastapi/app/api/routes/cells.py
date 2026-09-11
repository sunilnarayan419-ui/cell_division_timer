"""Cell / Biological Sample management endpoints."""

from typing import Optional
from fastapi import APIRouter, Query, Response, status
from app.api.deps import CellServiceDep
from app.schemas.cell import CellCreate, CellResponse, CellUpdate
from app.schemas.common import ErrorResponse
from app.utils.pagination import PaginatedResponse, PaginationParams

router = APIRouter()


@router.post(
    "",
    response_model=CellResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a Biological Cell Sample",
    responses={
        400: {"model": ErrorResponse, "description": "Validation failure"},
        409: {"model": ErrorResponse, "description": "Sample ID already exists"},
    },
)
def create_cell(
    payload: CellCreate,
    service: CellServiceDep,
) -> CellResponse:
    """Register a new biological sample or cell line."""
    return service.create_cell(payload)


@router.get(
    "",
    response_model=PaginatedResponse[CellResponse],
    summary="List Biological Cell Samples",
    description="Retrieve paginated list of cell lines with optional filtering by organism or morphology.",
)
def list_cells(
    service: CellServiceDep,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    organism: Optional[str] = Query(None, description="Filter by organism (case-insensitive substring)"),
    cell_type: Optional[str] = Query(None, description="Filter by cell type"),
    search: Optional[str] = Query(None, description="Search across ID, name, organism, or cell type"),
) -> PaginatedResponse[CellResponse]:
    """List cell samples with pagination and filtering."""
    pagination = PaginationParams(page=page, page_size=page_size)
    return service.list_cells(
        pagination=pagination,
        organism=organism,
        cell_type=cell_type,
        search=search,
    )


@router.get(
    "/{cell_id}",
    response_model=CellResponse,
    summary="Retrieve Cell Sample by ID",
    responses={404: {"model": ErrorResponse, "description": "Cell not found"}},
)
def get_cell(
    cell_id: str,
    service: CellServiceDep,
) -> CellResponse:
    """Retrieve metadata and division count for a specific cell sample."""
    return service.get_cell_response(cell_id)


@router.put(
    "/{cell_id}",
    response_model=CellResponse,
    summary="Update Cell Sample Metadata",
    responses={404: {"model": ErrorResponse, "description": "Cell not found"}},
)
def update_cell(
    cell_id: str,
    payload: CellUpdate,
    service: CellServiceDep,
) -> CellResponse:
    """Update metadata for an existing cell sample."""
    return service.update_cell(cell_id, payload)


@router.delete(
    "/{cell_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Cell Sample",
    description="Deletes cell sample and all associated division observation records via database cascade.",
    responses={404: {"model": ErrorResponse, "description": "Cell not found"}},
)
def delete_cell(
    cell_id: str,
    service: CellServiceDep,
) -> Response:
    """Delete a cell sample."""
    service.delete_cell(cell_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
