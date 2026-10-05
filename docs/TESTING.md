# Testing & Verification Guide

> **Research baseline:** [RESEARCH_PLAN.md](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/docs/RESEARCH_PLAN.md) establishes research evaluation goals. This document details the automated unit test suite, verification scripts, and empirical evaluation protocol.

---

## 1. Automated Unit Test Suite

The repository includes a fast, self-contained unit test suite under [`backend/tests/`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/tests/) executing via `pytest`.

Tests use protocol-driven stubbing to isolate logic from heavy machine-learning weights, allowing the entire suite to run in **under 1 second** without an active internet connection, GPU, or running Ollama daemon.

### Current Test Suite Results (10 / 10 Passing)

```text
backend\tests\test_ingestion.py::test_load_scheme_register PASSED        [ 10%]
backend\tests\test_ingestion.py::test_slug_from_url PASSED               [ 20%]
backend\tests\test_ingestion.py::test_clean_text_strips_markup PASSED    [ 30%]
backend\tests\test_ingestion.py::test_document_from_payload_has_required_fields PASSED [ 40%]
backend\tests\test_ingestion.py::test_ingest_schemes_writes_active_english_json PASSED [ 50%]
backend\tests\test_pipeline.py::test_pipeline_passes_retrieved_context_to_generator PASSED [ 60%]
backend\tests\test_pipeline.py::test_pipeline_returns_no_results_when_retriever_empty PASSED [ 70%]
backend\tests\test_fallback_routing.py::test_fallback_router_direct_route PASSED [ 80%]
backend\tests\test_fallback_routing.py::test_fallback_router_fallback_route PASSED [ 90%]
backend\tests\test_fallback_routing.py::test_fallback_router_confidence_clamping PASSED [100%]

============================= 10 passed in 0.50s ==============================
```

### Running the Unit Tests

From the repository root:
```bash
pytest backend/tests/test_ingestion.py backend/tests/test_pipeline.py backend/tests/test_fallback_routing.py -v
```

Or from the `backend/` directory:
```bash
cd backend
pytest tests/ -v
```

---

## 2. Test Module Breakdown

### A. Ingestion Tests ([`backend/tests/test_ingestion.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/tests/test_ingestion.py))
- `test_load_scheme_register`: Validates parsing of `title: URL` lines from `schemes_list.txt`.
- `test_slug_from_url`: Verifies extraction of canonical slugs from myScheme URLs.
- `test_clean_text_strips_markup`: Ensures HTML markup and markdown links/syntax are stripped cleanly.
- `test_document_from_payload_has_required_fields`: Confirms API response transformation preserves `doc_id`, `title`, `source_url`, `content`, and `metadata`.
- `test_ingest_schemes_writes_active_english_json`: Tests that mocked API ingestion writes valid JSON to `active_english.json`.

### B. Pipeline Orchestration Tests ([`backend/tests/test_pipeline.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/tests/test_pipeline.py))
- `test_pipeline_passes_retrieved_context_to_generator`: Uses protocol stubs to verify context assembly and citation propagation without loading PyTorch or Ollama.
- `test_pipeline_returns_no_results_when_retriever_empty`: Confirms that empty retrieval yields an immediate `"no_results"` response with confidence `0.0`.

### C. Fallback Routing Tests ([`backend/tests/test_fallback_routing.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/tests/test_fallback_routing.py))
- `test_fallback_router_direct_route`: Confirms scores $\ge 0.6$ trigger `route = "direct"` without caveats.
- `test_fallback_router_fallback_route`: Confirms scores $< 0.6$ trigger `route = "fallback"` and append the official portal verification caveat.
- `test_fallback_router_confidence_clamping`: Confirms out-of-bound scores ($<0.0$ or $>1.0$) are clamped safely to $[0.0, 1.0]$.

---

## 3. Runtime Verification Scripts

Helper scripts in [`backend/scripts/`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/scripts/) provide diagnostic checks:

| Script | Purpose | Command |
|---|---|---|
| `status.py` | Verify total documents, ChromaDB collection count, and metadata completeness. | `python backend/scripts/status.py` |
| `corpus_summary.py` | Display granular document and chunk breakdown across myScheme and Goa government PDF sources. | `python backend/scripts/corpus_summary.py` |
| `smoke_retrieval.py` | Run quick dense + BM25 retrieval for sample queries. | `python backend/scripts/smoke_retrieval.py` |
| `test_api_live.py` | Test running FastAPI server via live HTTP requests. | `python backend/scripts/test_api_live.py` |
| `test_konkani_query.py` | Execute end-to-end Konkani queries against the live server. | `python backend/scripts/test_konkani_query.py` |

---

## 4. Stage-Isolated Empirical Evaluation Protocol

For upcoming research publications, evaluation will be conducted stage-by-stage across 15–20 curated Goan Konkani question-answer pairs:

```
[Query in Konkani] ──> Stage 1: Translation ──> [Query in English]
                    ──> Stage 2: Retrieval   ──> [Top-k Passages]
                    ──> Stage 3: Generation  ──> [English Answer]
                    ──> Stage 4: Translation ──> [Konkani Answer]
```

1. **Translation Quality:** Measured via `chrF++` and `BLEU` against human-verified gold references.
2. **Retrieval Performance:** Measured via `Recall@k` ($k \in \{1, 3, 5\}$), `MRR`, and `Hit Rate` against ground-truth document IDs.
3. **Generation Faithfulness:** Measured via NLI entailment / groundedness ratio (fraction of claims supported by context).
4. **Fallback Efficiency:** Evaluated by measuring false-alarm rates and latency differences between direct and fallback routes.
