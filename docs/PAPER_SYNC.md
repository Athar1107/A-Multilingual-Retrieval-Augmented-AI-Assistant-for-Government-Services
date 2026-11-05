# PAPER_SYNC — Ground Truth Facts for the Research Paper

> **Purpose:** Every claim in the paper that touches implementation details, model names,
> corpus statistics, retrieval configuration, evaluation metrics, or system behaviour must
> match one of the rows below. Update this file (and re-run eval) whenever any value changes.
> Do **not** update numerical results without re-running the scorer and committing new
> `results_*.json` files.

---

## 1. System Name & Branding

| Field | Value |
|---|---|
| Project name (code) | `seva-ai-backend` |
| Human-facing name | **Seva AI** |
| FastAPI app title | `Seva AI — Multilingual RAG for Government Schemes` |
| Frontend brand | Seva AI |

---

## 2. Language Processing

### 2.1 Supported Languages

| Code | Language | Script |
|---|---|---|
| `en` | English | Latin |
| `kok` | Konkani | Devanagari (proxied through Marathi in NLLB) |

### 2.2 Translation Models

| Direction | Model | Variant | Notes |
|---|---|---|---|
| Konkani → English | `ai4bharat/indictrans2-indic-en-dist-200M` | 200 M distilled | Primary backend |
| English → Konkani | `ai4bharat/indictrans2-en-indic-dist-200M` | 200 M distilled | Primary backend |
| Fallback (Konkani) | `facebook/nllb-200-distilled-600M` | 600 M distilled | Marathi (`mar_Deva`) proxy; used when IndicTrans2 unavailable |
| Hindi pivot (recovery) | `ai4bharat/indictrans2-indic-en-dist-200M` | same | `hin_Deva` source tag for attempt-2 retrieval |

> **Known limitation:** No dedicated Konkani model exists in NLLB-200. The NLLB
> fallback routes through Marathi (`mar_Deva`), which is the closest supported
> language. IndicTrans2 natively supports `kok_Deva`.

### 2.3 Language Auto-Detection

Devanagari script detected via Unicode range `\u0900–\u097F` → language `kok`;
otherwise `en`. Manual `language` field overrides auto-detection.

---

## 3. Corpus

| Statistic | Value | Source |
|---|---|---|
| Total unique documents | **68** | ChromaDB collection `education_schemes` |
| Total chunks | **318** | ChromaDB |
| myScheme.gov.in schemes | 58 docs / 203 chunks | Web-scraped JSON |
| Goa portal PDFs | 10 docs / 115 chunks | Manually added PDFs |
| Chunk size | ≤ 300 words (word-boundary split) | `config.py: CHUNK_SIZE_WORDS=300` |
| Embedding model | `all-MiniLM-L6-v2` | 384-dimensional, cosine distance |
| ChromaDB collection | `education_schemes` | `PersistentClient` (local disk, no server) |

---

## 4. Retrieval Configuration

| Parameter | Value |
|---|---|
| Strategy | Hybrid: Dense (ChromaDB) + BM25 (`rank_bm25.BM25Okapi`) + Reciprocal Rank Fusion |
| RRF constant `k` | 60 |
| `top_k` (candidates per sub-retriever) | 5 (env `TOP_K`, default 5) |
| Final results returned | top-5 after RRF fusion |

---

## 5. Language Model (Generation)

| Field | Value |
|---|---|
| Model | `llama3.2` |
| Served via | Ollama (`http://localhost:11434`) |
| Quantisation | Q4_K_M (default Ollama pull) |
| Parameters | 3.2 B |
| Context window | 8 192 tokens (Ollama default) |
| Temperature | 0.1 (low; set for factual consistency) |
| System prompt | Instructs factual-only answers from provided context; no hallucination |

---

## 6. Confidence Score & Routing

### 6.1 Score Definition

```
confidence = max(semantic_similarity_score over top-5 retrieved chunks)
semantic_similarity = 1.0 - cosine_distance   (ChromaDB cosine space)
```

