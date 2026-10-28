# Government AI Assistant — Backend Dockerfile
# Build: docker build -t gov-ai-backend ./backend
# Run via docker-compose.yml at project root.

FROM python:3.11-slim

# Security: run as non-root user
RUN useradd -m -u 1001 appuser

WORKDIR /app

# System deps for PyMuPDF and curl (health check)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Layer 1: core web deps (changes rarely)
RUN pip install --no-cache-dir \
    httpx \
    fastapi \
    "uvicorn[standard]" \
    pydantic \
    pydantic-settings

# Layer 2: heavy ML deps (cached separately)
RUN pip install --no-cache-dir \
    sentence-transformers \
    chromadb \
    rank-bm25 \
    sentencepiece \
    transformers \
    pymupdf

# Copy application source
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser scripts/ ./scripts/

# Create persistent data directories
RUN mkdir -p /app/data/processed /app/data/indexes/chroma && \
    chown -R appuser:appuser /app/data

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -sf http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
