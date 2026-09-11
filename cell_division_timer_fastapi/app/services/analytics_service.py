"""Analytics service for scientific cell division and kinetics reporting."""

from collections import defaultdict
from typing import List
from sqlalchemy.orm import Session
from app.repositories.division_repository import DivisionRepository
from app.schemas.analytics import (
    BatchAnalyticsItem,
    GenerationAnalyticsItem,
    GroupedAnalyticsItem,
    MetricStatistics,
    OverallAnalyticsSummary,
    TemperatureAnalyticsItem,
)
from app.utils.biology import compute_descriptive_stats


class AnalyticsService:
    """Calculates scientific and statistical summaries over experimental observations."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = DivisionRepository(db)

    def _stats_to_schema(self, stats: dict) -> MetricStatistics:
        return MetricStatistics(
            count=stats["count"],
            mean=stats["mean"],
            median=stats["median"],
            std_dev=stats["std_dev"],
            min=stats["min"],
            max=stats["max"],
            cv_percent=stats["cv_percent"],
        )

    def get_summary(self) -> OverallAnalyticsSummary:
        """Calculate overall statistics across all experimental division observations."""
        records = self.repo.get_all_records_with_cell()
        total = len(records)

        outliers = [r for r in records if r.is_outlier]
        outlier_count = len(outliers)
        clean_count = total - outlier_count

        unique_cells = len(set(r.cell_id for r in records))
        unique_batches = len(set(r.experimental_batch for r in records))

        div_durations = [r.division_duration_minutes for r in records]
        cycle_durations = [r.cell_cycle_duration_hours for r in records]
        growth_rates = [r.growth_rate for r in records]

        return OverallAnalyticsSummary(
            total_observations=total,
            outlier_count=outlier_count,
            clean_observation_count=clean_count,
            unique_cells_count=unique_cells,
            unique_batches_count=unique_batches,
            division_duration_minutes=self._stats_to_schema(compute_descriptive_stats(div_durations)),
            cell_cycle_duration_hours=self._stats_to_schema(compute_descriptive_stats(cycle_durations)),
            growth_rate_per_hour=self._stats_to_schema(compute_descriptive_stats(growth_rates)),
        )

    def get_by_cell_type(self) -> List[GroupedAnalyticsItem]:
        """Aggregate timing metrics grouped by biological cell type."""
        records = self.repo.get_all_records_with_cell()
        grouped = defaultdict(lambda: {"div": [], "cycle": [], "growth": []})

        for r in records:
            cell_type = r.cell.cell_type if r.cell else "Unknown"
            grouped[cell_type]["div"].append(r.division_duration_minutes)
            grouped[cell_type]["cycle"].append(r.cell_cycle_duration_hours)
            grouped[cell_type]["growth"].append(r.growth_rate)

        results = []
        for cell_type, data in sorted(grouped.items()):
            results.append(
                GroupedAnalyticsItem(
                    group_value=cell_type,
                    observations=len(data["div"]),
                    division_duration_minutes=self._stats_to_schema(compute_descriptive_stats(data["div"])),
                    cell_cycle_duration_hours=self._stats_to_schema(compute_descriptive_stats(data["cycle"])),
                    growth_rate_per_hour=self._stats_to_schema(compute_descriptive_stats(data["growth"])),
                )
            )
        return results

    def get_by_condition(self) -> List[GroupedAnalyticsItem]:
        """Aggregate timing metrics grouped by experimental perturbation condition."""
        records = self.repo.get_all_records_with_cell()
        grouped = defaultdict(lambda: {"div": [], "cycle": [], "growth": []})

        for r in records:
            cond = r.experimental_condition
            grouped[cond]["div"].append(r.division_duration_minutes)
            grouped[cond]["cycle"].append(r.cell_cycle_duration_hours)
            grouped[cond]["growth"].append(r.growth_rate)

        results = []
        for cond, data in sorted(grouped.items()):
            results.append(
                GroupedAnalyticsItem(
                    group_value=cond,
                    observations=len(data["div"]),
                    division_duration_minutes=self._stats_to_schema(compute_descriptive_stats(data["div"])),
                    cell_cycle_duration_hours=self._stats_to_schema(compute_descriptive_stats(data["cycle"])),
                    growth_rate_per_hour=self._stats_to_schema(compute_descriptive_stats(data["growth"])),
                )
            )
        return results

    def get_by_temperature(self) -> List[TemperatureAnalyticsItem]:
        """Aggregate kinetics across distinct incubation temperatures."""
        records = self.repo.get_all_records_with_cell()
        grouped = defaultdict(lambda: {"div": [], "cycle": [], "growth": []})

        for r in records:
            temp = r.temperature_celsius
            grouped[temp]["div"].append(r.division_duration_minutes)
            grouped[temp]["cycle"].append(r.cell_cycle_duration_hours)
            grouped[temp]["growth"].append(r.growth_rate)

        results = []
        for temp in sorted(grouped.keys()):
            data = grouped[temp]
            results.append(
                TemperatureAnalyticsItem(
                    temperature_celsius=temp,
                    observations=len(data["div"]),
                    division_duration_minutes=self._stats_to_schema(compute_descriptive_stats(data["div"])),
                    cell_cycle_duration_hours=self._stats_to_schema(compute_descriptive_stats(data["cycle"])),
                    growth_rate_per_hour=self._stats_to_schema(compute_descriptive_stats(data["growth"])),
                )
            )
        return results

    def get_by_generation(self) -> List[GenerationAnalyticsItem]:
        """Aggregate division duration and cycle times across sequential generations."""
        records = self.repo.get_all_records_with_cell()
        grouped = defaultdict(lambda: {"div": [], "cycle": [], "growth": []})

        for r in records:
            gen = r.generation
            grouped[gen]["div"].append(r.division_duration_minutes)
            grouped[gen]["cycle"].append(r.cell_cycle_duration_hours)
            grouped[gen]["growth"].append(r.growth_rate)

        results = []
        for gen in sorted(grouped.keys()):
            data = grouped[gen]
            results.append(
                GenerationAnalyticsItem(
                    generation=gen,
                    observations=len(data["div"]),
                    division_duration_minutes=self._stats_to_schema(compute_descriptive_stats(data["div"])),
                    cell_cycle_duration_hours=self._stats_to_schema(compute_descriptive_stats(data["cycle"])),
                    growth_rate_per_hour=self._stats_to_schema(compute_descriptive_stats(data["growth"])),
                )
            )
        return results

    def get_batches(self) -> List[BatchAnalyticsItem]:
        """Provide batch-level statistical quality control and condition summaries."""
        records = self.repo.get_all_records_with_cell()
        grouped = defaultdict(
            lambda: {
                "replicates": set(),
                "conditions": set(),
                "outliers": 0,
                "div": [],
                "cycle": [],
            }
        )

        for r in records:
            b_info = grouped[r.experimental_batch]
            b_info["replicates"].add(r.replicate)
            b_info["conditions"].add(r.experimental_condition)
            if r.is_outlier:
                b_info["outliers"] += 1
            b_info["div"].append(r.division_duration_minutes)
            b_info["cycle"].append(r.cell_cycle_duration_hours)

        results = []
        for batch_id in sorted(grouped.keys()):
            b_info = grouped[batch_id]
            total_obs = len(b_info["div"])
            outlier_rate = round((b_info["outliers"] / total_obs * 100.0) if total_obs > 0 else 0.0, 2)

            results.append(
                BatchAnalyticsItem(
                    batch_id=batch_id,
                    replicates=sorted(list(b_info["replicates"])),
                    conditions=sorted(list(b_info["conditions"])),
                    total_observations=total_obs,
                    outlier_count=b_info["outliers"],
                    outlier_rate_percent=outlier_rate,
                    division_duration_minutes=self._stats_to_schema(compute_descriptive_stats(b_info["div"])),
                    cell_cycle_duration_hours=self._stats_to_schema(compute_descriptive_stats(b_info["cycle"])),
                )
            )
        return results
