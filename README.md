# Government AI Assistant

> An enterprise-grade multilingual RAG-powered AI assistant for Indian Government Services — supporting English and Goan Konkani (Devanagari).

---

## What It Does

Citizens can ask questions about government schemes in **English or Goan Konkani** and get grounded, cited answers from official sources.

**Knowledge base covers:**
- Central Government Schemes (PM Scholarship, NMMSS, Overseas Scholarships, etc.)
- Gujarat / Goa State Schemes
- Internship Schemes (DPIIT, NITI, DRDO, AICTE-MITACS)
- Education, Welfare, and Financial Assistance Schemes

**Example queries:**
- `"What is the benefit amount of PM scholarship scheme?"` → ₹2,500/month (boys), ₹3,000/month (girls)
- `"  "` → Konkani answer with sources

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend API | Python + FastAPI + Uvicorn |
| LLM | Llama 3.2 via Ollama (local, CPU) |
| Embeddings | `all-MiniLM-L6-v2` (ChromaDB) |
| Vector Store | ChromaDB (203 chunks, 58 schemes) |
| Hybrid Search | Dense + BM25 + RRF fusion |
| Translation | IndicTrans2 200M (Goan Konkani ↔ English) |
| Fallback Translation | NLLB-200 600M (ungated, Marathi proxy) |
| Data Source | myScheme.gov.in public API |

---

## Current Status

| Component | Status |
|---|---|
| 58 schemes ingested from myScheme API | ✅ |
| ChromaDB indexed (203 chunks) | ✅ |
| Hybrid retrieval (dense + BM25 + RRF) | ✅ |
| LLM generation (llama3.2) | ✅ |
| Goan Konkani ↔ English translation | ✅ |
| REST API (`/query`, `/health`, `/translate/status`) | ✅ |
| CI passing (10 tests) | ✅ |
| Frontend chat UI | 🔜 Planned |
| Docker deployment | 🔜 Planned |

---

## Quick Start

### Prerequisites
- Python 3.11+
- [Ollama](https://ollama.com) running with `llama3.2` pulled
- HuggingFace account with access to IndicTrans2 models (optional — falls back to NLLB)

### 1. Clone and set up

```bash
git clone https://github.com/Athar1107/A-Multilingual-Retrieval-Augmented-AI-Assistant-for-Government-Services.git
cd "A-Multilingual-Retrieval-Augmented-AI-Assistant-for-Government-Services"

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# Install dependencies
pip install httpx fastapi pydantic pydantic-settings uvicorn
pip install chromadb sentence-transformers rank-bm25 sentencepiece
```

### 2. Configure environment

```bash
cp backend/.env.example backend/.env
# Edit backend/.env and set:
# HF_TOKEN=your_huggingface_token  (for native Konkani translation)
# OLLAMA_MODEL=llama3.2
```

### 3. Ingest the corpus

```bash
cd backend
python scripts/run_ingestion.py    # Downloads 58 schemes from myScheme API
python -m app.rag.indexing         # Builds ChromaDB vector index
```

### 4. Start the server

**Windows:** Double-click `start_server.bat`

**Linux/Mac:**
```bash
cd backend
HF_TOKEN=your_token OLLAMA_MODEL=llama3.2 uvicorn app.main:app --port 8000
```

### 5. Test it

Open **http://127.0.0.1:8000/docs** in your browser.

Or use curl:
```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{"text": "What is the PM scholarship benefit?", "language": "en"}'
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `GET` | `/translate/status` | Active translation backend |
| `POST` | `/query` | Ask a question (English or Konkani) |
| `GET` | `/docs` | Swagger UI |

### Request format

```json
{
  "text": "Your question here",
  "language": "en"
}
```

`language`: `"en"` for English, `"kok"` for Goan Konkani

### Response format

```json
{
  "query": "What is the PM scholarship benefit?",
  "answer": "The PM scholarship provides ₹2,500/month for boys...",
  "confidence": 0.971,
  "route": "direct",
  "sources": [
    {
      "title": "Prime Minister's Scholarship Scheme",
      "source_url": "https://www.myscheme.gov.in/schemes/pmss"
    }
  ]
}
```

---

## Translation

The system supports **two translation backends**:

| Backend | Konkani Support | Setup Required |
|---|---|---|
| IndicTrans2 200M (ai4bharat) | Native `gom_Deva` (Goan Konkani) | HF_TOKEN + model access |
| NLLB-200 600M (Facebook) | `mar_Deva` proxy (Marathi/Devanagari) | None — downloads automatically |

Check active backend: `GET /translate/status`

---

## Project Documentation

All planning and architecture docs are in `docs/`:

| File | Contents |
|---|---|
| [AGENT.md](docs/AGENT.md) | Rules for all contributors |
| [PROJECT.md](docs/PROJECT.md) | Vision, goals, requirements |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design with diagrams |
| [RAG_PIPELINE.md](docs/RAG_PIPELINE.md) | Detailed RAG pipeline spec |
| [RESEARCH_PLAN.md](docs/RESEARCH_PLAN.md) | Research scope and methodology |
| [IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md) | Current implementation audit |

---

## Running Tests

```bash
cd backend
pytest tests/test_ingestion.py tests/test_pipeline.py tests/test_fallback_routing.py -v
```

10 tests — all passing.

---

### Frontend development

The chatbot UI is a React + Vite application in the frontend folder. Run
npm ci and then npm run dev from that folder. Vite proxies API calls to
http://127.0.0.1:8000 during local development. For containers, docker compose
up --build builds the Vite application into the Nginx image and serves it at
http://localhost.

*Read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a pull request.*
