"""System and database connectivity health endpoints."""

from datetime import datetime
from fastapi import APIRouter, Response, status
from app.core.config import get_settings
from app.core.database import check_db_health
from app.schemas.common import HealthResponse

router = APIRouter()
settings = get_settings()


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["System Health"],
    summary="Application & Database Health Check",
    description="Returns live operational status of the API, runtime environment, and active database connection latency.",
)
def health_check(response: Response) -> HealthResponse:
    """Check application readiness and database connectivity."""
    db_health = check_db_health()
    overall_status = "healthy" if db_health.get("connected") else "degraded"

    if overall_status != "healthy":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status=overall_status,
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        timestamp=datetime.utcnow(),
        database=db_health,
    )
