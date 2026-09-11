"""Common reusable schemas and response models."""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Application and database health check payload."""

    status: str = Field(..., examples=["healthy"])
    app_name: str
    version: str
    environment: str
    timestamp: datetime
    database: Dict[str, Any]


class MessageResponse(BaseModel):
    """Generic informative API response."""

    message: str
    success: bool = True
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standard error response model."""

    detail: str
    code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
