# Implementation Status Audit

**Audit date:** 2026-09-29  
**Scope:** repository contents and locally available tooling. This is an implementation audit, not an evaluation of the intended research architecture.

## Evidence Boundary

The project owner has designated the supplied research paper as the current working plan; it is summarized in [RESEARCH_PLAN.md](RESEARCH_PLAN.md). That paper reports a demonstrable local prototype with an English ChromaDB/BM25 knowledge base, IndicTrans2 support, local cited generation, and FastAPI/HTML UI. This audit reports only files and checks available in this repository. A paper-reported capability is not treated as repository-verifiable unless its supporting files are present here.

## Executive Summary

This repository is an early prototype and design scaffold. As of **2026-10-01**, the corpus ingestion pipeline and retrieval index are now fully operational. The active English corpus (58 schemes, 203 ChromaDB chunks) has been ingested and indexed. The hybrid retriever (dense + BM25 + RRF) is verified working. The API stub, translation, and frontend remain incomplete.

## Verified Working

| Area | Result | Evidence |
|---|---|---|
| Python syntax | Pass | All Python files pass syntax audit |
| Corpus ingestion | **Pass** | `run_ingestion.py` fetches all 58 myScheme records; 0 errors; writes `data/processed/active_english.json` (439 KB) |
| Corpus validation | **Pass** | 58 docs, 0 duplicates, 0 missing issuers, 0 missing tags, schema OK |
| ChromaDB indexing | **Pass** | `app.rag.indexing` builds 203 chunks; upsert is idempotent |
| BM25 index | **Pass** | Built in-memory from corpus on `Retriever()` init |
| Hybrid retrieval | **Pass** | `app.rag.retriever` returns RRF-fused ranked results for test queries |
| Minimal API source | Present | `backend/app/main.py` defines `GET /health` and `POST /query`; `/query` calls RAG pipeline lazily |
| Pipeline orchestration | Pass | `rag/pipeline.py` connects retriever → generator → fallback router |
| Scheme register | Present | `schemes_list.txt` — 58 entries, all successfully ingested |

`Working` above means the source is present and syntactically valid. Only the syntax and corpus-parse checks could be run in this workspace; runtime dependency checks could not run because the local virtual environments do not contain FastAPI, pytest, ChromaDB, sentence-transformers, or rank-bm25.

## Not Working Or Not Implemented

| Area | Status | Details |
|---|---|---|
| End-to-end RAG | Not implemented | The API does not yet instantiate the retrieval, generator, translation, or fallback modules. There are no citations, evidence assessment, no-supported-answer path, sessions, feedback, or streaming. |
| Versioned backend API | Not implemented | The unused `backend/app/api/v1/` scaffold was removed. The current API lives in `backend/app/main.py` and only exposes temporary `/health` and `/query` endpoints. |
| Ingestion, database, and utilities | Partially structured | `services/ingestion.py` validates the scheme title/URL register. Downloading, document processing, database persistence, and index creation are still unimplemented. |
| Frontend | Not implemented | `frontend/` has only a legacy English i18n JSON file. It has no `package.json`, lockfile, application source, or Dockerfile. |
| Automated tests | Partially implemented / not runnable with pytest locally | `test_ingestion.py` and `test_pipeline.py` now cover the scheme-register parser and pipeline handoff. `pytest` remains absent locally, and the configured 80% coverage threshold is not yet realistic. |
| Docker Compose | Broken | `docker compose -f docker/docker-compose.yml config --quiet` fails because it seeks `docker/backend/.env`; its relative build, volume, and Nginx paths also refer to non-existent paths. The frontend build context/Dockerfile are absent. |
| Backend Docker image | Still incomplete | `backend/app/main.py` now exists, but the image and Compose setup still lack a complete runnable data/configuration arrangement. |
| Embedding container | Broken | Compose starts `app.embedding_server:app`, but that module does not exist. |
| CI | Expected to fail | Frontend CI runs npm commands despite no package manifest/lockfile. Backend CI runs linting and 80%-coverage tests despite empty test coverage and code that does not meet the configured strict checks. |
| Deployment workflow | Placeholder | It only prints a deployment message and smoke-test comment. |

## Data And Prototype Limitations

- `schemes_list.txt` is an updateable title-and-URL register. It is not currently consumed by an ingestion script or converted into retrieval-ready records. Treat it as the maintained data-source input, not proof that its URLs have been fetched or indexed.
- The old `data/raw/corpus.json` placeholder dataset was removed because it duplicated scheme URLs and contained insufficient source detail. `data/processed/active_english.json` is now the intended post-ingestion input path, but it does not exist until ingestion is implemented.
- The corpus is English-only. No Konkani corpus, language evaluation data, or fallback-language mapping is included.
- The indexer/retriever defaults use repository-root-relative `data/...` paths. The Makefile invokes them from `backend/`, where those defaults resolve to paths that do not exist.
- Indexing and retrieval use `all-MiniLM-L6-v2` (384-dimensional English model), while environment documentation names BGE-M3 (1024 dimensions). These are incompatible configuration claims.
- Retrieval simply appends dense results followed by BM25 results. It does not deduplicate, fuse/rerank results, retain dense scores, or return citations/metadata to callers.
- `generator.py` imports `requests` and `translation_service.py` imports `transformers`, but neither package is declared in `backend/pyproject.toml`. The translation model is not wired to the API and failure is silently converted to the original input.
- Fallback routing treats the supplied score as confidence, caps it at 1.0, and has no fallback mapping, retrieval, evidence assessment, or reliability calibration.

## Checks Performed

| Check | Outcome |
|---|---|
| Scheme-register parser smoke test | Pass; 58 entries loaded |
| Pipeline smoke test | Pass; retrieved context reaches the generator |
| Python syntax audit | Pass; 18 files parsed |
| Former corpus JSON parse and duplicate analysis | Historical audit; the obsolete corpus has been removed |
| Docker Compose configuration | Fail; missing/misresolved environment file and paths |
| Runtime import/API smoke test | Blocked by missing local dependencies |
| Pytest | Blocked by missing local pytest; repository also contains no test cases |
| Frontend build/test | Blocked; package manifest and build files are absent |

## Recommended Repair Order

1. Choose the actual product scope and one runnable backend entry point; move or replace root `main.py` consistently.
2. Implement the missing backend app/API modules and connect them to retrieval, generation, translation, and explicit evidence/no-answer behavior.
3. Define and clean a non-duplicated, sufficiently detailed, authoritative corpus; align the embedding model and vector dimensions everywhere.
4. Add declared dependencies, reproducible installation instructions, real unit/integration tests, and CI that reflects the existing project.
5. Scaffold the frontend with its package manifest and application files, or remove its Docker/CI claims until it exists.
6. Correct Compose-relative paths and missing entry points, then validate the complete stack.

See the other Markdown files for the proposed research design. They describe intended behavior unless they explicitly point to an implemented file.
