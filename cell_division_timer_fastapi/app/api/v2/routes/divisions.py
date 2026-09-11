"""API v2 Beta routes for Cell Division Records."""

from datetime import datetime, timezone
import math
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.api.deps import DivisionServiceDep
from app.api.v2.schemas import (
    BatchAnalyzeRequest,
    BatchAnalyzeResponse,
    CellDivisionV2Response,
    MitoticSubphaseTiming,
)
from app.utils.pagination import PaginatedResponse, PaginationParams

router = APIRouter(tags=["v2 Cell Division Records (Beta)"])


def _enhance_division_to_v2(record: dict) -> CellDivisionV2Response:
    """Decorate a v1 division record with v2 beta mitotic subphase estimates and arrest probability."""
    duration = record.get("division_duration_minutes", 30.0)
    is_outlier = record.get("is_outlier", False)

    # Biological typical phase proportions: Prophase ~35%, Metaphase ~30%, Anaphase ~15%, Telophase ~20%
    if is_outlier:
        # Outlier indicates extended metaphase delay (e.g. Spindle Assembly Checkpoint)
        prophase = round(duration * 0.15, 2)
        metaphase = round(duration * 0.65, 2)
        anaphase = round(duration * 0.10, 2)
        telophase = round(duration * 0.10, 2)
        arrest_score = min(1.0, round((duration / 60.0) * 0.5, 2))
        delay_index = round(metaphase / (duration * 0.30), 2)
    else:
        prophase = round(duration * 0.35, 2)
        metaphase = round(duration * 0.30, 2)
        anaphase = round(duration * 0.15, 2)
        telophase = round(duration * 0.20, 2)
        arrest_score = 0.05
        delay_index = 1.0

    subphases = MitoticSubphaseTiming(
        prophase_minutes=prophase,
        metaphase_minutes=metaphase,
        anaphase_minutes=anaphase,
        telophase_minutes=telophase,
    )

    data = dict(record)
    data["mitotic_subphases"] = subphases
    data["checkpoint_delay_index"] = delay_index
    data["arrest_probability_score"] = arrest_score
    return CellDivisionV2Response(**data)


@router.post(
    "/divisions/batch-analyze",
    response_model=BatchAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Batch Kinetic Profiler (v2 Beta)",
)
def batch_analyze_kinetics(payload: BatchAnalyzeRequest) -> BatchAnalyzeResponse:
    """Analyze a batch of division observations in a single request.

    Computes overall population kinetics, growth rates, biological outlier rejections,
    and estimates Q10 temperature coefficient if multiple temperature tiers exist.
    """
    total = len(payload.observations)
    if total == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch observation list cannot be empty",
        )

    durations = [o.division_duration_minutes for o in payload.observations]
    growth_rates = [
        math.log(2) / o.cell_cycle_duration_hours if o.cell_cycle_duration_hours > 0 else 0.0
        for o in payload.observations
    ]

    mean_div = sum(durations) / total
    mean_growth = sum(growth_rates) / total

    # Check outliers (duration > 3x mean or cycle < div)
    outlier_count = 0
    for o in payload.observations:
        if o.division_duration_minutes >= o.cell_cycle_duration_hours * 60 or o.division_duration_minutes > 100:
            outlier_count += 1

    outlier_rate = round((outlier_count / total) * 100, 2)

    # Q10 estimate if varying temperatures exist
    temps = sorted(list(set(o.temperature_celsius for o in payload.observations)))
    q10_estimate: Optional[float] = None
    if len(temps) >= 2:
        t1, t2 = temps[0], temps[-1]
        rates_t1 = [
            math.log(2) / o.cell_cycle_duration_hours
            for o in payload.observations
            if o.temperature_celsius == t1 and o.cell_cycle_duration_hours > 0
        ]
        rates_t2 = [
            math.log(2) / o.cell_cycle_duration_hours
            for o in payload.observations
            if o.temperature_celsius == t2 and o.cell_cycle_duration_hours > 0
        ]
        if rates_t1 and rates_t2 and (t2 - t1) != 0:
            k1 = sum(rates_t1) / len(rates_t1)
            k2 = sum(rates_t2) / len(rates_t2)
            if k1 > 0 and k2 > 0:
                q10_estimate = round(math.pow(k2 / k1, 10.0 / (t2 - t1)), 2)

    return BatchAnalyzeResponse(
        batch_name=payload.batch_name,
        total_processed=total,
        mean_division_minutes=round(mean_div, 2),
        mean_growth_rate_per_hour=round(mean_growth, 4),
        outlier_count=outlier_count,
        outlier_rate_percent=outlier_rate,
        arrhenius_q10_estimate=q10_estimate,
        processed_at=datetime.now(timezone.utc),
    )


@router.get(
    "/divisions",
    response_model=PaginatedResponse[CellDivisionV2Response],
    summary="List Division Records with v2 Subphase Resolution (Beta)",
)
def list_divisions_v2(
    service: DivisionServiceDep,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    cell_id: Optional[str] = Query(None, description="Filter by cell sample ID"),
    organism: Optional[str] = Query(None, description="Filter by organism name"),
    experimental_batch: Optional[str] = Query(None, description="Filter by experimental batch ID"),
    is_outlier: Optional[bool] = Query(None, description="Filter by biological outlier flag"),
) -> PaginatedResponse[CellDivisionV2Response]:
    """Retrieve paginated division records with v2 mitotic subphase breakdowns and arrest scoring."""
    v1_result = service.list_divisions(
        pagination=PaginationParams(page=page, page_size=page_size),
        cell_id=cell_id,
        organism=organism,
        batch=experimental_batch,
        is_outlier=is_outlier,
    )

    v2_items = [_enhance_division_to_v2(item.model_dump()) for item in v1_result.items]

    return PaginatedResponse.create(
        items=v2_items,
        total=v1_result.total,
        page=v1_result.page,
        page_size=v1_result.page_size,
    )


@router.get(
    "/divisions/{division_id}",
    response_model=CellDivisionV2Response,
    summary="Get Single Division Record with v2 Subphase Telemetry (Beta)",
)
def get_division_v2(division_id: int, service: DivisionServiceDep) -> CellDivisionV2Response:
    """Retrieve a single division record enriched with mitotic subphase and checkpoint telemetry."""
    record = service.get_division(division_id)
    return _enhance_division_to_v2(record.model_dump())
