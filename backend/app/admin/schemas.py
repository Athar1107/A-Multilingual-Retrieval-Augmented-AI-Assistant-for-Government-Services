"""Pydantic models for the operational admin API."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class OverviewResponse(BaseModel):
    total_queries: int
    queries_24h: int
    avg_latency_ms: float | None
    p95_latency_ms: float | None
    avg_stage_latency_ms: dict[str, float | None]
    route_distribution: dict[str, int]
    fallback_rate: float | None
    error_rate: float | None
    avg_confidence: float | None
    uptime_seconds: float
    corpus_documents: int
    corpus_chunks: int
    queries_per_hour: list[dict[str, int]]
    confidence_histogram: list[dict[str, float | int]]


class QueryLogItem(BaseModel):
    id: str
    ts: float
    language: str | None
    query_preview: str | None
    route: str | None
    confidence: float | None
    translator_backend: str | None
    retrieved_doc_ids: list[str]
    latency_ms: float | None
    latency_translate_in_ms: float | None = None
    latency_retrieve_ms: float | None = None
    latency_generate_ms: float | None = None
    latency_translate_out_ms: float | None = None
    status: str | None
    error_type: str | None
    source: str | None = None


class QueryListResponse(BaseModel):
    items: list[QueryLogItem]
    total: int
    limit: int
    offset: int


class SourceCorpusCard(BaseModel):
    source: str
    documents: int
    chunks: int


class CorpusDocument(BaseModel):
    doc_id: str
    title: str
    source_url: str
    chunk_count: int
    source: str


class CorpusListResponse(BaseModel):
    sources: list[SourceCorpusCard]
    documents: list[CorpusDocument]
    total_documents: int
    total_chunks: int


class CorpusChunk(BaseModel):
    chunk_id: str
    chunk_index: int | None
    text: str
    title: str | None = None
    source_url: str | None = None


class CorpusDocumentDetail(BaseModel):
    doc_id: str
    title: str | None
    source_url: str | None
    chunks: list[CorpusChunk]


class EvalRunSummary(BaseModel):
    name: str
    scorer_version: str | None
    summary: dict[str, Any] = Field(default_factory=dict)


class EvalRunDetail(BaseModel):
    name: str
    scorer_version: str | None
    summary: dict[str, Any]
    results: list[dict[str, Any]]


class SystemHealth(BaseModel):
    name: str
    ok: bool
    detail: str


class SystemResponse(BaseModel):
    models: dict[str, str]
    translator_backend: str
    thresholds: dict[str, float | int | bool]
    health: list[SystemHealth]


class DebugQueryRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2_000)
    language: Literal["en", "kok"] | None = None


class DebugChunk(BaseModel):
    doc_id: str | None
    title: str | None
    content: str
    dense_score: float | None
    bm25_score: float | None
    fused_score: float | None
    source_url: str | None = None


class DebugQueryResponse(BaseModel):
    translated_query: str
    hints_applied: list[str]
    chunks: list[DebugChunk]
    confidence: float
    route: str
    route_reason: str
    answer: str
    latencies_ms: dict[str, float]
    translator_backend: str | None = None
    source: Literal["admin"] = "admin"


class ReindexRequest(BaseModel):
    confirm: bool


class ReindexStatus(BaseModel):
    running: bool
    started_at: float | None = None
    finished_at: float | None = None
    error: str | None = None
    chunk_count: int | None = None
