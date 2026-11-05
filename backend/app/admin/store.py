"""SQLite query_log and admin audit trail. Logging failures must be raised to callers."""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from app.config import PROJECT_ROOT

_local = threading.local()
RETENTION_SECONDS = 30 * 24 * 60 * 60


def query_log_path() -> Path:
    configured = os.environ.get("QUERY_LOG_DB_PATH", "").strip()
    return Path(configured) if configured else PROJECT_ROOT / "data" / "query_log.db"


def _connect() -> sqlite3.Connection:
    path = query_log_path()
    cached_path = getattr(_local, "path", None)
    if getattr(_local, "conn", None) is None or cached_path != str(path):
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        _local.conn = conn
        _local.path = str(path)
        _init(conn)
    return _local.conn


def _init(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS query_log (
            id TEXT PRIMARY KEY,
            ts REAL NOT NULL,
            language TEXT,
            query_preview TEXT,
            route TEXT,
            confidence REAL,
            translator_backend TEXT,
            retrieved_doc_ids TEXT,
            latency_ms REAL,
            latency_translate_in_ms REAL,
            latency_retrieve_ms REAL,
            latency_generate_ms REAL,
            latency_translate_out_ms REAL,
            status TEXT,
            error_type TEXT,
            source TEXT DEFAULT 'public'
        );
        CREATE INDEX IF NOT EXISTS idx_query_log_ts ON query_log(ts DESC);
        CREATE INDEX IF NOT EXISTS idx_query_log_source ON query_log(source, ts DESC);
        CREATE TABLE IF NOT EXISTS admin_audit (
            id TEXT PRIMARY KEY,
            ts REAL NOT NULL,
            username TEXT,
            action TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            details TEXT
        );
        """
    )
    conn.commit()


def purge_old_rows(now: float | None = None) -> None:
    cutoff = (now or time.time()) - RETENTION_SECONDS
    conn = _connect()
    conn.execute("DELETE FROM query_log WHERE ts < ?", (cutoff,))
    conn.commit()


def log_query(
    *,
    language: str | None,
    query_preview: str,
    route: str | None,
    confidence: float | None,
    translator_backend: str | None,
    retrieved_doc_ids: list[str] | None,
    latency_ms: float | None,
    latency_translate_in_ms: float | None = None,
    latency_retrieve_ms: float | None = None,
    latency_generate_ms: float | None = None,
    latency_translate_out_ms: float | None = None,
    status: str = "ok",
    error_type: str | None = None,
    source: str = "public",
) -> str:
    purge_old_rows()
    log_id = str(uuid.uuid4())
    conn = _connect()
    conn.execute(
        """
        INSERT INTO query_log (
            id, ts, language, query_preview, route, confidence, translator_backend,
            retrieved_doc_ids, latency_ms, latency_translate_in_ms, latency_retrieve_ms,
            latency_generate_ms, latency_translate_out_ms, status, error_type, source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            log_id,
            time.time(),
            language,
            (query_preview or "")[:80],
            route,
            confidence,
            translator_backend,
            json.dumps(retrieved_doc_ids or []),
            latency_ms,
            latency_translate_in_ms,
            latency_retrieve_ms,
            latency_generate_ms,
            latency_translate_out_ms,
            status,
            error_type,
            source,
        ),
    )
    conn.commit()
    return log_id


