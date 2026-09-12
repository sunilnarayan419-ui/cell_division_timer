"""Pydantic schemas for PubMed / NCBI literature evidence responses."""

from typing import List, Optional

from pydantic import BaseModel, Field


class LiteratureArticle(BaseModel):
    """Normalized PubMed article metadata (NCBI internal fields are not exposed)."""

    pmid: str
    title: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    journal: Optional[str] = None
    publication_date: Optional[str] = None
    doi: Optional[str] = None
    abstract: Optional[str] = None
    pubmed_url: Optional[str] = None


class LiteratureSearchResponse(BaseModel):
    """Response envelope for a PubMed literature search."""

    query: str
    count: int = Field(..., description="Number of articles returned in this response")
    total_available: int = Field(0, description="Total matching records reported by NCBI")
    articles: List[LiteratureArticle] = Field(default_factory=list)
    source: str = "NCBI PubMed (E-utilities)"
