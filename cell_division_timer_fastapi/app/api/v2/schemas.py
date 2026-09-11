"""Pydantic schemas for API v2 beta endpoints."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.division import CellDivisionBase, CellDivisionResponse


class MitoticSubphaseTiming(BaseModel):
    """Mitotic sub-phase duration breakdown (v2 beta capability)."""

    prophase_minutes: float = Field(..., ge=0.0, description="Prophase chromosome condensation duration")
    metaphase_minutes: float = Field(..., ge=0.0, description="Metaphase spindle equatorial alignment duration")
    anaphase_minutes: float = Field(..., ge=0.0, description="Anaphase sister chromatid separation duration")
    telophase_minutes: float = Field(..., ge=0.0, description="Telophase nuclear reassembly and cytokinesis")


class CellDivisionV2Response(CellDivisionResponse):
    """Enhanced division observation record in v2 beta with subphase resolution."""

    mitotic_subphases: Optional[MitoticSubphaseTiming] = None
    checkpoint_delay_index: float = Field(
        default=1.0,
        ge=0.0,
        description="Ratio of observed metaphase duration vs baseline control",
    )
    arrest_probability_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Probabilistic spindle assembly arrest score (0.0=normal, 1.0=arrested)",
    )


class BatchDivisionObservation(BaseModel):
    """Input payload for batch kinetic analysis."""

    cell_id: str
    temperature_celsius: float
    division_duration_minutes: float
    cell_cycle_duration_hours: float
    experimental_condition: str


class BatchAnalyzeRequest(BaseModel):
    """Batch kinetic analysis request body."""

    batch_name: str = Field(..., min_length=1, max_length=64, examples=["BATCH-2024-V2-EXP1"])
    observations: List[BatchDivisionObservation] = Field(..., min_length=1, max_length=500)


class BatchAnalyzeResponse(BaseModel):
    """Batch kinetic analysis response body."""

    batch_name: str
    total_processed: int
    mean_division_minutes: float
    mean_growth_rate_per_hour: float
    outlier_count: int
    outlier_rate_percent: float
    arrhenius_q10_estimate: Optional[float] = None
    processed_at: datetime


class Q10KineticsModel(BaseModel):
    """Arrhenius Q10 temperature coefficient modeling."""

    reference_temperature_celsius: float
    elevated_temperature_celsius: float
    reference_growth_rate: float
    elevated_growth_rate: float
    q10_temperature_coefficient: float
    activation_energy_kj_mol: float
    biological_interpretation: str


class V2BetaStatusResponse(BaseModel):
    """v2 beta lifecycle status and capabilities."""

    version: str = "2.0.0-beta.1"
    status: str = "beta"
    deprecation_notice: Optional[str] = None
    lifecycle: str = "active-development"
    features: List[str]
    backward_compatibility: Dict[str, Any]
    changelog: List[str]
