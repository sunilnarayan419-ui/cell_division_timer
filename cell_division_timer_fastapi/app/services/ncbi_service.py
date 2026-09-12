"""NCBI E-utilities service.

Provides a clean, backend-only client for querying PubMed literature via the
NCBI E-utilities API (ESearch -> ESummary -> optional EFetch), with
normalization into application-level response objects.

Security:
    The NCBI API key is read exclusively from application settings
    (environment variables / .env). It is never logged, never returned to
    the caller, and never exposed to the frontend.
"""

from __future__ import annotations

import logging
from typing import Any, Optional
from xml.etree import ElementTree

import httpx

from app.core.config import get_settings
from app.schemas.literature import LiteratureArticle

logger = logging.getLogger("cell_division_timer.ncbi")


class NCBIServiceError(Exception):
    """Base exception for NCBI service failures.

    Carries a safe, user-facing ``detail`` message (never containing
    secrets or raw upstream payloads) and an HTTP-status-like ``status_code``
    hint that the API layer can use when translating to an HTTPException.
    """

    def __init__(self, detail: str, status_code: int = 502) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class NCBIConfigurationError(NCBIServiceError):
    """Raised when required NCBI configuration (e.g. API key) is missing."""

    def __init__(self, detail: str) -> None:
        super().__init__(detail, status_code=503)


class NCBIUpstreamError(NCBIServiceError):
    """Raised when the NCBI API returns an error, times out, or is unreachable."""


