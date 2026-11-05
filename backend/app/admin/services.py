"""Admin read models: corpus, eval runs, live health. No invented counts."""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any
from urllib.parse import urlparse

import httpx

from app.config import (
    CHROMA_COLLECTION_NAME,
    CHROMA_INDEX_PATH,
    CHUNK_SIZE_WORDS,
    CONFIDENCE_THRESHOLD,
    EMBEDDING_MODEL_NAME,
    OLLAMA_MODEL,
    OLLAMA_URL,
    PROJECT_ROOT,
    TOP_K_DEFAULT,
    USE_RETRIEVAL_HINTS,
)

EVAL_DIR = PROJECT_ROOT / "backend" / "eval"
_SECRET_MARKERS = ("KEY", "TOKEN", "SECRET", "PASSWORD")


def _source_label(url: str) -> str:
    host = urlparse(url or "").hostname or ""
    if "myscheme.gov.in" in host:
        return "myscheme"
    if host:
        return host.replace("www.", "")
    return "unknown"


def load_chroma_payload() -> tuple[list[str], list[dict[str, Any]], list[str]]:
    import chromadb

    client = chromadb.PersistentClient(path=str(CHROMA_INDEX_PATH))
    coll = client.get_collection(CHROMA_COLLECTION_NAME)
    payload = coll.get(include=["documents", "metadatas"])
    return payload.get("ids") or [], payload.get("metadatas") or [], payload.get("documents") or []


def load_chroma_rows() -> tuple[list[str], list[dict[str, Any]]]:
    ids, metas, _ = load_chroma_payload()
    return ids, metas


def corpus_snapshot() -> dict[str, Any]:
    try:
        ids, metas = load_chroma_rows()
    except Exception:
        return {"sources": [], "documents": [], "total_documents": 0, "total_chunks": 0}

    docs: dict[str, dict[str, Any]] = {}
    source_docs: dict[str, set[str]] = defaultdict(set)
    source_chunks: dict[str, int] = defaultdict(int)
    for meta in metas:
        meta = meta or {}
        doc_id = str(meta.get("scheme_id") or "")
        url = str(meta.get("source_url") or "")
        title = str(meta.get("title") or doc_id)
        source = _source_label(url)
        if not doc_id:
            continue
        source_docs[source].add(doc_id)
        source_chunks[source] += 1
        entry = docs.setdefault(doc_id, {"doc_id": doc_id, "title": title, "source_url": url, "chunk_count": 0, "source": source})
        entry["chunk_count"] += 1
        if title:
            entry["title"] = title
        if url:
            entry["source_url"] = url
    documents = sorted(docs.values(), key=lambda item: item["title"].lower())
    sources = [
        {"source": name, "documents": len(source_docs[name]), "chunks": source_chunks[name]}
        for name in sorted(source_docs)
    ]
    return {
        "sources": sources,
        "documents": documents,
        "total_documents": len(docs),
        "total_chunks": len(ids),
    }


def corpus_document(doc_id: str) -> dict[str, Any] | None:
    try:
        ids, metas, documents = load_chroma_payload()
    except Exception:
        return None

    chunks = []
    title = None
    source_url = None
    for idx, meta in enumerate(metas):
        meta = meta or {}
        if str(meta.get("scheme_id") or "") != doc_id:
            continue
        title = meta.get("title") or title
        source_url = meta.get("source_url") or source_url
        chunks.append(
            {
                "chunk_id": ids[idx] if idx < len(ids) else f"{doc_id}_{idx}",
                "chunk_index": meta.get("chunk_index"),
                "text": documents[idx] if idx < len(documents) else "",
                "title": meta.get("title"),
                "source_url": meta.get("source_url"),
            }
        )
    if not chunks:
        return None
    chunks.sort(key=lambda item: item["chunk_index"] if item["chunk_index"] is not None else 0)
    return {"doc_id": doc_id, "title": title, "source_url": source_url, "chunks": chunks}


def list_eval_runs() -> list[dict[str, Any]]:
    runs = []
    if not EVAL_DIR.is_dir():
        return runs
    for path in sorted(EVAL_DIR.glob("results_*.json")):
        name = path.stem.removeprefix("results_")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        runs.append(
            {
                "name": name,
                "scorer_version": payload.get("scorer_version") or (payload.get("summary") or {}).get("scorer_version"),
                "summary": payload.get("summary") or {},
            }
        )
    return runs


def load_eval_run(name: str) -> dict[str, Any] | None:
    if not name or any(ch in name for ch in ("/", "\\", "..")):
        return None
    allowed = {path.stem.removeprefix("results_"): path for path in EVAL_DIR.glob("results_*.json")}
    path = allowed.get(name)
    if path is None:
        return None
    resolved = path.resolve()
    if EVAL_DIR.resolve() not in resolved.parents and resolved.parent != EVAL_DIR.resolve():
        return None
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    return {
        "name": name,
        "scorer_version": payload.get("scorer_version") or (payload.get("summary") or {}).get("scorer_version"),
        "summary": payload.get("summary") or {},
        "results": payload.get("results") or [],
    }


def _ollama_health() -> dict[str, Any]:
    try:
        response = httpx.get(f"{OLLAMA_URL.rstrip('/')}/api/tags", timeout=2.0)
        return {"name": "ollama", "ok": response.status_code == 200, "detail": f"HTTP {response.status_code}"}
    except Exception as exc:
        return {"name": "ollama", "ok": False, "detail": type(exc).__name__}


def _chroma_health() -> dict[str, Any]:
    try:
        ids, _metas = load_chroma_rows()
        return {"name": "chroma", "ok": True, "detail": f"{len(ids)} chunks"}
    except Exception as exc:
        return {"name": "chroma", "ok": False, "detail": type(exc).__name__}


def _translator_health(pipeline: Any) -> dict[str, Any]:
    translator = getattr(pipeline, "translator", None) if pipeline is not None else None
    if translator is None:
        return {"name": "translator", "ok": False, "detail": "not_loaded"}
    backend = getattr(translator, "backend_name", "unknown")
    return {"name": "translator", "ok": backend not in ("none", "unknown"), "detail": str(backend)}


def system_snapshot(pipeline: Any, uptime_seconds: float) -> dict[str, Any]:
    translator = getattr(pipeline, "translator", None) if pipeline is not None else None
    backend = getattr(translator, "backend_name", "not_loaded") if translator is not None else "not_loaded"
    return {
        "models": {
            "embedding": EMBEDDING_MODEL_NAME,
            "generator": OLLAMA_MODEL,
            "ollama_url": OLLAMA_URL,
        },
        "translator_backend": backend,
        "thresholds": {
            "confidence_threshold": CONFIDENCE_THRESHOLD,
            "top_k": TOP_K_DEFAULT,
            "chunk_size_words": CHUNK_SIZE_WORDS,
            "use_retrieval_hints": USE_RETRIEVAL_HINTS,
            "uptime_seconds": uptime_seconds,
        },
        "health": [_ollama_health(), _chroma_health(), _translator_health(pipeline)],
    }


def redact_mapping(values: dict[str, Any]) -> dict[str, Any]:
    redacted = {}
    for key, value in values.items():
        if any(marker in key.upper() for marker in _SECRET_MARKERS):
            continue
        if isinstance(value, dict):
            redacted[key] = redact_mapping(value)
        else:
            redacted[key] = value
    return redacted
