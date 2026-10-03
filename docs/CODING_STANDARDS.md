# Coding Standards

> **Research baseline:** Preserve the Konkani (Devanagari) user-language / English active-corpus boundary and keep translation-audit data out of active retrieval code. See [RESEARCH_PLAN.md](RESEARCH_PLAN.md).

## Purpose

These standards guide future implementation work. They are engineering standards, not research claims.

## General Principles

- Keep code consistent with the documented Multilingual RAG architecture.
- Distinguish implemented behavior from proposed or planned behavior in comments, docs, and tests.
- Do not hardcode unsupported language mappings, benchmark targets, model names, or thresholds.
- Prefer small, testable components with explicit inputs and outputs.
- Preserve provenance and reproducibility for corpus, evaluation, and model configuration.

## Python Backend

Expected standards if the FastAPI backend is implemented:

- Use type hints for public functions.
- Keep API models explicit and validated.
- Keep retrieval, evidence assessment, generation, and language processing as separable services.
- Make thresholds and model names configuration-driven.
- Avoid broad exception swallowing.
- Do not log sensitive user data by default.
- Unit-test behavior before relying on integration tests.

## Data And RAG Code

- Treat source documents as untrusted input.
- Keep active retrieval corpus separate from reference/translation/audit material.
- Store enough metadata to reproduce retrieval and citations.
- Keep chunking and indexing configuration versioned.
- Do not call initial settings optimal without evaluation.
- Ensure citation identifiers can be traced to source documents and chunks.

## Language Processing

- Do not assume fixed language support beyond finalized project scope.
- Konkani is the primary case study.
- Fallback-language mapping must be configured from research decisions, not inferred ad hoc.
- Preserve citation markers during translation or rewriting.
- Flag uncertainty rather than silently changing meaning.

## Frontend

If the frontend is implemented:

- Keep UI copy aligned with the education-domain target.
- Display no-supported-answer states clearly.
- Make citations accessible and inspectable.
- Do not imply that answers are guaranteed correct.
- Avoid stale legacy UI-language assumptions from the previous prototype unless they are intentionally retained.

## Testing

- Add unit tests for individual pipeline components.
- Add integration tests for pipeline flow.
- Add evaluation tests only after datasets are defined.
- Record metric results only from actual runs.
- Keep test fixtures small, auditable, and clearly marked synthetic or real.

## Documentation Discipline

- Update `docs/` when implementation changes architecture or API behavior.
- Mark unresolved decisions as To be determined.
- Mark proposed research components as proposed until implemented and evaluated.
- Do not invent results, datasets, thresholds, or model versions.
