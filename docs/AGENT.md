# Agent Instructions

> **Research baseline:** [RESEARCH_PLAN.md](RESEARCH_PLAN.md) is the owner-approved current plan. Use [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) only for claims about files that are actually in this repository.

## Project Direction

This repository is being repositioned as a **Multilingual RAG** research/prototype project for low-resource and under-resourced Indian languages. **Konkani is the primary case study**. The target domain is education and government education-scheme information.

Future coding agents must not preserve old broad government-services or English/Gujarati assumptions unless the current code or finalized specification explicitly requires them.

## Core Rules

- Respect the architecture documented in `ARCHITECTURE.md`.
- Modify application code only when explicitly asked; some tasks are documentation-only.
- Distinguish existing scaffold, previous prototype configuration, proposed architecture, research components, planned implementation, and To be determined items.
- Do not invent language support, fallback mappings, datasets, thresholds, model versions, evaluation scores, API behavior, or deployment infrastructure.
- Keep documentation and code consistent.
- Preserve research reproducibility.

## Current Repository Reality

Established from the repository:

- Backend dependencies include FastAPI, ChromaDB, LangChain, Ollama, sentence-transformers, rank-bm25, SQLAlchemy, SQLite/PostgreSQL drivers, and document-processing libraries.
- Docker Compose contains a local development stack for backend, frontend, ChromaDB, Ollama, embedding, and Nginx.
- Backend modules are mostly placeholders.
- Frontend is mostly placeholders plus one legacy English i18n string file.
- Data folders are placeholders from the old broad government-services prototype.

Do not claim the target Multilingual RAG system is already implemented unless code proves it.

## Research Discipline

Adaptive Fallback Language Routing is proposed as a research component.

Agents must:

- Treat fallback routing as proposed until implemented.
- Never infer a fallback language mapping.
- Use this wording when unresolved: "Fallback-language mapping: To be determined based on linguistic/resource criteria and experimental evaluation."
- Mention trade-offs: additional latency, additional processing, cascading translation errors, semantic drift, and uncertain performance improvement.
- Avoid claiming fallback routing is guaranteed to improve answers.

Evidence assessment is required in the target architecture.

Agents must:

- Use this wording when unresolved: "Evidence/confidence threshold: To be determined experimentally."
- Avoid treating retrieval scores as correctness guarantees.
- Avoid treating citations as guarantees that every generated claim is supported.

## Hallucination And Grounding Language

Use academically defensible wording:

"RAG can reduce the risk of unsupported generation by grounding responses in retrieved evidence, but it does not eliminate hallucinations or guarantee correctness."

Do not say:

- RAG eliminates hallucinations.
- Retrieval guarantees correctness.
- Citations guarantee correctness.
- Translation guarantees semantic preservation.
- Fallback guarantees better answers.

## Language Scope

Separate:

- Architecture-level multilingual capability.
- Currently implemented language support.
- Languages actually evaluated.
- Future language support.

Konkani is the primary case study. Additional languages are To be determined unless finalized elsewhere.

## Documentation Consistency Checklist

When updating documentation, check:

- `PROJECT.md` agrees with `ARCHITECTURE.md`.
- `ARCHITECTURE.md` agrees with `RAG_PIPELINE.md`.
- `RAG_PIPELINE.md` agrees with `PROMPTS.md`.
- `IMPLEMENTATION.md` agrees with `TASKS.md`.
- `TASKS.md` agrees with `ROADMAP.md`.
- `TESTING.md` evaluates the architecture actually described.
- `DATA_MODEL.md` matches the documented pipeline.
- `API_SPEC.md` does not contradict the architecture.

Search for stale English/UI-language assumptions, broad government-services scope, fixed unsupported languages, fabricated metric targets, unsupported model versions, or claims that components are fully implemented.
