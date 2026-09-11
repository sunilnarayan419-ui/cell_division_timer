"""API v2 Beta router module."""

from fastapi import APIRouter
from app.api.routes import cells, data_transfer
from app.api.v2.routes import analytics as v2_analytics
from app.api.v2.routes import divisions as v2_divisions
from app.api.v2.routes import status as v2_status

api_router_v2 = APIRouter()

# Register v2 endpoints
api_router_v2.include_router(v2_status.router, prefix="/beta", tags=["v2 Beta Lifecycle"])
api_router_v2.include_router(v2_divisions.router, tags=["v2 Cell Division Records (Beta)"])
api_router_v2.include_router(v2_analytics.router, tags=["v2 Predictive Analytics (Beta)"])

# Mount core resource routers under v2 prefix to ensure full endpoint parity
api_router_v2.include_router(cells.router, prefix="/cells", tags=["v2 Cells & Samples (Beta)"])
api_router_v2.include_router(data_transfer.router, prefix="/data", tags=["v2 Data Import & Export (Beta)"])
