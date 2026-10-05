# Implementation Task Checklist

> **Research baseline:** [RESEARCH_PLAN.md](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/docs/RESEARCH_PLAN.md) outlines project goals; [IMPLEMENTATION_STATUS.md](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/docs/IMPLEMENTATION_STATUS.md) documents verified completion.

---

## 1. Documentation & Research Preparation
- [x] Reposition repository toward Multilingual RAG for under-resourced Indian languages.
- [x] Focus primary case study on Goan Konkani in Devanagari script (`gom_Deva`).
- [x] Target domain: Goan education, scholarship schemes, youth welfare, and public policy.
- [x] Document authoritative source families (myScheme, SCERT Goa, DOL Goa, Goa Government).
- [x] Synchronize all 15 documentation files with verified codebase execution.

---

## 2. Knowledge-Base Preparation & Ingestion
- [x] Maintain scheme URL register in [`schemes_list.txt`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/schemes_list.txt) (58 schemes).
- [x] Implement [`app/services/ingestion.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/services/ingestion.py) to fetch cleaned scheme records via myScheme v6 API.
- [x] Generate cleaned English corpus file at `data/processed/active_english.json` (439 KB).
- [x] Implement [`app/ingestion/pdf_loader.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/ingestion/pdf_loader.py) with PyMuPDF to parse 10 Goa government PDF circulars.
- [x] Implement 300-word chunker with title preservation.
- [x] Build ChromaDB vector index in collection `education_schemes` (cosine distance).
- [x] Ingest and index **68 documents** yielding **318 searchable chunks**.

---

## 3. RAG Pipeline Implementation
- [x] Implement hybrid dense vector search via ChromaDB using `all-MiniLM-L6-v2` embeddings.
- [x] Implement sparse keyword search via `BM25Okapi` spanning all 318 indexed chunks.
- [x] Implement Reciprocal Rank Fusion (RRF, $k=60$) with 300-char prefix deduplication ([`retriever.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/rag/retriever.py)).
- [x] Formulate grounded context window capped at 2,000 characters.
- [x] Integrate local Ollama `llama3.2` with low temperature (`0.1`) and token cap (`num_predict=200`) ([`generator.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/rag/generator.py)).
- [x] Implement [`fallback_routing.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/rag/fallback_routing.py) with normalized RRF score and confidence threshold $\tau = 0.6$.
- [x] Append official verification disclaimer caveat on low-confidence results.
- [x] Implement two-tier translation layer ([`translation.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/rag/translation.py)) with IndicTrans2 200M (`gom_Deva`), NLLB-200 600M (`mar_Deva` proxy), and passthrough mode.
- [x] Extract unique source provenance citations from retrieved passages.
- [x] Implement [`pipeline.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/rag/pipeline.py) orchestrator with Protocol-driven dependency injection.

---

## 4. API & Client Integration
- [x] Implement FastAPI entry point in [`backend/app/main.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/main.py).
- [x] Implement `/health` liveness probe endpoint.
- [x] Implement `/translate/status` backend diagnostics endpoint.
- [x] Implement `/query` end-to-end RAG query endpoint.
- [x] Add CORS middleware allowing cross-origin requests.
- [x] Lazy-load heavy ML models on first query to ensure instant server boot.
- [x] Offload CPU ML inference to threadpool via `asyncio.to_thread`.
- [x] Build modern, responsive single-page chat UI ([`chat.html`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/chat.html)) with English/Konkani toggles, prompt suggestions, and citation badges.
- [x] Create Windows launcher script ([`start_server.bat`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/start_server.bat)) with port management.

---

## 5. Automated Testing & Verification
- [x] Implement unit tests for ingestion parsing, schema validation, and URL slugging (`test_ingestion.py`).
- [x] Implement unit tests for pipeline orchestration and stubbed retrieval (`test_pipeline.py`).
- [x] Implement unit tests for confidence calculation and fallback routing thresholds (`test_fallback_routing.py`).
- [x] All 10 tests passing on `pytest` in < 1 second.
- [x] Verify live corpus status via `backend/scripts/status.py`.
- [x] Verify corpus breakdown via `backend/scripts/corpus_summary.py`.

---

## 6. Upcoming Research & Optimization Tasks
- [ ] Assemble 15–20 gold-standard Goan Konkani question-answer pairs for quantitative evaluation.
- [ ] Execute stage-isolated evaluation measuring Recall@k, faithfulness / groundedness ratio, chrF++, and BLEU.
- [ ] Implement Server-Sent Events (SSE) streaming on `/query` for real-time word-by-word generation.
- [ ] Support `BAAI/bge-m3` (1024-dim) multilingual embedding model via environment variable.
- [ ] Polish Docker Compose container orchestration.
