"""Tests for Biological domain logic and mathematical calculations."""

from datetime import datetime, timezone
import pytest
from app.utils.biology import (
    calculate_division_duration_minutes,
    calculate_specific_growth_rate,
    compute_descriptive_stats,
    evaluate_biological_metrics,
)


def test_division_duration_calculation():
    """Verify correct minute calculation and validation error on reversed timestamps."""
    start = datetime(2024, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
    end = datetime(2024, 3, 1, 10, 45, 30, tzinfo=timezone.utc)
    duration = calculate_division_duration_minutes(start, end)
    assert duration == 45.5

    # Reversed timestamp raises ValueError
    with pytest.raises(ValueError, match="cannot be earlier"):
        calculate_division_duration_minutes(end, start)


def test_specific_growth_rate_calculation():
    """Verify mu = ln(2)/doubling_time formula."""
    mu = calculate_specific_growth_rate(2.0)
    assert abs(mu - 0.3466) < 0.001

    with pytest.raises(ValueError, match="strictly positive"):
        calculate_specific_growth_rate(0)

    with pytest.raises(ValueError, match="strictly positive"):
        calculate_specific_growth_rate(-1.5)


def test_evaluate_biological_metrics_plausibility():
    """Verify biological outlier tagging."""
    # Healthy yeast observation
    is_outlier, flag = evaluate_biological_metrics(
        organism="Saccharomyces cerevisiae",
        division_duration_minutes=25.0,
        cell_cycle_duration_hours=2.0,
        temperature_celsius=30.0,
    )
    assert is_outlier is False
    assert flag == "PASS"

    # Extreme temperature shock
    is_outlier, flag = evaluate_biological_metrics(
        organism="Saccharomyces cerevisiae",
        division_duration_minutes=25.0,
        cell_cycle_duration_hours=2.0,
        temperature_celsius=75.0,
    )
    assert is_outlier is True
    assert "OUTLIER" in flag

    # Division duration exceeding cell cycle
    is_outlier, flag = evaluate_biological_metrics(
        organism="Saccharomyces cerevisiae",
        division_duration_minutes=150.0,
        cell_cycle_duration_hours=1.0,  # 1 hour = 60 min, division = 150 min
        temperature_celsius=30.0,
    )
    assert is_outlier is True
    assert flag == "SUSPECT_DIVISION_EXCEEDS_CYCLE"


def test_compute_descriptive_stats():
    """Verify descriptive statistics engine."""
    empty_stats = compute_descriptive_stats([])
    assert empty_stats["count"] == 0
    assert empty_stats["mean"] is None

    single_stats = compute_descriptive_stats([42.0])
    assert single_stats["count"] == 1
    assert single_stats["mean"] == 42.0
    assert single_stats["std_dev"] == 0.0

    multi_stats = compute_descriptive_stats([10.0, 20.0, 30.0])
    assert multi_stats["count"] == 3
    assert multi_stats["mean"] == 20.0
    assert multi_stats["median"] == 20.0
    assert multi_stats["min"] == 10.0
    assert multi_stats["max"] == 30.0
    assert multi_stats["std_dev"] == 10.0
    assert multi_stats["cv_percent"] == 50.0
