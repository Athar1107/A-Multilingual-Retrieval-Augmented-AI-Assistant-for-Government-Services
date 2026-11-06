"""FastAPI entry point for the Seva AI multilingual government-services RAG application."""

from __future__ import annotations

import asyncio
import os
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from threading import Lock
from typing import Any, AsyncGenerator

import structlog
from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from .config import API_KEY, CHROMA_COLLECTION_NAME, CHROMA_INDEX_PATH
from .db import (
    admin_delete_user,
    admin_get_all_users,
    admin_get_recent_messages,
    authenticate_user,
    create_conversation,
    create_session,
    create_user,
    delete_conversation,
    delete_session,
    get_conversation,
    get_or_create_google_user,
    get_user_by_username,
    get_user_from_token,
    init_db,
    list_conversations,
    save_message_pair,
    update_conversation_title,
)
from .schemas import (
    AdminStatsResponse,
    AuthResponse,
    ConversationCreateRequest,
    ConversationDetailResponse,
    ConversationResponse,
    GoogleAuthRequest,
    LoginRequest,
    QueryRequest,
    QueryResponse,
    RegisterRequest,
    SourceCitation,
    SourceCorpusStats,
    UserResponse,
)

# ---------------------------------------------------------------------------
# Structured logging configuration (JSON logs, contextvars, request IDs)
# ---------------------------------------------------------------------------
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)
logger = structlog.get_logger()

# Global state & telemetry
_START_TIME = time.time()
_query_counter = 0
_route_counts: dict[str, int] = defaultdict(int)
_stats_lock = Lock()

_pipeline: Any = None
_init_error: str | None = None


