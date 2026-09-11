"""Cell / Sample Pydantic validation schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CellBase(BaseModel):
    """Base biological attributes for a cell/sample."""

    name: str = Field(..., min_length=1, max_length=128, examples=["BY4741 Wild Type"])
    organism: str = Field(..., min_length=1, max_length=128, examples=["Saccharomyces cerevisiae"])
    cell_type: str = Field(..., min_length=1, max_length=128, examples=["Budding yeast"])
    passage_number: Optional[int] = Field(default=1, ge=0, le=500, examples=[4])
    source_line: Optional[str] = Field(default=None, max_length=128, examples=["ATCC 204508"])
    description: Optional[str] = Field(default=None, examples=["Haploid laboratory strain BY4741"])


class CellCreate(CellBase):
    """Payload for registering a new cell line / biological sample."""

    id: str = Field(
        ...,
        min_length=2,
        max_length=64,
        pattern=r"^[A-Za-z0-9_\-]+$",
        examples=["CELL-SC-001"],
        description="Unique alphanumeric identifier for the biological sample",
    )


class CellUpdate(BaseModel):
    """Payload for partially modifying a registered cell line."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=128)
    organism: Optional[str] = Field(default=None, min_length=1, max_length=128)
    cell_type: Optional[str] = Field(default=None, min_length=1, max_length=128)
    passage_number: Optional[int] = Field(default=None, ge=0, le=500)
    source_line: Optional[str] = Field(default=None, max_length=128)
    description: Optional[str] = Field(default=None)


class CellResponse(CellBase):
    """Serialized cell line response."""

    id: str
    created_at: datetime
    updated_at: datetime
    division_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)
