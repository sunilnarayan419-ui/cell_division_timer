"""Analytical schemas for life-science metrics aggregation."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class MetricStatistics(BaseModel):
    """Statistical distribution metrics for a biological parameter."""

    count: int = Field(..., description="Number of valid observations")
    mean: Optional[float] = Field(None, description="Arithmetic mean")
    median: Optional[float] = Field(None, description="Median (50th percentile)")
    std_dev: Optional[float] = Field(None, description="Sample standard deviation")
    min: Optional[float] = Field(None, description="Minimum observed value")
    max: Optional[float] = Field(None, description="Maximum observed value")
    cv_percent: Optional[float] = Field(
        None,
        description="Coefficient of variation (std_dev / mean * 100), metric of biological dispersion",
    )


class OverallAnalyticsSummary(BaseModel):
    """Comprehensive statistical summary across all recorded division events."""

    total_observations: int
    outlier_count: int
    clean_observation_count: int
    unique_cells_count: int
    unique_batches_count: int
    division_duration_minutes: MetricStatistics
    cell_cycle_duration_hours: MetricStatistics
    growth_rate_per_hour: MetricStatistics


class GroupedAnalyticsItem(BaseModel):
    """Statistical breakdown for a specific biological or experimental grouping."""

    group_value: str
    observations: int
    division_duration_minutes: MetricStatistics
    cell_cycle_duration_hours: MetricStatistics
    growth_rate_per_hour: MetricStatistics


class TemperatureAnalyticsItem(BaseModel):
    """Statistical breakdown by incubation temperature."""

    temperature_celsius: float
    observations: int
    division_duration_minutes: MetricStatistics
    cell_cycle_duration_hours: MetricStatistics
    growth_rate_per_hour: MetricStatistics


class GenerationAnalyticsItem(BaseModel):
    """Statistical kinetics across consecutive cell generations."""

    generation: int
    observations: int
    division_duration_minutes: MetricStatistics
    cell_cycle_duration_hours: MetricStatistics
    growth_rate_per_hour: MetricStatistics


class BatchAnalyticsItem(BaseModel):
    """Quality control and statistical metrics for an experimental batch."""

    batch_id: str
    replicates: List[int]
    conditions: List[str]
    total_observations: int
    outlier_count: int
    outlier_rate_percent: float
    division_duration_minutes: MetricStatistics
    cell_cycle_duration_hours: MetricStatistics
