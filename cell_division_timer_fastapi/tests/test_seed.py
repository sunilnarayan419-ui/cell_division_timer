"""Tests for database seeding mechanism and synthetic data generator."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
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

    # Observed/calculated consistency: the seed generator must not invent a
    # duration/timestamp pair that contradict each other.
    for d in divisions:
        implied_minutes = (d.division_end_time - d.division_start_time).total_seconds() / 60.0
        assert abs(implied_minutes - d.division_duration_minutes) < 0.01


@pytest.fixture
def isolated_seed_db(monkeypatch: pytest.MonkeyPatch):
    """Give seed_database() its own throw-away database.

    Seeding performs real commits, so it must never share a database with
    the rest of the suite's per-test rollback-isolated `db_session`/`client`
    fixtures, and it must never share the real application database file.
    Table creation here simulates migrations having already been applied
    (`alembic upgrade head`), matching how seed_database() is meant to be
    run in practice.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    monkeypatch.setattr("app.seed.engine", engine)
    monkeypatch.setattr("app.seed.SessionLocal", SessionLocal)

    yield engine

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_seed_database_execution(isolated_seed_db):
    """Verify seed_database execution is idempotent."""
    count1 = seed_database()
    assert count1 >= 100

    # Second call should be idempotent and not duplicate
    count2 = seed_database()
    assert count2 == count1


def test_seed_database_force_reseed(isolated_seed_db):
    """force_reseed=True should clear and regenerate records rather than accumulate."""
    first = seed_database()
    second = seed_database(force_reseed=True)
    assert first == second


def test_seed_database_requires_migrations(monkeypatch: pytest.MonkeyPatch):
    """seed_database() must refuse to run against an unmigrated database.

    Schema management belongs to Alembic; the seed script must never fall
    back to creating tables itself (that would let the schema silently
    diverge from the migration history).
    """
    bare_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    monkeypatch.setattr("app.seed.engine", bare_engine)

    with pytest.raises(RuntimeError, match="alembic upgrade head"):
        seed_database()

    bare_engine.dispose()
