# Government AI Assistant — Backend Dockerfile
# Build: docker build -t gov-ai-backend ./backend
# Run via docker-compose.yml at project root.

FROM python:3.11-slim

# Security: run as non-root user
RUN useradd -m -u 1001 appuser

WORKDIR /app

# Install system dependencies needed by PyMuPDF and sentence-transformers
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Separate layers: heavy ML libs cached unless requirements change
COPY pyproject.toml ./

# Install pip dependencies directly (no uv, no extras complexity)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        httpx \
        fastapi \
        "uvicorn[standard]" \
        pydantic \
        pydantic-settings \
        chromadb \
        sentence-transformers \
        rank-bm25 \
        sentencepiece \
        transformers \
        torch --index-url https://download.pytorch.org/whl/cpu \
        pymupdf

# Copy application source
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser scripts/ ./scripts/

# Create data directory
RUN mkdir -p /app/data/processed /app/data/indexes/chroma && \
    chown -R appuser:appuser /app/data

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -sf http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
