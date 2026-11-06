"""Request and response models shared by the API and RAG pipeline."""

from __future__ import annotations

import re
from typing import Any, Literal

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
    conversation_id: str | None = Field(
        default=None,
        description="Optional conversation ID to append this exchange to logged-in user history.",
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
    conversation_id: str | None = None
    fallback_path_used: str = "none"
    translated_query: str | None = None
    english_answer: str | None = None
    retrieved_chunks: list[str] = Field(default_factory=list)


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


# ---------------------------------------------------------------------------
# User Authentication & Chat History Schemas
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=128)
    full_name: str = Field(min_length=1, max_length=100)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class GoogleAuthRequest(BaseModel):
    credential: str = Field(description="Google ID Token from Google Identity Services or dev token")
    email: str | None = Field(default=None, description="Optional email for Google sign in")
    name: str | None = Field(default=None, description="Optional full name for Google sign in")


class UserResponse(BaseModel):
    id: str
    username: str
    full_name: str
    role: str


class AuthResponse(BaseModel):
    token: str
    user: UserResponse


class ConversationCreateRequest(BaseModel):
    title: str = Field(default="New Scheme Consultation", max_length=100)


class MessageResponse(BaseModel):
    id: str
    role: str
    text: str
    language: str | None = "en"
    confidence: float | None = None
    route: str | None = None
    sources: list[dict[str, Any]] = Field(default_factory=list)
    created_at: str


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int = 0


class ConversationDetailResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: list[MessageResponse]
