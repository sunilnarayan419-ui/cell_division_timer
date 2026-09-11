"""Cell / Biological Sample repository for data persistence."""

from typing import List, Optional, Tuple
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.models.cell import Cell
from app.models.division import CellDivisionRecord
from app.repositories.base import BaseRepository


class CellRepository(BaseRepository[Cell]):
    """Data-access layer for Cell entities."""

    def __init__(self, db: Session) -> None:
        super().__init__(Cell, db)

    def exists(self, cell_id: str) -> bool:
        """Check if a cell record exists by ID."""
        stmt = select(func.count(Cell.id)).where(Cell.id == cell_id)
        return bool(self.db.execute(stmt).scalar_one() > 0)

    def get_with_filters(
        self,
        offset: int = 0,
        limit: int = 20,
        organism: Optional[str] = None,
        cell_type: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Tuple[Cell, int]], int]:
        """Fetch cells with optional filtering and division counts, plus total count."""
        # Subquery for division counts
        div_count_subq = (
            select(
                CellDivisionRecord.cell_id,
                func.count(CellDivisionRecord.id).label("division_count"),
            )
            .group_by(CellDivisionRecord.cell_id)
            .subquery()
        )

        base_query = (
            select(
                Cell,
                func.coalesce(div_count_subq.c.division_count, 0).label("division_count"),
            )
            .outerjoin(div_count_subq, Cell.id == div_count_subq.c.cell_id)
        )

        count_query = select(func.count(Cell.id))

        filters = []
        if organism:
            filters.append(Cell.organism.ilike(f"%{organism}%"))
        if cell_type:
            filters.append(Cell.cell_type.ilike(f"%{cell_type}%"))
        if search:
            search_pattern = f"%{search}%"
            filters.append(
                or_(
                    Cell.id.ilike(search_pattern),
                    Cell.name.ilike(search_pattern),
                    Cell.organism.ilike(search_pattern),
                    Cell.cell_type.ilike(search_pattern),
                )
            )

        if filters:
            base_query = base_query.where(*filters)
            count_query = count_query.where(*filters)

        total = self.db.execute(count_query).scalar_one()

        base_query = base_query.order_by(Cell.id).offset(offset).limit(limit)
        results = self.db.execute(base_query).all()

        # Results are tuples of (Cell, division_count)
        return [(row[0], int(row[1])) for row in results], total

    def get_division_count(self, cell_id: str) -> int:
        """Count division records associated with a specific cell."""
        stmt = select(func.count(CellDivisionRecord.id)).where(
            CellDivisionRecord.cell_id == cell_id
        )
        return self.db.execute(stmt).scalar_one()
