# Tasks

> **Research baseline:** Tasks must preserve the English active-index / Konkani-Marathi translation-audit separation and treat fallback routing as experimental. See [RESEARCH_PLAN.md](RESEARCH_PLAN.md).

## Status

This checklist tracks future work for the target Multilingual RAG project. Future implementation tasks are not completed unless code and tests later demonstrate completion.

## Documentation And Research Preparation

- [x] Reposition documentation toward Multilingual RAG for under-resourced Indian languages.
- [x] Identify Konkani as the primary case study.
- [x] Narrow target domain to education and government education-scheme information.
- [x] Mark unresolved language scope, fallback mapping, thresholds, datasets, and model choices as To be determined.
- [ ] Finalize research questions.
- [ ] Finalize source-selection criteria.
- [ ] Define reproducibility requirements.

## Repository Preparation

- [ ] Audit legacy UI-language and broad government-services assumptions in source code and UI text.
- [ ] Decide whether to rename old data folders or keep them for compatibility.
- [ ] Create implementation issues from this documentation.
- [ ] Confirm development environment and dependency strategy.

## Knowledge-Base Preparation

- [ ] Identify official education/government sources for the active retrieval corpus.
- [ ] Define active retrieval corpus versus reference/translation/audit material.
- [ ] Collect source documents.
- [ ] Record provenance and metadata.
- [ ] Implement document parsing.
- [ ] Implement cleaning.
- [ ] Implement chunking.
- [ ] Implement metadata validation.
- [ ] Implement indexing.

## RAG Pipeline

- [ ] Implement query language identification.
- [ ] Implement language processing / translation where required.
- [ ] Implement dense retrieval where selected.
- [ ] Implement lexical retrieval where selected.
- [ ] Implement hybrid retrieval / result combination where selected.
- [ ] Implement evidence assessment.
- [ ] Implement grounded generation.
- [ ] Implement citation formatting.
- [ ] Implement no-supported-answer behavior.

## Adaptive Fallback Routing

- [ ] Define fallback-language mapping criteria.
- [ ] Select fallback mapping only after research justification.
- [ ] Implement configurable fallback policy.
- [ ] Implement fallback evidence assessment.
- [ ] Measure fallback activation and success.
- [ ] Measure latency impact.
- [ ] Measure answer-quality differences.
- [ ] Analyze translation errors and semantic drift.

## API And Frontend Integration

- [ ] Implement health endpoints.
- [ ] Implement chat endpoint.
- [ ] Implement search endpoint.
- [ ] Implement source metadata endpoints.
- [ ] Implement feedback endpoint if needed.
- [ ] Update frontend copy for the education/Konkani target.
- [ ] Connect frontend to grounded answers, citations, and no-supported-answer states.

## Testing And Evaluation

- [ ] Unit-test individual components.
- [ ] Integration-test pipeline stages.
- [ ] Build retrieval evaluation dataset.
- [ ] Evaluate Recall@k, retrieval hit rate, and evidence/citation accuracy.
- [ ] Evaluate answer correctness and faithfulness/groundedness.
- [ ] Evaluate language processing / translation quality where applicable.
- [ ] Evaluate fallback routing.
- [ ] Run end-to-end evaluation.

## Documentation Maintenance

- [ ] Keep API spec aligned with implemented endpoints.
- [ ] Keep data model aligned with implemented schema.
- [ ] Record model versions and configuration only after selection.
- [ ] Record experimental results only after experiments are run.
- [ ] Document limitations and unresolved decisions in every release.
