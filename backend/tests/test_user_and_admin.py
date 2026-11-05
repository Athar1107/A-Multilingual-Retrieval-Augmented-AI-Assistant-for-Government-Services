import os
import pytest
from starlette.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("API_KEY", "dev-secret-key-123")
    from app.db import init_db
    init_db()


def test_user_registration_login_and_me():
    # Register a test user
    reg_res = client.post(
        "/api/auth/register",
        json={
            "username": "citizen_test",
            "password": "Password123!",
            "full_name": "Test Citizen",
        },
    )
    # May already exist in repeated runs, so accept 200 or 400
    if reg_res.status_code == 200:
        data = reg_res.json()
        assert "token" in data
        assert data["user"]["username"] == "citizen_test"
        assert data["user"]["role"] == "user"

    # Login
    login_res = client.post(
        "/api/auth/login",
        json={"username": "citizen_test", "password": "Password123!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["token"]
    assert len(token) > 20

    # Get /api/auth/me
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "citizen_test"


def test_google_sign_in():
    # Test Google Sign In with email / credential
    res = client.post(
        "/api/auth/google",
        json={
            "credential": "test_google_token",
            "email": "citizen.google@gmail.com",
            "name": "Google Verified Citizen",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "token" in data
    assert data["user"]["username"] == "citizen.google@gmail.com"
    assert data["user"]["full_name"] == "Google Verified Citizen"
    assert data["user"]["role"] == "user"

    # Second sign-in with same email should reuse account
    res2 = client.post(
        "/api/auth/google",
        json={
            "credential": "test_google_token_2",
            "email": "citizen.google@gmail.com",
        },
    )
    assert res2.status_code == 200
    assert res2.json()["user"]["id"] == data["user"]["id"]


def test_conversations_crud_for_user():
    # Login as citizen_test
    login_res = client.post(
        "/api/auth/login",
        json={"username": "citizen_test", "password": "Password123!"},
    )
    token = login_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create conversation
    create_res = client.post(
        "/api/conversations",
        json={"title": "Goa Scholarship Questions"},
        headers=headers,
    )
    assert create_res.status_code == 200
    conv_id = create_res.json()["id"]
    assert conv_id

    # List conversations
    list_res = client.get("/api/conversations", headers=headers)
    assert list_res.status_code == 200
    conv_ids = [c["id"] for c in list_res.json()]
    assert conv_id in conv_ids

    # Rename conversation
    rename_res = client.patch(
        f"/api/conversations/{conv_id}",
        json={"title": "Renamed Consultation"},
        headers=headers,
    )
    assert rename_res.status_code == 200

    # Get conversation details
    detail_res = client.get(f"/api/conversations/{conv_id}", headers=headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["title"] == "Renamed Consultation"
    assert "messages" in detail_res.json()

    # Delete conversation
    del_res = client.delete(f"/api/conversations/{conv_id}", headers=headers)
    assert del_res.status_code == 200


def test_admin_dashboard_security():
    # 1. Anonymous user cannot access admin dashboard (401)
    unauth = client.get("/admin/dashboard")
    assert unauth.status_code == 401

    # 2. Regular user cannot access admin dashboard (403)
    login_res = client.post(
        "/api/auth/login",
        json={"username": "citizen_test", "password": "Password123!"},
    )
    user_token = login_res.json()["token"]
    forbidden = client.get("/admin/dashboard", headers={"Authorization": f"Bearer {user_token}"})
    assert forbidden.status_code == 403

    # 3. Default seeded admin CAN access admin dashboard
    admin_login = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "Admin@123"},
    )
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["token"]
    admin_res = client.get("/admin/dashboard", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_res.status_code == 200
    dash = admin_res.json()
    assert "stats" in dash
    assert "users" in dash
    assert "recent_messages" in dash
    assert dash["stats"]["total_documents"] == 68

    # 4. API Key also allows admin dashboard access
    api_key = os.environ.get("API_KEY", "dev-secret-key-123")
    api_res = client.get("/admin/dashboard", headers={"X-API-Key": api_key})
    assert api_res.status_code == 200
