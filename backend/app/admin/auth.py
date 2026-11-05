"""Admin API authentication: env ADMIN_API_KEY + header X-Admin-Key."""

from __future__ import annotations

import hmac
import os
import threading
import time
from collections import defaultdict, deque

import structlog
from fastapi import Header, HTTPException, Request

logger = structlog.get_logger()


class _AdminRateLimiter:
    """In-memory sliding window rate limiter for admin endpoints."""

    def __init__(self, limit: int = 120, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allowed(self, client_id: str) -> bool:
        now = time.monotonic()
        with self._lock:
            requests = self._requests[client_id]
            while requests and requests[0] <= now - self.window_seconds:
                requests.popleft()
            if len(requests) >= self.limit:
                return False
            requests.append(now)
            return True


ADMIN_RATE_LIMIT = int(os.environ.get("ADMIN_RATE_LIMIT_PER_MINUTE", "120"))
_admin_limiter = _AdminRateLimiter(limit=ADMIN_RATE_LIMIT)


def _constant_time_equal(given: str, expected: str) -> bool:
    given_b = given.encode("utf-8")
    expected_b = expected.encode("utf-8")
    if len(given_b) != len(expected_b):
        hmac.compare_digest(expected_b, expected_b)
        return False
    return hmac.compare_digest(given_b, expected_b)


def require_admin_key(
    request: Request,
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
    x_admin_user: str | None = Header(default=None, alias="X-Admin-User"),
) -> dict[str, str]:
    """Fail closed if the admin key is unset; 401 on missing or wrong credentials."""
    client_id = request.client.host if request.client else "unknown"

    # Enforce rate limiting across /admin/* endpoints
    if not _admin_limiter.allowed(client_id):
        logger.warning("admin_rate_limit_exceeded", path=str(request.url.path), client=client_id)
        raise HTTPException(status_code=429, detail="Admin rate limit exceeded.")

    expected_key = os.environ.get("ADMIN_API_KEY", "").strip()
    if not expected_key:
        logger.warning("admin_auth_unconfigured", path=str(request.url.path), client=client_id)
        raise HTTPException(status_code=503, detail="Admin API is not configured.")

    if not x_admin_key:
        logger.warning("admin_auth_failed", reason="missing_key", path=str(request.url.path), client=client_id)
        raise HTTPException(status_code=401, detail="Invalid or missing admin credentials.")

    if not _constant_time_equal(x_admin_key.strip(), expected_key):
        logger.warning(
            "admin_auth_failed",
            reason="bad_credentials",
            path=str(request.url.path),
            client=client_id,
        )
        raise HTTPException(status_code=401, detail="Invalid or missing admin credentials.")

    username = (x_admin_user or os.environ.get("ADMIN_USERNAME", "") or "Atharv").strip()
    return {"username": username}
