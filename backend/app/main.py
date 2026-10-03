"""FastAPI entry point for the Konkani public-service RAG application."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas import QueryRequest, QueryResponse, SourceCitation

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy-initialized pipeline — heavy ML models are loaded on first query,
# not at import time, to keep ``uvicorn`` startup fast.
# ---------------------------------------------------------------------------

_pipeline: Any = None
_init_error: str | None = None


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

# Allow the (future) frontend to call the API from a different origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        raise HTTPException(
            status_code=503,
            detail=f"RAG pipeline is not available: {exc}",
        ) from exc

    # Run the synchronous pipeline in a thread to avoid blocking the
    # async event loop (embedding + BM25 + Ollama calls are CPU/IO heavy).
    result = await asyncio.to_thread(
        pipeline.answer,
        query=request.text,
        language=request.language,
    )

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
