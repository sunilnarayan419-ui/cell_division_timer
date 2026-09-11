"""Cell Division Records REST API endpoints."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Query, Response, status
from app.api.deps import DivisionServiceDep
from app.schemas.common import ErrorResponse
from app.schemas.division import (
    CellDivisionCreate,
    CellDivisionResponse,
    CellDivisionUpdate,
)
from app.utils.pagination import PaginatedResponse, PaginationParams

router = APIRouter()


@router.post(
    "",
    response_model=CellDivisionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a Cell Division Event",
    description="Logs a division event. Automatically computes division duration, specific growth rate, and biological outlier flags.",
    responses={
        400: {"model": ErrorResponse, "description": "Validation failure"},
        404: {"model": ErrorResponse, "description": "Parent cell ID does not exist"},
    },
)
def create_division(
    payload: CellDivisionCreate,
    service: DivisionServiceDep,
) -> CellDivisionResponse:
    """Record a cell division event."""
    return service.create_division(payload)


@router.get(
    "",
    response_model=PaginatedResponse[CellDivisionResponse],
    summary="List and Filter Cell Division Records",
    description="Retrieve paginated division observations with multi-dimensional biological and experimental filters.",
)
def list_divisions(
    service: DivisionServiceDep,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Records per page"),
    cell_id: Optional[str] = Query(None, description="Filter by exact Cell ID"),
    organism: Optional[str] = Query(None, description="Filter by organism name"),
    cell_type: Optional[str] = Query(None, description="Filter by cell type"),
    batch: Optional[str] = Query(None, description="Filter by experimental batch"),
    replicate: Optional[int] = Query(None, ge=1, description="Filter by replicate number"),
    condition: Optional[str] = Query(None, description="Filter by experimental condition"),
    min_temp: Optional[float] = Query(None, description="Minimum incubation temperature (°C)"),
    max_temp: Optional[float] = Query(None, description="Maximum incubation temperature (°C)"),
    generation: Optional[int] = Query(None, ge=1, description="Filter by generation cycle number"),
    is_outlier: Optional[bool] = Query(None, description="Filter by biological outlier flag"),
    start_date: Optional[datetime] = Query(None, description="Filter divisions starting on or after timestamp"),
    end_date: Optional[datetime] = Query(None, description="Filter divisions ending on or before timestamp"),
    sort_by: str = Query("division_start_time", description="Sort field (division_start_time, division_duration_minutes, cell_cycle_duration_hours, growth_rate, generation, temperature_celsius)"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort direction ('asc' or 'desc')"),
) -> PaginatedResponse[CellDivisionResponse]:
    """List cell division records with pagination and filters."""
    pagination = PaginationParams(page=page, page_size=page_size)
    return service.list_divisions(
        pagination=pagination,
        cell_id=cell_id,
        organism=organism,
        cell_type=cell_type,
        batch=batch,
        replicate=replicate,
        condition=condition,
        min_temp=min_temp,
        max_temp=max_temp,
        generation=generation,
        is_outlier=is_outlier,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get(
    "/{division_id}",
    response_model=CellDivisionResponse,
    summary="Retrieve Division Record by ID",
    responses={404: {"model": ErrorResponse, "description": "Division record not found"}},
)
def get_division(
    division_id: int,
    service: DivisionServiceDep,
) -> CellDivisionResponse:
    """Retrieve a single division record with biological context."""
    return service.get_division_response(division_id)


@router.put(
    "/{division_id}",
    response_model=CellDivisionResponse,
    summary="Update Division Record",
    responses={404: {"model": ErrorResponse, "description": "Division record not found"}},
)
def update_division(
    division_id: int,
    payload: CellDivisionUpdate,
    service: DivisionServiceDep,
) -> CellDivisionResponse:
    """Update an existing division record and recompute kinetic parameters."""
    return service.update_division(division_id, payload)


@router.delete(
    "/{division_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Division Record",
    responses={404: {"model": ErrorResponse, "description": "Division record not found"}},
)
def delete_division(
    division_id: int,
    service: DivisionServiceDep,
) -> Response:
    """Delete a division record."""
    service.delete_division(division_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
