# Agent Instructions

> **Research baseline:** [RESEARCH_PLAN.md](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/docs/RESEARCH_PLAN.md) is the owner-approved research baseline. See [IMPLEMENTATION_STATUS.md](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/docs/IMPLEMENTATION_STATUS.md) for verified repository execution and current runtime metrics.

## Project Direction

This repository is a **Multilingual Retrieval-Augmented Generation (RAG)** system for public service information access in low-resource and under-resourced Indian languages. **Konkani (Devanagari script) is the primary case study**, alongside English. The target domain is Goan education and government scholarship/public-policy schemes.

Future coding agents must not revert to old broad generic government-services or English/Gujarati assumptions unless explicitly required.

## Core Rules

- Respect the architecture documented in [`ARCHITECTURE.md`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/docs/ARCHITECTURE.md).
- Modify application code only when explicitly asked; keep documentation and code synchronized.
- Distinguish active implemented behavior, current configuration, empirical research components, and future roadmap items.
- Do not invent unsupported languages, unverified datasets, benchmark scores, or deployment infrastructure.
- Keep documentation and code consistent.
- Preserve research reproducibility and citation provenance.

## Current Repository Reality

Established from the verified codebase:

- **Backend:** FastAPI application running via Uvicorn (`backend/app/main.py`), featuring `/query`, `/health`, and `/translate/status`.
- **Active Knowledge Base:** 68 authoritative documents (58 from myScheme public API + 10 Goa government PDF documents from SCERT Goa, DOL Goa, and Goa Government portals) yielding **318 indexed chunks** in ChromaDB (`education_schemes` collection).
- **Retrieval Engine:** Hybrid retrieval combining dense vector search (`all-MiniLM-L6-v2`, 384-dim) and sparse search (`rank-bm25` over all 318 chunks) fused via Reciprocal Rank Fusion (RRF, $k=60$).
- **Generation:** Local Ollama running `llama3.2` with strict context grounding and citation extraction.
- **Translation Layer:** Two-tier translation service (`app/rag/translation.py`):
  1. IndicTrans2 200M (`gom_Deva` ↔ `eng_Latn`) when `HF_TOKEN` is configured.
  2. NLLB-200 distilled 600M ungated fallback (proxying Konkani via `mar_Deva`).
  3. Passthrough if translation models are offline.
- **Fallback Routing:** Implemented in `app/rag/fallback_routing.py` using normalized RRF scores against `CONFIDENCE_THRESHOLD = 0.6`. Low-confidence responses append official verification disclaimers.
- **Frontend:** Lightweight, responsive single-page web client (`chat.html`) supporting English/Konkani query switching, suggestion chips, citations, and confidence badges.
- **Testing:** 10 automated unit tests passing across ingestion, RAG pipeline, and fallback routing (`backend/tests/`).

## Research Discipline

Adaptive Fallback Language Routing is implemented as an operational component with empirical evaluation ongoing.

Agents must:

- Acknowledge that fallback routing is implemented in code (`app/rag/fallback_routing.py`) with a baseline threshold of `0.6`, while reporting that optimal threshold tuning and extended language mappings remain active research questions.
- Maintain transparent discussions of trade-offs: additional latency, cascaded translation errors, semantic drift, and potential hallucination risks.
- Avoid claiming fallback routing or RAG is guaranteed to eliminate errors.

## Evidence & Grounding Language

Use academically defensible wording:

> "RAG reduces the risk of unsupported generation by grounding responses in retrieved evidence, but it does not eliminate hallucinations or guarantee factual correctness."

Do not claim:
- RAG eliminates hallucinations.
- Retrieval guarantees correctness.
- Citations guarantee that every generated clause is factually true.
- Translation preserves 100% of nuanced legal/administrative semantics.

## Language Scope

- **Implemented & Verified:** English (`en`) and Goan Konkani in Devanagari script (`kok` / `gom_Deva` / `mar_Deva` proxy).
- **Primary Case Study:** Goan Konkani (`gom_Deva`).
- **Future Work:** Additional Indian languages (e.g. Marathi, Hindi) and BHASHINI API integration.

## Documentation Consistency Checklist

When updating documentation, ensure:

- [`PROJECT.md`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/docs/PROJECT.md) agrees with [`ARCHITECTURE.md`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/docs/ARCHITECTURE.md).
- [`ARCHITECTURE.md`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/docs/ARCHITECTURE.md) agrees with [`RAG_PIPELINE.md`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/docs/RAG_PIPELINE.md).
- [`RAG_PIPELINE.md`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/docs/RAG_PIPELINE.md) agrees with [`PROMPTS.md`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/docs/PROMPTS.md).
- [`IMPLEMENTATION.md`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/docs/IMPLEMENTATION.md) agrees with [`TASKS.md`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/docs/TASKS.md) and [`IMPLEMENTATION_STATUS.md`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/docs/IMPLEMENTATION_STATUS.md).
- [`DATA_MODEL.md`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/docs/DATA_MODEL.md) matches [`schemas.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/schemas.py) and ChromaDB metadata.
- [`API_SPEC.md`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/docs/API_SPEC.md) accurately reflects the active FastAPI endpoints.
