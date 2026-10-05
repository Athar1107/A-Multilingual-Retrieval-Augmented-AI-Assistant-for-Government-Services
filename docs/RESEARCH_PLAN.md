# Research Plan Baseline

**Source of truth:** `konkani-rag-research-paper-v7.md`, owner-approved research baseline.  
See [IMPLEMENTATION_STATUS.md](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/docs/IMPLEMENTATION_STATUS.md) for verified repository implementation.

---

## 1. Research Scope & Problem

The project investigates **Multilingual Retrieval-Augmented Generation (RAG)** for public service information access in low-resource and under-resourced Indian languages. The primary case study is **Goan Konkani in Devanagari script (`gom_Deva`)** in the domain of **Goan education and government scholarship/public-policy schemes**.

The research addresses three fundamental challenges:
1. **Resource Scarcity:** Very few administrative and legal documents are published in native Konkani.
2. **Translation Fragility:** Direct machine translation of policy documents introduces cascading errors into critical numbers (eligibility age, income limits, stipends).
3. **LLM Hallucination:** Out-of-the-box LLMs hallucinate scheme guidelines when queried in low-resource Indian languages.

---

## 2. Research Hypothesis

> "A stage-isolated Multilingual RAG architecture—coupling an authoritative English knowledge base with hybrid dense/sparse retrieval and high-precision translation—can provide grounded, cited policy guidance in low-resource Indian languages while mitigating unsupported generation."

---

## 3. Implemented Prototype Architecture (Status: Verified Operational)

| Subsystem | Implemented Research Component | Technical Configuration |
|---|---|---|
| **Active Knowledge Base** | Official English policy corpus | 68 documents (58 myScheme + 10 Goa State Government PDFs) |
| **Vector Index** | ChromaDB Persistent Collection | 318 chunks, cosine distance, `all-MiniLM-L6-v2` (384-dim) |
| **Lexical Index** | BM25Okapi sparse search | In-memory token index over all 318 ChromaDB chunks |
| **Rank Fusion** | Reciprocal Rank Fusion | Constant $k=60$, 300-char prefix deduplication |
| **Language Processing** | Two-tier translation layer | IndicTrans2 200M (`gom_Deva` ↔ `eng_Latn`) + NLLB-200 600M (`mar_Deva` proxy) |
| **LLM Generation** | Grounded local generation | Ollama `llama3.2` (temperature 0.1, prompt cap 2000 chars) |
| **Fallback Routing** | Confidence-gated disclaimer routing | Baseline threshold $\tau = 0.6$, caveat attached on low score |
| **Client Interface** | Single-page responsive application | [`chat.html`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/chat.html) with language toggle and citation cards |

---

## 4. Empirical Evaluation Protocol (Active Agenda)

To rigorously assess the system without allowing translation noise to obscure retrieval failure, evaluation must use **stage-isolated measurement**:

### A. Gold-Standard Evaluation Dataset (To Be Formatted)
- **Target:** 15–20 curated question-answer pairs in Goan Konkani covering:
  - Scholarship eligibility (caste, income ceiling, age criteria).
  - Financial benefit amounts (monthly stipends, fee waivers).
  - Application guidelines and required documentation.
  - Negative queries (schemes not in corpus, e.g. PM Kisan).

### B. Stage-by-Stage Metrics

| Stage | Focus Question | Metrics |
|---|---|---|
| **1. Translation** | Does translation preserve proper nouns and figures? | chrF / chrF++, BLEU against human-verified references |
| **2. Retrieval** | Are the correct policy chunks retrieved? | Recall@k ($k \in \{1, 3, 5\}$), MRR, Hit Rate |
| **3. Generation** | Is the answer grounded and factual? | Faithfulness / Groundedness ratio, Answer Correctness |
| **4. Fallback Routing** | Does confidence routing prevent misleading answers? | Fallback activation rate, false-alarm rate, latency overhead |

---

## 5. Ethical Governance

- **Attribution & Provenance:** Every response provides direct links to official portals (`myscheme.gov.in`, `scert.goa.gov.in`, `dol.goa.gov.in`).
- **Cautious Disclosure:** RAG reduces hallucination but does not guarantee infallibility; users are reminded to verify official scheme guidelines before submitting formal government applications.
