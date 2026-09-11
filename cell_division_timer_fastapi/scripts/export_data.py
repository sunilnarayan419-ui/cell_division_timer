"""CLI script for exporting the cell division dataset to output/ directory."""

import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.services.csv_service import CSVService


def main() -> None:
    db = SessionLocal()
    try:
        service = CSVService(db)
        csv_data = service.export_divisions_to_csv()

        os.makedirs("output", exist_ok=True)
        out_file = os.path.join("output", "cell_division_export.csv")
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(csv_data)

        print(f"Export completed! Dataset saved to: {out_file}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
