# Government AI Assistant — Makefile
# Usage: make <target>

.PHONY: dev test lint format build clean help

# ─── Development ─────────────────────────────────────────────────────────────

dev:
	@echo "Starting development stack..."
	docker compose -f docker/docker-compose.yml up

dev-build:
	@echo "Building and starting development stack..."
	docker compose -f docker/docker-compose.yml up --build

down:
	docker compose -f docker/docker-compose.yml down

# ─── Testing ─────────────────────────────────────────────────────────────────

test:
	@echo "Running backend tests..."
	cd backend && python -m pytest tests/unit/ tests/integration/ -v --tb=short
	@echo "Running frontend tests..."
	cd frontend && npm run test:run

test-backend:
	cd backend && python -m pytest tests/unit/ tests/integration/ -v --cov=app --cov-report=term-missing

test-frontend:
	cd frontend && npm run test:run -- --coverage

test-rag:
	@echo "Running RAG evaluation (slow — requires LLM)..."
	cd backend && python -m pytest tests/rag_eval/ -m rag_eval -v

# ─── Linting & Formatting ────────────────────────────────────────────────────

lint:
	@echo "Linting backend..."
	cd backend && ruff check app/ tests/
	cd backend && mypy app/ --strict
	@echo "Linting frontend..."
	cd frontend && npm run lint

format:
	@echo "Formatting backend..."
	cd backend && black app/ tests/
	cd backend && ruff check app/ tests/ --fix
	@echo "Formatting frontend..."
	cd frontend && npm run format

format-check:
	cd backend && black --check app/ tests/
	cd frontend && npm run format:check

# ─── Build ───────────────────────────────────────────────────────────────────

build:
	@echo "Building backend Docker image..."
	docker build -t gov-ai-backend:latest ./backend
	@echo "Building frontend Docker image..."
	docker build -t gov-ai-frontend:latest ./frontend

# ─── Data & Ingestion ────────────────────────────────────────────────────────

ingest:
	@echo "Running document ingestion..."
	cd backend && python -m app.services.ingestion

rebuild-index:
	@echo "Rebuilding ChromaDB index..."
	cd backend && python scripts/rebuild_index.py --confirm

# ─── Cleanup ─────────────────────────────────────────────────────────────────

clean:
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find backend -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf backend/.pytest_cache backend/.mypy_cache backend/.ruff_cache
	rm -rf frontend/node_modules/.cache frontend/dist

# ─── Help ────────────────────────────────────────────────────────────────────

help:
	@echo ""
	@echo "Government AI Assistant — Available Make Targets"
	@echo "================================================="
	@echo "  dev            Start full development stack (Docker)"
	@echo "  dev-build      Rebuild and start development stack"
	@echo "  down           Stop all containers"
	@echo "  test           Run all tests (backend + frontend)"
	@echo "  test-backend   Run backend tests with coverage"
	@echo "  test-frontend  Run frontend tests with coverage"
	@echo "  test-rag       Run RAG evaluation (slow)"
	@echo "  lint           Run all linters"
	@echo "  format         Auto-format all code"
	@echo "  format-check   Check formatting without changes"
	@echo "  build          Build production Docker images"
	@echo "  ingest         Run document ingestion pipeline"
	@echo "  rebuild-index  Rebuild ChromaDB index from scratch"
	@echo "  clean          Remove cache and build artifacts"
	@echo ""
