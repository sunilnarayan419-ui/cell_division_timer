"""Main FastAPI application entrypoint."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import api_router
from app.api.routes.health import router as health_router
from app.api.v2 import api_router_v2
from app.core.config import get_settings
from app.core.database import check_db_health
from app.core.logging import logger
from app.core.middleware import APIVersioningMiddleware
from app.services.ncbi_service import close_ncbi_http_client

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup and shutdown hooks.

    Database schema management is owned exclusively by Alembic
    (``alembic upgrade head``), not by the application process. Running
    ``Base.metadata.create_all()`` here as well as maintaining Alembic
    migrations is an architectural inconsistency: the two can silently
    diverge (e.g. a column added in a migration but never applied because
    create_all() already "satisfied" SQLAlchemy for tables that already
    exist). Startup here only *verifies* connectivity and logs a clear
    error if migrations have not been applied; it never creates or alters
    tables. (`Base.metadata.create_all()` is still used, deliberately, by
    the isolated in-memory test database in tests/conftest.py.)
    """
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.APP_ENV}]")
    health = check_db_health()
    if health["status"] == "healthy":
        logger.info(f"Database connectivity verified ({health['dialect']}, {health['latency_ms']}ms)")
    else:
        logger.error(
            "Database is not reachable at startup. Ensure the database is running and "
            f"that migrations have been applied (`alembic upgrade head`). Detail: {health.get('error')}"
        )

    yield

    await close_ncbi_http_client()
    logger.info("Shutting down Cell Division Timer API gracefully")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "**Cell Division Timer** is a production biotechnology life-sciences backend platform "
        "for tracking, modeling, and analyzing cell-cycle and mitotic division dynamics across "
        "experimental conditions, temperature gradients, and cellular generations."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    lifespan=lifespan,
)

# Configure Cross-Origin Resource Sharing (CORS)
# Note: browsers reject `allow_credentials=True` combined with a wildcard
# origin, so credentials are only enabled when explicit origins are configured.
_cors_allows_credentials = "*" not in settings.CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=_cors_allows_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Versioning & Header-Based Routing Middleware
app.add_middleware(
    APIVersioningMiddleware,
    default_version=settings.DEFAULT_API_VERSION,
)


# Global Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Provide clean, structured error responses for Pydantic validation failures."""
    errors = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err.get("loc", []))
        errors.append(f"{field}: {err.get('msg')}")
    error_message = "; ".join(errors)
    logger.warning(f"Validation error on {request.method} {request.url.path}: {error_message}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": error_message,
            "code": "VALIDATION_ERROR",
            "errors": jsonable_encoder(exc.errors()),
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all exception handler to prevent unhandled internal leakages."""
    logger.error(f"Unhandled internal server error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred while processing the request",
            "code": "INTERNAL_SERVER_ERROR",
        },
    )


# Mount routers
app.include_router(health_router)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
app.include_router(api_router_v2, prefix=settings.API_V2_PREFIX)


@app.get("/", tags=["General"], summary="Root API Directory")
def root_info() -> dict:
    """API root metadata, versioning guidelines, and documentation links."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "documentation": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "versions": {
            "v1": {
                "prefix": settings.API_V1_PREFIX,
                "status": "stable",
                "lifecycle": "production",
                "description": "Standard biological cell and division kinetics API",
            },
            "v2-beta": {
                "prefix": settings.API_V2_PREFIX,
                "status": "beta",
                "lifecycle": "active-development",
                "status_endpoint": f"{settings.API_V2_PREFIX}/beta/status",
                "description": "Enhanced subphase resolution, batch analysis, and Arrhenius predictive modeling",
            },
        },
        "versioning": {
            "default_version": settings.DEFAULT_API_VERSION,
            "supported_versions": settings.SUPPORTED_API_VERSIONS,
            "header_routing": {
                "header": "X-API-Version",
                "accepted_values": ["1", "v1", "2", "v2", "2-beta"],
                "vendor_accept": "Accept: application/vnd.celldivision.v2+json",
                "query_parameter": "?api-version=2",
            },
        },
        "message": "Cell Division Timer - Biotechnology Life-Sciences Platform Active",
    }
