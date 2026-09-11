"""API routes module."""

from fastapi import APIRouter
from app.api.routes import analytics, cells, data_transfer, divisions, health

api_router = APIRouter()

# Register resource routers
api_router.include_router(cells.router, prefix="/cells", tags=["Cells & Samples"])
api_router.include_router(divisions.router, prefix="/divisions", tags=["Cell Division Records"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Biotechnology Analytics"])
api_router.include_router(data_transfer.router, prefix="/data", tags=["Data Import & Export"])
