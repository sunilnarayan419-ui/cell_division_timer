"""Biological domain logic, kinetics calculations, and validation rules."""

import math
from datetime import datetime
from typing import Dict, List, Optional, Tuple


# Reference biological ranges for common model organisms in life-science research
BIOLOGICAL_REFERENCE_RANGES: Dict[str, Dict[str, Tuple[float, float]]] = {
    "Saccharomyces cerevisiae": {
        "division_duration_min": (15.0, 55.0),
        "cell_cycle_hours": (1.0, 4.5),
        "temperature_celsius": (18.0, 40.0),
    },
    "Escherichia coli": {
        "division_duration_min": (8.0, 35.0),
        "cell_cycle_hours": (0.25, 2.5),
        "temperature_celsius": (15.0, 44.0),
    },
    "Homo sapiens": {
        "division_duration_min": (35.0, 160.0),
        "cell_cycle_hours": (14.0, 40.0),
        "temperature_celsius": (32.0, 41.0),
    },
    "Mus musculus": {
        "division_duration_min": (35.0, 150.0),
        "cell_cycle_hours": (12.0, 36.0),
        "temperature_celsius": (32.0, 41.0),
    },
    "Schizosaccharomyces pombe": {
        "division_duration_min": (15.0, 60.0),
        "cell_cycle_hours": (1.8, 5.0),
        "temperature_celsius": (18.0, 38.0),
    },
}

# Global extreme physical limits for any cellular system
GLOBAL_LIMITS = {
    "min_division_min": 1.0,
    "max_division_min": 600.0,
    "min_cycle_hours": 0.1,
    "max_cycle_hours": 120.0,
    "min_temp_c": 0.0,
    "max_temp_c": 60.0,
}


def calculate_division_duration_minutes(start_time: datetime, end_time: datetime) -> float:
    """Calculate the active division/mitosis duration in minutes.

    Raises:
        ValueError: If division_end_time occurs before division_start_time.
    """
    if end_time < start_time:
        raise ValueError(
            f"Division end time ({end_time.isoformat()}) cannot be earlier than "
            f"start time ({start_time.isoformat()})"
        )
    delta_seconds = (end_time - start_time).total_seconds()
    return round(delta_seconds / 60.0, 2)


def calculate_specific_growth_rate(cell_cycle_duration_hours: float) -> float:
    """Calculate the specific growth rate mu (in hr^-1) from cell-cycle doubling time.

    Formula:
        mu = ln(2) / Doubling_Time (hours)

    Raises:
        ValueError: If cell-cycle duration is non-positive.
    """
    if cell_cycle_duration_hours <= 0:
        raise ValueError(
            f"Cell-cycle duration must be strictly positive, got {cell_cycle_duration_hours}"
        )
    mu = math.log(2) / cell_cycle_duration_hours
    return round(mu, 4)


def evaluate_biological_metrics(
    organism: Optional[str],
    division_duration_minutes: float,
    cell_cycle_duration_hours: float,
    temperature_celsius: float,
) -> Tuple[bool, str]:
    """Evaluate division timing metrics against biological and physical plausibility thresholds.

    Returns:
        Tuple[is_outlier: bool, quality_flag: str]
    """
    # 1. Check absolute physical limits
    if division_duration_minutes < GLOBAL_LIMITS["min_division_min"]:
        return True, "OUTLIER_DURATION_TOO_SHORT"
    if division_duration_minutes > GLOBAL_LIMITS["max_division_min"]:
        return True, "OUTLIER_DURATION_EXCESSIVE"

    if cell_cycle_duration_hours < GLOBAL_LIMITS["min_cycle_hours"]:
        return True, "OUTLIER_CYCLE_TOO_SHORT"
    if cell_cycle_duration_hours > GLOBAL_LIMITS["max_cycle_hours"]:
        return True, "OUTLIER_CYCLE_EXCESSIVE"

    if (
        temperature_celsius < GLOBAL_LIMITS["min_temp_c"]
        or temperature_celsius > GLOBAL_LIMITS["max_temp_c"]
    ):
        return True, "OUTLIER_EXTREME_TEMPERATURE"

    # 2. Division duration cannot exceed the entire cell cycle
    cycle_in_minutes = cell_cycle_duration_hours * 60.0
    if division_duration_minutes >= cycle_in_minutes:
        return True, "SUSPECT_DIVISION_EXCEEDS_CYCLE"

    # 3. Organism-specific plausible range verification
    if organism and organism in BIOLOGICAL_REFERENCE_RANGES:
        ref = BIOLOGICAL_REFERENCE_RANGES[organism]
        min_div, max_div = ref["division_duration_min"]
        min_cyc, max_cyc = ref["cell_cycle_hours"]
        min_temp, max_temp = ref["temperature_celsius"]

        # If more than 50% outside typical biological window, flag as suspect
        if division_duration_minutes < min_div * 0.5 or division_duration_minutes > max_div * 2.0:
            return True, "OUTLIER_SPECIES_DURATION"
        if cell_cycle_duration_hours < min_cyc * 0.5 or cell_cycle_duration_hours > max_cyc * 2.0:
            return True, "OUTLIER_SPECIES_CYCLE"
        if temperature_celsius < min_temp - 5.0 or temperature_celsius > max_temp + 5.0:
            return True, "OUTLIER_SPECIES_TEMP"

    return False, "PASS"


def compute_descriptive_stats(values: List[float]) -> Dict[str, Optional[float]]:
    """Compute standard descriptive statistics (mean, median, std_dev, min, max, CV).

    Returns a clean dictionary of metrics rounded for reporting.
    """
    if not values:
        return {
            "count": 0,
            "mean": None,
            "median": None,
            "std_dev": None,
            "min": None,
            "max": None,
            "cv_percent": None,
        }

    n = len(values)
    sorted_vals = sorted(values)
    total = sum(sorted_vals)
    mean_val = total / n

    # Median
    if n % 2 == 1:
        median_val = sorted_vals[n // 2]
    else:
        median_val = (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2.0

    # Sample standard deviation (or 0 if n == 1)
    if n > 1:
        variance = sum((x - mean_val) ** 2 for x in sorted_vals) / (n - 1)
        std_dev = math.sqrt(variance)
    else:
        std_dev = 0.0

    # Coefficient of variation (CV = std_dev / mean * 100)
    cv_percent = (std_dev / mean_val * 100.0) if mean_val != 0 else 0.0

    return {
        "count": n,
        "mean": round(mean_val, 2),
        "median": round(median_val, 2),
        "std_dev": round(std_dev, 2),
        "min": round(sorted_vals[0], 2),
        "max": round(sorted_vals[-1], 2),
        "cv_percent": round(cv_percent, 2),
    }
