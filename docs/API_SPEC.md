# API Specification

> **Research baseline:** [RESEARCH_PLAN.md](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/docs/RESEARCH_PLAN.md) outlines the architectural principles. This document specifies the active, running REST API implemented in [`backend/app/main.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/main.py) and [`backend/app/schemas.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/schemas.py).

## Status: Live & Implemented

The API is built using **FastAPI** and served with **Uvicorn** (standard port `8000`). It features lazy pipeline initialization to ensure rapid server boot times, CORS middleware enabled for cross-origin web clients, and automatic Swagger documentation at `/docs`.

Base URL (Local Development): `http://127.0.0.1:8000`

---

## Active Endpoints Summary

| Method | Endpoint | Purpose | Implemented |
|---|---|---|---|
| `GET` | `/health` | Process health and liveness check | ✅ Yes |
| `GET` | `/translate/status` | Active translation backend state and diagnostic note | ✅ Yes |
| `POST` | `/query` | End-to-end RAG query (English & Goan Konkani) | ✅ Yes |
| `GET` | `/docs` | Interactive Swagger UI documentation | ✅ Yes |
| `GET` | `/openapi.json` | Generated OpenAPI 3.1 specification schema | ✅ Yes |

---

## Endpoint Details

### 1. Health Check

Checks basic process liveness.

- **URL:** `/health`
- **Method:** `GET`
- **Authentication:** None

#### Response (`200 OK`)
```json
{
  "status": "ok"
}
```

---

### 2. Translation Service Status

Inspects which translation engine is currently active in the running pipeline.

- **URL:** `/translate/status`
- **Method:** `GET`
- **Authentication:** None

#### Response Fields:
- `backend` (string): Current translation backend. Values:
  - `"indictrans2"`: AI4Bharat IndicTrans2 200M model (native `gom_Deva` / `kok`).
  - `"nllb_marathi_proxy"`: Meta NLLB-200 600M model (using Marathi `mar_Deva` pivot for Konkani).
  - `"none"`: Translation disabled; English queries only.
  - `"not_loaded"`: Pipeline has not yet received its first query (lazy-load pending).
- `note` (string): Human-readable operational explanation.

#### Example Response (`200 OK`)
```json
{
  "backend": "indictrans2",
  "note": "Native Konkani (kok_Deva) via IndicTrans2"
}
```

---

### 3. Query Execution (`/query`)

Runs an English or Goan Konkani query through the full multilingual RAG pipeline:
1. Translates non-English queries to English.
2. Conducts hybrid dense (ChromaDB) and sparse (BM25) search with Reciprocal Rank Fusion.
3. Formulates context from top passages.
4. Generates a grounded response via local Ollama (`llama3.2`).
5. Evaluates retrieval confidence via `FallbackRouter`.
6. Translates the final answer back to the requested user language (if Konkani).
7. Gathers source provenance URLs.

- **URL:** `/query`
- **Method:** `POST`
- **Headers:** `Content-Type: application/json`
- **Request Model:** [`QueryRequest`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/schemas.py#L6-L14)
- **Response Model:** [`QueryResponse`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/schemas.py#L23-L31)

#### Request Body
```json
{
  "text": "What is the benefit amount for the PM scholarship scheme?",
  "language": "en"
}
```

#### Field Specifications:
- `text` (string, required): 1 to 2,000 characters. The user's question.
- `language` (string, optional): ISO code. Defaults to `"en"`. Supported values:
  - `"en"`: English.
  - `"kok"`: Goan Konkani (Devanagari script).

#### Response Body (`200 OK`)
```json
{
  "query": "What is the benefit amount for the PM scholarship scheme?",
  "answer": "The Prime Minister's Scholarship Scheme provides financial assistance of ₹2,500 per month for male students and ₹3,000 per month for female students to pursue professional degree courses.",
  "confidence": 0.9833,
  "route": "direct",
  "sources": [
    {
      "title": "Prime Minister's Scholarship Scheme",
      "source_url": "https://www.myscheme.gov.in/schemes/pmss"
    }
  ]
}
```

#### Low-Confidence / Fallback Response Example
When normalized retrieval confidence is below `0.6`, `route` is marked `"fallback"` and a verification caveat is automatically attached:
```json
{
  "query": "What are the rules for sports quota grants?",
  "answer": "Under the Free Education for Sports Medal Winners scheme, eligible athletes receive financial support for tuition and training fees.\n\n⚠️ I found some related information but I'm not confident enough to give a definitive answer. Please verify with the official scheme portal at https://www.myscheme.gov.in or contact the relevant government office.",
  "confidence": 0.4500,
  "route": "fallback",
  "sources": [
    {
      "title": "Free Education For Sports Medal Winners / Participants In National / International Competitions",
      "source_url": "https://www.myscheme.gov.in/schemes/fesmwpnie"
    }
  ]
}
```

#### Error Responses:
- `422 Unprocessable Entity`: Validation failure (empty string or text > 2000 chars).
- `503 Service Unavailable`: Pipeline initialization error (e.g. missing ChromaDB index or unavailable model assets).

---

## Client Integration

### CORS Configuration
The production frontend is served by Nginx on the same origin as the API.
For development, CORS accepts only the comma-separated origins explicitly set
in ALLOWED_ORIGINS; credentialed wildcard CORS is not enabled.

### cURL Example
```bash
curl -X POST "http://127.0.0.1:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"text": "मुलींसाठी कोणत्या शिष्यवृत्ती योजना उपलब्ध आहेत?", "language": "kok"}'
```
