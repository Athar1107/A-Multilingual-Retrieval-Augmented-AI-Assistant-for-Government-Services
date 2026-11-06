# Seva AI — Multilingual Government Services Assistant

> A source-grounded multilingual Retrieval-Augmented Generation (RAG) assistant for Indian and Goan Government Services — supporting English and Goan Konkani (Devanagari).

---

## What It Does

Citizens can ask questions about government schemes in **English or Goan Konkani** and get grounded, cited answers from official sources.

**Knowledge base covers:**
- Central Government Schemes (PM Scholarship, NMMSS, National Overseas Scholarships, etc.)
- Goa State Government Schemes & Citizen Charters (STSE Goa, Directorate of Official Language, South Goa Collectorate, etc.)
- Internship Schemes (DPIIT, AICTE-Mitacs, etc.)
- Education, Welfare, Fellowship, and Financial Assistance Schemes

**Example queries:**
- `"What is the monthly scholarship amount for boys under the Prime Minister Scholarship Scheme?"` → ₹2,500/month (boys), ₹3,000/month (girls)
- `"पीएम शिष्यवृत्ती योजनेंत मुलांक दरमहिन्याला किती रुपये मेळतात?"` → Konkani grounded answer with official sources and confidence routing

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend UI | React 18 + Vite SPA (`frontend/`) |
| Backend API | Python 3.11+ + FastAPI + Uvicorn + Structlog |
| LLM | Llama 3.2 via Ollama (local inference) |
| Embeddings | `all-MiniLM-L6-v2` (384-dim, cosine space) |
| Vector Store | ChromaDB `PersistentClient` (318 chunks, 68 documents) |
| Hybrid Search | Dense ChromaDB + Sparse BM25 + Reciprocal Rank Fusion (RRF, $k=60$) |
| Translation | IndicTrans2 200M distilled (`gom_Deva` ↔ `eng_Latn`, with Hindi pivot fallback) |
| Fallback Translation | NLLB-200 600M (ungated, `mar_Deva` script proxy) |
| Security | API-key authentication (`X-API-Key`), Sliding Window rate limiting |
| Deployment | Docker Compose (Nginx reverse proxy + Backend + Ollama) |

---

## Current Status

