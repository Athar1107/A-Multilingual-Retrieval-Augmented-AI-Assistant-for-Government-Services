import os
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import QueryRequest, detect_query_language


def test_health_has_security_headers() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_query_schema_rejects_unknown_language_and_extra_fields() -> None:
    client = TestClient(app)

    unknown_language = client.post("/query", json={"text": "hello", "language": "mr"})
    extra_field = client.post("/query", json={"text": "hello", "language": "en", "admin": True})

    assert unknown_language.status_code == 422
    assert extra_field.status_code == 422


def test_api_key_auth_on_query_and_health_stays_open(monkeypatch) -> None:
    monkeypatch.setenv("API_KEY", "test-secret-key")
    client = TestClient(app)

    # /health stays open without key
    assert client.get("/health").status_code == 200

    # /query fails with 401 when key is missing or wrong
    missing_key = client.post("/query", json={"text": "scholarship", "language": "en"})
    assert missing_key.status_code == 401

    wrong_key = client.post(
        "/query",
        json={"text": "scholarship", "language": "en"},
        headers={"X-API-Key": "wrong-key"},
    )
    assert wrong_key.status_code == 401


def test_admin_stats_protected_and_returns_corpus_breakdown(monkeypatch) -> None:
    monkeypatch.setenv("API_KEY", "test-secret-key")
    client = TestClient(app)

    # Unauthenticated /admin/stats fails
    res_unauth = client.get("/admin/stats")
    assert res_unauth.status_code == 401

    # Authenticated /admin/stats succeeds
    res_auth = client.get("/admin/stats", headers={"X-API-Key": "test-secret-key"})
    assert res_auth.status_code == 200
    data = res_auth.json()

    assert "total_documents" in data
    assert "total_chunks" in data
    assert "corpus" in data
    assert "myscheme" in data["corpus"]
    assert "goa_portal_pdf" in data["corpus"]
    assert "uptime_seconds" in data
    assert "query_count" in data
    assert "route_distribution" in data


def test_language_auto_detection() -> None:
    # Auto-detect script
    assert detect_query_language("What is the PM scholarship?") == "en"
    assert detect_query_language("मुलांक दरमहिन्याला किती रुपये मेळतात?") == "kok"

    # QueryRequest auto-resolves when language is None
    req_deva = QueryRequest(text="मुलांक किती रुपये मेळतात?")
    assert req_deva.language is None
    assert req_deva.resolve_language() == "kok"

    req_en = QueryRequest(text="How much scholarship is provided?")
    assert req_en.resolve_language() == "en"

    # Manual toggle acts as override
    req_override = QueryRequest(text="Devanagari query in english mode", language="en")
    assert req_override.resolve_language() == "en"
