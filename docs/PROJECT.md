# Project

> **Research baseline:** [RESEARCH_PLAN.md](RESEARCH_PLAN.md) reflects the current owner-approved Konkani-English plan. [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) separately reports what is visible in this repository.

## Purpose

This project is a research-aligned **Multilingual RAG** prototype for low-resource and under-resourced Indian languages. **Konkani in Devanagari is the primary case study**. The domain is Goan education and government scholarship/public-policy guidance, including schemes, eligibility, application guidance, benefits, official guidelines, and notifications.

The current repository began as a broader government-services assistant prototype. Some scaffolding and technology choices from that prototype remain, but the target project direction is now narrower and research-focused.

## Problem

Education-scheme information is often distributed across government websites, PDFs, circulars, and notifications. Users who prefer under-resourced Indian languages may face additional access barriers when official documents are unavailable, incomplete, or difficult to search in their language.

The project investigates whether a Multilingual RAG system can improve access to education-scheme information while keeping answers grounded in retrieved evidence.

## Research Motivation

RAG can reduce the risk of unsupported generation by grounding responses in retrieved evidence, but it does not eliminate hallucinations or guarantee correctness. This project therefore emphasizes evidence assessment, citation discipline, no-supported-answer behavior, and reproducible evaluation.

The research includes **Adaptive Fallback Language Routing** as an experimental component. Fallback-language mapping is **To be determined based on linguistic/resource criteria and experimental evaluation**.

## Target Users And Context

Target users are people seeking education-related government information in an Indian-language context, especially where Konkani access is important. Possible users include students, parents, school staff, community support workers, and researchers evaluating multilingual information-access systems.

These user groups are target-context assumptions for the project direction, not evidence that a user study has already been completed.

## Scope

Current language and corpus boundary:

- Konkani (Devanagari) is the current user-facing source language (`L1`); English is the active knowledge-base and pivot language.
- myScheme, SCERT Goa, and Directorate of Official Language Goa are the intended authoritative source families.
- Native Konkani and Marathi source material is reserved for an offline translation-audit reference set, not the active retrieval index.

In scope:

- Multilingual RAG architecture for low-resource or under-resourced Indian languages.
- Konkani as the primary case study.
- Education and government education-scheme information.
- Official or authoritative source documents where available.
- Knowledge-base preparation, chunking, metadata, indexing, retrieval, evidence assessment, grounded answer generation, citation presentation, and no-supported-answer behavior.
- Research evaluation of retrieval, generation, language processing, and fallback routing.

Out of scope for the current target:

- A broad all-government-services assistant covering unrelated services such as licenses, registrations, ration cards, voter ID, PAN, or Aadhaar unless later justified by the education domain.
- Claims of fixed language support beyond the finalized and evaluated scope.
- Claims that RAG, translation, retrieval, or citations guarantee correctness.
- Production deployment commitments before infrastructure is selected.

## Expected Capabilities

Planned target capabilities:

- Accept a user query in the relevant user language.
- Identify or handle query language where required.
- Retrieve supporting evidence from an active education-domain corpus.
- Combine dense and lexical retrieval where applicable.
- Assess whether retrieved evidence is sufficient for grounded answering.
- Generate an answer only when evidence is adequate.
- Present evidence or citations with the answer.
- Return a no-supported-answer response when evidence is insufficient.
- Route to a fallback language only when the research design supports doing so.

## Current Repository Status

Existing prototype evidence from the repository:

- Backend dependency configuration includes FastAPI, ChromaDB, LangChain, Ollama, sentence-transformers, rank-bm25, SQLAlchemy, SQLite/PostgreSQL drivers, PyMuPDF, BeautifulSoup, Unstructured, langdetect, and testing tools.
- Docker Compose describes a local stack with frontend, backend, ChromaDB, Ollama, embedding service, Nginx, and SQLite-oriented configuration.
- Backend application modules are mostly placeholders.
- Frontend is mostly a scaffold with one legacy English i18n file from the previous prototype.
- Data folders are placeholders, including old broad government-service categories.

Not yet implemented or not established:

- Target Konkani education corpus.
- Final language scope beyond the Konkani case study.
- Adaptive fallback routing.
- Evidence/confidence threshold.
- Evaluation dataset and metrics results.
- Final model choices and deployment infrastructure.

## Limitations

- Evaluation dataset: To be determined.
- Evidence/confidence threshold: To be determined experimentally.
- Fallback-language mapping: To be determined based on linguistic/resource criteria and experimental evaluation.
- Language-processing approach: To be determined.
- Existing implementation status: scaffold / previous prototype planning, not a complete target system.
