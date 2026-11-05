"""Request and response models shared by the API and RAG pipeline."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


def detect_query_language(text: str) -> Literal["en", "kok"]:
    """Detect whether query contains Devanagari script (Goan Konkani) or Latin (English)."""
    if re.search(r"[\u0900-\u097F]", text):
        return "kok"
    return "en"


class QueryRequest(BaseModel):
    """A citizen query in Konkani or English with optional language auto-detection."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    text: str = Field(min_length=1, max_length=2_000)
    language: Literal["en", "kok"] | None = Field(
        default=None,
        description="Query language: 'en' (English), 'kok' (Goan Konkani), or None for auto-detection.",
    )

    @field_validator("text")
    @classmethod
    def reject_empty_after_normalisation(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Query text cannot be blank")
        return value

    def resolve_language(self) -> Literal["en", "kok"]:
        """Return explicit language override if provided, otherwise auto-detect."""
        if self.language is not None:
            return self.language
        return detect_query_language(self.text)


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
    translator_backend: str | None = None
    retrieval_hint_applied: bool = False
    retrieved_doc_ids: list[str] = Field(default_factory=list)


class SourceCorpusStats(BaseModel):
    documents: int
    chunks: int


class AdminStatsResponse(BaseModel):
    """System analytics and corpus telemetry for administrators."""

    uptime_seconds: float
    query_count: int
    translator_backend: str
    corpus: dict[str, SourceCorpusStats]
    total_documents: int
    total_chunks: int
    route_distribution: dict[str, int]
