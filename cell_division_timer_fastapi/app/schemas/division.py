"""Cell Division Record Pydantic validation schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class CellDivisionBase(BaseModel):
    """Core experimental attributes for a cell division observation."""

    cell_id: str = Field(..., min_length=1, max_length=64, examples=["CELL-SC-001"])
    experimental_batch: str = Field(..., min_length=1, max_length=64, examples=["BATCH-2024-01"])
    replicate: int = Field(default=1, ge=1, le=50, examples=[1])
    experimental_condition: str = Field(..., min_length=1, max_length=128, examples=["Control"])
    medium: str = Field(..., min_length=1, max_length=128, examples=["YPD Complete"])
    temperature_celsius: float = Field(..., ge=-10.0, le=100.0, examples=[30.0])
    generation: int = Field(default=1, ge=1, le=1000, examples=[2])

    division_start_time: datetime = Field(..., examples=["2024-03-01T10:00:00Z"])
    division_end_time: datetime = Field(..., examples=["2024-03-01T10:28:30Z"])
    cell_cycle_duration_hours: float = Field(..., gt=0.0, le=200.0, examples=[2.1])

    notes: Optional[str] = Field(default=None, examples=["Clean cytokinesis observed via phase contrast"])
    metadata_json: Optional[str] = Field(default=None, examples=['{"microscope": "Zeiss Axio 2", "channel": "GFP"}'])


class CellDivisionCreate(CellDivisionBase):
    """Payload for creating a cell division record.

    `division_duration_minutes` and `growth_rate` are ALWAYS calculated from
    the source measurements (division_start_time/division_end_time and
    cell_cycle_duration_hours respectively) and cannot be supplied directly.

    If a manual override is scientifically necessary (e.g. correcting for a
    known instrument clock offset), use the explicit `*_override` fields
    together with a mandatory `*_override_reason`. OBSERVED != CALCULATED !=
    OVERRIDE unless explicitly documented via these reason fields.
    """

    duration_override_minutes: Optional[float] = Field(
        default=None,
        ge=0.0,
        description=(
            "Explicit manual override for division duration, in minutes. "
            "Must be supplied together with duration_override_reason. "
            "Leave both unset to use the value calculated from the timestamps."
        ),
    )
    duration_override_reason: Optional[str] = Field(
        default=None,
        max_length=256,
        description="Required justification when duration_override_minutes is supplied.",
    )
    growth_rate_override: Optional[float] = Field(
        default=None,
        ge=0.0,
        description=(
            "Explicit manual override for specific growth rate mu (hr^-1). "
            "Must be supplied together with growth_rate_override_reason. "
            "Leave both unset to use mu = ln(2) / cell_cycle_duration_hours."
        ),
    )
    growth_rate_override_reason: Optional[str] = Field(
        default=None,
        max_length=256,
        description="Required justification when growth_rate_override is supplied.",
    )

    @model_validator(mode="after")
    def validate_division_timestamps(self) -> "CellDivisionCreate":
        if self.division_end_time < self.division_start_time:
            raise ValueError(
                f"division_end_time ({self.division_end_time}) cannot be earlier than "
                f"division_start_time ({self.division_start_time})"
            )
        return self

    @model_validator(mode="after")
    def validate_override_pairs(self) -> "CellDivisionCreate":
        if (self.duration_override_minutes is None) != (self.duration_override_reason is None):
            raise ValueError(
                "duration_override_minutes and duration_override_reason must be "
                "supplied together (a manual override always needs a documented reason)."
            )
        if (self.growth_rate_override is None) != (self.growth_rate_override_reason is None):
            raise ValueError(
                "growth_rate_override and growth_rate_override_reason must be "
                "supplied together (a manual override always needs a documented reason)."
            )
        return self


class CellDivisionUpdate(BaseModel):
    """Payload for updating an existing division record."""

    experimental_batch: Optional[str] = Field(default=None, min_length=1, max_length=64)
    replicate: Optional[int] = Field(default=None, ge=1, le=50)
    experimental_condition: Optional[str] = Field(default=None, min_length=1, max_length=128)
    medium: Optional[str] = Field(default=None, min_length=1, max_length=128)
    temperature_celsius: Optional[float] = Field(default=None, ge=-10.0, le=100.0)
    generation: Optional[int] = Field(default=None, ge=1, le=1000)

    division_start_time: Optional[datetime] = None
    division_end_time: Optional[datetime] = None
    cell_cycle_duration_hours: Optional[float] = Field(default=None, gt=0.0, le=200.0)

    duration_override_minutes: Optional[float] = Field(
        default=None,
        ge=0.0,
        description=(
            "Explicit manual override for division duration, in minutes. When "
            "provided, duration_override_reason must be provided in the same "
            "request. Send both as null to clear a previously-set override."
        ),
    )
    duration_override_reason: Optional[str] = Field(default=None, max_length=256)
    growth_rate_override: Optional[float] = Field(
        default=None,
        ge=0.0,
        description=(
            "Explicit manual override for specific growth rate mu (hr^-1). When "
            "provided, growth_rate_override_reason must be provided in the same "
            "request. Send both as null to clear a previously-set override."
        ),
    )
    growth_rate_override_reason: Optional[str] = Field(default=None, max_length=256)

    is_outlier: Optional[bool] = None
    quality_flag: Optional[str] = Field(default=None, max_length=32)
    notes: Optional[str] = None
    metadata_json: Optional[str] = None

    @model_validator(mode="after")
    def validate_updated_timestamps(self) -> "CellDivisionUpdate":
        # NOTE: this only catches the case where BOTH timestamps are supplied
        # in the same request. Validating the FINAL merged record (existing +
        # partial update) against the current DB state happens in
        # DivisionService.update_division, since that is the only place the
        # existing record is available.
        if self.division_start_time and self.division_end_time:
            if self.division_end_time < self.division_start_time:
                raise ValueError("division_end_time cannot precede division_start_time")
        return self

    @model_validator(mode="after")
    def validate_override_pairs(self) -> "CellDivisionUpdate":
        fields_set = self.model_fields_set
        if "duration_override_minutes" in fields_set or "duration_override_reason" in fields_set:
            if (self.duration_override_minutes is None) != (self.duration_override_reason is None):
                raise ValueError(
                    "duration_override_minutes and duration_override_reason must be "
                    "updated together (both set to clear, or both provided to override)."
                )
        if "growth_rate_override" in fields_set or "growth_rate_override_reason" in fields_set:
            if (self.growth_rate_override is None) != (self.growth_rate_override_reason is None):
                raise ValueError(
                    "growth_rate_override and growth_rate_override_reason must be "
                    "updated together (both set to clear, or both provided to override)."
                )
        return self


class CellDivisionResponse(CellDivisionBase):
    """Serialized division record response with biological computed metrics."""

    id: int

    # Official stored values actually used by QC/analytics/sorting: equal to
    # the calculated_* values below unless an explicit override was supplied.
    division_duration_minutes: float
    growth_rate: float

    # Always-present calculated values, so a caller can see the raw
    # calculation even when an override is active.
    calculated_duration_minutes: Optional[float] = None
    calculated_growth_rate: Optional[float] = None

    duration_override_minutes: Optional[float] = None
    duration_override_reason: Optional[str] = None
    growth_rate_override: Optional[float] = None
    growth_rate_override_reason: Optional[str] = None

    is_outlier: bool
    quality_flag: str
    created_at: datetime
    updated_at: datetime

    # Embedded biological context if joined
    organism: Optional[str] = None
    cell_type: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
