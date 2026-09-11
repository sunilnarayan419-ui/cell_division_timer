"""Database seeding script for generating 100 scientifically plausible synthetic division records.

DISCLAIMER: All generated records are SYNTHETIC/ASSUMED BENCHMARK DATA for
development, algorithmic testing, and analytics demonstration. They do not represent
clinical or verified wet-lab observations.
"""

import csv
import json
import os
import random
from datetime import datetime, timedelta, timezone
from typing import List, Tuple
from app.core.database import Base, SessionLocal, engine
from app.core.logging import logger
from app.models.cell import Cell
from app.models.division import CellDivisionRecord
from app.utils.biology import (
    calculate_division_duration_minutes,
    calculate_specific_growth_rate,
    evaluate_biological_metrics,
)

# Seed definitions for reproducibility
RANDOM_SEED = 42
TARGET_RECORD_COUNT = 100

SAMPLE_CELLS: List[dict] = [
    {
        "id": "CELL-SC-001",
        "name": "S. cerevisiae BY4741 WT",
        "organism": "Saccharomyces cerevisiae",
        "cell_type": "Budding yeast",
        "passage_number": 3,
        "source_line": "ATCC 204508",
        "description": "Standard haploid laboratory yeast strain for cell cycle control studies.",
    },
    {
        "id": "CELL-EC-001",
        "name": "E. coli K-12 MG1655",
        "organism": "Escherichia coli",
        "cell_type": "Rod-shaped bacterium",
        "passage_number": 1,
        "source_line": "ATCC 47076",
        "description": "Wild-type prophage-free bacterial model for prokaryotic division timing.",
    },
    {
        "id": "CELL-HELA-001",
        "name": "HeLa CCL-2",
        "organism": "Homo sapiens",
        "cell_type": "Epithelial adenocarcinoma",
        "passage_number": 14,
        "source_line": "ATCC CCL-2",
        "description": "Human immortal cell line used extensively for mitosis checkpoint analysis.",
    },
    {
        "id": "CELL-NIH3T3-001",
        "name": "NIH/3T3 Fibroblast",
        "organism": "Mus musculus",
        "cell_type": "Embryonic fibroblast",
        "passage_number": 8,
        "source_line": "ATCC CRL-1658",
        "description": "Contact-inhibited murine fibroblast line for growth factor kinetic kinetics.",
    },
]

CONDITIONS = [
    ("Control (Standard Media)", 1.0, 1.0),
    ("Nutrient Depletion (0.1% Glucose)", 1.35, 1.25),
    ("Thermal Stress (+5°C)", 1.20, 1.15),
    ("Rapamycin Inhibition (10 nM)", 1.45, 1.30),
    ("Osmotic Stress (0.4M Sorbitol)", 1.30, 1.20),
]

BATCHES = ["BATCH-2024-Q1", "BATCH-2024-Q2", "BATCH-2024-Q3", "BATCH-2024-Q4"]


def generate_synthetic_data() -> Tuple[List[Cell], List[CellDivisionRecord]]:
    """Generate 100 scientifically grounded synthetic division records across 4 biological cell models."""
    rng = random.Random(RANDOM_SEED)

    # 1. Initialize Cell instances
    cell_models = [Cell(**data) for data in SAMPLE_CELLS]

    # Baseline physiological parameters per cell type: (base_cycle_hrs, base_div_min, baseline_temp, medium)
    cell_baselines = {
        "CELL-SC-001": (2.1, 26.0, 30.0, "YPD Broth"),
        "CELL-EC-001": (0.65, 16.0, 37.0, "LB Broth"),
        "CELL-HELA-001": (22.5, 75.0, 37.0, "DMEM + 10% FBS"),
        "CELL-NIH3T3-001": (19.0, 85.0, 37.0, "DMEM + 10% BCS"),
    }

    division_records: List[CellDivisionRecord] = []
    base_time = datetime(2024, 3, 1, 8, 0, 0, tzinfo=timezone.utc)

    # Generate records distributed across cells
    per_cell_count = TARGET_RECORD_COUNT // len(SAMPLE_CELLS)  # 25 per cell line = 100 total
    record_id_counter = 1

    for cell in SAMPLE_CELLS:
        cid = cell["id"]
        base_cycle, base_div, base_temp, medium = cell_baselines[cid]

        for i in range(per_cell_count):
            cond_name, cycle_multiplier, div_multiplier = rng.choice(CONDITIONS)
            batch = rng.choice(BATCHES)
            replicate = (i % 3) + 1
            generation = (i % 5) + 1

            # Adjust temperature if heat stress condition
            if "Thermal Stress" in cond_name:
                temperature = base_temp + 5.0
            elif rng.random() < 0.15:
                # Slight temperature fluctuation (+/- 1.5 C)
                temperature = round(base_temp + rng.uniform(-1.5, 1.5), 1)
            else:
                temperature = base_temp

            # Biological noise (+/- 8%)
            noise_cycle = rng.uniform(0.92, 1.08)
            noise_div = rng.uniform(0.90, 1.10)

            # Inject 4 deliberate outliers in the 100 dataset for quality control testing
            is_deliberate_outlier = record_id_counter in [15, 38, 62, 89]

            if is_deliberate_outlier:
                if record_id_counter == 15:
                    # Mitotic arrest (excessive cytokinesis duration)
                    div_duration = round(base_div * 4.5, 2)
                    cycle_duration = round(base_cycle * 2.2, 2)
                elif record_id_counter == 38:
                    # Extreme temperature shock
                    temperature = 49.5
                    div_duration = round(base_div * 1.5, 2)
                    cycle_duration = round(base_cycle * 2.0, 2)
                elif record_id_counter == 62:
                    # Premature fragmentation / abnormally short
                    div_duration = 2.0
                    cycle_duration = round(base_cycle * 0.8, 2)
                else:
                    # Division duration exceeding cell cycle
                    cycle_duration = 0.5
                    div_duration = 35.0
            else:
                cycle_duration = round(base_cycle * cycle_multiplier * noise_cycle, 2)
                div_duration = round(base_div * div_multiplier * noise_div, 2)

            # Start and End times
            time_offset_days = (record_id_counter * 0.6)
            start_time = base_time + timedelta(days=time_offset_days, hours=(i * 1.8))
            end_time = start_time + timedelta(minutes=div_duration)

            growth_rate = calculate_specific_growth_rate(cycle_duration)

            # Quality validation
            is_outlier, quality_flag = evaluate_biological_metrics(
                organism=cell["organism"],
                division_duration_minutes=div_duration,
                cell_cycle_duration_hours=cycle_duration,
                temperature_celsius=temperature,
            )

            rec = CellDivisionRecord(
                cell_id=cid,
                experimental_batch=batch,
                replicate=replicate,
                experimental_condition=cond_name,
                medium=medium,
                temperature_celsius=temperature,
                generation=generation,
                division_start_time=start_time,
                division_end_time=end_time,
                division_duration_minutes=div_duration,
                cell_cycle_duration_hours=cycle_duration,
                growth_rate=growth_rate,
                is_outlier=is_outlier,
                quality_flag=quality_flag,
                notes=f"Synthetic benchmark observation #{record_id_counter}. Seed={RANDOM_SEED}",
                metadata_json=json.dumps(
                    {
                        "source": "synthetic_seed_v1",
                        "objective": "100x Oil Immersion",
                        "imaging_channel": "DAPI/GFP",
                        "deliberate_outlier": is_deliberate_outlier,
                    }
                ),
            )
            division_records.append(rec)
            record_id_counter += 1

    return cell_models, division_records


