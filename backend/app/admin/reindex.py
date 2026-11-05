"""Background corpus reindex with a single-flight lock."""

from __future__ import annotations

import threading
import time
from typing import Any

_lock = threading.Lock()
_state: dict[str, Any] = {
    "running": False,
    "started_at": None,
    "finished_at": None,
    "error": None,
    "chunk_count": None,
}


def status() -> dict[str, Any]:
    return dict(_state)


def try_start() -> bool:
    with _lock:
        if _state["running"]:
            return False
        _state.update({"running": True, "started_at": time.time(), "finished_at": None, "error": None})
        return True


def run_reindex() -> None:
    try:
        from app.rag.indexing import CorpusIndexer

        count = CorpusIndexer().index_corpus()
        with _lock:
            _state["chunk_count"] = int(count)
            _state["error"] = None
    except Exception as exc:
        with _lock:
            _state["error"] = str(exc)
            _state["chunk_count"] = None
    finally:
        with _lock:
            _state["running"] = False
            _state["finished_at"] = time.time()
