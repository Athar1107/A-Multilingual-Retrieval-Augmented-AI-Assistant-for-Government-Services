"""Request and response models shared by the API and RAG pipeline."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class QueryRequest(BaseModel):
    """A citizen query in Konkani or another supported input language."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    text: str = Field(min_length=1, max_length=2_000)
    language: Literal["en", "kok"] = Field(
        default="en",
        description="Supported query language: 'en' (English) or 'kok' (Goan Konkani).",
    )

    @field_validator("text")
    @classmethod
    def reject_empty_after_normalisation(cls, value: str) -> str:
        if not value:
            raise ValueError("Query text cannot be blank")
        return value


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
