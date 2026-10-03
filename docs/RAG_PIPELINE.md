# RAG Pipeline

> **Research baseline:** The active corpus is English. Konkani (Devanagari) is the primary user language; native Konkani/Marathi documents are offline translation-audit references. See [RESEARCH_PLAN.md](RESEARCH_PLAN.md).

## Status

This is the target pipeline specification for the Multilingual RAG research prototype. It is documentation for planned implementation, not proof that the pipeline is already implemented.

## 1. Knowledge Acquisition

Collect official or authoritative education-related government sources such as schemes, scholarships, financial assistance notices, eligibility documents, application guidelines, benefits, and notifications.

Current status:

- Target corpus: To be determined.
- Source-selection criteria: To be determined.
- Corpus size: To be determined.

## 2. Document Processing

Planned processing:

- Parse PDFs, HTML, text, or other selected source formats.
- Preserve source identity, URL or origin, issuing body, date information where available, and language metadata where known.
- Separate active retrieval documents from translation, reference, or audit material.

Repository evidence: dependencies include PyMuPDF, BeautifulSoup, Unstructured, and lxml, but processing modules are placeholders.

## 3. Cleaning

Planned cleaning should remove or normalize boilerplate, repeated headers/footers, broken whitespace, encoding artifacts, and layout noise without deleting legally or administratively meaningful text.

Konkani-specific and script-specific cleaning rules are To be determined.

## 4. Chunking

Chunking should create retrieval-sized units that preserve enough context for education-scheme questions. Chunk size, overlap, and boundary rules are not experimentally finalized.

Initial prototype configuration values from old documentation must be treated only as defaults if reused, not optimal settings.

## 5. Metadata

Planned metadata may include:

- Source document identifier.
- Title.
- Source URL or file path.
- Issuing body or department where known.
- Document date where known.
- Domain/category such as scholarship, eligibility, benefit, or application process.
- Language code where known.
- Chunk position and page/section reference where available.
- Active corpus versus reference/audit classification.

Exact required fields are To be determined during implementation.

## 6. Indexing

Planned indexing:

- Dense vector indexing where applicable.
- Lexical indexing where applicable.
- Metadata filters for domain, source, language, and date where implemented.

Repository evidence: ChromaDB and rank-bm25 are present in dependency/config files. Final embedding model and retrieval store configuration are To be determined.

## 7. Query Processing

The target system should:

- Receive the user query.
- Identify language or route language handling where required.
- Normalize the query without changing meaning.
- Apply language processing / translation where required by the selected route.

No final list of supported languages is established. Konkani is the primary case study.

## 8. Retrieval

Retrieval should search the active retrieval corpus and return candidate evidence chunks.

Planned retrieval modes:

- Dense retrieval.
- Lexical retrieval.
- Hybrid retrieval / result combination where applicable.

Specific top-k values, weights, retrieval thresholds, and reranking choices are To be determined experimentally.

## 9. Evidence Assessment

Evidence assessment decides whether retrieved material is sufficient to answer the query.

Required caution:

- Retrieval scores do not guarantee correctness.
- Retrieved evidence does not automatically guarantee factual correctness.
- Citations do not guarantee that every generated claim is supported.
- Evidence/confidence threshold: To be determined experimentally.

## 10. Adaptive Fallback Routing

Adaptive Fallback Language Routing is a **proposed research component**, not an implemented feature in the current scaffold.

Conceptual behavior:

1. Try the primary language route.
2. Retrieve and assess evidence.
3. If evidence is insufficient, use a fallback language route if the finalized research design defines one.
4. Retrieve and assess fallback evidence.
5. If evidence is still insufficient, return a no-supported-answer response.

Fallback-language mapping: To be determined based on linguistic/resource criteria and experimental evaluation.

Possible trade-offs:

- Additional latency.
- Additional processing.
- Cascading translation errors.
- Semantic drift.
- Uncertain performance improvement.

## 11. Grounded Generation

When evidence is sufficient, the generation model should answer only from retrieved evidence and explicitly avoid unsupported claims.

Generation model: To be determined. Repository configuration mentions Ollama/Llama 3.1 from the previous prototype, but this is not a finalized target model.

## 12. Output-Language Handling

The response should be delivered in the appropriate output language where supported by the target design. Output translation must preserve citation markers and should not introduce new claims.

Language-processing technology and quality criteria are To be determined.

## 13. Evidence And Citations

Answers should include citations or evidence references sufficient for user review. Citation format is To be determined, but each cited claim should be traceable to retrieved source material.

## 14. No-Supported-Answer Behavior

If evidence is insufficient after the allowed route(s), the system should say that it cannot provide a supported answer from the available sources and should avoid fabricating eligibility, deadlines, benefits, or application instructions.
