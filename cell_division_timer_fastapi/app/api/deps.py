"""FastAPI request dependencies and service providers."""

from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.analytics_service import AnalyticsService
from app.services.cell_service import CellService
from app.services.csv_service import CSVService
from app.services.division_service import DivisionService
from app.services.ncbi_service import NCBIService

# Annotated database session
DBSession = Annotated[Session, Depends(get_db)]


def get_cell_service(db: DBSession) -> CellService:
    """Provide initialized CellService instance."""
    return CellService(db)


def get_division_service(db: DBSession) -> DivisionService:
    """Provide initialized DivisionService instance."""
    return DivisionService(db)


def get_analytics_service(db: DBSession) -> AnalyticsService:
    """Provide initialized AnalyticsService instance."""
    return AnalyticsService(db)


def get_csv_service(db: DBSession) -> CSVService:
    """Provide initialized CSVService instance."""
    return CSVService(db)


def get_ncbi_service() -> NCBIService:
    """Provide initialized NCBIService instance.

    Deliberately has no database dependency: the literature/NCBI integration
    is an isolated external-API service, not tied to AnalyticsService or the
    persistence layer.
    """
    return NCBIService()


CellServiceDep = Annotated[CellService, Depends(get_cell_service)]
DivisionServiceDep = Annotated[DivisionService, Depends(get_division_service)]
AnalyticsServiceDep = Annotated[AnalyticsService, Depends(get_analytics_service)]
CSVServiceDep = Annotated[CSVService, Depends(get_csv_service)]
NCBIServiceDep = Annotated[NCBIService, Depends(get_ncbi_service)]
