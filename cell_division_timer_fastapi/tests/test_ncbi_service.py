"""Unit tests for NCBIService.

These tests never contact the real NCBI API and never require a real
NCBI_API_KEY: all HTTP calls are mocked via `respx`, and configuration is
injected through a fake settings object rather than the environment.
"""

from types import SimpleNamespace

import httpx
import pytest
import respx

from app.services.ncbi_service import (
    NCBIConfigurationError,
    NCBIService,
    NCBIUpstreamError,
)


def make_settings(**overrides) -> SimpleNamespace:
    """Build a minimal fake settings object with sane NCBI defaults."""
    defaults = dict(
        NCBI_API_KEY="TEST-FAKE-KEY-NOT-REAL",
        NCBI_TOOL="cell_division_timer_tests",
        NCBI_EMAIL="tests@example.com",
        NCBI_BASE_URL="https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
        NCBI_DEFAULT_RETMAX=10,
        NCBI_TIMEOUT=5.0,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_service(monkeypatch: pytest.MonkeyPatch, **settings_overrides) -> NCBIService:
    settings = make_settings(**settings_overrides)
    monkeypatch.setattr("app.services.ncbi_service.get_settings", lambda: settings)
    return NCBIService()


ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"


@pytest.mark.asyncio
async def test_missing_api_key_raises_configuration_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """A missing NCBI_API_KEY should fail fast with a clear, safe error."""
    service = make_service(monkeypatch, NCBI_API_KEY="")

    with pytest.raises(NCBIConfigurationError):
        await service.search_pubmed(query="cell division kinetics")


@pytest.mark.asyncio
async def test_empty_query_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """An empty search query should be rejected before any HTTP call is made."""
    service = make_service(monkeypatch)

    with pytest.raises(Exception):
        await service.search_pubmed(query="   ")


@pytest.mark.asyncio
@respx.mock
async def test_search_pubmed_articles_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Happy path: ESearch -> PMIDs -> ESummary -> normalized articles."""
    service = make_service(monkeypatch)

    respx.get(ESEARCH_URL).mock(
        return_value=httpx.Response(
            200,
            json={"esearchresult": {"count": "1", "idlist": ["12345678"]}},
        )
    )
    respx.get(ESUMMARY_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "result": {
                    "uids": ["12345678"],
                    "12345678": {
                        "title": "Kinetics of Cell Division in Budding Yeast",
                        "authors": [{"name": "Doe J"}, {"name": "Smith A"}],
                        "fulljournalname": "Journal of Cell Biology",
                        "pubdate": "2023",
                        "articleids": [
                            {"idtype": "doi", "value": "10.1234/example.doi"}
                        ],
                    },
                }
            },
        )
    )

    result = await service.search_pubmed_articles(query="cell division kinetics", retmax=5)

    assert result["count"] == 1
    assert result["source"] == "NCBI PubMed (E-utilities)"
    article = result["articles"][0]
    assert article.pmid == "12345678"
    assert article.title == "Kinetics of Cell Division in Budding Yeast"
    assert article.authors == ["Doe J", "Smith A"]
    assert article.doi == "10.1234/example.doi"
    assert article.pubmed_url == "https://pubmed.ncbi.nlm.nih.gov/12345678/"


@pytest.mark.asyncio
@respx.mock
async def test_search_pubmed_empty_results(monkeypatch: pytest.MonkeyPatch) -> None:
    """No matching PMIDs should return an empty, well-formed result (not an error)."""
    service = make_service(monkeypatch)

    respx.get(ESEARCH_URL).mock(
        return_value=httpx.Response(
            200,
            json={"esearchresult": {"count": "0", "idlist": []}},
        )
    )

    result = await service.search_pubmed_articles(query="an extremely unlikely query xyz123")

    assert result["count"] == 0
    assert result["articles"] == []


@pytest.mark.asyncio
@respx.mock
async def test_ncbi_http_error_is_wrapped(monkeypatch: pytest.MonkeyPatch) -> None:
    """A non-2xx NCBI response should raise a safe NCBIUpstreamError, not a raw exception."""
    service = make_service(monkeypatch)

    respx.get(ESEARCH_URL).mock(return_value=httpx.Response(500))

    with pytest.raises(NCBIUpstreamError):
        await service.search_pubmed(query="cell division")


@pytest.mark.asyncio
@respx.mock
async def test_ncbi_timeout_is_wrapped(monkeypatch: pytest.MonkeyPatch) -> None:
    """A network timeout should raise a safe NCBIUpstreamError with a 504 hint."""
    service = make_service(monkeypatch)

    respx.get(ESEARCH_URL).mock(side_effect=httpx.TimeoutException("timed out"))

    with pytest.raises(NCBIUpstreamError) as excinfo:
        await service.search_pubmed(query="cell division")
    assert excinfo.value.status_code == 504


@pytest.mark.asyncio
@respx.mock
async def test_ncbi_malformed_json_is_wrapped(monkeypatch: pytest.MonkeyPatch) -> None:
    """A malformed (non-JSON) NCBI response should not propagate a raw parsing exception."""
    service = make_service(monkeypatch)

    respx.get(ESEARCH_URL).mock(
        return_value=httpx.Response(200, text="<html>not json</html>")
    )

    with pytest.raises(NCBIUpstreamError):
        await service.search_pubmed(query="cell division")


@pytest.mark.asyncio
@respx.mock
async def test_invalid_pmid_summary_is_skipped_not_fatal(monkeypatch: pytest.MonkeyPatch) -> None:
    """A PMID that NCBI could not summarize should be skipped, not crash the whole search."""
    service = make_service(monkeypatch)

    respx.get(ESEARCH_URL).mock(
        return_value=httpx.Response(
            200,
            json={"esearchresult": {"count": "1", "idlist": ["99999999"]}},
        )
    )
    # ESummary result missing the requested PMID entirely (e.g. withdrawn record)
    respx.get(ESUMMARY_URL).mock(
        return_value=httpx.Response(200, json={"result": {"uids": []}})
    )

    result = await service.search_pubmed_articles(query="cell division")

    assert result["count"] == 0
    assert result["articles"] == []


def test_api_key_never_appears_in_repr_or_common_params_when_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When no key is configured, no api_key param should be attached to requests."""
    service = make_service(monkeypatch, NCBI_API_KEY="")
    assert "api_key" not in service.common_params
    assert service.is_configured is False


def test_api_key_included_in_params_when_present(monkeypatch: pytest.MonkeyPatch) -> None:
    """When a key is configured, it is attached to outgoing request params (never logged)."""
    service = make_service(monkeypatch, NCBI_API_KEY="some-key")
    assert service.common_params.get("api_key") == "some-key"
    assert service.is_configured is True
