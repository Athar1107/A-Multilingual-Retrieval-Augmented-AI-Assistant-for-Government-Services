"""Request and response models shared by the API and RAG pipeline."""

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """A citizen query in Konkani or another supported input language."""

    text: str = Field(min_length=1, max_length=2_000)
    language: str = Field(
        default="en",
        description="ISO 639-1 language code for the query (e.g. 'en', 'kok', 'mr')",
    )


class SourceCitation(BaseModel):
    """Provenance for a passage used to answer a query."""

    title: str
    source_url: str


class QueryResponse(BaseModel):
    """The response contract for a grounded answer."""

    query: str
    answer: str
    confidence: float
    route: str = "direct"
    sources: list[SourceCitation]