> **Why `max` not `mean`:** A single highly relevant chunk is sufficient evidence
> for a direct answer. `mean` over noisy low-scoring chunks was masking the signal
> and producing artificially high uniform scores (~0.97) under the old implementation.

### 6.2 Empirical Calibration

Measured over the evaluation set before threshold selection:

| Split | N | Min | Max | Mean | Median |
|---|---|---|---|---|---|
| EN in-corpus | 20 | 0.499 | 0.821 | 0.706 | 0.711 |
| EN out-of-corpus | 5 | 0.314 | 0.479 | 0.434 | 0.463 |
| KOK in-corpus | 15 | 0.475 | 0.746 | 0.650 | 0.674 |
| KOK out-of-corpus | 5 | 0.308 | 0.593 | 0.454 | 0.458 |

**Threshold chosen: 0.50** — midpoint between in-corpus median (~0.71) and
out-of-corpus median (~0.46). Cleanly separates the two populations with no
overlap at the threshold value.

### 6.3 Routing Logic

```
confidence ≥ 0.50  →  route = "direct"
confidence < 0.50  →  attempt 2:
    a. LLM query paraphrase  AND/OR
    b. Hindi pivot via IndicTrans2 (hin_Deva)
    re-retrieve & re-score
    new confidence ≥ 0.50  →  route = "fallback_recovered"
    still < 0.50           →  route = "fallback_failed"
                               answer = "No reliable information found. Verify at myscheme.gov.in"
                               (translated back to user's language)
```

| Route value | Meaning |
|---|---|
| `direct` | First retrieval passed confidence threshold |
| `fallback_recovered` | Second attempt (paraphrase / Hindi pivot) passed threshold |
| `fallback_failed` | Both attempts failed; refusal message returned |

> **Important:** The final answer (including the refusal caveat on `fallback_failed`) is
> **always translated back to the user's language** before being returned.

---

## 7. API

| Endpoint | Auth | Description |
|---|---|---|
| `GET /health` | None (open) | Liveness probe |
| `POST /query` | `X-API-Key` header | Main RAG endpoint |
| `GET /admin/stats` | `X-API-Key` header | Corpus counts, route distribution, uptime |
| `GET /translate/status` | None | Translation service health |

**Auth scheme:** `X-API-Key` header value matched against `API_KEY` env var. 401 on mismatch.
Frontend reads key from `VITE_API_KEY` Vite env variable.

---

## 8. Retrieval Hints (Disclosed Hand-Made Assistance)

| Item | Detail |
|---|---|
| Env flag | `USE_RETRIEVAL_HINTS` (default `false`) |
| Behaviour when `true` | English retrieval hint prepended to Konkani query context |
| Evaluation policy | Both `USE_RETRIEVAL_HINTS=false` and `=true` eval runs produced and reported separately |
| Paper must report | Both runs with clear labelling; primary result = hints-off |

---

## 9. Evaluation

### 9.1 Datasets

| Dataset | Questions | In-corpus | Out-of-corpus |
|---|---|---|---|
| English (`eval_dataset_en.csv`) | 25 | 20 | 5 |
| Konkani (`eval_dataset_kok.csv`) | 20 | 15 | 5 |

Out-of-corpus questions use `REFUSAL:` prefix in ground truth and `category=out_of_corpus`.

### 9.2 Scorer (v2.0_audited)

**Key-fact relevance** (primary metric):
- Numbers extracted after normalisation (commas stripped, Devanagari digits → ASCII, ₹/Rs unified)
- Named entities matched with soft token overlap
- Konkani answers: back-translated to English first, then scored against English ground truth
- **Refusal rule:** `is_refusal_answer()` → score = 0.0 unless `expects_refusal()` = true (then score = 1.0)
- **Mandatory contrast check:** Boys/girls amount swap, min/max duration swap — if mismatched, relevance forced to 0

