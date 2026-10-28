# Security & Privacy

> **Research baseline:** Protect source provenance, retrieved evidence, and user privacy in the Multilingual RAG pipeline. See [RESEARCH_PLAN.md](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/docs/RESEARCH_PLAN.md) and [IMPLEMENTATION_STATUS.md](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/docs/IMPLEMENTATION_STATUS.md).

---

## Security Philosophy

The Government AI Assistant is designed as an informative public policy guidance assistant. Because government decisions involve citizen welfare, financial eligibility, and legal rights, the system emphasizes **provable citation grounding**, **confidence-based warning caveats**, and **strict privacy by design**.

---

## Active Security & Privacy Controls

### 1. Secrets Management & API Tokens
- Sensitive tokens such as `HF_TOKEN` (used to download gated IndicTrans2 weights) are loaded exclusively from environment variables or `backend/.env`.
- `backend/.env` is strictly ignored in [`.gitignore`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/.gitignore), preventing accidental leakage to public repositories.
- In [`start_server.bat`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/start_server.bat), placeholder strings are documented without baking credentials into scripts.

### 2. Input Validation & DoS Prevention
- All incoming JSON payloads to [`POST /query`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/main.py#L111) are strongly validated via Pydantic ([`QueryRequest`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/schemas.py#L6-L14)):
  - Minimum query length: 1 character.
  - Maximum query length: 2,000 characters.
  - Queries exceeding bounds immediately fail with HTTP `422 Unprocessable Entity` before triggering heavy ML routines.
- In [`generator.py`](file:///c:/Users/athar/coding/model%20review/A%20Multilingual%20Retrieval-Augmented%20AI%20Assistant%20for%20Government%20Services/backend/app/rag/generator.py), context strings are strictly truncated to `MAX_CONTEXT_CHARS = 2000`, preventing context stuffing attacks and unbounded CPU consumption.
- Model generation is capped at `num_predict = 200` output tokens.

### 3. Prompt Injection Defense & Grounding
To prevent user queries or third-party documents from hijacking LLM instructions:
- The system instructions are isolated in Ollama's `"system"` prompt field, separate from user context.
- The prompt explicitly commands:
  > *"Answer questions based ONLY on the provided context about government schemes. If the context does not contain enough information to answer the question, say so clearly."*
- Temperature is locked to `0.1` to curtail imaginative drift or adversarial prompt injection responses.

### 4. Low-Confidence Fallback Warnings
- Retrieval confidence is evaluated against `CONFIDENCE_THRESHOLD = 0.6`.
- If candidate passages lack sufficient relevance, the system flags the response with `route: "fallback"` and appends:
  > *"⚠️ I found some related information but I'm not confident enough to give a definitive answer. Please verify with the official scheme portal at https://www.myscheme.gov.in or contact the relevant government office."*
- This prevents citizens from acting upon dubious or ambiguous interpretations of policy documents.

### 5. Citizen Privacy & Data Minimization
- **Stateless Execution:** Queries are processed in memory and returned. The system does not persist citizen queries, IP addresses, or conversation histories to database tables.
- **Local On-Premises Inference:** The entire retrieval, translation, and generation stack runs locally on the host machine via Ollama and PyTorch. No user queries or government scheme queries are transmitted to external proprietary AI APIs (such as OpenAI or Google).

### 6. Safe Error Handling
- Exceptions during pipeline execution return clean JSON error responses (`503 Service Unavailable` with friendly messages) without exposing Python stack traces, internal file paths, or system credentials to the client.

### 7. Browser, API, and Deployment Boundaries
- The production web client is served by Nginx on the same origin as the API. It uses a strict Content Security Policy and only external, same-origin JavaScript and CSS files.
- User questions and model responses are rendered with DOM textContent, never interpolated as HTML. Official-source links are validated as http/https URLs and opened with noopener noreferrer.
- CORS accepts only origins explicitly named in ALLOWED_ORIGINS; credentialed wildcard CORS is not enabled.
- The query endpoint is protected at the proxy and application layers by a 16 KB request limit and per-minute rate limits. The ChromaDB, Ollama, and backend containers are not published directly to the host in the production Compose topology.
- HTTP security headers include CSP, X-Content-Type-Options: nosniff, X-Frame-Options: DENY, Referrer-Policy: no-referrer, and a restrictive Permissions-Policy.

## Operational Requirement

Nginx in this repository terminates HTTP only. A public deployment must place
it behind a TLS-enabled load balancer or configure TLS certificates directly
in Nginx before accepting internet traffic. Security controls reduce risk; no
application can honestly guarantee the absence of every future vulnerability.
