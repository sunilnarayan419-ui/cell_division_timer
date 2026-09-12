"""Service layer for Cell Division Records and biological calculations."""

from datetime import datetime
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.division import CellDivisionRecord
from app.repositories.cell_repository import CellRepository
from app.repositories.division_repository import DivisionRepository
from app.schemas.division import (
    CellDivisionCreate,
    CellDivisionResponse,
    CellDivisionUpdate,
)
from app.utils.biology import (
    calculate_division_duration_minutes,
    calculate_specific_growth_rate,
    evaluate_biological_metrics,
)
from app.utils.pagination import PaginatedResponse, PaginationParams


class DivisionService:
    """Business logic for Cell Division observation events."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = DivisionRepository(db)
        self.cell_repo = CellRepository(db)

    def _format_response(self, record: CellDivisionRecord) -> CellDivisionResponse:
        """Helper to serialize model to response with cell biological context."""
        resp = CellDivisionResponse.model_validate(record)
        if record.cell:
            resp.organism = record.cell.organism
            resp.cell_type = record.cell.cell_type
        # Always surface the raw calculated values alongside the official
        # stored ones, so a caller can see whether/how far an active
        # override deviates from what the source measurements imply.
        resp.calculated_duration_minutes = calculate_division_duration_minutes(
            record.division_start_time, record.division_end_time
        )
        resp.calculated_growth_rate = calculate_specific_growth_rate(
            record.cell_cycle_duration_hours
        )
        return resp

    def get_division(self, division_id: int) -> CellDivisionRecord:
        """Retrieve a division observation record by ID.

        Raises:
            HTTPException: 404 if record not found.
        """
        record = self.repo.get_by_id_with_cell(division_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cell division record #{division_id} was not found",
            )
        return record

    def get_division_response(self, division_id: int) -> CellDivisionResponse:
        """Retrieve division record serialized as response."""
        record = self.get_division(division_id)
        return self._format_response(record)

    def list_divisions(
        self,
        pagination: PaginationParams,
        cell_id: Optional[str] = None,
        organism: Optional[str] = None,
        cell_type: Optional[str] = None,
        batch: Optional[str] = None,
        replicate: Optional[int] = None,
        condition: Optional[str] = None,
        min_temp: Optional[float] = None,
        max_temp: Optional[float] = None,
        generation: Optional[int] = None,
        is_outlier: Optional[bool] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sort_by: str = "division_start_time",
        sort_order: str = "desc",
    ) -> PaginatedResponse[CellDivisionResponse]:
        """List and filter cell division records."""
        records, total = self.repo.get_with_filters(
            offset=pagination.offset,
            limit=pagination.limit,
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

        items = [self._format_response(r) for r in records]
        return PaginatedResponse.create(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    def create_division(self, data: CellDivisionCreate) -> CellDivisionResponse:
        """Create a new division record with biological validation and automated kinetics calculations."""
        # 1. Verify cell parent entity exists
        cell = self.cell_repo.get_by_id(data.cell_id)
        if not cell:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent cell sample with ID '{data.cell_id}' does not exist",
            )

        # 2. Duration is always calculated from the source timestamps unless an
        #    explicit, reason-documented override is supplied (schema validation
        #    guarantees duration_override_minutes and duration_override_reason
        #    are either both present or both absent).
        div_duration = calculate_division_duration_minutes(
            data.division_start_time, data.division_end_time
        )
        if data.duration_override_minutes is not None:
            div_duration = data.duration_override_minutes

        # 3. Same pattern for specific growth rate.
        growth_rate = calculate_specific_growth_rate(data.cell_cycle_duration_hours)
        if data.growth_rate_override is not None:
            growth_rate = data.growth_rate_override

        # 4. Biological plausibility and outlier detection
        is_outlier, quality_flag = evaluate_biological_metrics(
            organism=cell.organism,
            division_duration_minutes=div_duration,
            cell_cycle_duration_hours=data.cell_cycle_duration_hours,
            temperature_celsius=data.temperature_celsius,
        )

        record = CellDivisionRecord(
            cell_id=data.cell_id,
            experimental_batch=data.experimental_batch,
            replicate=data.replicate,
            experimental_condition=data.experimental_condition,
            medium=data.medium,
            temperature_celsius=data.temperature_celsius,
            generation=data.generation,
            division_start_time=data.division_start_time,
            division_end_time=data.division_end_time,
            division_duration_minutes=div_duration,
            cell_cycle_duration_hours=data.cell_cycle_duration_hours,
            growth_rate=growth_rate,
            duration_override_minutes=data.duration_override_minutes,
            duration_override_reason=data.duration_override_reason,
            growth_rate_override=data.growth_rate_override,
            growth_rate_override_reason=data.growth_rate_override_reason,
            is_outlier=is_outlier,
            quality_flag=quality_flag,
            notes=data.notes,
            metadata_json=data.metadata_json,
        )

        created = self.repo.create(record)
        return self._format_response(created)

    def update_division(self, division_id: int, data: CellDivisionUpdate) -> CellDivisionResponse:
        """Update an existing division record and recompute affected biological metrics.

        Validation and derived-value recomputation are always performed against
        the FINAL MERGED record (existing DB values overlaid with the incoming
        partial update), never against the incoming fields in isolation. This
        prevents a PATCH that only supplies one of `division_start_time` /
        `division_end_time` from silently producing an internally-inconsistent
        record (e.g. an end time that ends up before the new start time).
        """
        record = self.get_division(division_id)
        update_dict = data.model_dump(exclude_unset=True)

        # 1. Compute the effective (post-merge) values for every field that
        #    participates in cross-field validation or a derived calculation,
        #    BEFORE mutating the record.
        effective_start_time = update_dict.get("division_start_time", record.division_start_time)
        effective_end_time = update_dict.get("division_end_time", record.division_end_time)
        effective_cycle_hours = update_dict.get(
            "cell_cycle_duration_hours", record.cell_cycle_duration_hours
        )
        effective_duration_override = update_dict.get(
            "duration_override_minutes", record.duration_override_minutes
        )
        effective_growth_override = update_dict.get(
            "growth_rate_override", record.growth_rate_override
        )

        # 2. Validate the FINAL merged state before touching the record.
        if effective_end_time < effective_start_time:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Resulting division_end_time "
                    f"({effective_end_time}) would precede division_start_time "
                    f"({effective_start_time}) after applying this update."
                ),
            )

        # 3. Apply raw (non-derived) fields to the record.
        for field, value in update_dict.items():
            setattr(record, field, value)

        # 4. Recompute derived values from the effective merged state. This
        #    always uses calculate_*() as the source of truth, only falling
        #    back to an explicit override when one is in effect after the
        #    merge (existing or newly supplied in this request).
        needs_duration_recalc = (
            "division_start_time" in update_dict
            or "division_end_time" in update_dict
            or "duration_override_minutes" in update_dict
        )
        if needs_duration_recalc:
            calculated_duration = calculate_division_duration_minutes(
                effective_start_time, effective_end_time
            )
            record.division_duration_minutes = (
                effective_duration_override
                if effective_duration_override is not None
                else calculated_duration
            )

        needs_growth_recalc = (
            "cell_cycle_duration_hours" in update_dict or "growth_rate_override" in update_dict
        )
        if needs_growth_recalc:
            calculated_growth_rate = calculate_specific_growth_rate(effective_cycle_hours)
            record.growth_rate = (
                effective_growth_override
                if effective_growth_override is not None
                else calculated_growth_rate
            )

        # Re-evaluate biological thresholds if not manually overridden
        if "is_outlier" not in update_dict or "quality_flag" not in update_dict:
            organism = record.cell.organism if record.cell else None
            is_outlier, quality_flag = evaluate_biological_metrics(
                organism=organism,
                division_duration_minutes=record.division_duration_minutes,
                cell_cycle_duration_hours=record.cell_cycle_duration_hours,
                temperature_celsius=record.temperature_celsius,
            )
            if "is_outlier" not in update_dict:
                record.is_outlier = is_outlier
            if "quality_flag" not in update_dict:
                record.quality_flag = quality_flag

        updated = self.repo.update(record)
        return self._format_response(updated)

    def delete_division(self, division_id: int) -> None:
        """Delete an existing division observation record."""
        record = self.get_division(division_id)
        self.repo.delete(record)
