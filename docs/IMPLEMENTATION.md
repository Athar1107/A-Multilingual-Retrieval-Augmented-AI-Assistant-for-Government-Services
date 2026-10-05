# Implementation Architecture & Guide

> **Research baseline:** [RESEARCH_PLAN.md](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/docs/RESEARCH_PLAN.md) establishes the research foundation. This document describes the implemented application architecture and execution state across the codebase.

---

## 1. Implemented Repository Layout

The project uses a streamlined, modular layout centered on the Python FastAPI backend and a clean browser client:

```
├── schemes_list.txt            # Maintained register of 58 authoritative myScheme URLs
├── chat.html                   # Interactive browser chat UI (English & Konkani toggle)
├── start_server.bat            # Windows startup script for FastAPI/Uvicorn server
├── main.py                     # Root compatibility launcher
├── data/
│   ├── processed/
│   │   └── active_english.json # Cleaned 58 myScheme JSON records (439 KB)
│   └── indexes/
│       └── chroma/             # Persistent ChromaDB SQLite/hnsw storage (318 chunks)
├── backend/
│   ├── pyproject.toml          # Project configuration, dependencies, and pytest settings
│   ├── app/
│   │   ├── config.py           # Centralized configuration (paths, models, knobs)
│   │   ├── schemas.py          # Pydantic API schemas (QueryRequest, QueryResponse)
│   │   ├── main.py             # FastAPI entry point, CORS, lifespan, /query, /health
│   │   ├── ingestion/
│   │   │   └── pdf_loader.py   # PyMuPDF extractor for SCERT & DOL Goa PDF circulars
│   │   ├── services/
│   │   │   └── ingestion.py    # myScheme v6 public API ingestion & cleaning service
│   │   └── rag/
│   │       ├── indexing.py     # SentenceTransformer embedder & ChromaDB batch indexer
│   │       ├── retriever.py    # Hybrid dense + BM25 retriever with RRF fusion (k=60)
│   │       ├── generator.py    # Ollama llama3.2 grounded response generator
│   │       ├── fallback_routing.py # Confidence evaluation & caveat appending (tau=0.6)
│   │       ├── translation.py  # IndicTrans2 (gom_Deva) & NLLB-200 (mar_Deva proxy)
│   │       └── pipeline.py     # End-to-end RAG orchestrator with protocol interfaces
│   ├── scripts/                # Status, corpus summary, smoke retrieval, and test scripts
│   └── tests/                  # Pytest unit tests (test_ingestion, test_pipeline, etc.)
└── docs/                       # Synchronized project and research documentation
```

---

## 2. Core Implemented Subsystems

### A. Corpus Ingestion & Indexing
- **myScheme Ingestion:** [`app/services/ingestion.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/services/ingestion.py) iterates over [`schemes_list.txt`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/schemes_list.txt), queries the myScheme v6 public API, cleans markdown/HTML formatting, and writes `data/processed/active_english.json`.
- **Goa PDF Ingestion:** [`app/ingestion/pdf_loader.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/ingestion/pdf_loader.py) downloads and processes official PDFs from SCERT Goa, DOL Goa, and Goa Government portals.
- **Vector Indexing:** [`app/rag/indexing.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/rag/indexing.py) segments documents into 300-word chunks, embeds them with `all-MiniLM-L6-v2`, and upserts them into ChromaDB (`education_schemes` collection). Current indexed total: **68 documents, 318 chunks**.

### B. Hybrid Retrieval & Fusion
- Dense vector retrieval queries ChromaDB for the top-$k$ nearest chunks.
- Sparse keyword retrieval runs `BM25Okapi` in-memory across all 318 indexed chunks.
- Reciprocal Rank Fusion (RRF, $k=60$) combines dense and sparse candidate rankings without requiring score calibration across dissimilar metrics.
- Deduplication occurs across candidate chunks using the first 300 characters.

### C. Language Processing & Translation Layer
- Two-tier translation facade implemented in [`app/rag/translation.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/rag/translation.py):
  1. **IndicTrans2 200M:** Selected when `HF_TOKEN` is present, performing direct translation between `gom_Deva` (Goan Konkani Devanagari) and `eng_Latn`.
  2. **NLLB-200 600M:** Ungated fallback using Marathi (`mar_Deva`) as a script-compatible pivot for Konkani.
  3. **Passthrough:** Gracefully processes queries in English if no translation model is active.

### D. Grounded Answer Generation & Routing
- [`app/rag/generator.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/rag/generator.py) formats a strict prompt containing context (capped at 2,000 characters) and sends it to local Ollama (`llama3.2`).
- [`app/rag/fallback_routing.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/rag/fallback_routing.py) normalizes the average RRF score ($raw\_avg \times 60$) to $[0, 1]$. If confidence $< 0.6$, the route is tagged as `"fallback"` and an official verification warning is appended.

### E. Frontend Chat Client
- [`chat.html`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/chat.html) provides an instant interactive interface with language selection, real-time status indication, source citation badges, and confidence meters.

---

## 3. Verified Verification & Test Status

- **Automated Tests:** 10 unit tests in `backend/tests/` verifying ingestion parsing, end-to-end pipeline mocking, and fallback routing confidence thresholds.
- **Verification Scripts:**
  - `python backend/scripts/status.py`: Verifies corpus size (58 JSON documents, 318 chunks, 0 missing issuers/tags).
  - `python backend/scripts/corpus_summary.py`: Displays breakdown across myScheme and Goa Government PDF sources.

---

## 4. Planned Extensions

1. **Evaluation Dataset:** Construct a formal gold set of 15–20 Goan Konkani question-answer pairs with human-verified ground truth for stage-isolated RAGAS / BLEU / chrF++ evaluation.
2. **Multilingual Embedding Upgrade:** Optional toggle to `BAAI/bge-m3` (1024-dim) for native cross-lingual embedding retrieval.
3. **Containerized Deployment:** Polish Docker Compose setup for production deployment.
