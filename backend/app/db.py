"""Database management module for Seva AI.

Provides persistent storage for users, authentication sessions, per-user chat
history (conversations & messages), and administrative audit logging using
thread-safe SQLite.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from .config import PROJECT_ROOT

DB_PATH: Path = PROJECT_ROOT / "data" / "seva_ai.db"
_local = threading.local()


def _get_connection() -> sqlite3.Connection:
    """Thread-local connection for concurrent safety."""
    if not hasattr(_local, "conn") or _local.conn is None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        _local.conn = conn
    return _local.conn


def init_db() -> None:
    """Initialize database tables and seed default admin account."""
    conn = _get_connection()
    with conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                expires_at REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                role TEXT NOT NULL,
                text TEXT NOT NULL,
                language TEXT DEFAULT 'en',
                confidence REAL,
                route TEXT,
                sources_json TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                endpoint TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id, updated_at DESC);
            CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id, created_at ASC);
            CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
            """
        )

    # Seed default administrator accounts if not present
    if not get_user_by_username("atharv"):
        create_user(
            username="Atharv",
            password="admin@1234",
            full_name="Atharv (Lead Admin)",
            role="admin",
        )
    default_admin_username = os.environ.get("ADMIN_DEFAULT_USERNAME", "admin")
    default_admin_password = os.environ.get("ADMIN_DEFAULT_PASSWORD", "Admin@123")
    if not get_user_by_username(default_admin_username):
        create_user(
            username=default_admin_username,
            password=default_admin_password,
            full_name="System Administrator",
            role="admin",
        )


# ---------------------------------------------------------------------------
# Cryptographic Password & Token Utilities
# ---------------------------------------------------------------------------

def _hash_password(password: str, salt: str) -> str:
    """PBKDF2-HMAC-SHA256 with 100,000 iterations."""
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    ).hex()


