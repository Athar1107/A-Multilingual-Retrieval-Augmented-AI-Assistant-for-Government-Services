# Roadmap

> **Research baseline:** Prioritize the Konkani-English retrieval route and the stage-isolated evaluation protocol before experimental fallback routing. See [RESEARCH_PLAN.md](RESEARCH_PLAN.md).

## Status

This roadmap reflects the target Multilingual RAG research project. It is a planning document, not a completion report.

## Phase 1: Documentation And Research Alignment

Goals:

- Align documentation with the education-domain Multilingual RAG direction.
- Identify Konkani as the primary case study.
- Separate current scaffold, proposed architecture, research components, and future implementation.

Status: documentation update in progress/completed as applicable.

## Phase 2: Corpus And Research Design

Goals:

- Define official source-selection criteria.
- Identify education/government education-scheme documents.
- Define active retrieval corpus versus reference/translation/audit material.
- Define research questions and evaluation protocol.

Open decisions:

- Evaluation dataset: To be determined.
- Source list and corpus size: To be determined.
- Final language scope: To be determined.

## Phase 3: Knowledge-Base Preparation

Goals:

- Implement document collection, parsing, cleaning, chunking, metadata, embedding, and indexing.
- Preserve provenance and citation references.

Technologies may reuse existing prototype dependencies where appropriate, but final model and storage choices remain To be determined.

## Phase 4: Retrieval And Evidence Assessment

Goals:

- Implement dense retrieval where selected.
- Implement lexical retrieval where selected.
- Implement hybrid retrieval where useful.
- Implement evidence assessment and no-supported-answer decisioning.

Evidence/confidence threshold: To be determined experimentally.

## Phase 5: Grounded Generation And Language Processing

Goals:

- Implement grounded answer generation.
- Implement citation-preserving output.
- Implement language processing / translation where required.
- Ensure unsupported answers are rejected.

Final generation and language-processing models: To be determined.

## Phase 6: Adaptive Fallback Routing Experiment

Goals:

- Define fallback-language mapping criteria.
- Implement configurable fallback routing only after mapping is justified.
- Evaluate whether fallback improves evidence availability or answer quality.
- Measure latency and semantic-drift risks.

Fallback-language mapping: To be determined based on linguistic/resource criteria and experimental evaluation.

## Phase 7: API And Frontend Integration

Goals:

- Implement planned API endpoints.
- Update the legacy frontend framing to the finalized Konkani research scope.
- Display grounded answers, citations, no-supported-answer states, and feedback controls where applicable.

## Phase 8: Testing, Evaluation, And Refinement

Goals:

- Run unit and integration tests.
- Run retrieval, generation, language-processing, fallback, and end-to-end evaluations.
- Record results only after experiments are performed.
- Refine corpus, retrieval, prompts, and routing based on evidence.

## Phase 9: Finalization

Goals:

- Freeze documented architecture for the prototype submission.
- Document limitations.
- Publish reproducibility notes.
- Align implementation, API specification, data model, prompts, tests, and roadmap.
