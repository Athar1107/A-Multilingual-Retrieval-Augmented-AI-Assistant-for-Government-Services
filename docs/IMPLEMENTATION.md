# Implementation Plan

> **Research baseline:** Build the Konkani (Devanagari)-to-English active-corpus route first. Keep native Konkani/Marathi documents as translation-audit references and treat fallback routing as experimental. See [RESEARCH_PLAN.md](RESEARCH_PLAN.md).

## Status

This document describes the implementation plan for the target Multilingual RAG architecture. It does not claim the target system has already been implemented.

## Existing Prototype Functionality

Established from the repository:

- Backend dependency file exists and names FastAPI, ChromaDB, LangChain, Ollama, sentence-transformers, rank-bm25, SQLAlchemy, SQLite/PostgreSQL drivers, and document-processing libraries.
- Docker Compose defines services for frontend, backend, ChromaDB, Ollama, embedding, Nginx, and persistence volumes.
- Backend modules exist for API, ingestion, RAG, services, database, utilities, and models, but most are placeholders.
- Frontend source tree exists mostly as placeholders with one legacy English i18n file.
- Data directories exist as placeholders and reflect the old broad government-services prototype.

## Simplified Repository Layout

The implementation uses a small structure: `backend/app/main.py` is the canonical API entry point; `schemas.py` contains request/response models; `rag/` contains indexing, retrieval, translation, generation, and pipeline code; and `services/ingestion.py` reads the maintained `schemes_list.txt` register. Generated English corpus data belongs in `data/processed/`, indexes in `data/indexes/`, and Konkani/Marathi translation references in `data/translation_audit/`.

## Components Requiring Modification

- Documentation and terminology must use Multilingual RAG as the primary project identity.
- Domain scope must shift from broad government services to education and government education-scheme information.
- Legacy UI-language assumptions must shift to the Konkani primary case study and language-agnostic architecture where unresolved.
- Existing data folder categories should be reviewed before implementation because they reflect the previous prototype.
- Frontend copy and i18n should be updated later to match the education/Konkani direction.

## Components Requiring New Implementation

The owner-approved implementation order is English active-corpus retrieval for Konkani queries, evidence-backed Konkani delivery, then stage-isolated evaluation. Do not add native Konkani/Marathi audit documents to the active index without documenting a research-plan change.

- Target corpus collection and source governance.
- Document parsing, cleaning, metadata extraction, and chunking.
- Active retrieval corpus indexing.
- Dense retrieval, lexical retrieval, and hybrid result combination where selected.
- Evidence assessment.
- Grounded generation with citation discipline.
- No-supported-answer behavior.
- API contracts and frontend integration.
- Evaluation workflow.

## Research Components

Adaptive Fallback Language Routing is proposed as a research component.

Required implementation concerns:

- It must not infer fallback mappings automatically.
- Fallback-language mapping is To be determined based on linguistic/resource criteria and experimental evaluation.
- It must measure latency, fallback activation, fallback success, answer quality, and possible semantic drift.
- It must allow no-supported-answer when evidence remains insufficient.

Evidence assessment is also a target research/engineering component.

- Evidence/confidence threshold: To be determined experimentally.
- Retrieval scores, evidence snippets, and citations must not be treated as guarantees of correctness.

## Suggested Phases

1. Documentation and research alignment.
2. Corpus definition and source-selection criteria.
3. Knowledge-base preparation pipeline.
4. Retrieval pipeline implementation.
5. Evidence assessment design.
6. Grounded generation and no-supported-answer behavior.
7. Language-processing integration.
8. Adaptive fallback routing experiment.
9. API and frontend integration.
10. Evaluation dataset and test harness.
11. Experimental runs, analysis, and refinement.
12. Final documentation and reproducibility package.

## Future Work

- Finalize language scope and evaluation languages.
- Select embedding, generation, and language-processing models.
- Decide persistence, deployment, and observability stack.
- Build human evaluation protocols for Konkani and any additional languages.
- Determine whether fallback routing improves outcomes enough to justify added complexity.

## Non-Implementation Reminder

This documentation task does not implement application code, RAG, translation, fallback routing, APIs, database schema, or frontend changes.