class NCBIService:
    """Client for interacting with NCBI E-utilities (ESearch, ESummary, EFetch)."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_url = self.settings.NCBI_BASE_URL.rstrip("/")

        self.common_params: dict[str, str] = {
            "tool": self.settings.NCBI_TOOL,
        }
        if self.settings.NCBI_EMAIL:
            self.common_params["email"] = self.settings.NCBI_EMAIL

        # Only include the API key when configured. Never logged.
        if self.settings.NCBI_API_KEY:
            self.common_params["api_key"] = self.settings.NCBI_API_KEY

    @property
    def is_configured(self) -> bool:
        """Whether an NCBI API key has been supplied via environment configuration."""
        return bool(self.settings.NCBI_API_KEY)

    def _require_configuration(self) -> None:
        if not self.is_configured:
            raise NCBIConfigurationError(
                "NCBI integration is not configured. Set NCBI_API_KEY (and ideally "
                "NCBI_EMAIL) in the backend .env file to enable literature search."
            )

    async def _get_json(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        """Issue a GET request against an E-utilities JSON endpoint with unified error handling."""
        url = f"{self.base_url}/{endpoint}"
        try:
            async with httpx.AsyncClient(timeout=self.settings.NCBI_TIMEOUT) as client:
                response = await client.get(url, params=params)
        except httpx.TimeoutException as exc:
            logger.error("NCBI request to %s timed out", endpoint)
            raise NCBIUpstreamError(
                "The NCBI E-utilities service did not respond in time. Please try again.",
                status_code=504,
            ) from exc
        except httpx.RequestError as exc:
            logger.error("NCBI request to %s failed: %s", endpoint, exc.__class__.__name__)
            raise NCBIUpstreamError(
                "Unable to reach the NCBI E-utilities service.",
                status_code=502,
            ) from exc

        if response.status_code == 429:
            logger.warning("NCBI rate limit hit on %s", endpoint)
            raise NCBIUpstreamError(
                "NCBI rate limit exceeded. Please slow down requests and try again shortly.",
                status_code=429,
            )
        if response.status_code >= 400:
            logger.error("NCBI returned HTTP %s for %s", response.status_code, endpoint)
            raise NCBIUpstreamError(
                f"NCBI E-utilities returned an error (HTTP {response.status_code}).",
                status_code=502,
            )

        try:
            return response.json()
        except ValueError as exc:
            logger.error("NCBI returned a non-JSON/malformed response from %s", endpoint)
            raise NCBIUpstreamError(
                "Received a malformed response from NCBI E-utilities.",
                status_code=502,
            ) from exc

    async def search_pubmed(self, query: str, retmax: Optional[int] = None) -> dict[str, Any]:
        """Search PubMed using NCBI ESearch and return the raw ESearch JSON payload."""
        self._require_configuration()

        if not query or not query.strip():
            raise NCBIServiceError("Search query must not be empty.", status_code=400)

        if retmax is None:
            retmax = self.settings.NCBI_DEFAULT_RETMAX

        params = {
            **self.common_params,
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": retmax,
        }
        return await self._get_json("esearch.fcgi", params)

    async def get_pubmed_summaries(self, pmids: list[str]) -> dict[str, Any]:
        """Retrieve PubMed document summaries for a list of PMIDs using ESummary."""
        if not pmids:
            return {}

        self._require_configuration()

        params = {
            **self.common_params,
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "json",
        }
        return await self._get_json("esummary.fcgi", params)

    async def get_pubmed_abstracts(self, pmids: list[str]) -> dict[str, str]:
        """Retrieve plain-text abstracts for a list of PMIDs using EFetch.

        Returns a mapping of ``{pmid: abstract_text}``. PMIDs without an
        available abstract are omitted rather than raising an error, since a
        missing abstract should not fail the overall search.
        """
        if not pmids:
            return {}

        self._require_configuration()

        params = {
            **self.common_params,
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "rettype": "abstract",
        }
        url = f"{self.base_url}/efetch.fcgi"

        try:
            async with httpx.AsyncClient(timeout=self.settings.NCBI_TIMEOUT) as client:
                response = await client.get(url, params=params)
        except httpx.TimeoutException:
            logger.warning("NCBI EFetch timed out; continuing without abstracts")
            return {}
        except httpx.RequestError:
            logger.warning("NCBI EFetch request failed; continuing without abstracts")
            return {}

        if response.status_code >= 400:
            logger.warning("NCBI EFetch returned HTTP %s; continuing without abstracts", response.status_code)
            return {}

        try:
            root = ElementTree.fromstring(response.text)
        except ElementTree.ParseError:
            logger.warning("NCBI EFetch returned malformed XML; continuing without abstracts")
            return {}

        abstracts: dict[str, str] = {}
        for article in root.findall(".//PubmedArticle"):
            pmid_el = article.find(".//PMID")
            if pmid_el is None or not pmid_el.text:
                continue
            pmid = pmid_el.text.strip()

            texts = [
                (node.text or "").strip()
                for node in article.findall(".//Abstract/AbstractText")
            ]
            texts = [t for t in texts if t]
            if texts:
                abstracts[pmid] = " ".join(texts)

        return abstracts

    @staticmethod
    def _normalize_summary(pmid: str, doc: dict[str, Any]) -> LiteratureArticle:
        """Convert a raw ESummary document into a normalized LiteratureArticle."""
        authors = [
            a.get("name", "")
            for a in doc.get("authors", [])
            if isinstance(a, dict) and a.get("name")
        ]

        doi: Optional[str] = None
        for article_id in doc.get("articleids", []):
            if isinstance(article_id, dict) and article_id.get("idtype") == "doi":
                doi = article_id.get("value")
                break

        return LiteratureArticle(
            pmid=pmid,
            title=doc.get("title") or None,
            authors=authors,
            journal=doc.get("fulljournalname") or doc.get("source") or None,
            publication_date=doc.get("pubdate") or None,
            doi=doi,
            abstract=None,
            pubmed_url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        )

    async def search_pubmed_articles(
        self,
        query: str,
        retmax: Optional[int] = None,
        include_abstracts: bool = False,
    ) -> dict[str, Any]:
        """Search PubMed and return normalized article metadata.

        Workflow: ESearch -> PMIDs -> ESummary -> normalized articles,
        optionally enriched with EFetch abstracts.
        """
        search_result = await self.search_pubmed(query=query, retmax=retmax)

        pmids = search_result.get("esearchresult", {}).get("idlist", [])
        total_available_raw = search_result.get("esearchresult", {}).get("count", "0")
        try:
            total_available = int(total_available_raw)
        except (TypeError, ValueError):
            total_available = len(pmids)

        if not pmids:
            return {
                "query": query,
                "count": 0,
                "total_available": total_available,
                "articles": [],
                "source": "NCBI PubMed (E-utilities)",
            }

        summaries_payload = await self.get_pubmed_summaries(pmids)
        summary_result = summaries_payload.get("result", {}) if summaries_payload else {}

        abstracts: dict[str, str] = {}
        if include_abstracts:
            abstracts = await self.get_pubmed_abstracts(pmids)

        articles: list[LiteratureArticle] = []
        for pmid in pmids:
            doc = summary_result.get(pmid)
            if not isinstance(doc, dict):
                # Skip PMIDs NCBI could not summarize (invalid/withdrawn records)
                # rather than failing the entire search.
                continue
            article = self._normalize_summary(pmid, doc)
            if pmid in abstracts:
                article.abstract = abstracts[pmid]
            articles.append(article)

        return {
            "query": query,
            "count": len(articles),
            "total_available": total_available,
            "articles": articles,
            "source": "NCBI PubMed (E-utilities)",
        }
