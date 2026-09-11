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
    """Payload for creating a cell division record."""

    # Optional manual overrides; if omitted, computed automatically using domain formulas
    division_duration_minutes: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Active division duration in minutes (computed automatically if omitted)",
    )
    growth_rate: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Specific growth rate mu in hr^-1 (computed automatically if omitted)",
    )

    @model_validator(mode="after")
    def validate_division_timestamps(self) -> "CellDivisionCreate":
        if self.division_end_time < self.division_start_time:
            raise ValueError(
                f"division_end_time ({self.division_end_time}) cannot be earlier than "
                f"division_start_time ({self.division_start_time})"
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

    is_outlier: Optional[bool] = None
    quality_flag: Optional[str] = Field(default=None, max_length=32)
    notes: Optional[str] = None
    metadata_json: Optional[str] = None

    @model_validator(mode="after")
    def validate_updated_timestamps(self) -> "CellDivisionUpdate":
        if self.division_start_time and self.division_end_time:
            if self.division_end_time < self.division_start_time:
                raise ValueError("division_end_time cannot precede division_start_time")
        return self


class CellDivisionResponse(CellDivisionBase):
    """Serialized division record response with biological computed metrics."""

    id: int
    division_duration_minutes: float
    growth_rate: float
    is_outlier: bool
    quality_flag: str
    created_at: datetime
    updated_at: datetime

    # Embedded biological context if joined
    organism: Optional[str] = None
    cell_type: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
