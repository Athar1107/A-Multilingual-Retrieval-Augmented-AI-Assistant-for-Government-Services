# Research Plan Baseline

**Source of truth:** `konkani-rag-research-paper-v7.md`, supplied by the project owner on 2026-09-29. This document translates that paper into repository documentation. It does not overwrite the separate source-tree audit in [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md).

## Research Scope

The project is a multilingual Retrieval-Augmented Generation (RAG) research prototype for public-service information access in low-resource Indian languages. The primary case study is **Konkani written in Devanagari**, in the domain of **Goan education and government scholarship schemes**.

The system is intended to give grounded policy guidance; it is not a guarantee of factual correctness. Retrieval, citations, translation, and fallback routing may reduce risks but do not eliminate hallucination, semantic drift, or error propagation.

## Language Taxonomy

| Tier | Defined scope |
|---|---|
| Architecture | Language-agnostic design for under-resourced scripts with a multilingual embedding or NMT path. |
| Current prototype route | Konkani (Devanagari) is the input/output language (`L1`); English is the active knowledge-base and pivot language. |
| Evaluation | A hand-written gold set of 15–20 Konkani question-answer pairs. Results are not yet available. |
| Future languages | Any additional Indian languages are future work, not an implementation or evaluation claim. |

The fallback language (`L2`) is **to be determined based on linguistic/resource criteria and experimental evaluation**. It must not be hardcoded or presented as a proven improvement.

## Data Governance

The intended authoritative sources are:

- **myScheme** (`myscheme.gov.in`) for central and state schemes;
- **SCERT Goa** (`scert.goa.gov.in`) for scholarship and education guidance;
- **Directorate of Official Language, Goa** (`dol.goa.gov.in`) for policy documents and citizen charters.

The active retrieval index contains English policy documents. Native Konkani and Marathi material from SCERT Goa and DOL Goa belongs to an offline **translation-audit reference set** and must not be added to the active retrieval index without a documented design change.

### Maintained Scheme Register

[`schemes_list.txt`](../schemes_list.txt) is the maintained input register for myScheme records. Each line currently provides a human-readable scheme title and its myScheme URL. It is expected to change as schemes are added, removed, or corrected.

This register is not itself the active retrieval corpus. Ingestion must fetch or otherwise capture the authoritative English document content, record provenance and collection date, validate/deduplicate records, and write retrieval-ready documents and metadata before indexing. Keep the register version or collection timestamp with each ingestion run so index contents remain reproducible.

## Component Classification

| Classification | Research-plan position |
|---|---|
| Implemented local-prototype capabilities | English knowledge base; ChromaDB dense retrieval; SQLite/BM25 sparse retrieval; IndicTrans2 supporting translation; local quantized generation with protected inline citations; FastAPI/Uvicorn backend and a single-page HTML/JS chat UI. |
| Proposed | Language identification/direct multilingual processing; dual-metric evidence validation using vector similarity plus NLI entailment. |
| Experimental | Adaptive Fallback Language Routing; confidence threshold `tau`; dense/sparse fusion weight `alpha`. |
| Future work | PostgreSQL/pgvector or Qdrant scaling, LangGraph reflection, low-fertility tokenizers, and BHASHINI integration. |

The preceding “implemented” row reports the prototype status in the research paper. Whether a capability is represented by the files in this repository is reported separately in [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md); do not conflate the two evidence sources.

## Target Runtime Flow

1. Receive a Konkani-Devanagari query and perform language-aware preprocessing.
2. Search the active English corpus with parallel dense and BM25 retrieval.
3. Merge candidates using a normalized fusion method; `alpha` is experimental.
4. Assess evidence using vector similarity and NLI entailment; `tau` is experimental.
5. If evidence is sufficient, generate a grounded Konkani answer with protected inline source tags.
6. If evidence is insufficient, evaluate the experimental fallback path through `L2`; otherwise return a no-supported-answer response.

## Evaluation Protocol

Use stage-isolated comparison so translation noise does not hide retrieval failure:

| Stage | Measures |
|---|---|
| Retrieval | Recall@k, context precision/recall, MRR, nDCG |
| Generation | Answer correctness, relevance, faithfulness/NLI entailment ratio, Token-F1/Exact Match |
| Supporting translation | chrF/chrF++ and BLEU against human-verified references |
| Fallback | Rescue rate and latency overhead |

Compare a native primary route, an English-pivot translation route, and the fallback-routing approach. No metric result, threshold, or performance advantage is currently claimed.
