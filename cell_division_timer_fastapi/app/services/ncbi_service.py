"""NCBI E-utilities service."""

from typing import Any

import httpx

from app.core.config import get_settings


class NCBIService:
    """Client for interacting with NCBI E-utilities."""

    def __init__(self):
        self.settings = get_settings()

        self.base_url = self.settings.NCBI_BASE_URL

        self.common_params = {
            "tool": self.settings.NCBI_TOOL,
            "email": self.settings.NCBI_EMAIL,
        }

        # Only include API key when configured.
        if self.settings.NCBI_API_KEY:
            self.common_params["api_key"] = (
                self.settings.NCBI_API_KEY
            )

    async def search_pubmed(
        self,
        query: str,
        retmax: int | None = None,
    ) -> dict[str, Any]:
        """
        Search PubMed using NCBI ESearch.

        Args:
            query: PubMed/Entrez search query.
            retmax: Maximum number of PMIDs to return.

        Returns:
            Raw NCBI ESearch JSON response.
        """

        if retmax is None:
            retmax = self.settings.NCBI_DEFAULT_RETMAX

        params = {
            **self.common_params,
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": retmax,
        }

        async with httpx.AsyncClient(
            timeout=self.settings.NCBI_TIMEOUT
        ) as client:

            response = await client.get(
                f"{self.base_url}/esearch.fcgi",
                params=params,
            )

            response.raise_for_status()

            return response.json()


async def get_pubmed_summaries(
    self,
    pmids: list[str],
) -> dict[str, Any]:
    """
    Retrieve PubMed document summaries using ESummary.
    """

    if not pmids:
        return {}

    params = {
        **self.common_params,
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "json",
    }

    async with httpx.AsyncClient(
        timeout=self.settings.NCBI_TIMEOUT
    ) as client:

        response = await client.get(
            f"{self.base_url}/esummary.fcgi",
            params=params,
        )

        response.raise_for_status()

        return response.json()

async def search_pubmed_articles(
    self,
    query: str,
    retmax: int | None = None,
) -> dict[str, Any]:
    """
    Search PubMed and retrieve article summaries.
    """

    search_result = await self.search_pubmed(
        query=query,
        retmax=retmax,
    )

    pmids = (
        search_result
        .get("esearchresult", {})
        .get("idlist", [])
    )

    if not pmids:
        return {
            "query": query,
            "count": 0,
            "articles": [],
        }

    summaries = await self.get_pubmed_summaries(
        pmids
    )

    return {
        "query": query,
        "count": len(pmids),
        "pmids": pmids,
        "summaries": summaries,
    }