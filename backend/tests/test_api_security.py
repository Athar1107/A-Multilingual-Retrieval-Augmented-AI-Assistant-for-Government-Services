from fastapi.testclient import TestClient

from app.main import app


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
