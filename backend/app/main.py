"""FastAPI entry point for the Konkani public-service RAG application."""

import asyncio
import logging
import os
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from threading import Lock
from typing import Any, AsyncGenerator

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from .schemas import QueryRequest, QueryResponse, SourceCitation

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy-initialized pipeline — heavy ML models are loaded on first query,
# not at import time, to keep ``uvicorn`` startup fast.
# ---------------------------------------------------------------------------

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
    """Lazily initialize the RAG pipeline on the first request."""
    global _pipeline, _init_error
    if _pipeline is not None:
        return _pipeline
    if _init_error is not None:
        raise RuntimeError(_init_error)
    try:
        from .rag.pipeline import RAGPipeline

        _pipeline = RAGPipeline()
        logger.info("RAG pipeline initialized successfully.")
        return _pipeline
    except Exception as exc:
        _init_error = str(exc)
        logger.exception("Failed to initialize RAG pipeline")
        raise RuntimeError(_init_error) from exc


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logger.info("Konkani Public-Service RAG starting up...")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="Konkani Public-Service RAG",
    description=(
        "Multilingual RAG API for Goan education and government scheme "
        "information.  Supports English and Konkani (Devanagari) queries."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# The production UI is served by nginx on the same origin. Development origins
# may be opted into via ALLOWED_ORIGINS; do not use a wildcard for this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    max_age=600,
)


@app.middleware("http")
async def security_controls(request: Request, call_next: Any) -> Response:
    """Apply low-cost request limits and response hardening before model work."""
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
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
    response.headers["Cache-Control"] = "no-store" if request.url.path == "/query" else "no-cache"
    return response


@app.get("/health")
async def health() -> dict[str, str]:
    """Return basic process liveness."""
    return {"status": "ok"}


@app.get("/translate/status")
async def translate_status() -> dict[str, str]:
    """Return which translation backend is active.

    Backends:
      indictrans2         — ai4bharat IndicTrans2 (native kok_Deva, needs HF_TOKEN)
      nllb_marathi_proxy  — NLLB-200 600M, Konkani via Marathi pivot (ungated)
      none                — translation disabled; queries processed in English only
      not_loaded          — backend not yet initialized (loads on first query)
    """
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


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    """Run a user query through the full RAG pipeline.

    The pipeline is initialized lazily on the first request.  If the
    corpus or index is not available, a 503 response is returned with
    a helpful error message.
    """
    try:
        pipeline = _get_pipeline()
    except RuntimeError as exc:
        logger.warning("RAG pipeline unavailable: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="The assistant is temporarily unavailable. Please try again shortly.",
        ) from exc

    # Run the synchronous pipeline in a thread to avoid blocking the
    # async event loop (embedding + BM25 + Ollama calls are CPU/IO heavy).
    try:
        result = await asyncio.to_thread(
            pipeline.answer,
            query=request.text,
            language=request.language,
        )
    except Exception:
        logger.exception("Query processing failed")
        raise HTTPException(
            status_code=503,
            detail="The assistant is temporarily unavailable. Please try again shortly.",
        ) from None

    return QueryResponse(
        query=request.text,
        answer=result["answer"],
        confidence=result["confidence"],
        route=result.get("route", "direct"),
        sources=[
            SourceCitation(title=s["title"], source_url=s["source_url"])
            for s in result.get("sources", [])
        ],
    )