| Component | Status | Reality / Details |
|---|---|---|
| Corpus Ingestion | ✅ | **68 documents** (58 from myScheme.gov.in API + 10 official Goa government portal PDFs) |
| Vector Index | ✅ | **318 chunks** indexed in ChromaDB (`PersistentClient`) with dense embeddings & BM25 sparse index |
| Hybrid Retrieval | ✅ | Dense + BM25 fused via Reciprocal Rank Fusion ($k=60$) |
| LLM Generation | ✅ | `llama3.2` via Ollama local inference |
| Translation Layer | ✅ | IndicTrans2 200M distilled (native Goan Konkani `gom_Deva` ↔ English `eng_Latn`) with NLLB-200 fallback |
| Fallback Routing | ✅ | 3-state routing (`direct` \| `fallback_recovered` \| `fallback_failed`) with refusal detection & translation back |
| REST API | ✅ | FastAPI with `/query`, `/health`, `/translate/status`, `/admin/stats`, `/admin/dashboard`, `/api/auth/*`, `/api/conversations/*` |
| User Auth & Chat History | ✅ | PBKDF2-HMAC-SHA256 salted auth, persistent per-user consultations in SQLite, auto-saved conversations |
| Admin Command Center | ✅ | Secure dashboard for telemetry, corpus breakdown, user roster management & live query audit logs |
| Security | ✅ | `X-API-Key` & Bearer token auth, role-based access control, structlog sanitized JSON logging |
| Frontend Chat UI | ✅ | Present — React 18 + Vite SPA with consultation history sidebar, auth modal, route badges & admin console |
| Containerization | ✅ | Present — Multi-stage Dockerfile and Docker Compose with pinned images and Nginx reverse proxy |
| Automated Tests | ✅ | **26 unit and integration tests passing** (`backend/tests/`) |

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+ (for frontend)
- [Ollama](https://ollama.com) running with `llama3.2` model pulled (`ollama pull llama3.2`)
- Hugging Face token for IndicTrans2 (cached locally or set via `HF_TOKEN`)

### 1. Configure environment

```bash
# In backend/
cp backend/.env.example backend/.env
# Set API_KEY and optional HF_TOKEN in backend/.env

# In frontend/
cp frontend/.env.example frontend/.env
# Sets VITE_API_KEY matching backend API_KEY
```

### 2. Run backend

```bash
# Activate virtual environment
.\.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/macOS

# Run with uvicorn (pre-warms models during lifespan startup)
uvicorn app.main:app --app-dir backend --port 8000
```

### 3. Run frontend

```bash
cd frontend
npm ci
npm run dev
```

Open **http://localhost:5173** to chat with the assistant.

### 4. Or run via Docker Compose

```bash
docker compose up --build
```
Access the application at **http://localhost**.

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | Open | Health check and process liveness |
| `GET` | `/translate/status` | Open | Active translation backend status |
| `POST` | `/query` | `X-API-Key` | Ask a question in English or Konkani (auto-detects script) |
| `GET` | `/admin/stats` | `X-API-Key` | System uptime, query count, route telemetry, and corpus breakdown |

### Request format (`POST /query`)

```json
{
  "text": "What is the monthly scholarship amount for boys under the Prime Minister Scholarship Scheme?",
  "language": "en"
}
```
*Note: `language` is optional; if omitted, the backend auto-detects Devanagari script for Konkani.*

### Response format

```json
{
  "query": "What is the monthly scholarship amount for boys under the Prime Minister Scholarship Scheme?",
  "answer": "The monthly scholarship amount for boys under the Prime Minister Scholarship Scheme is ₹2,500 per month.",
  "confidence": 0.6729,
  "route": "direct",
  "sources": [
    {
      "title": "Prime Minister's Scholarship Scheme",
      "source_url": "https://www.myscheme.gov.in/schemes/pmss"
    }
  ],
  "translator_backend": "indictrans2",
  "retrieval_hint_applied": false,
  "retrieved_doc_ids": ["pmss"]
}
```

---

- **Security:**
  - Authenticated via `X-Admin-Key` header with constant-time HMAC digest (`hmac.compare_digest`).
  - Strict fail-closed policy (503 Service Unavailable if `ADMIN_API_KEY` is unset).
  - Rate-limited admin routes; failed attempts logged without exposing key values.
  - Secret redaction: `GET /admin/system` completely strips any fields containing `KEY`, `TOKEN`, `SECRET`, or `PASSWORD`.
  - Path traversal protection: evaluation run names validated against local filesystem directory whitelist.
  - Admin key held **only in React state** (never persisted in `localStorage` or cookies); flushes instantly on 401.

### Admin Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/admin/login` | Authenticate with username and password; exchanges for session admin key |
| `GET` | `/admin/auth/check` | Verify current `X-Admin-Key` validity |
| `GET` | `/admin/overview` | Total query counts, 24h volume, p95/avg latency, route donut, corpus stats |
| `GET` | `/admin/queries` | Filterable, paginated query log (`limit`, `offset`, `route`, `language`, `status`, `q`) |
| `GET` | `/admin/queries/{id}` | Detailed query trace with stage-level breakdown (translate_in, retrieve, generate, translate_out) |
| `GET` | `/admin/corpus` | Real-time ChromaDB collection telemetry broken down by source |
| `GET` | `/admin/corpus/{doc_id}` | Inspect chunks, dense/BM25 indexing, and token lengths for any document |
| `GET` | `/admin/eval/runs` | List audited evaluation runs from `backend/eval/` |
| `GET` | `/admin/eval/runs/{name}` | View per-question evaluation scores with `scorer_version` validation |
| `GET` | `/admin/system` | Model roster, translator backend, calibrated thresholds, live component health dots |
| `POST` | `/admin/debug/query` | Run real query pipeline with dense/BM25/fused scores (marked `source="admin"`) |
| `POST` | `/admin/reindex` | Trigger background corpus reindexing (`{"confirm": true}`, single-flight 409 locked) |
| `GET` | `/admin/reindex/status` | Current status and timestamp of background reindexing |

---

## User Authentication & Saved Consultations

Citizens can sign in or register to retain private chat history across devices:
- **Sign In / Create Account Modal:** Accessible via topbar button or sidebar promo card.
- **Demo Citizen Account:** `demo` / `demo1234`
- **Google Sign-In:** One-click OAuth login via `/api/auth/google`.
- **Private Consultations:** Per-user consultation history saved in SQLite database with instant reload and deletion.
- **Session Security:** PBKDF2-HMAC-SHA256 hashed passwords and cryptographically secure tokens.

---

## Running Evaluation

Run the audited v2.0 evaluation suite:

```bash
# Evaluate English dataset (25 queries: 20 in-corpus, 5 out-of-corpus)
python backend/eval/run_evaluation.py --dataset en

# Evaluate Konkani dataset (20 queries: 15 in-corpus, 5 out-of-corpus)
python backend/eval/run_evaluation.py --dataset kok

# Run both and generate manual grading export
python backend/eval/run_evaluation.py --dataset both
```

Exports:
- `backend/eval/results_<dataset>_<timestamp>.json`: structured metrics with `"scorer_version": "v2.0_audited"`
- `backend/eval/manual_grading.csv`: human verification sheet for native Konkani speakers.

---

## Running Tests

```bash
# Run full pytest suite (37 unit, integration, and admin operational tests)
pytest backend/tests/ -v

# Run frontend smoke tests
cd frontend && npm test
```