def seed_database(force_reseed: bool = False) -> int:
    """Idempotently populate database with sample cells and 100 synthetic division records.

    Returns:
        int: Number of division records present in database after seeding.
    """
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        existing_cells = db.query(Cell).count()
        existing_divisions = db.query(CellDivisionRecord).count()

        if existing_divisions >= TARGET_RECORD_COUNT and not force_reseed:
            logger.info(
                f"Database already seeded ({existing_cells} cells, {existing_divisions} divisions). Skipping."
            )
            return existing_divisions

        if force_reseed and existing_divisions > 0:
            logger.info("Clearing existing division records for forced reseed...")
            db.query(CellDivisionRecord).delete()
            db.query(Cell).delete()
            db.commit()

        cells, divisions = generate_synthetic_data()

        # Insert cells (avoid duplicates)
        for c in cells:
            if not db.query(Cell).filter(Cell.id == c.id).first():
                db.add(c)
        db.commit()

        # Insert divisions
        db.add_all(divisions)
        db.commit()

        total_divisions = db.query(CellDivisionRecord).count()
        logger.info(
            f"Successfully seeded {len(cells)} cells and {len(divisions)} division records "
            f"(Total in DB: {total_divisions})."
        )

        # Also persist to data/ directory as CSV and JSON benchmark files
        save_synthetic_files(divisions)

        return total_divisions
    except Exception as exc:
        db.rollback()
        logger.error(f"Error seeding database: {exc}")
        raise
    finally:
        db.close()


def save_synthetic_files(divisions: List[CellDivisionRecord]) -> None:
    """Save synthetic records to data/ directory for standalone data engineering benchmarks."""
    os.makedirs("data", exist_ok=True)
    csv_path = os.path.join("data", "synthetic_cell_divisions_100.csv")
    json_path = os.path.join("data", "synthetic_cell_divisions_100.json")

    # Write CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "record_id",
                "cell_id",
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
            ]
        )
        for idx, r in enumerate(divisions, 1):
            writer.writerow(
                [
                    idx,
                    r.cell_id,
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
                ]
            )

    # Write JSON
    json_data = [
        {
            "record_id": idx,
            "cell_id": r.cell_id,
            "experimental_batch": r.experimental_batch,
            "replicate": r.replicate,
            "experimental_condition": r.experimental_condition,
            "medium": r.medium,
            "temperature_celsius": r.temperature_celsius,
            "generation": r.generation,
            "division_start_time": r.division_start_time.isoformat(),
            "division_end_time": r.division_end_time.isoformat(),
            "division_duration_minutes": r.division_duration_minutes,
            "cell_cycle_duration_hours": r.cell_cycle_duration_hours,
            "growth_rate_per_hour": r.growth_rate,
            "is_outlier": r.is_outlier,
            "quality_flag": r.quality_flag,
        }
        for idx, r in enumerate(divisions, 1)
    ]
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)

    logger.info(f"Persisted synthetic datasets to {csv_path} and {json_path}")


if __name__ == "__main__":
    count = seed_database()
    print(f"Seeding completed successfully: {count} total division records in database.")
