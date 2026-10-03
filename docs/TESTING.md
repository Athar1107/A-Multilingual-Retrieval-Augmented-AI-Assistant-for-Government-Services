# Testing

> **Research baseline:** Evaluate 15-20 hand-written Konkani QA pairs with stage-isolated retrieval, generation, translation, and fallback measures. No results are currently claimed. See [RESEARCH_PLAN.md](RESEARCH_PLAN.md).

## Status

This document defines the target testing and evaluation strategy. It does not report completed tests, scores, thresholds, or benchmark results.

Evaluation dataset: To be determined.

## Unit Testing

Unit tests should cover individual components:

- Document loaders and parsers.
- Text cleaning.
- Chunking.
- Metadata extraction and validation.
- Language identification.
- Language processing / translation wrappers where applicable.
- Dense retriever adapters.
- Lexical retriever adapters.
- Hybrid retrieval combination.
- Evidence assessment.
- Citation formatting.
- No-supported-answer behavior.

## Integration Testing

Integration tests should verify interactions between components:

- Ingestion to searchable knowledge base.
- Query processing to retrieval.
- Retrieval to evidence assessment.
- Evidence assessment to grounded generation.
- No-supported-answer path.
- API to pipeline service.
- Frontend to API, once frontend implementation exists.

## Retrieval Evaluation

Possible retrieval metrics:

- Recall@k.
- Retrieval hit rate.
- Mean reciprocal rank where appropriate.
- Evidence/citation accuracy.
- Coverage of target education-domain question types.

No metric target is finalized. Thresholds are To be determined experimentally.

## Generation Evaluation

Possible generation criteria:

- Answer correctness.
- Faithfulness / groundedness.
- Citation support for factual claims.
- Handling of insufficient evidence.
- Clarity and usefulness.

RAG can reduce unsupported generation risk, but it does not eliminate hallucinations or guarantee correctness.

## Language-Processing Evaluation

Evaluate language and translation behavior where applicable:

- Meaning preservation.
- Terminology consistency.
- Citation-marker preservation.
- Proper handling of names, dates, monetary amounts, and official terms.
- User-facing fluency in the target language.

Language scope beyond the Konkani case study is To be determined.

## Fallback Evaluation

Adaptive Fallback Language Routing must be evaluated as a proposed research component.

Evaluate:

- Primary-route success.
- Fallback activation rate.
- Fallback success.
- Latency impact.
- Answer-quality differences.
- Cascading translation errors.
- Semantic drift.
- Cases where no-supported-answer is preferable.

Fallback-language mapping: To be determined based on linguistic/resource criteria and experimental evaluation.

## End-To-End Evaluation

End-to-end tests should cover:

- Supported query input.
- Retrieval and evidence assessment.
- Grounded answer with citations.
- No-supported-answer behavior.
- Output-language handling.
- Feedback collection if implemented.
- Failure modes such as unavailable retrieval store or model service.

## Test Data

Test data should be versioned and auditable. Synthetic examples may be used for unit tests, but evaluation claims require a documented evaluation dataset and procedure.

Do not record fabricated benchmark scores, accuracy values, Recall@k values, BLEU/COMET scores, latency measurements, or confidence thresholds.
