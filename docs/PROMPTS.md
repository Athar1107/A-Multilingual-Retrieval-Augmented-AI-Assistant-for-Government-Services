# Prompts & Model Conditioning

> **Research baseline:** Prompts must enforce strict evidence-based answering, cite official scheme names, and preserve factual fidelity across English and Konkani. See [RESEARCH_PLAN.md](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/docs/RESEARCH_PLAN.md).

---

## 1. Implemented LLM Generation Prompts ([`backend/app/rag/generator.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/rag/generator.py))

The answer generation module uses Ollama (`llama3.2`) with low temperature and an explicit length cap to prevent rambling, hallucinations, and CPU timeouts.

### System Prompt
```text
You are a helpful government services assistant. Answer questions based ONLY on the provided context about government schemes. If the context does not contain enough information to answer the question, say so clearly. Always be accurate and cite the scheme names when relevant. Keep answers concise (2-4 sentences).
```

### User Prompt Template
```text
Context:
{context}

Question: {query}

Answer in 3-5 sentences based only on the context. Mention the scheme name.
If the context lacks information, say so clearly.
```

### Runtime Generation Parameters
- **Context Truncation:** Trimmed to `MAX_CONTEXT_CHARS = 2000` to prevent LLM context-window overflow and keep CPU inference responsive.
- **Temperature:** `0.1` (minimizes creative variation, enforces strict factual grounding).
- **Token Output Limit:** `num_predict = 200` (ensures fast responses under CPU inference).
- **HTTP Timeout:** `180.0` seconds (generous threshold for local CPU computation).

---

## 2. Implemented Fallback Routing Caveat ([`backend/app/rag/fallback_routing.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/rag/fallback_routing.py#L10-L14))

When the normalized RRF retrieval score is below `0.6`, the system appends the official fallback caveat:

```text
⚠️ I found some related information but I'm not confident enough to give a definitive answer. Please verify with the official scheme portal at https://www.myscheme.gov.in or contact the relevant government office.
```

---

## 3. Implemented Translation Language Formatting ([`backend/app/rag/translation.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/rag/translation.py))

### IndicTrans2 Language Tagging
IndicTrans2 requires explicit source and target language prefix tags prepended to the input text:
- **Konkani (Devanagari) to English:**
  ```text
  gom_Deva eng_Latn {text}
  ```
- **English to Konkani (Devanagari):**
  ```text
  eng_Latn gom_Deva {text}
  ```
- Model settings: `max_length=256`, `num_beams=4`.

### NLLB-200 Language Tagging
- **Konkani (via Marathi proxy) to English:**
  - `src_lang = "mar_Deva"`, `forced_bos_token_id = "eng_Latn"`
- **English to Konkani (via Marathi proxy):**
  - `src_lang = "eng_Latn"`, `forced_bos_token_id = "mar_Deva"`
- Model settings: `max_length=256`, `num_beams=4`.

---

## 4. Evaluation Rubric & Prompts (For Gold-Set Testing)

For upcoming stage-isolated benchmark evaluations:

### Faithfulness / Groundedness Assessment
```text
Question: {query}
Retrieved Context: {context}
Generated Answer: {answer}

Task: Evaluate whether every factual claim (eligibility, monetary amount, criteria, scheme name) in the Generated Answer is directly supported by the Retrieved Context.
Assign:
- "Faithful": All claims supported by context.
- "Partially Faithful": Mostly supported, minor unverified detail.
- "Hallucinated": Contains specific unsupported numbers, criteria, or rules.
```

### Translation Fidelity Assessment
```text
Original ({source_lang}): {source_text}
Translation ({target_lang}): {translated_text}

Task: Verify that proper nouns (names of scholarships, ministries, portals) and monetary figures (e.g. ₹2,500) were accurately preserved without distortion.
```
