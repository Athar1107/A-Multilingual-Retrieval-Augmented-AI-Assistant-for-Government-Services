# Government AI Assistant — Backend Dockerfile
# Multi-stage build for minimal production image

# ─── Stage 1: Builder ────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install uv for fast dependency resolution
RUN pip install --no-cache-dir uv==0.3.0

# Copy dependency files first (leverages Docker layer cache)
COPY pyproject.toml ./

# Install production dependencies only
RUN uv pip install --system --no-cache-dir -e ".[production]" 2>/dev/null || \
    uv pip install --system --no-cache-dir .

# ─── Stage 2: Production ─────────────────────────────────────────────────────
FROM python:3.11-slim AS production

# Security: run as non-root user
RUN useradd -m -u 1001 -s /bin/bash appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser app/ ./app/

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/api/v1/health/live').raise_for_status()"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
