# Project Overview

> **Research baseline:** [RESEARCH_PLAN.md](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/docs/RESEARCH_PLAN.md) defines the research questions; [IMPLEMENTATION_STATUS.md](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/docs/IMPLEMENTATION_STATUS.md) details verified runtime execution.

---

## Purpose

The **Government AI Assistant** is a multilingual, privacy-conscious Retrieval-Augmented Generation (RAG) system built to make Indian government scheme information accessible to citizens in low-resource and under-resourced Indian languages.

**Goan Konkani in Devanagari script (`kok` / `gom_Deva`)** is the primary low-resource language case study, supported alongside English (`en`). The target domain focuses on **Goan educational scholarships, fellowship schemes, youth welfare, and public policy initiatives**.

---

## Problem Statement

Government scheme information is historically fragmented across central portals, state gazettes, department PDF circulars, and institutional notifications. Citizens who communicate predominantly in under-resourced Indian languages such as Konkani face steep access barriers:
1. Official circulars are almost exclusively published in English.
2. Direct translation via general-purpose online translators often mistranslates legal eligibility criteria, income caps, or stipend values.
3. Standard Large Language Models hallucinate scheme guidelines, deadlines, and benefits when answering in low-resource languages.

---

## Solution Architecture

This system bridges that gap through a grounded Multilingual RAG pipeline:
- **Authoritative English Knowledge Base:** An active retrieval corpus of **68 official documents** (58 central/state schemes from myScheme.gov.in + 10 state circulars/charters from SCERT Goa, DOL Goa, and Goa Government portals), segmented into **318 indexed passages**.
- **Hybrid Retrieval:** Dense semantic embeddings (`all-MiniLM-L6-v2`) combined with lexical keyword matching (`BM25Okapi`) fused via Reciprocal Rank Fusion ($k=60$) to accurately capture both conceptual inquiries ("higher education aid") and specific proper nouns ("Sant Sohirobanath Ambiye").
- **Language Bridge:** High-fidelity bidirectional translation using AI4Bharat's **IndicTrans2 200M** (`gom_Deva` ↔ `eng_Latn`) with Meta's **NLLB-200 600M** as an ungated fallback proxy.
- **Strictly Grounded Generation:** Local Ollama running `llama3.2` constrained to answer only from retrieved evidence, citing source URLs and scheme names.
- **Adaptive Fallback Routing:** Confidence evaluation against a verified threshold (`CONFIDENCE_THRESHOLD = 0.6`). When retrieval evidence is sparse or ambiguous, the system attaches official verification caveats.
- **Accessible UI:** A lightweight, dependency-free web client ([`chat.html`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/chat.html)) allowing citizens to seamlessly toggle between English and Konkani.

---

## Current Status & Verification

| Dimension | Implemented & Verified |
|---|---|
| **API Server** | FastAPI server running locally at `http://127.0.0.1:8000` with endpoints `/query`, `/health`, `/translate/status`, and Swagger UI (`/docs`). |
| **Active Knowledge Base** | 68 documents (58 JSON + 10 Goa State Government PDFs) → 318 chunks indexed in ChromaDB. |
| **Retrieval Engine** | Hybrid Dense + BM25 with Reciprocal Rank Fusion ($k=60$). |
| **Generation Engine** | Local Ollama `llama3.2` with low-temperature factual conditioning and prompt cap. |
| **Translation Engine** | Two-tier translation service with IndicTrans2 and NLLB-200. |
| **Fallback Routing** | Operational `FallbackRouter` returning direct answers or caveat-annotated fallback guidance. |
| **User Interface** | Functional `chat.html` web application. |
| **Automated Testing** | 10 unit tests passing on `pytest`. |

---

## Ethical Boundaries & Research Caution

- **Hallucination Mitigation:** Grounding generation in retrieved text substantially curtails unsupported claims, but cannot guarantee 100% factual accuracy.
- **Official Guidance:** The assistant acts as an informative guide; answers cite official portals (`myscheme.gov.in`, `scert.goa.gov.in`, `dol.goa.gov.in`) where citizens can verify eligibility and apply directly.
