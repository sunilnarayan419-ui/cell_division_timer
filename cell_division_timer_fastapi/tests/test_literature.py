"""Integration tests for the GET /api/v1/literature/search endpoint.

The NCBIService dependency is overridden with a fake implementation so these
tests run without any real NCBI credentials or network access.
"""

from typing import Optional

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_ncbi_service
from app.main import app
from app.schemas.literature import LiteratureArticle
from app.services.ncbi_service import NCBIConfigurationError, NCBIUpstreamError


class _FakeNCBIService:
    """Stand-in for NCBIService that never makes a real HTTP request."""

    def __init__(self, behavior: str = "success"):
        self.behavior = behavior

    async def search_pubmed_articles(
        self, query: str, retmax: Optional[int] = None, include_abstracts: bool = False
    ) -> dict:
        if self.behavior == "not_configured":
            raise NCBIConfigurationError("NCBI integration is not configured.")
        if self.behavior == "upstream_error":
            raise NCBIUpstreamError("NCBI E-utilities returned an error (HTTP 500).", status_code=502)
        if self.behavior == "empty":
            return {
                "query": query,
                "count": 0,
                "total_available": 0,
                "articles": [],
                "source": "NCBI PubMed (E-utilities)",
            }

        return {
            "query": query,
            "count": 1,
            "total_available": 1,
            "articles": [
                LiteratureArticle(
                    pmid="12345678",
                    title="Kinetics of Cell Division in Budding Yeast",
                    authors=["Doe J"],
                    journal="Journal of Cell Biology",
                    publication_date="2023",
                    doi="10.1234/example.doi",
                    abstract=None,
                    pubmed_url="https://pubmed.ncbi.nlm.nih.gov/12345678/",
                )
            ],
            "source": "NCBI PubMed (E-utilities)",
        }


@pytest.fixture
def override_ncbi():
    """Factory fixture to override the NCBIService dependency for a single test."""

    def _apply(behavior: str = "success"):
        app.dependency_overrides[get_ncbi_service] = lambda: _FakeNCBIService(behavior)

    yield _apply
    app.dependency_overrides.pop(get_ncbi_service, None)


def test_literature_search_success(client: TestClient, override_ncbi) -> None:
    override_ncbi("success")
    response = client.get("/api/v1/literature/search", params={"query": "cell division kinetics"})

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "cell division kinetics"
    assert data["count"] == 1
    assert data["articles"][0]["pmid"] == "12345678"
    assert data["articles"][0]["doi"] == "10.1234/example.doi"
    # The NCBI API key must never be present anywhere in the response.
    assert "api_key" not in response.text
    assert "NCBI_API_KEY" not in response.text


def test_literature_search_empty_results(client: TestClient, override_ncbi) -> None:
    override_ncbi("empty")
    response = client.get("/api/v1/literature/search", params={"query": "an extremely unlikely query xyz123"})

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert data["articles"] == []


def test_literature_search_missing_configuration(client: TestClient, override_ncbi) -> None:
    override_ncbi("not_configured")
    response = client.get("/api/v1/literature/search", params={"query": "cell division"})

    assert response.status_code == 503
    assert "detail" in response.json()


def test_literature_search_upstream_error(client: TestClient, override_ncbi) -> None:
    override_ncbi("upstream_error")
    response = client.get("/api/v1/literature/search", params={"query": "cell division"})

    assert response.status_code == 502


def test_literature_search_requires_query_param(client: TestClient, override_ncbi) -> None:
    override_ncbi("success")
    response = client.get("/api/v1/literature/search")
    assert response.status_code == 422


def test_literature_search_retmax_bounds(client: TestClient, override_ncbi) -> None:
    override_ncbi("success")
    response = client.get(
        "/api/v1/literature/search",
        params={"query": "cell division", "retmax": 500},
    )
    assert response.status_code == 422
