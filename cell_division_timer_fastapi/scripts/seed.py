"""CLI script for seeding the database with synthetic biological benchmark data."""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.seed import seed_database


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Cell Division Timer database.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reseed by clearing existing data first",
    )
    args = parser.parse_args()

    print(f"Executing database seed (force_reseed={args.force})...")
    total = seed_database(force_reseed=args.force)
    print(f"Database successfully seeded! Total division records: {total}")


if __name__ == "__main__":
    main()
