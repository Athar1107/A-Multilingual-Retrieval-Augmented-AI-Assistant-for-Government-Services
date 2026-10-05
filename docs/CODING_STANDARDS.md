# Coding Standards

> **Research baseline:** Preserve the Konkani (Devanagari) user-language / English active-corpus boundary and maintain strict separation between active indexed retrieval content and translation-audit references. See [RESEARCH_PLAN.md](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/docs/RESEARCH_PLAN.md).

---

## Purpose

These standards guide maintenance and extension of the Multilingual RAG assistant codebase. They ensure modularity, fast test cycles, clean type validation, and research reproducibility.

---

## Python Backend Standards

The backend is built with Python 3.11+ using **FastAPI**, **Pydantic v2**, **ChromaDB**, and **PyTorch**.

### 1. Separation of Concerns
Maintain clean decoupling across pipeline stages:
- **`app.config`:** Central repository for environment configurations, file paths, and tunable thresholds (`CONFIDENCE_THRESHOLD`, `CHUNK_SIZE_WORDS`, `TOP_K_DEFAULT`).
- **`app.schemas`:** Strict Pydantic models for all API request and response bodies (`QueryRequest`, `QueryResponse`, `SourceCitation`).
- **`app.rag.retriever`:** Hybrid retrieval and Reciprocal Rank Fusion logic only.
- **`app.rag.generator`:** Ollama LLM prompt formulation, connection management, and answer generation.
- **`app.rag.fallback_routing`:** Confidence thresholding and caveat appending.
- **`app.rag.translation`:** Translation abstractions and backend selection.
- **`app.rag.pipeline`:** High-level orchestrator connecting all stages.

### 2. Fast Startup & Lazy Loading
- **Never load heavy ML models at module import time.**
- In [`backend/app/main.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/main.py), use lazy initialization (`_get_pipeline()`) so Uvicorn boots in sub-second time.
- Offload synchronous, CPU-intensive ML inference (embeddings, Ollama HTTP calls, translation) into worker threads using `asyncio.to_thread` to prevent blocking FastAPI's async event loop.

### 3. Protocol-Driven Dependency Injection
To keep unit tests fast (< 1 second) and independent of heavyweight models (Torch, SentenceTransformers, Ollama):
- Define standard `typing.Protocol` interfaces in [`pipeline.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/rag/pipeline.py#L20-L36) (`RetrieverProtocol`, `GeneratorProtocol`, `FallbackRouterProtocol`, `TranslationProtocol`).
- The `RAGPipeline.__init__` must accept optional protocol instances. When provided, concrete heavy classes are never imported or instantiated.
- Support `translator=False` in unit tests to completely bypass translation model initialization.

### 4. Type Hints & Code Style
- Use comprehensive type annotations on all function signatures (`str | None`, `list[dict[str, Any]]`, etc.).
- Follow PEP 8 formatting with line length 88 (enforced via Ruff and Black).
- Catch specific exceptions (`httpx.ConnectError`, `FileNotFoundError`) and avoid bare `except:` statements.

---

## Data & RAG Engineering Standards

### 1. Ingestion Provenance
- Ingestion scripts ([`ingestion.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/services/ingestion.py) and [`pdf_loader.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/ingestion/pdf_loader.py)) must record:
  - Stable `doc_id` or slug.
  - Official canonical source URL (`source_url`).
  - Source family (`myScheme`, `SCERT_Goa`, `DOL_Goa`, `Goa_Gov`).
  - Ingestion timestamp (`collected_at`).
  - SHA-256 checksum or byte size where appropriate.
- Chunk text deterministically using word boundaries (`CHUNK_SIZE_WORDS = 300`).
- Ensure all vector store upserts are idempotent (`collection.upsert`).

### 2. Grounding & Citation Discipline
- Always extract provenance citations from the actual retrieved chunks that contributed to the context.
- Never invent URLs or scheme titles not present in the retrieved chunk metadata.
- When retrieval score is below `CONFIDENCE_THRESHOLD` (0.6), explicitly mark `route = "fallback"` and include the verification caveat instructing citizens to verify with official portals (`myscheme.gov.in`).

---

## Frontend Standards (`chat.html`)

- Zero external framework dependencies: write clean, accessible, modern Vanilla HTML/CSS/JavaScript.
- Maintain responsive layout with mobile and desktop support.
- Provide real-time UI cues: active language toggle (English / Konkani), status indicators, clickable prompt suggestions, confidence tags, and source citation links.
- Gracefully handle API errors and show clear error messages if backend services are offline.

---

## Testing Standards

- **Unit tests:** Placed under [`backend/tests/`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/tests/). All unit tests must run in under 2 seconds without external network or GPU requirements.
- **Mocking:** Use lightweight stub implementations adhering to protocols rather than mocking internal private methods.
- **Verification scripts:** Store end-to-end integration and smoke scripts under `backend/scripts/` (e.g. `status.py`, `corpus_summary.py`, `smoke_retrieval.py`).