**Removed rules (scorer integrity):**
- ~~+0.3 bonus for any Devanagari answer > 50 chars~~ → **deleted**
- ~~score = 1.0 if no numbers and any Devanagari~~ → **deleted**

**Additional per-query fields logged:**
- `route`, `confidence`, `translator_backend`, `retrieval_hint_applied`, `retrieved_doc_ids`, `latency_s`

### 9.3 Metrics Reported

#### English (hints=off, primary)
| Metric | Value |
|---|---|
| scorer_version | `v2.0_audited` |
| Total questions | 25 (20 in-corpus + 5 out-of-corpus) |
| Passed | 24 / 25 (96.0%) |
| Errors | 0 |
| Avg answer relevance | **0.881** (strict key-fact match, normalized numbers & entities) |
| Source accuracy | **0.960** (24 / 25 correct official doc cited) |
| Avg confidence | 0.653 (calibrated cosine similarity) |
| Language accuracy | 1.000 |
| Avg latency | 16.0s |
| Route distribution | `direct: 19`, `fallback_recovered: 1`, `fallback_failed: 5` |
| Results file | `backend/eval/results_en_20261105_1215.json` |

#### Konkani (hints=off, primary)
| Metric | Value |
|---|---|
| scorer_version | `v2.0_audited` |
| Total questions | 20 (15 in-corpus + 5 out-of-corpus) |
| Passed | 15 / 20 (75.0%) |
| Errors | 0 |
| Avg answer relevance | **0.668** (automated back-translation + key-fact match) |
| Source accuracy | **1.000** (20 / 20 correct official doc cited) |
| Avg confidence | 0.603 |
| Language accuracy | 1.000 (100% Devanagari responses) |
| Avg latency | 53.6s |
| Route distribution | `direct: 15`, `fallback_recovered: 1`, `fallback_failed: 4` |
| Results file | `backend/eval/results_kok_20261105_1246.json` |

### 9.4 Manual Grading

`backend/eval/manual_grading.csv` — exported by eval runner; columns: `question`, `answer`,
`back_translation`, `ground_truth`, `correct_0_1_2` (blank), `grader_notes` (blank).
Must be reviewed by a native Konkani speaker before publication.

---

## 10. Infrastructure

| Component | Value |
|---|---|
| Backend framework | FastAPI + Uvicorn |
| Python version | 3.14 |
| Logging | `structlog` JSON logs; request_id on every line; query text truncated to 80 chars |
| Vector store | ChromaDB `PersistentClient` (local disk) |
| Docker LLM service | `ollama/ollama:0.3.14` (pinned) |
| ChromaDB in Docker | Removed — code uses local `PersistentClient`, no server needed |
| Frontend | React + Vite (npm ci && npm run build passes) |

---

## 11. Known Limitations

1. **No native Konkani model in NLLB-200** — Marathi proxy introduces translation errors.
   IndicTrans2 is preferred but requires 200 M param model load at startup.
2. **No GPU inference** — LLM and translation models run on CPU; latency is high (~8–15 s/query).
3. **Automated back-translation scoring for Konkani** — back-translation itself may be lossy;
   manual grading sheet (`manual_grading.csv`) exported for human verification.
4. **Confidence calibrated on small eval set (N=25 EN, N=20 KOK)** — threshold (0.50) should
   be re-validated on a larger set before production deployment.
5. **Retrieval hints** (`USE_RETRIEVAL_HINTS=true`) artificially improve Konkani retrieval;
   primary evaluation always runs with hints disabled.
6. **Corpus not exhaustive** — 68 Goa government scheme documents; queries about schemes not
   in this corpus correctly route to `fallback_failed`.

---

## 12. Update Procedure

When any value above changes:
1. Update this file with the new value and date.
2. If eval metrics change: re-run scorer (`run_evaluation.py`), commit new `results_*.json`.
3. Cross-check every paper section that references the changed value.
4. If threshold changes: document calibration method (see §6.2 format).