def create_user(username: str, password: str, full_name: str, role: str = "user") -> dict[str, Any]:
    """Create a new user with securely salted password hash."""
    clean_user = username.strip().lower()
    salt = secrets.token_hex(16)
    pw_hash = _hash_password(password, salt)
    user_id = str(uuid.uuid4())

    conn = _get_connection()
    with conn:
        conn.execute(
            """
            INSERT INTO users (id, username, password_hash, salt, full_name, role)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, clean_user, pw_hash, salt, full_name.strip(), role),
        )
    return {
        "id": user_id,
        "username": clean_user,
        "full_name": full_name.strip(),
        "role": role,
    }


def get_or_create_google_user(email: str, full_name: str, google_sub: str = "") -> dict[str, Any]:
    """Retrieve existing user by email or register a new user verified via Google Sign-In."""
    clean_email = email.strip().lower()
    user = get_user_by_username(clean_email)
    if user:
        return {
            "id": user["id"],
            "username": user["username"],
            "full_name": user["full_name"],
            "role": user["role"],
        }

    user_id = str(uuid.uuid4())
    salt = secrets.token_hex(16)
    pw_hash = f"google_oauth_{google_sub or secrets.token_hex(8)}"
    display_name = full_name.strip() if full_name and full_name.strip() else clean_email.split("@")[0].title()

    conn = _get_connection()
    with conn:
        conn.execute(
            """
            INSERT INTO users (id, username, password_hash, salt, full_name, role)
            VALUES (?, ?, ?, ?, ?, 'user')
            """,
            (user_id, clean_email, pw_hash, salt, display_name),
        )
    return {
        "id": user_id,
        "username": clean_email,
        "full_name": display_name,
        "role": "user",
    }


def authenticate_user(username: str, password: str) -> dict[str, Any] | None:
    """Verify credentials and return user dict if valid."""
    user = get_user_by_username(username.strip().lower())
    if not user:
        return None
    expected_hash = _hash_password(password, user["salt"])
    if hmac.compare_digest(expected_hash, user["password_hash"]):
        return {
            "id": user["id"],
            "username": user["username"],
            "full_name": user["full_name"],
            "role": user["role"],
        }
    return None


def get_user_by_username(username: str) -> dict[str, Any] | None:
    conn = _get_connection()
    cur = conn.execute("SELECT * FROM users WHERE username = ?", (username.strip().lower(),))
    row = cur.fetchone()
    return dict(row) if row else None


def get_user_by_id(user_id: str) -> dict[str, Any] | None:
    conn = _get_connection()
    cur = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    return dict(row) if row else None


def create_session(user_id: str, duration_hours: int = 72) -> str:
    """Generate a high-entropy session token valid for duration_hours."""
    token = secrets.token_hex(32)
    expires_at = time.time() + (duration_hours * 3600)
    conn = _get_connection()
    with conn:
        conn.execute(
            "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
            (token, user_id, expires_at),
        )
    return token


def get_user_from_token(token: str) -> dict[str, Any] | None:
    """Resolve active session token to user dict."""
    if not token:
        return None
    conn = _get_connection()
    cur = conn.execute(
        """
        SELECT u.id, u.username, u.full_name, u.role, s.expires_at
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.token = ?
        """,
        (token,),
    )
    row = cur.fetchone()
    if not row:
        return None
    if row["expires_at"] < time.time():
        delete_session(token)
        return None
    return {
        "id": row["id"],
        "username": row["username"],
        "full_name": row["full_name"],
        "role": row["role"],
    }


def delete_session(token: str) -> None:
    conn = _get_connection()
    with conn:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))


# ---------------------------------------------------------------------------
# Per-User Conversation and Message Operations
# ---------------------------------------------------------------------------

def create_conversation(user_id: str, title: str = "New Scheme Consultation") -> dict[str, Any]:
    conv_id = str(uuid.uuid4())
    conn = _get_connection()
    with conn:
        conn.execute(
            "INSERT INTO conversations (id, user_id, title) VALUES (?, ?, ?)",
            (conv_id, user_id, title[:100]),
        )
    return {
        "id": conv_id,
        "user_id": user_id,
        "title": title[:100],
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def list_conversations(user_id: str, limit: int = 50) -> list[dict[str, Any]]:
    conn = _get_connection()
    cur = conn.execute(
        """
        SELECT c.id, c.title, c.created_at, c.updated_at,
               (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id) as message_count
        FROM conversations c
        WHERE c.user_id = ?
        ORDER BY c.updated_at DESC
        LIMIT ?
        """,
        (user_id, limit),
    )
    return [dict(r) for r in cur.fetchall()]


def get_conversation(conv_id: str, user_id: str) -> dict[str, Any] | None:
    conn = _get_connection()
    cur = conn.execute(
        "SELECT id, title, created_at, updated_at FROM conversations WHERE id = ? AND user_id = ?",
        (conv_id, user_id),
    )
    conv = cur.fetchone()
    if not conv:
        return None

    cur_msgs = conn.execute(
        """
        SELECT id, role, text, language, confidence, route, sources_json, created_at
        FROM messages
        WHERE conversation_id = ?
        ORDER BY created_at ASC
        """,
        (conv_id,),
    )
    messages = []
    for m in cur_msgs.fetchall():
        msg_dict = dict(m)
        try:
            msg_dict["sources"] = json.loads(msg_dict.get("sources_json") or "[]")
        except Exception:
            msg_dict["sources"] = []
        messages.append(msg_dict)

    res = dict(conv)
    res["messages"] = messages
    return res


def update_conversation_title(conv_id: str, user_id: str, title: str) -> bool:
    conn = _get_connection()
    with conn:
        cur = conn.execute(
            "UPDATE conversations SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
            (title[:100], conv_id, user_id),
        )
        return cur.rowcount > 0


def delete_conversation(conv_id: str, user_id: str) -> bool:
    conn = _get_connection()
    with conn:
        cur = conn.execute(
            "DELETE FROM conversations WHERE id = ? AND user_id = ?",
            (conv_id, user_id),
        )
        return cur.rowcount > 0


def save_message_pair(
    conversation_id: str,
    user_text: str,
    assistant_text: str,
    language: str = "en",
    confidence: float | None = None,
    route: str | None = None,
    sources: list[dict[str, Any]] | None = None,
) -> None:
    """Save both user question and assistant answer atomically and touch conversation updated_at."""
    sources_json = json.dumps(sources or [], ensure_ascii=False)
    u_msg_id = str(uuid.uuid4())
    a_msg_id = str(uuid.uuid4())

    conn = _get_connection()
    with conn:
        conn.execute(
            """
            INSERT INTO messages (id, conversation_id, role, text, language)
            VALUES (?, ?, 'user', ?, ?)
            """,
            (u_msg_id, conversation_id, user_text, language),
        )
        conn.execute(
            """
            INSERT INTO messages (id, conversation_id, role, text, language, confidence, route, sources_json)
            VALUES (?, ?, 'assistant', ?, ?, ?, ?, ?)
            """,
            (a_msg_id, conversation_id, assistant_text, language, confidence, route, sources_json),
        )
        conn.execute(
            "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (conversation_id,),
        )


# ---------------------------------------------------------------------------
# Admin Panel Data & Analytics Queries
# ---------------------------------------------------------------------------

def admin_get_all_users() -> list[dict[str, Any]]:
    conn = _get_connection()
    cur = conn.execute(
        """
        SELECT u.id, u.username, u.full_name, u.role, u.created_at,
               COUNT(DISTINCT c.id) as conversation_count,
               COUNT(m.id) as message_count
        FROM users u
        LEFT JOIN conversations c ON c.user_id = u.id
        LEFT JOIN messages m ON m.conversation_id = c.id AND m.role = 'user'
        GROUP BY u.id
        ORDER BY u.created_at DESC
        """
    )
    return [dict(r) for r in cur.fetchall()]


def admin_delete_user(user_id: str) -> bool:
    conn = _get_connection()
    with conn:
        cur = conn.execute("DELETE FROM users WHERE id = ? AND role != 'admin'", (user_id,))
        return cur.rowcount > 0


def admin_get_recent_messages(limit: int = 50) -> list[dict[str, Any]]:
    conn = _get_connection()
    cur = conn.execute(
        """
        SELECT m.id, m.conversation_id, m.role, SUBSTR(m.text, 1, 120) as text_preview,
               m.language, m.confidence, m.route, m.created_at,
               u.username
        FROM messages m
        JOIN conversations c ON m.conversation_id = c.id
        JOIN users u ON c.user_id = u.id
        ORDER BY m.created_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    return [dict(r) for r in cur.fetchall()]


def record_audit_log(endpoint: str, action: str, user_id: str | None = None, details: str = "") -> None:
    conn = _get_connection()
    with conn:
        conn.execute(
            "INSERT INTO audit_logs (id, user_id, endpoint, action, details) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), user_id, endpoint, action, details),
        )