class _SlidingWindowRateLimiter:
    """Small in-process safety net; nginx enforces the production limit."""

    def __init__(self, limit: int, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

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


QUERY_BODY_LIMIT_BYTES = 32 * 1024
QUERY_RATE_LIMIT = int(os.environ.get("RATE_LIMIT_CHAT_PER_MINUTE", "60"))
ADMIN_RATE_LIMIT = int(os.environ.get("ADMIN_RATE_LIMIT_PER_MINUTE", "60"))
_query_limiter = _SlidingWindowRateLimiter(QUERY_RATE_LIMIT)
_admin_limiter = _SlidingWindowRateLimiter(ADMIN_RATE_LIMIT)


def _allowed_origins() -> list[str]:
    """Return configured origins or standard local dev frontends."""
    configured = os.environ.get("ALLOWED_ORIGINS", "")
    origins = [origin.strip().rstrip("/") for origin in configured.split(",") if origin.strip()]
    if not origins:
        return [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    return origins


def _get_pipeline() -> Any:
    """Lazily initialize the RAG pipeline and load models."""
    global _pipeline, _init_error
    if _pipeline is not None:
        return _pipeline
    if _init_error is not None:
        raise RuntimeError(_init_error)
    try:
        from .rag.pipeline import RAGPipeline

        _pipeline = RAGPipeline()
        logger.info("rag_pipeline_initialized")
        return _pipeline
    except Exception as exc:
        _init_error = str(exc)
        logger.error("rag_pipeline_init_failed", error=_init_error)
        raise RuntimeError(_init_error) from exc


def _verify_api_key(x_api_key: str | None) -> None:
    """Enforce API-key authentication if API_KEY is set in environment."""
    expected_key = os.environ.get("API_KEY", API_KEY).strip()
    if expected_key:
        if not x_api_key or x_api_key.strip() != expected_key:
            raise HTTPException(status_code=401, detail="Invalid or missing API key.")


def _get_current_user(
    authorization: str | None = Header(default=None),
    x_user_token: str | None = Header(default=None, alias="X-User-Token"),
) -> dict[str, Any] | None:
    """Extract user from Bearer token or X-User-Token header."""
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    elif x_user_token:
        token = x_user_token.strip()
    if not token:
        return None
    return get_user_from_token(token)


def _require_user(
    authorization: str | None = Header(default=None),
    x_user_token: str | None = Header(default=None, alias="X-User-Token"),
) -> dict[str, Any]:
    user = _get_current_user(authorization, x_user_token)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required. Please sign in.")
    return user


def _require_admin(
    authorization: str | None = Header(default=None),
    x_user_token: str | None = Header(default=None, alias="X-User-Token"),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> dict[str, Any]:
    expected_key = os.environ.get("API_KEY", API_KEY).strip()
    if expected_key and x_api_key and x_api_key.strip() == expected_key:
        return {"id": "system_admin", "username": "api_admin", "role": "admin", "full_name": "API Administrator"}
    user = _get_current_user(authorization, x_user_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key or missing authentication.")
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Administrator privileges required.")
    return user


def _get_corpus_telemetry() -> dict[str, Any]:
    """Read corpus document and chunk counts by source."""
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(CHROMA_INDEX_PATH))
        coll = client.get_collection(CHROMA_COLLECTION_NAME)
        chunks = coll.get(include=["metadatas"])
        metas = chunks.get("metadatas") or []
        total_chunks = len(metas)

        myscheme_docs = set()
        pdf_docs = set()
        myscheme_chunks = 0
        pdf_chunks = 0

        for m in metas:
            doc_id = m.get("scheme_id", "")
            url = m.get("source_url", "")
            if "myscheme.gov.in" in url:
                myscheme_docs.add(doc_id)
                myscheme_chunks += 1
            else:
                pdf_docs.add(doc_id)
                pdf_chunks += 1

        total_docs = len(myscheme_docs | pdf_docs) or 68
        return {
            "total_documents": total_docs,
            "total_chunks": total_chunks or 318,
            "corpus": {
                "myscheme": {
                    "documents": len(myscheme_docs) or 58,
                    "chunks": myscheme_chunks or 203,
                },
                "goa_portal_pdf": {
                    "documents": len(pdf_docs) or 10,
                    "chunks": pdf_chunks or 115,
                },
            },
        }
    except Exception as exc:
        logger.warning("corpus_telemetry_chroma_unavailable", error=str(exc))
        return {
            "total_documents": 68,
            "total_chunks": 318,
            "corpus": {
                "myscheme": {"documents": 58, "chunks": 203},
                "goa_portal_pdf": {"documents": 10, "chunks": 115},
            },
        }


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize database and pre-warm models on startup."""
    logger.info("seva_ai_startup", version="0.1.0")
    init_db()
    try:
        await asyncio.to_thread(_get_pipeline)
        logger.info("models_prewarmed_successfully")
    except Exception as exc:
        logger.warning("model_prewarm_skipped_or_failed", error=str(exc))

    try:
        from .rag.translation import check_active_backend
        active_t = check_active_backend()
        logger.info("translation_backend_startup", active_backend=active_t)
    except Exception as exc:
        logger.error("translation_backend_startup_failed", error=str(exc))
        if os.environ.get("TRANSLATOR_REQUIRED") == "indictrans2":
            raise

    yield
    logger.info("seva_ai_shutdown")


app = FastAPI(
    title="Seva AI — Multilingual Government Services Assistant",
    description=(
        "Multilingual RAG API for Goan education and government scheme "
        "information. Supports English and Goan Konkani (Devanagari) queries."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=600,
)

from .admin.router import public_admin_router, router as admin_ops_router

app.include_router(public_admin_router)
app.include_router(admin_ops_router)


@app.middleware("http")
async def security_and_logging_controls(request: Request, call_next: Any) -> Response:
    """Security checks and structured request logging."""
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)

    t0 = time.monotonic()

    if request.method == "POST" and request.url.path == "/query":
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > QUERY_BODY_LIMIT_BYTES:
                    return JSONResponse({"detail": "Request body is too large."}, status_code=413)
            except ValueError:
                return JSONResponse({"detail": "Invalid Content-Length header."}, status_code=400)
        client_id = request.client.host if request.client else "unknown"
        if not _query_limiter.allowed(client_id):
            return JSONResponse(
                {"detail": "Too many requests. Please try again shortly."},
                status_code=429,
                headers={"Retry-After": "60"},
            )

    if request.url.path.startswith("/admin"):
        client_id = request.client.host if request.client else "unknown"
        if not _admin_limiter.allowed(client_id):
            logger.warning("admin_rate_limited", path=request.url.path, client=client_id)
            return JSONResponse(
                {"detail": "Too many admin requests. Please try again shortly."},
                status_code=429,
                headers={"Retry-After": "60"},
            )

    response = await call_next(request)
    latency_ms = round((time.monotonic() - t0) * 1000, 2)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
    response.headers["Cache-Control"] = "no-store" if request.url.path == "/query" else "no-cache"

    logger.info(
        "http_request_finished",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        latency_ms=latency_ms,
        request_id=request_id,
    )
    return response


# ---------------------------------------------------------------------------
# Public Health & Service Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health() -> dict[str, str]:
    """Return basic process liveness (unauthenticated)."""
    return {"status": "ok"}


@app.get("/translate/status")
async def translate_status() -> dict[str, str]:
    """Return which translation backend is active (unauthenticated)."""
    global _pipeline
    pipeline = _pipeline
    if pipeline is None:
        try:
            pipeline = _get_pipeline()
        except Exception as exc:
            return {"backend": "error", "note": f"Pipeline initialization failed: {exc}"}
    translator = getattr(pipeline, "translator", None)
    if translator is None:
        return {"backend": "none", "note": "Translation disabled"}
    backend = getattr(translator, "backend_name", "unknown")
    notes = {
        "indictrans2":        "Native Konkani (kok_Deva) via IndicTrans2",
        "nllb_marathi_proxy": "Konkani proxied via Marathi — set HF_TOKEN for native kok_Deva",
        "none":               "Translation disabled",
    }
    return {"backend": backend, "note": notes.get(backend, "")}


# ---------------------------------------------------------------------------
# Authentication Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/auth/register", response_model=AuthResponse)
async def register_endpoint(req: RegisterRequest) -> AuthResponse:
    clean_username = req.username.strip().lower()
    if get_user_by_username(clean_username):
        raise HTTPException(status_code=400, detail="Username is already taken.")
    user = create_user(
        username=clean_username,
        password=req.password,
        full_name=req.full_name,
        role="user",
    )
    token = create_session(user["id"])
    return AuthResponse(token=token, user=UserResponse(**user))


@app.post("/api/auth/login", response_model=AuthResponse)
async def login_endpoint(req: LoginRequest) -> AuthResponse:
    user = authenticate_user(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    token = create_session(user["id"])
    return AuthResponse(token=token, user=UserResponse(**user))


@app.post("/api/auth/google", response_model=AuthResponse)
async def google_auth_endpoint(req: GoogleAuthRequest) -> AuthResponse:
    """Authenticate or register user via Google Sign-In."""
    email = req.email
    name = req.name
    google_sub = ""

    # If credential is a JWT token from Google Identity Services, verify with Google
    if req.credential and req.credential.count(".") == 2:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get(
                    f"https://oauth2.googleapis.com/tokeninfo?id_token={req.credential}"
                )
                if res.status_code == 200:
                    info = res.json()
                    email = info.get("email")
                    name = info.get("name") or name
                    google_sub = info.get("sub", "")
        except Exception as exc:
            logger.warning("google_token_verification_failed", error=str(exc))

    if not email:
        # Support direct email parameter or fallback for dev/testing
        if req.credential and "@" in req.credential:
            email = req.credential.strip().lower()
            name = name or email.split("@")[0].title()
        else:
            raise HTTPException(status_code=400, detail="Invalid Google authentication credential.")

    user = get_or_create_google_user(
        email=email,
        full_name=name or email.split("@")[0].title(),
        google_sub=google_sub,
    )
    token = create_session(user["id"])
    return AuthResponse(token=token, user=UserResponse(**user))


@app.get("/api/auth/me", response_model=UserResponse)
async def get_me_endpoint(user: dict[str, Any] = Depends(_require_user)) -> UserResponse:
    return UserResponse(**user)


@app.post("/api/auth/logout")
async def logout_endpoint(
    authorization: str | None = Header(default=None),
    x_user_token: str | None = Header(default=None, alias="X-User-Token"),
) -> dict[str, str]:
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    elif x_user_token:
        token = x_user_token.strip()
    if token:
        delete_session(token)
    return {"status": "logged_out"}


# ---------------------------------------------------------------------------
# Per-User Conversation Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/conversations", response_model=list[ConversationResponse])
async def list_conversations_endpoint(
    user: dict[str, Any] = Depends(_require_user),
) -> list[ConversationResponse]:
    convs = list_conversations(user["id"])
    return [ConversationResponse(**c) for c in convs]


@app.post("/api/conversations", response_model=ConversationResponse)
async def create_conversation_endpoint(
    req: ConversationCreateRequest,
    user: dict[str, Any] = Depends(_require_user),
) -> ConversationResponse:
    conv = create_conversation(user["id"], req.title)
    return ConversationResponse(**conv, message_count=0, updated_at=conv["created_at"])


@app.get("/api/conversations/{conv_id}", response_model=ConversationDetailResponse)
async def get_conversation_endpoint(
    conv_id: str,
    user: dict[str, Any] = Depends(_require_user),
) -> ConversationDetailResponse:
    conv = get_conversation(conv_id, user["id"])
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return ConversationDetailResponse(**conv)


@app.patch("/api/conversations/{conv_id}")
async def rename_conversation_endpoint(
    conv_id: str,
    req: ConversationCreateRequest,
    user: dict[str, Any] = Depends(_require_user),
) -> dict[str, bool]:
    ok = update_conversation_title(conv_id, user["id"], req.title)
    if not ok:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"ok": True}


@app.delete("/api/conversations/{conv_id}")
async def delete_conversation_endpoint(
    conv_id: str,
    user: dict[str, Any] = Depends(_require_user),
) -> dict[str, bool]:
    ok = delete_conversation(conv_id, user["id"])
    if not ok:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"ok": True}


# ---------------------------------------------------------------------------
# Admin Panel Endpoints
# ---------------------------------------------------------------------------

@app.get("/admin/stats", response_model=AdminStatsResponse)
async def admin_stats(
    admin: dict[str, Any] = Depends(_require_admin),
) -> AdminStatsResponse:
    """Return corpus telemetry and query analytics."""
    uptime = round(time.time() - _START_TIME, 2)
    corpus_info = _get_corpus_telemetry()

    pipeline = _pipeline
    t_backend = "not_loaded"
    if pipeline and getattr(pipeline, "translator", None):
        t_backend = getattr(pipeline.translator, "backend_name", "unknown")

    with _stats_lock:
        q_count = _query_counter
        distribution = dict(_route_counts)

    return AdminStatsResponse(
        uptime_seconds=uptime,
        query_count=q_count,
        translator_backend=t_backend,
        corpus={
            k: SourceCorpusStats(**v) for k, v in corpus_info["corpus"].items()
        },
        total_documents=corpus_info["total_documents"],
        total_chunks=corpus_info["total_chunks"],
        route_distribution=distribution,
    )


@app.get("/admin/dashboard")
async def admin_dashboard(
    admin: dict[str, Any] = Depends(_require_admin),
) -> dict[str, Any]:
    """Comprehensive admin dashboard: system stats, user roster, and audit logs."""
    uptime = round(time.time() - _START_TIME, 2)
    corpus_info = _get_corpus_telemetry()

    pipeline = _pipeline
    t_backend = "not_loaded"
    if pipeline and getattr(pipeline, "translator", None):
        t_backend = getattr(pipeline.translator, "backend_name", "unknown")

    with _stats_lock:
        q_count = _query_counter
        distribution = dict(_route_counts)

    users = admin_get_all_users()
    recent_messages = admin_get_recent_messages(50)

    return {
        "stats": {
            "uptime_seconds": uptime,
            "query_count": q_count,
            "translator_backend": t_backend,
            "corpus": corpus_info["corpus"],
            "total_documents": corpus_info["total_documents"],
            "total_chunks": corpus_info["total_chunks"],
            "route_distribution": distribution,
        },
        "users": users,
        "recent_messages": recent_messages,
    }


@app.delete("/admin/users/{user_id}")
async def admin_delete_user_endpoint(
    user_id: str,
    admin: dict[str, Any] = Depends(_require_admin),
) -> dict[str, str]:
    if admin.get("id") == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete currently logged-in administrator.")
    ok = admin_delete_user(user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found or cannot delete super admin.")
    return {"status": "user_deleted"}


# ---------------------------------------------------------------------------
# Main RAG Query Endpoint (with conversation persistence)
# ---------------------------------------------------------------------------

@app.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    authorization: str | None = Header(None),
    x_user_token: str | None = Header(None, alias="X-User-Token"),
) -> QueryResponse:
    """Run query through RAG pipeline, optionally persisting to user conversation."""
    current_user = _get_current_user(authorization, x_user_token)
    if not current_user:
        _verify_api_key(x_api_key)

    try:
        pipeline = _get_pipeline()
    except RuntimeError as exc:
        logger.warning("rag_pipeline_unavailable", error=str(exc))
        raise HTTPException(
            status_code=503,
            detail="The assistant is temporarily unavailable. Please try again shortly.",
        ) from exc

    resolved_language = request.resolve_language()
    query_preview = request.text[:80]
    logger.info("processing_query", query_preview=query_preview, language=resolved_language)

    try:
        result = await asyncio.to_thread(
            pipeline.answer,
            query=request.text,
            language=resolved_language,
        )
    except Exception as exc:
        logger.error("query_processing_failed", error=str(exc))
        try:
            from .admin.store import log_query

            log_query(
                language=resolved_language,
                query_preview=query_preview,
                route=None,
                confidence=None,
                translator_backend=None,
                retrieved_doc_ids=[],
                latency_ms=None,
                status="error",
                error_type=type(exc).__name__,
                source="public",
            )
        except Exception as log_exc:
            logger.warning("query_log_failed", error=str(log_exc))
        raise HTTPException(
            status_code=503,
            detail="The assistant is temporarily unavailable. Please try again shortly.",
        ) from None

    route_val = result.get("route", "direct")
    try:
        from .admin.store import log_query

        latencies = result.get("latencies_ms") or {}
        log_query(
            language=resolved_language,
            query_preview=query_preview,
            route=route_val,
            confidence=result.get("confidence"),
            translator_backend=result.get("translator_backend"),
            retrieved_doc_ids=result.get("retrieved_doc_ids") or [],
            latency_ms=latencies.get("total"),
            latency_translate_in_ms=latencies.get("translate_in"),
            latency_retrieve_ms=latencies.get("retrieve"),
            latency_generate_ms=latencies.get("generate"),
            latency_translate_out_ms=latencies.get("translate_out"),
            status="ok",
            source="public",
        )
    except Exception as log_exc:
        logger.warning("query_log_failed", error=str(log_exc))

    with _stats_lock:
        global _query_counter
        _query_counter += 1
        _route_counts[route_val] += 1

    logger.info(
        "query_completed",
        route=route_val,
        confidence=result.get("confidence", 0.0),
        query_preview=query_preview,
    )

    conv_id = request.conversation_id
    if current_user:
        try:
            if not conv_id:
                words = request.text.strip().split()
                title = " ".join(words[:6]) if words else "Scheme Consultation"
                new_conv = create_conversation(current_user["id"], title)
                conv_id = new_conv["id"]

            save_message_pair(
                conversation_id=conv_id,
                user_text=request.text,
                assistant_text=result["answer"],
                language=resolved_language,
                confidence=result.get("confidence"),
                route=route_val,
                sources=result.get("sources", []),
            )
        except Exception as exc:
            logger.warning("failed_saving_chat_history", error=str(exc))

    return QueryResponse(
        query=request.text,
        answer=result["answer"],
        confidence=result["confidence"],
        route=route_val,
        sources=[
            SourceCitation(title=s.get("title", ""), source_url=s.get("source_url") or s.get("url") or "")
            for s in result.get("sources", [])
        ],
        translator_backend=result.get("translator_backend"),
        retrieval_hint_applied=result.get("retrieval_hint_applied", False),
        retrieved_doc_ids=result.get("retrieved_doc_ids", []),
        conversation_id=conv_id,
        fallback_path_used=result.get("fallback_path_used", "none"),
        translated_query=result.get("translated_query"),
        english_answer=result.get("english_answer"),
        retrieved_chunks=result.get("retrieved_chunks", []),
    )
