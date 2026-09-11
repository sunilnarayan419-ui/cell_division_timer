from pydantic import BaseModel


class LiteratureArticle(BaseModel):
    pmid: str
    title: str | None = None
    authors: list[str] = []
    journal: str | None = None
    publication_date: str | None = None
    doi: str | None = None
    abstract: str | None = None
    pubmed_url: str | None = None