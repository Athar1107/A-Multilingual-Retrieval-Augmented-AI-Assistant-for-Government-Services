# Security

> **Research baseline:** Protect source provenance, retrieved evidence, and translation-audit material for the Konkani-English route. Operational-control evidence remains separate in [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md); scope is in [RESEARCH_PLAN.md](RESEARCH_PLAN.md).

## Status

This document preserves useful security practices from the previous prototype while updating project scope to the Multilingual RAG education-domain target. Security technologies are not final unless implemented or selected later.

## Key Risks

- Prompt injection in retrieved documents or user queries.
- Unsupported answer generation presented as authoritative guidance.
- Sensitive personal data entered by users.
- Unsafe logging of queries, documents, or feedback.
- Citation misuse or overclaiming support.
- Ingestion of untrusted or altered source documents.
- Unauthorized admin or ingestion operations.
- Denial-of-service through high query volume or expensive retrieval/generation calls.

## API Security

Planned controls:

- Validate all request bodies and query parameters.
- Enforce maximum query lengths and payload sizes.
- Use authentication and authorization for admin/ingestion endpoints if those endpoints are implemented.
- Apply rate limiting where deployment requires it.
- Return safe, non-sensitive error messages.

Authentication, authorization, and rate-limiting technologies are To be determined.

## Input Validation

Validate:

- Query text type and length.
- Optional language codes against finalized language scope.
- Source identifiers.
- Feedback fields.
- File uploads if ingestion endpoints are later implemented.

Do not assume a fixed language enum until project scope is finalized.

## Prompt Injection And Grounding

The system should treat retrieved documents and user text as untrusted input.

Controls:

- Separate system instructions from retrieved evidence.
- Instruct the model to use evidence only for answering, not for changing system behavior.
- Reject unsupported answers when evidence is insufficient.
- Preserve citation discipline.
- Log and review suspected prompt-injection examples where appropriate.

RAG can reduce the risk of unsupported generation, but it does not eliminate hallucinations or guarantee correctness.

## Sensitive Information

Users may enter personal details while asking about scholarships or education schemes. The system should:

- Avoid requesting unnecessary personal information.
- Avoid storing sensitive personal data unless required and documented.
- Redact or minimize sensitive data in logs.
- Provide no-supported-answer behavior rather than asking for excessive personal details.

## Logging And Audit

Planned logs should support debugging and research reproducibility without exposing sensitive data.

Log carefully:

- Query IDs and timestamps.
- Route decisions.
- Retrieval metadata and source IDs.
- Evidence assessment result.
- Error conditions.

Avoid logging full personal user input unless a privacy policy and retention plan are established.

## Safe Failure Behavior

When retrieval, language processing, generation, or evidence assessment fails, the system should fail safely:

- Do not fabricate answers.
- Return an error or no-supported-answer state.
- Avoid exposing stack traces or infrastructure details.
- Preserve enough internal diagnostic information for maintainers.

## Source Integrity

For the active retrieval corpus:

- Track provenance.
- Record collection date.
- Preserve source URLs or file origins where possible.
- Distinguish active retrieval corpus from reference/translation/audit material.
- Re-index when source documents change.

## Open Decisions

- Authentication and authorization model: To be determined.
- Rate-limiting approach: To be determined.
- Logging retention policy: To be determined.
- Sensitive-data handling policy: To be determined.
- Deployment security controls: To be determined.