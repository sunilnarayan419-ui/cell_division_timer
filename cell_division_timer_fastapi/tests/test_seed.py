"""Tests for database seeding mechanism and synthetic data generator."""

from app.seed import generate_synthetic_data, seed_database


def test_synthetic_data_generator_properties():
    """Verify generated synthetic dataset satisfies life-sciences requirements."""
    cells, divisions = generate_synthetic_data()

    # 100 division records
    assert len(divisions) == 100
    # 4 distinct cell lines
    assert len(cells) == 4

    # Every division must have a valid cell_id belonging to the cells
    cell_ids = {c.id for c in cells}
    for d in divisions:
        assert d.cell_id in cell_ids
        assert d.division_duration_minutes > 0
        assert d.cell_cycle_duration_hours > 0
        assert d.growth_rate > 0
        assert -10.0 <= d.temperature_celsius <= 100.0

    # Ensure deliberate outliers exist in benchmark set
    outliers = [d for d in divisions if d.is_outlier]
    assert len(outliers) >= 3


def test_seed_database_execution(db_session):
    """Verify seed_database execution is idempotent."""
    count1 = seed_database()
    assert count1 >= 100

    # Second call should be idempotent and not duplicate
    count2 = seed_database()
    assert count2 == count1
