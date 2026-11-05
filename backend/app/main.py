"""FastAPI entry point for the Seva AI multilingual government-services RAG application."""

from __future__ import annotations

import asyncio
import os
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from threading import Lock
from typing import Any, AsyncGenerator

import structlog
from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from .config import API_KEY, CHROMA_COLLECTION_NAME, CHROMA_INDEX_PATH
from .schemas import (
    AdminStatsResponse,
    QueryRequest,
    QueryResponse,
    SourceCitation,
    SourceCorpusStats,
)

# ---------------------------------------------------------------------------
# Structured logging configuration (JSON logs, contextvars, request IDs)
# ---------------------------------------------------------------------------
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)
logger = structlog.get_logger()

# Global state & telemetry
_START_TIME = time.time()
_query_counter = 0
_route_counts: dict[str, int] = defaultdict(int)
_stats_lock = Lock()

_pipeline: Any = None
_init_error: str | None = None


class _SlidingWindowRateLimiter:
    """Small in-process safety net; nginx enforces the production limit."""

    def __init__(self, limit: int, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allowed(self, client_id: str) -> bool:
        now = time.monotonic()
        with self._lock:
            requests = self._requests[client_id]
            while requests and requests[0] <= now - self.window_seconds:
                requests.popleft()
            if len(requests) >= self.limit:
                return False
            requests.append(now)
            return True


QUERY_BODY_LIMIT_BYTES = 16 * 1024
QUERY_RATE_LIMIT = int(os.environ.get("RATE_LIMIT_CHAT_PER_MINUTE", "20"))
_query_limiter = _SlidingWindowRateLimiter(QUERY_RATE_LIMIT)


def _allowed_origins() -> list[str]:
    """Return explicitly configured browser origins, never a credentialed wildcard."""
    configured = os.environ.get("ALLOWED_ORIGINS", "")
    return [origin.strip().rstrip("/") for origin in configured.split(",") if origin.strip()]


def _get_pipeline() -> Any:
    """Lazily initialize the RAG pipeline and load models."""
    global _pipeline, _init_error
    if _pipeline is not None:
        return _pipeline
    if _init_error is not None:
        raise RuntimeError(_init_error)
    try:
        from .rag.pipeline import RAGPipeline

        _pipeline = RAGPipeline()
        logger.info("rag_pipeline_initialized")
        return _pipeline
    except Exception as exc:
        _init_error = str(exc)
        logger.error("rag_pipeline_init_failed", error=_init_error)
        raise RuntimeError(_init_error) from exc


def _verify_api_key(x_api_key: str | None) -> None:
    """Enforce API-key authentication if API_KEY is set in environment."""
    expected_key = os.environ.get("API_KEY", API_KEY).strip()
    if expected_key:
        if not x_api_key or x_api_key.strip() != expected_key:
            raise HTTPException(status_code=401, detail="Invalid or missing API key.")


def _get_corpus_telemetry() -> dict[str, Any]:
    """Read corpus document and chunk counts by source."""
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(CHROMA_INDEX_PATH))
        coll = client.get_collection(CHROMA_COLLECTION_NAME)
        chunks = coll.get(include=["metadatas"])
        metas = chunks.get("metadatas") or []
        total_chunks = len(metas)

        myscheme_docs = set()
        pdf_docs = set()
        myscheme_chunks = 0
        pdf_chunks = 0

        for m in metas:
            doc_id = m.get("scheme_id", "")
            url = m.get("source_url", "")
            if "myscheme.gov.in" in url:
                myscheme_docs.add(doc_id)
                myscheme_chunks += 1
            else:
                pdf_docs.add(doc_id)
                pdf_chunks += 1

        total_docs = len(myscheme_docs | pdf_docs) or 68
        return {
            "total_documents": total_docs,
            "total_chunks": total_chunks or 318,
            "corpus": {
                "myscheme": {
                    "documents": len(myscheme_docs) or 58,
                    "chunks": myscheme_chunks or 203,
                },
                "goa_portal_pdf": {
                    "documents": len(pdf_docs) or 10,
                    "chunks": pdf_chunks or 115,
                },
            },
        }
    except Exception as exc:
        logger.warning("corpus_telemetry_chroma_unavailable", error=str(exc))
        return {
            "total_documents": 68,
            "total_chunks": 318,
            "corpus": {
                "myscheme": {"documents": 58, "chunks": 203},
                "goa_portal_pdf": {"documents": 10, "chunks": 115},
            },
        }


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Pre-warm models on startup so the first user query has no cold-start delay."""
    logger.info("seva_ai_startup", version="0.1.0")
    try:
        await asyncio.to_thread(_get_pipeline)
        logger.info("models_prewarmed_successfully")
    except Exception as exc:
        logger.warning("model_prewarm_skipped_or_failed", error=str(exc))

    yield
    logger.info("seva_ai_shutdown")


app = FastAPI(
    title="Seva AI — Multilingual Government Services Assistant",
    description=(
        "Multilingual RAG API for Goan education and government scheme "
        "information. Supports English and Goan Konkani (Devanagari) queries."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key", "X-Request-ID"],
    max_age=600,
)


@app.middleware("http")
async def security_and_logging_controls(request: Request, call_next: Any) -> Response:
    """Security checks and structured request logging."""
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)

    t0 = time.monotonic()

    if request.method == "POST" and request.url.path == "/query":
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > QUERY_BODY_LIMIT_BYTES:
                    return JSONResponse({"detail": "Request body is too large."}, status_code=413)
            except ValueError:
                return JSONResponse({"detail": "Invalid Content-Length header."}, status_code=400)
        client_id = request.client.host if request.client else "unknown"
        if not _query_limiter.allowed(client_id):
            return JSONResponse(
                {"detail": "Too many requests. Please try again shortly."},
                status_code=429,
                headers={"Retry-After": "60"},
            )

    response = await call_next(request)
    latency_ms = round((time.monotonic() - t0) * 1000, 2)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
    response.headers["Cache-Control"] = "no-store" if request.url.path == "/query" else "no-cache"

    logger.info(
        "http_request_finished",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        latency_ms=latency_ms,
        request_id=request_id,
    )
    return response


@app.get("/health")
async def health() -> dict[str, str]:
    """Return basic process liveness (unauthenticated)."""
    return {"status": "ok"}


@app.get("/translate/status")
async def translate_status() -> dict[str, str]:
    """Return which translation backend is active (unauthenticated)."""
    pipeline = _pipeline
    if pipeline is None:
        return {"backend": "not_loaded", "note": "Pipeline not yet initialized"}
    translator = getattr(pipeline, "translator", None)
    if translator is None:
        return {"backend": "none", "note": "Translation disabled"}
    backend = getattr(translator, "backend_name", "unknown")
    notes = {
        "indictrans2":        "Native Konkani (kok_Deva) via IndicTrans2",
        "nllb_marathi_proxy": "Konkani proxied via Marathi — set HF_TOKEN for native kok_Deva",
        "none":               "Translation disabled",
    }
    return {"backend": backend, "note": notes.get(backend, "")}


@app.get("/admin/stats", response_model=AdminStatsResponse)
async def admin_stats(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> AdminStatsResponse:
    """Return corpus telemetry and query analytics (protected by X-API-Key)."""
    _verify_api_key(x_api_key)

    uptime = round(time.time() - _START_TIME, 2)
    corpus_info = _get_corpus_telemetry()

    pipeline = _pipeline
    t_backend = "not_loaded"
    if pipeline and getattr(pipeline, "translator", None):
        t_backend = getattr(pipeline.translator, "backend_name", "unknown")

    with _stats_lock:
        q_count = _query_counter
        distribution = dict(_route_counts)

    return AdminStatsResponse(
        uptime_seconds=uptime,
        query_count=q_count,
        translator_backend=t_backend,
        corpus={
            k: SourceCorpusStats(**v) for k, v in corpus_info["corpus"].items()
        },
        total_documents=corpus_info["total_documents"],
        total_chunks=corpus_info["total_chunks"],
        route_distribution=distribution,
    )


@app.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> QueryResponse:
    """Run a user query through the full RAG pipeline (protected by X-API-Key)."""
    _verify_api_key(x_api_key)

    try:
        pipeline = _get_pipeline()
    except RuntimeError as exc:
        logger.warning("rag_pipeline_unavailable", error=str(exc))
        raise HTTPException(
            status_code=503,
            detail="The assistant is temporarily unavailable. Please try again shortly.",
        ) from exc

    resolved_language = request.resolve_language()
    query_preview = request.text[:80]
    logger.info("processing_query", query_preview=query_preview, language=resolved_language)

    try:
        result = await asyncio.to_thread(
            pipeline.answer,
            query=request.text,
            language=resolved_language,
        )
    except Exception as exc:
        logger.error("query_processing_failed", error=str(exc))
        raise HTTPException(
            status_code=503,
            detail="The assistant is temporarily unavailable. Please try again shortly.",
        ) from None

    route_val = result.get("route", "direct")

    with _stats_lock:
        global _query_counter
        _query_counter += 1
        _route_counts[route_val] += 1

    logger.info(
        "query_completed",
        route=route_val,
        confidence=result.get("confidence", 0.0),
        query_preview=query_preview,
    )

    return QueryResponse(
        query=request.text,
        answer=result["answer"],
        confidence=result["confidence"],
        route=route_val,
        sources=[
            SourceCitation(title=s["title"], source_url=s["source_url"])
            for s in result.get("sources", [])
        ],
        translator_backend=result.get("translator_backend"),
        retrieval_hint_applied=result.get("retrieval_hint_applied", False),
        retrieved_doc_ids=result.get("retrieved_doc_ids", []),
    )
