# Data Model

> **Research baseline:** Model active English retrieval documents separately from Konkani/Marathi translation-audit references. See [RESEARCH_PLAN.md](RESEARCH_PLAN.md); repository evidence remains in [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md).

## Status

The current backend model files are placeholders. This document defines the target conceptual data model and labels fields as planned/proposed where they are not implemented.

Existing repository evidence:

- `data/` contains placeholder folders for raw, processed, metadata, and ChromaDB storage.
- `backend/pyproject.toml` includes SQLAlchemy, SQLite/PostgreSQL drivers, ChromaDB, sentence-transformers, and rank-bm25.
- No implemented database schema was found in backend model files.

## Source Document

Represents an official or authoritative education-domain source.

Planned fields:

| Field | Status | Notes |
|---|---|---|
| `id` | Planned | Stable internal identifier. |
| `title` | Planned | Source title where available. |
| `source_uri` | Planned | URL, file path, or repository origin. |
| `issuing_body` | Planned | Department/authority where known. |
| `document_type` | Planned | Scheme, scholarship, notification, guideline, FAQ, etc. |
| `language` | Planned | Language code where known; final supported set To be determined. |
| `published_date` | Planned | Optional, only if known. |
| `collected_at` | Planned | Ingestion timestamp. |
| `corpus_role` | Proposed | `active_retrieval`, `reference`, `translation`, or `audit`; exact enum To be determined. |

## Document Metadata

Metadata should support filtering, auditability, and citation. It should not invent facts that are missing from the source.

Planned metadata categories:

- Source provenance.
- Education-domain category.
- Jurisdiction or geography where explicitly known.
- Language and script where known.
- Date information where available.
- License/access notes where available.

## Chunk

Represents a segment of a source document used for retrieval.

Planned fields:

| Field | Status | Notes |
|---|---|---|
| `id` | Planned | Stable chunk identifier. |
| `document_id` | Planned | Links to source document. |
| `text` | Planned | Cleaned chunk text. |
| `chunk_index` | Planned | Position within document. |
| `page_start` / `page_end` | Planned | Optional, where page data exists. |
| `section_title` | Planned | Optional. |
| `language` | Planned | Language of chunk where known. |
| `metadata` | Planned | Structured fields used for filtering/citation. |

Chunk size and overlap are To be determined experimentally.

## Embedding / Index Representation

Represents search index entries for chunks.

Planned/proposed fields:

| Field | Status | Notes |
|---|---|---|
| `chunk_id` | Planned | Links index entry to chunk. |
| `embedding_vector` | Planned | Stored in vector database where applicable. |
| `embedding_model` | To be determined | Do not finalize a model until selected. |
| `index_name` | Planned | Search collection/index identifier. |
| `lexical_terms` | Proposed | For BM25 or other lexical index if implemented. |
| `created_at` | Planned | Indexing timestamp. |

Repository configuration names ChromaDB and rank-bm25, but final index schema is not implemented.

## Retrieval Result

Represents evidence candidates returned for a query.

Planned fields:

| Field | Status | Notes |
|---|---|---|
| `chunk_id` | Planned | Retrieved chunk. |
| `document_id` | Planned | Source document. |
| `text` | Planned | Retrieved evidence text or reference. |
| `retrieval_method` | Planned | Dense, lexical, hybrid, or fallback route; final enum To be determined. |
| `score` | Planned | Retrieval score; not proof of correctness. |
| `rank` | Planned | Position in returned results. |
| `route` | Proposed | Primary or fallback route if fallback routing is implemented. |

## Evidence / Citation

Represents evidence presented to the user or used to support generation.

Planned fields:

| Field | Status | Notes |
|---|---|---|
| `citation_id` | Planned | Display identifier such as `[1]`; exact format To be determined. |
| `document_id` | Planned | Source document. |
| `chunk_id` | Planned | Supporting chunk. |
| `source_uri` | Planned | Link/path where available. |
| `title` | Planned | Source title. |
| `page_or_section` | Planned | Optional reference location. |
| `supporting_text` | Planned | Evidence excerpt or reference. |

Citations must be treated as support references, not guarantees that every generated claim is correct.

## Query

Planned fields:

| Field | Status | Notes |
|---|---|---|
| `id` | Planned | Query identifier. |
| `session_id` | Planned | Optional session link. |
| `raw_text` | Planned | Original user query. |
| `detected_language` | Planned | To be determined by language identification. |
| `normalized_text` | Planned | Optional normalized query. |
| `route_used` | Proposed | Primary/fallback route tracking if implemented. |
| `created_at` | Planned | Timestamp. |

## Response

Planned fields:

| Field | Status | Notes |
|---|---|---|
| `id` | Planned | Response identifier. |
| `query_id` | Planned | Links to query. |
| `answer_text` | Planned | Grounded answer or no-supported-answer message. |
| `output_language` | Planned | Final response language where known. |
| `citations` | Planned | Supporting evidence references. |
| `evidence_status` | Proposed | Sufficient / insufficient; exact values To be determined. |
| `generated_at` | Planned | Timestamp. |

## Session

Planned fields:

| Field | Status | Notes |
|---|---|---|
| `id` | Planned | Session identifier. |
| `started_at` | Planned | Session start. |
| `last_active_at` | Planned | Optional. |
| `preferred_language` | Planned | Optional; final language set To be determined. |
| `messages` | Planned | Query/response history if retained. |

## Feedback

Feedback is applicable if the implementation includes user ratings or comments.

Planned fields:

| Field | Status | Notes |
|---|---|---|
| `id` | Planned | Feedback identifier. |
| `response_id` | Planned | Response being evaluated. |
| `rating` | Planned | Exact scale To be determined. |
| `comment` | Planned | Optional user text. |
| `created_at` | Planned | Timestamp. |

## Open Decisions

- Final persistence layer: To be determined.
- Final language-code enum: To be determined.
- Final source metadata requirements: To be determined.
- Embedding model and dimensionality: To be determined.
- Evidence/confidence threshold: To be determined experimentally.
- Fallback-language mapping: To be determined based on linguistic/resource criteria and experimental evaluation.
