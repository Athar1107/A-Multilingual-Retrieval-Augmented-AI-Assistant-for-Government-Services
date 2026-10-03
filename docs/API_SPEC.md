# API Specification

> **Research baseline:** API behavior must support Konkani (Devanagari) queries over the English active corpus, traceable citations, and a no-supported-answer outcome. Fallback routing remains experimental; see [RESEARCH_PLAN.md](RESEARCH_PLAN.md).

## Status

The existing backend API modules are mostly placeholders. This specification preserves a useful target API shape while clearly distinguishing existing scaffold from planned endpoints. No source code is changed by this documentation.

## Existing Scaffold

Repository evidence:

- `backend/pyproject.toml` includes FastAPI and related dependencies.
- Files exist for `chat.py`, `search.py`, `sources.py`, `feedback.py`, `admin.py`, and `health.py`.
- `chat.py` contains only a comment indicating implementation is pending.
- Other API files are effectively empty placeholders.

No fully implemented endpoint behavior is established from the current source.

## Planned API Principles

- Responses must distinguish grounded answers from no-supported-answer responses.
- API contracts must not assume a fixed list of supported languages until finalized.
- Retrieval evidence and citations should be traceable to source documents.
- Fallback routing fields should be optional/proposed until implemented.
- Numeric thresholds and model-specific metadata should not be hardcoded in documentation unless finalized.

## Planned Endpoints

### Health

`GET /api/v1/health/live`

Planned purpose: process liveness check.

`GET /api/v1/health/ready`

Planned purpose: readiness check for dependencies such as retrieval store, relational store, model service, or embedding service where used.

Dependency names and checks are To be determined.

### Chat

`POST /api/v1/chat/message`

Planned request:

```json
{
  "session_id": "optional-session-id",
  "query": "user question",
  "language": "optional language code"
}
```

Planned response:

```json
{
  "answer": "grounded answer or no-supported-answer message",
  "output_language": "to be determined",
  "evidence_status": "sufficient_or_insufficient",
  "citations": [],
  "route": {
    "primary_language": "to be determined",
    "fallback_attempted": false,
    "fallback_language": "to be determined"
  }
}
```

Fallback route fields are proposed and should not be required until implemented.

### Search

`GET /api/v1/search`

Planned purpose: retrieve evidence chunks/documents from the active retrieval corpus.

Possible query parameters:

- `q`: query text.
- `language`: optional language filter; final allowed values To be determined.
- `document_type`: optional education-domain filter.
- `limit`: optional result count; default To be determined.

### Sources

`GET /api/v1/sources`

Planned purpose: list indexed or available source documents.

The API must distinguish indexed active retrieval corpus entries from reference/audit material if both exist.

`GET /api/v1/sources/{source_id}`

Planned purpose: return source metadata and available chunks or citation details where allowed.

### Feedback

`POST /api/v1/feedback`

Planned purpose: collect user or evaluator feedback on a response.

Schema and rating scale: To be determined.

### Admin / Ingestion

Admin endpoints are planned only if the implementation requires runtime ingestion or maintenance operations.

Authentication/authorization requirements: To be determined.

## Not Yet Specified

- Final OpenAPI schema.
- Authentication model.
- Rate limits.
- Error code taxonomy.
- Final language enum.
- Evidence/confidence threshold.
- Fallback-language mapping.
- Final deployment URLs.
