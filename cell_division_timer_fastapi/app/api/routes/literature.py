"""PubMed / NCBI literature evidence endpoints.

Dependency direction: API -> NCBIService -> HTTPX -> NCBI E-utilities.
This router does not depend on the database, AnalyticsService, or any other
unrelated service, keeping the external-API integration cleanly isolated.
"""

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import NCBIServiceDep
from app.schemas.common import ErrorResponse
from app.schemas.literature import LiteratureSearchResponse
from app.services.ncbi_service import NCBIServiceError

router = APIRouter()


@router.get(
    "/search",
    response_model=LiteratureSearchResponse,
    summary="Search PubMed Literature via NCBI E-utilities",
    description=(
        "Searches PubMed for supporting literature evidence using the NCBI E-utilities "
        "API (ESearch -> ESummary). Requires a backend NCBI_API_KEY to be configured; "
        "the key is never exposed to clients."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Invalid or empty query"},
        502: {"model": ErrorResponse, "description": "NCBI E-utilities error or malformed response"},
        503: {"model": ErrorResponse, "description": "NCBI integration not configured"},
        504: {"model": ErrorResponse, "description": "NCBI E-utilities request timed out"},
    },
)
async def search_literature(
    service: NCBIServiceDep,
    query: str = Query(..., min_length=1, description="PubMed/Entrez search query", examples=["cell division kinetics"]),
    retmax: int = Query(10, ge=1, le=100, description="Maximum number of articles to return"),
    include_abstracts: bool = Query(
        False,
        description="Also fetch abstracts via EFetch (slower; one extra NCBI request)",
    ),
) -> LiteratureSearchResponse:
    """Search PubMed and return normalized article metadata for the given query."""
    try:
        result = await service.search_pubmed_articles(
            query=query,
            retmax=retmax,
            include_abstracts=include_abstracts,
        )
    except NCBIServiceError as exc:
        # Never leak raw NCBI payloads, credentials, or internal exception details.
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    return LiteratureSearchResponse(**result)
