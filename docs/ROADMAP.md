# Project Roadmap

> **Research baseline:** [RESEARCH_PLAN.md](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/docs/RESEARCH_PLAN.md) establishes research milestones; [IMPLEMENTATION_STATUS.md](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/docs/IMPLEMENTATION_STATUS.md) documents verified completion.

---

## Progress Overview

```
Phase 1: Architecture & Scope Alignment      [████████████████████] 100% (Completed)
Phase 2: Corpus Ingestion (myScheme + PDFs)  [████████████████████] 100% (Completed)
Phase 3: Hybrid Retrieval & Vector Indexing  [████████████████████] 100% (Completed)
Phase 4: LLM Generation & Fallback Routing   [████████████████████] 100% (Completed)
Phase 5: Bidirectional Konkani Translation   [████████████████████] 100% (Completed)
Phase 6: REST API & Interactive Chat UI      [████████████████████] 100% (Completed)
Phase 7: Automated Unit Testing              [████████████████████] 100% (Completed)
Phase 8: Gold-Set Empirical Evaluation       [░░░░░░░░░░░░░░░░░░░░]   0% (Upcoming)
Phase 9: Streaming (SSE) & Model Scaling     [░░░░░░░░░░░░░░░░░░░░]   0% (Future)
```

---

## Completed Phases

### Phase 1: Architecture & Research Realignment (Completed ✅)
- Aligned project scope exclusively with **Multilingual RAG for Indian Government Services**.
- Established **Goan Konkani in Devanagari (`gom_Deva`)** as the primary low-resource case study alongside English.
- Defined target domain: Goan education, student scholarships, youth welfare, and citizen charters.

### Phase 2: Authoritative Corpus Ingestion (Completed ✅)
- Implemented [`backend/app/services/ingestion.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/services/ingestion.py) to ingest 58 schemes from myScheme v6 public API.
- Implemented [`backend/app/ingestion/pdf_loader.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/ingestion/pdf_loader.py) with PyMuPDF to extract 10 Goa government PDF circulars from SCERT Goa, DOL Goa, Tribal Welfare, and South Goa Collectorate.
- Result: **68 authoritative documents** cleanly parsed and stored.

### Phase 3: Hybrid Indexing & Retrieval Engine (Completed ✅)
- Implemented 300-word chunker and batch vector indexing into ChromaDB collection `education_schemes` (cosine distance).
- Indexed **318 passages** using `all-MiniLM-L6-v2` embeddings.
- Built in-memory `BM25Okapi` keyword index spanning all 318 chunks.
- Implemented Reciprocal Rank Fusion (RRF, $k=60$) with prefix-based deduplication in [`retriever.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/rag/retriever.py).

### Phase 4: Local LLM Generation & Confidence Routing (Completed ✅)
- Integrated local Ollama `llama3.2` with low temperature (`0.1`), max context window cap (2,000 characters), and output token limiting (`num_predict = 200`).
- Implemented [`fallback_routing.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/rag/fallback_routing.py) with RRF score normalization and confidence threshold $\tau = 0.6$. Appends official portal verification caveat on low confidence.

### Phase 5: Multi-Tier Konkani Translation Layer (Completed ✅)
- Built [`translation.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/rag/translation.py) providing:
  - Primary: AI4Bharat IndicTrans2 200M (`gom_Deva` ↔ `eng_Latn`).
  - Fallback: Meta NLLB-200 600M (`mar_Deva` proxy for Konkani).
  - Passthrough: English-only execution if translation is offline.

### Phase 6: REST API & Interactive Browser UI (Completed ✅)
- FastAPI server with endpoints: `/query`, `/health`, `/translate/status`, `/docs`.
- Built [`chat.html`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/chat.html) single-page client with language toggles, prompt suggestions, and citation badges.
- Created [`start_server.bat`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/start_server.bat) for one-click Windows startup.

### Phase 7: Automated Unit Testing (Completed ✅)
- 10 automated unit tests passing across ingestion, pipeline execution, and confidence routing (`backend/tests/`).

---

## Upcoming Phases

### Phase 8: Gold-Set Empirical Evaluation (Active Next Step 🎯)
- Assemble 15–20 gold-standard Goan Konkani question-answer pairs against indexed schemes.
- Execute stage-isolated evaluation measuring Recall@k, faithfulness / groundedness, chrF++, and BLEU.
- Document quantitative baseline scores in `docs/TESTING.md`.

### Phase 9: Streaming SSE & Multilingual Embedding Upgrade (Planned)
- Implement Server-Sent Events (SSE) streaming on `/query` for reduced perceived latency.
- Provide toggle for `BAAI/bge-m3` (1024-dim) multilingual embeddings for cross-lingual dense search.

### Phase 10: Production Docker Deployment (Planned)
- Refine `docker-compose.yml` to package backend, Ollama, and ChromaDB containers for one-command multi-platform deployment.
