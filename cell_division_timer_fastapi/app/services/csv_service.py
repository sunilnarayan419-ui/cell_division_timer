"""CSV Import and Export service for lab instruments and data exchange."""

import csv
import io
from datetime import datetime
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from app.models.cell import Cell
from app.models.division import CellDivisionRecord
from app.repositories.cell_repository import CellRepository
from app.repositories.division_repository import DivisionRepository
from app.utils.biology import (
    calculate_division_duration_minutes,
    calculate_specific_growth_rate,
    evaluate_biological_metrics,
)


class CSVService:
    """Handles biological data interchange via CSV formatting."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.cell_repo = CellRepository(db)
        self.div_repo = DivisionRepository(db)

    def export_divisions_to_csv(self) -> str:
        """Export all division observations and cell lineage context into CSV string."""
        records = self.div_repo.get_all_records_with_cell()
        output = io.StringIO()
        writer = csv.writer(output)

        # Header row
        writer.writerow(
            [
                "record_id",
                "cell_id",
                "organism",
                "cell_type",
                "experimental_batch",
                "replicate",
                "experimental_condition",
                "medium",
                "temperature_celsius",
                "generation",
                "division_start_time",
                "division_end_time",
                "division_duration_minutes",
                "cell_cycle_duration_hours",
                "growth_rate_per_hour",
                "is_outlier",
                "quality_flag",
                "notes",
            ]
        )

        for r in records:
            writer.writerow(
                [
                    r.id,
                    r.cell_id,
                    r.cell.organism if r.cell else "",
                    r.cell.cell_type if r.cell else "",
                    r.experimental_batch,
                    r.replicate,
                    r.experimental_condition,
                    r.medium,
                    r.temperature_celsius,
                    r.generation,
                    r.division_start_time.isoformat(),
                    r.division_end_time.isoformat(),
                    r.division_duration_minutes,
                    r.cell_cycle_duration_hours,
                    r.growth_rate,
                    r.is_outlier,
                    r.quality_flag,
                    r.notes or "",
                ]
            )

        return output.getvalue()

    def import_divisions_from_csv(self, csv_content: str) -> Dict[str, Any]:
        """Import division observations from CSV. Automatically registers missing cells.

        Returns:
            Dict summarizing created records and any row-level validation errors.
        """
        reader = csv.DictReader(io.StringIO(csv_content))
        created_records: List[CellDivisionRecord] = []
        errors: List[Dict[str, Any]] = []

        row_index = 1
        for row in reader:
            row_index += 1
            try:
                cell_id = row.get("cell_id", "").strip()
                if not cell_id:
                    raise ValueError("Missing required 'cell_id'")

                # Register parent cell if missing
                if not self.cell_repo.exists(cell_id):
                    organism = row.get("organism", "Synthetic organism").strip() or "Synthetic organism"
                    cell_type = row.get("cell_type", "Synthetic type").strip() or "Synthetic type"
                    new_cell = Cell(
                        id=cell_id,
                        name=f"Auto-imported {cell_id}",
                        organism=organism,
                        cell_type=cell_type,
                    )
                    self.cell_repo.create(new_cell)

                cell = self.cell_repo.get_by_id(cell_id)

                start_time = datetime.fromisoformat(row["division_start_time"].strip().replace("Z", "+00:00"))
                end_time = datetime.fromisoformat(row["division_end_time"].strip().replace("Z", "+00:00"))
                cycle_hours = float(row["cell_cycle_duration_hours"])
                temp_c = float(row.get("temperature_celsius", 30.0))

                div_duration = calculate_division_duration_minutes(start_time, end_time)
                growth_rate = calculate_specific_growth_rate(cycle_hours)

                is_outlier, quality_flag = evaluate_biological_metrics(
                    organism=cell.organism if cell else None,
                    division_duration_minutes=div_duration,
                    cell_cycle_duration_hours=cycle_hours,
                    temperature_celsius=temp_c,
                )

                record = CellDivisionRecord(
                    cell_id=cell_id,
                    experimental_batch=row.get("experimental_batch", "BATCH-IMPORT").strip(),
                    replicate=int(row.get("replicate", 1)),
                    experimental_condition=row.get("experimental_condition", "Standard").strip(),
                    medium=row.get("medium", "Standard").strip(),
                    temperature_celsius=temp_c,
                    generation=int(row.get("generation", 1)),
                    division_start_time=start_time,
                    division_end_time=end_time,
                    division_duration_minutes=div_duration,
                    cell_cycle_duration_hours=cycle_hours,
                    growth_rate=growth_rate,
                    is_outlier=is_outlier,
                    quality_flag=quality_flag,
                    notes=row.get("notes", "").strip() or None,
                )
                created_records.append(record)
            except Exception as exc:
                errors.append({"row": row_index, "error": str(exc), "data": row})

        if created_records:
            self.div_repo.bulk_create(created_records)

        return {
            "success": len(errors) == 0,
            "imported_count": len(created_records),
            "errors_count": len(errors),
            "errors": errors,
        }
