# RAG Pipeline Specification

> **Research baseline:** [RESEARCH_PLAN.md](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/docs/RESEARCH_PLAN.md) establishes the research baseline. This document details the step-by-step pipeline as implemented in [`backend/app/rag/pipeline.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/rag/pipeline.py) and supporting modules.

---

## Pipeline Overview

The pipeline executes a synchronous 8-step workflow on a background worker thread (`asyncio.to_thread`):
```
User Query ──> [1. Translate Query] ──> [2. Hybrid Retrieve] ──> [3. Assemble Context] ──>
              ──> [4. Generate Answer] ──> [5. Fallback Route] ──> [6. Translate Answer] ──>
              ──> [7. Extract Citations] ──> QueryResponse
```

---

## Detailed Pipeline Stages

### Stage 1: Query Ingestion & Translation
- Input: User query string and language code (`"en"` or `"kok"`).
- Implementation: [`app/rag/translation.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/rag/translation.py)
- Logic:
  - If language is `"en"`, query is passed through unmodified.
  - If language is `"kok"`, it is translated to English via **IndicTrans2** (`gom_Deva` → `eng_Latn`) or **NLLB-200** (`mar_Deva` → `eng_Latn`).
  - If translation models are not loaded, the raw text is passed through.

### Stage 2: Hybrid Dense & Lexical Retrieval
- Implementation: [`app/rag/retriever.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/rag/retriever.py)
- Sub-steps:
  1. **Dense Search:** Query embedded via `SentenceTransformer("all-MiniLM-L6-v2")` and matched against ChromaDB `education_schemes` collection using cosine similarity ($top\_k$).
  2. **Sparse Search:** Tokenized query matched using `BM25Okapi` over all 318 indexed chunks in ChromaDB.
  3. **Reciprocal Rank Fusion (RRF):** Both ranked lists are combined using constant $k=60$:
     $$RRF(d) = \sum_{m \in \{\text{dense}, \text{bm25}\}} \frac{1}{60 + \text{rank}_m(d)}$$
  4. **Deduplication:** Deduped using the first 300 characters of each passage. Returns the top 5 fused passages.

### Stage 3: Context Assembly
- Retrieved passages are combined into a clean text block separated by newlines (`\n\n`).
- If no passages are retrieved, the pipeline returns immediately with `route = "no_results"` and confidence `0.0`.

### Stage 4: Grounded Answer Generation
- Implementation: [`app/rag/generator.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/rag/generator.py)
- Context length is capped at `MAX_CONTEXT_CHARS = 2000` to prevent token bloat.
- Formatted prompt sent via HTTP POST to Ollama (`/api/generate`):
  - Model: `llama3.2`
  - Temperature: `0.1` (strict factual grounding)
  - `num_predict`: `200` output tokens
  - Timeout: 180s

### Stage 5: Confidence Calculation & Fallback Routing
- Implementation: [`app/rag/fallback_routing.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/rag/fallback_routing.py)
- **Score Normalization:** RRF scores are small ($\approx 0.01 - 0.03$). Average RRF score is normalized:
  $$\text{normalised\_score} = \min(\text{raw\_avg} \times 60, 1.0)$$
- **Routing Decision:**
  - If $\text{confidence} \ge 0.6$: `route = "direct"`, raw generated answer preserved.
  - If $\text{confidence} < 0.6$: `route = "fallback"`, appends official verification caveat directing user to `myscheme.gov.in`.

### Stage 6: Output Language Translation
- If original query was in Konkani and the route is `"direct"`, the English answer is translated back to Konkani Devanagari (`eng_Latn` → `gom_Deva` or `mar_Deva` proxy).

### Stage 7: Source Citation & Provenance Extraction
- Unique source URLs and titles are deduplicated across retrieved chunks:
  ```python
  sources = [
      SourceCitation(title=r["title"], source_url=r["source_url"])
      for r in results if r["source_url"]
  ]
  ```

---

## Knowledge Base Construction (Offline)

1. **myScheme Ingestion ([`ingestion.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/services/ingestion.py)):**
   - Parses URLs in `schemes_list.txt`.
   - Fetches scheme records via public v6 REST API (`https://api.myscheme.gov.in/schemes/v6/public/schemes/{slug}`).
   - Cleans HTML and markdown formatting; saves structured JSON to `data/processed/active_english.json` (58 schemes).
2. **Goa PDF Ingestion ([`pdf_loader.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/ingestion/pdf_loader.py)):**
   - Downloads 10 official PDF circulars and charters.
   - Extracts and cleans text using PyMuPDF (`fitz`), stripping page headers, footers, and line noise.
3. **Chunking & Embedding ([`indexing.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/rag/indexing.py)):**
   - Chunks text at 300 words with title prepended.
   - Encodes chunks into 384-dimensional dense vectors with `all-MiniLM-L6-v2`.
   - Batch upserts into ChromaDB `education_schemes` collection (Total: **318 chunks** across 68 documents).
