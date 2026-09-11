"""Biotechnology Analytics and Kinetic Profiling endpoints."""

from typing import List
from fastapi import APIRouter
from app.api.deps import AnalyticsServiceDep
from app.schemas.analytics import (
    BatchAnalyticsItem,
    GenerationAnalyticsItem,
    GroupedAnalyticsItem,
    OverallAnalyticsSummary,
    TemperatureAnalyticsItem,
)

router = APIRouter()


@router.get(
    "/summary",
    response_model=OverallAnalyticsSummary,
    summary="Comprehensive Kinetics & Timing Summary",
    description="Calculates overall statistical metrics (mean, median, standard deviation, min, max, coefficient of variation) across all cell division observations.",
)
def get_analytics_summary(
    service: AnalyticsServiceDep,
) -> OverallAnalyticsSummary:
    """Retrieve overarching statistical parameters for division durations and cycle kinetics."""
    return service.get_summary()


@router.get(
    "/by-cell-type",
    response_model=List[GroupedAnalyticsItem],
    summary="Analytics Stratified by Cell Type",
    description="Statistical breakdown of division duration, cell-cycle duration, and specific growth rates across biological cell morphologies.",
)
def get_analytics_by_cell_type(
    service: AnalyticsServiceDep,
) -> List[GroupedAnalyticsItem]:
    """Retrieve statistical kinetics grouped by cell type."""
    return service.get_by_cell_type()


@router.get(
    "/by-condition",
    response_model=List[GroupedAnalyticsItem],
    summary="Analytics Stratified by Experimental Condition",
    description="Comparative analysis of division kinetics under various media perturbations, nutrient stresses, and chemical treatments.",
)
def get_analytics_by_condition(
    service: AnalyticsServiceDep,
) -> List[GroupedAnalyticsItem]:
    """Retrieve statistical kinetics grouped by experimental condition."""
    return service.get_by_condition()


@router.get(
    "/by-temperature",
    response_model=List[TemperatureAnalyticsItem],
    summary="Analytics Stratified by Incubation Temperature",
    description="Temperature dependency analysis of division timing and growth kinetics.",
)
def get_analytics_by_temperature(
    service: AnalyticsServiceDep,
) -> List[TemperatureAnalyticsItem]:
    """Retrieve kinetic statistics across distinct incubation temperatures."""
    return service.get_by_temperature()


@router.get(
    "/by-generation",
    response_model=List[GenerationAnalyticsItem],
    summary="Analytics Stratified by Generation Cycle",
    description="Tracks division duration progression, replicative stability, and cycle timing shifts across consecutive generations.",
)
def get_analytics_by_generation(
    service: AnalyticsServiceDep,
) -> List[GenerationAnalyticsItem]:
    """Retrieve timing kinetics across sequential cell generations."""
    return service.get_by_generation()


@router.get(
    "/batches",
    response_model=List[BatchAnalyticsItem],
    summary="Batch Quality Control and Kinetics",
    description="Batch-level statistical quality control metrics, replicate summaries, and outlier rates.",
)
def get_analytics_batches(
    service: AnalyticsServiceDep,
) -> List[BatchAnalyticsItem]:
    """Retrieve experimental batch quality control and kinetics aggregations."""
    return service.get_batches()
