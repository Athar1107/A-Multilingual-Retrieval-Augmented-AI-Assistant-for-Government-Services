"""Central configuration for paths, models, and tunable parameters.

All values have defaults for local development and can be overridden with
environment variables for Docker / production deployment.
"""

import os
from pathlib import Path


def _find_project_root() -> Path:
    """Locate the repository root locally or use the container working directory."""
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "schemes_list.txt").exists():
            return candidate
    return Path.cwd()


PROJECT_ROOT = _find_project_root()
SCHEME_REGISTER_PATH = PROJECT_ROOT / "schemes_list.txt"
PROCESSED_CORPUS_PATH = PROJECT_ROOT / "data" / "processed" / "active_english.json"
CHROMA_INDEX_PATH = PROJECT_ROOT / "data" / "indexes" / "chroma"
BM25_INDEX_PATH = PROJECT_ROOT / "data" / "indexes" / "bm25"

# Embedding model — ``all-MiniLM-L6-v2`` (384-dim) ships as the default for
# low-resource development.  Set the ``EMBEDDING_MODEL`` env-var to
# ``BAAI/bge-m3`` for the 1024-dim multilingual production model described in
# the research paper.
EMBEDDING_MODEL_NAME: str = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Ollama LLM configuration
OLLAMA_URL: str = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL: str = os.environ.get("OLLAMA_MODEL", "llama3.2")

# RAG tuning knobs
TOP_K_DEFAULT: int = int(os.environ.get("TOP_K", "5"))
CONFIDENCE_THRESHOLD: float = float(os.environ.get("CONFIDENCE_THRESHOLD", "0.6"))
CHUNK_SIZE_WORDS: int = int(os.environ.get("CHUNK_SIZE_WORDS", "300"))
CHROMA_COLLECTION_NAME: str = "education_schemes"
CHROMA_MAX_BATCH_SIZE: int = 5_000  # ChromaDB per-call upsert limit
