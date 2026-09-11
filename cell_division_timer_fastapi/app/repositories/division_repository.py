"""Cell Division Records repository for querying and analytics data-access."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload
from app.models.cell import Cell
from app.models.division import CellDivisionRecord
from app.repositories.base import BaseRepository


class DivisionRepository(BaseRepository[CellDivisionRecord]):
    """Data-access layer for CellDivisionRecord entities."""

    def __init__(self, db: Session) -> None:
        super().__init__(CellDivisionRecord, db)

    def get_by_id_with_cell(self, division_id: int) -> Optional[CellDivisionRecord]:
        """Fetch division record with eager-loaded Cell relationship."""
        stmt = (
            select(CellDivisionRecord)
            .options(joinedload(CellDivisionRecord.cell))
            .where(CellDivisionRecord.id == division_id)
        )
        return self.db.execute(stmt).scalars().first()

    def get_with_filters(
        self,
        offset: int = 0,
        limit: int = 20,
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
    ) -> Tuple[List[CellDivisionRecord], int]:
        """Fetch division records matching composite filters, with pagination and sorting."""
        stmt = select(CellDivisionRecord).join(CellDivisionRecord.cell).options(
            joinedload(CellDivisionRecord.cell)
        )
        count_stmt = select(func.count(CellDivisionRecord.id)).join(CellDivisionRecord.cell)

        filters = []
        if cell_id:
            filters.append(CellDivisionRecord.cell_id == cell_id)
        if organism:
            filters.append(Cell.organism.ilike(f"%{organism}%"))
        if cell_type:
            filters.append(Cell.cell_type.ilike(f"%{cell_type}%"))
        if batch:
            filters.append(CellDivisionRecord.experimental_batch == batch)
        if replicate is not None:
            filters.append(CellDivisionRecord.replicate == replicate)
        if condition:
            filters.append(CellDivisionRecord.experimental_condition.ilike(f"%{condition}%"))
        if min_temp is not None:
            filters.append(CellDivisionRecord.temperature_celsius >= min_temp)
        if max_temp is not None:
            filters.append(CellDivisionRecord.temperature_celsius <= max_temp)
        if generation is not None:
            filters.append(CellDivisionRecord.generation == generation)
        if is_outlier is not None:
            filters.append(CellDivisionRecord.is_outlier == is_outlier)
        if start_date is not None:
            filters.append(CellDivisionRecord.division_start_time >= start_date)
        if end_date is not None:
            filters.append(CellDivisionRecord.division_end_time <= end_date)

        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        total = self.db.execute(count_stmt).scalar_one()

        # Sorting
        sort_column_map = {
            "id": CellDivisionRecord.id,
            "division_start_time": CellDivisionRecord.division_start_time,
            "division_end_time": CellDivisionRecord.division_end_time,
            "division_duration_minutes": CellDivisionRecord.division_duration_minutes,
            "cell_cycle_duration_hours": CellDivisionRecord.cell_cycle_duration_hours,
            "growth_rate": CellDivisionRecord.growth_rate,
            "generation": CellDivisionRecord.generation,
            "temperature_celsius": CellDivisionRecord.temperature_celsius,
            "replicate": CellDivisionRecord.replicate,
        }

        col = sort_column_map.get(sort_by, CellDivisionRecord.division_start_time)
        stmt = stmt.order_by(desc(col) if sort_order.lower() == "desc" else col)

        stmt = stmt.offset(offset).limit(limit)
        results = self.db.execute(stmt).scalars().all()
        return list(results), total

    def get_all_records_with_cell(self) -> List[CellDivisionRecord]:
        """Fetch all records joined with their cell model for analytics or CSV export."""
        stmt = (
            select(CellDivisionRecord)
            .options(joinedload(CellDivisionRecord.cell))
            .order_by(CellDivisionRecord.id)
        )
        return list(self.db.execute(stmt).scalars().all())

    def bulk_create(self, records: List[CellDivisionRecord]) -> List[CellDivisionRecord]:
        """Bulk insert multiple division records inside a single transaction."""
        self.db.add_all(records)
        self.db.commit()
        return records