def write_audit(username: str, action: str, endpoint: str, details: dict[str, Any] | None = None) -> None:
    conn = _connect()
    conn.execute(
        """
        INSERT INTO admin_audit (id, ts, username, action, endpoint, details)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (str(uuid.uuid4()), time.time(), username, action, endpoint, json.dumps(details or {})),
    )
    conn.commit()


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    try:
        item["retrieved_doc_ids"] = json.loads(item.get("retrieved_doc_ids") or "[]")
    except json.JSONDecodeError:
        item["retrieved_doc_ids"] = []
    return item


def list_queries(
    *,
    limit: int = 50,
    offset: int = 0,
    route: str | None = None,
    language: str | None = None,
    status: str | None = None,
    q: str | None = None,
    include_admin: bool = False,
) -> tuple[list[dict[str, Any]], int]:
    clauses = [] if include_admin else ["source != 'admin'"]
    params: list[Any] = []
    if route:
        clauses.append("route = ?")
        params.append(route)
    if language:
        clauses.append("language = ?")
        params.append(language)
    if status:
        clauses.append("status = ?")
        params.append(status)
    if q:
        clauses.append("query_preview LIKE ?")
        params.append(f"%{q[:80]}%")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    conn = _connect()
    total = conn.execute(f"SELECT COUNT(*) FROM query_log {where}", params).fetchone()[0]
    rows = conn.execute(
        f"SELECT * FROM query_log {where} ORDER BY ts DESC LIMIT ? OFFSET ?",
        [*params, limit, offset],
    ).fetchall()
    return [_row_to_dict(row) for row in rows], int(total)


def get_query(log_id: str) -> dict[str, Any] | None:
    conn = _connect()
    row = conn.execute("SELECT * FROM query_log WHERE id = ?", (log_id,)).fetchone()
    return _row_to_dict(row) if row else None


def public_stats() -> dict[str, Any]:
    conn = _connect()
    now = time.time()
    day_ago = now - 86400
    where = "WHERE source != 'admin'"
    total = conn.execute(f"SELECT COUNT(*) FROM query_log {where}").fetchone()[0]
    last_24h = conn.execute(f"SELECT COUNT(*) FROM query_log {where} AND ts >= ?", (day_ago,)).fetchone()[0]
    lat_row = conn.execute(
        f"""
        SELECT AVG(latency_ms) AS avg_lat,
               AVG(latency_translate_in_ms) AS avg_tin,
               AVG(latency_retrieve_ms) AS avg_ret,
               AVG(latency_generate_ms) AS avg_gen,
               AVG(latency_translate_out_ms) AS avg_tout,
               AVG(confidence) AS avg_conf
        FROM query_log {where} AND latency_ms IS NOT NULL
        """
    ).fetchone()
    latencies = [r[0] for r in conn.execute(f"SELECT latency_ms FROM query_log {where} AND latency_ms IS NOT NULL ORDER BY latency_ms").fetchall()]
    p95 = None
    if latencies:
        idx = min(len(latencies) - 1, int(round(0.95 * (len(latencies) - 1))))
        p95 = latencies[idx]
    routes = {r["route"] or "unknown": r["n"] for r in conn.execute(f"SELECT route, COUNT(*) AS n FROM query_log {where} GROUP BY route")}
    errors = conn.execute(f"SELECT COUNT(*) FROM query_log {where} AND status = 'error'").fetchone()[0]
    fallback_n = conn.execute(
        f"SELECT COUNT(*) FROM query_log {where} AND route IN ('fallback_recovered', 'fallback_failed')"
    ).fetchone()[0]
    hours = conn.execute(
        f"""
        SELECT CAST((ts / 3600) AS INTEGER) * 3600 AS bucket, COUNT(*) AS n
        FROM query_log {where} AND ts >= ?
        GROUP BY bucket ORDER BY bucket
        """,
        (day_ago,),
    ).fetchall()
    confs = [r[0] for r in conn.execute(f"SELECT confidence FROM query_log {where} AND confidence IS NOT NULL").fetchall()]
    histogram = [0] * 10
    for value in confs:
        bucket = min(9, max(0, int(float(value) * 10)))
        histogram[bucket] += 1
    return {
        "total_queries": int(total),
        "queries_24h": int(last_24h),
        "avg_latency_ms": float(lat_row["avg_lat"]) if lat_row and lat_row["avg_lat"] is not None else None,
        "p95_latency_ms": float(p95) if p95 is not None else None,
        "avg_stage_latency_ms": {
            "translate_in": float(lat_row["avg_tin"]) if lat_row and lat_row["avg_tin"] is not None else None,
            "retrieve": float(lat_row["avg_ret"]) if lat_row and lat_row["avg_ret"] is not None else None,
            "generate": float(lat_row["avg_gen"]) if lat_row and lat_row["avg_gen"] is not None else None,
            "translate_out": float(lat_row["avg_tout"]) if lat_row and lat_row["avg_tout"] is not None else None,
        },
        "route_distribution": routes,
        "fallback_rate": (fallback_n / total) if total else None,
        "error_rate": (errors / total) if total else None,
        "avg_confidence": float(lat_row["avg_conf"]) if lat_row and lat_row["avg_conf"] is not None else None,
        "queries_per_hour": [{"ts": int(row["bucket"]), "count": int(row["n"])} for row in hours],
        "confidence_histogram": [{"bucket": i / 10, "count": histogram[i]} for i in range(10)],
    }
