"""Auth, session and CSRF coverage (spec Sections 3, 7.4.1, 7.6)."""
from __future__ import annotations

from .conftest import csrf, register_user


def test_register_login_logout_flow(client):
    email = "flow@example.com"
    register_user(client, email)
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["data"]["user"]["email"] == email

    out = client.post("/api/v1/auth/logout", json={}, headers=csrf(client))
    assert out.status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401

    bad = client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPass123!"})
    assert bad.status_code == 401
    assert bad.json()["error"]["code"] == "INVALID_CREDENTIALS"

    ok = client.post("/api/v1/auth/login", json={"email": email, "password": "StrongPass123!"})
    assert ok.status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 200


def test_register_validation_and_duplicate(client):
    weak = client.post(
        "/api/v1/auth/register",
        json={"name": "Weak", "email": "weak@example.com", "password": "short"},
    )
    assert weak.status_code == 422

    register_user(client, "dup@example.com")
    dup = client.post(
        "/api/v1/auth/register",
        json={"name": "Dup", "email": "dup@example.com", "password": "StrongPass123!", "terms_accepted": True},
    )
    assert dup.status_code == 409
    # Spec 7.6: the duplicate message must not confirm the account exists —
    # it uses the ambiguous "may already exist" phrasing.
    assert "may already exist" in dup.json()["error"]["message"].lower()


def test_csrf_required_for_mutations(client):
    register_user(client, "csrf@example.com")
    r = client.post("/api/v1/todos", json={"title": "no csrf"})
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "CSRF_FAILED"
    ok = client.post("/api/v1/todos", json={"title": "with csrf"}, headers=csrf(client))
    assert ok.status_code == 201


def test_unauthenticated_access_denied(client):
    client.post("/api/v1/auth/logout", json={}, headers=csrf(client))
    r = client.get("/api/v1/briefing")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHENTICATED"


def test_demo_session_seeds_mailbox(demo_client):
    data = demo_client.get("/api/v1/onboarding/status").json()["data"]
    assert data["state"] == "READY"
    assert data["mail_accounts"][0]["email_address"] == "you@demo.intenda.example"
    msgs = demo_client.get("/api/v1/emails?folder=inbox&limit=100").json()["data"]
    assert msgs["total"] >= 20
    threads = demo_client.get("/api/v1/threads?limit=100").json()["data"]
    assert threads["total"] >= 10  # seed: dozens of synthetic messages across many threads
    tasks = demo_client.get("/api/v1/tasks?limit=100").json()["data"]["items"]
    display_ids = {t["display_id"] for t in tasks}
    assert {"AG-2048", "AG-2051", "AG-2054"} <= display_ids


def test_password_reset_flow(client):
    email = "reset@example.com"
    register_user(client, email)
    r = client.post("/api/v1/auth/password/reset/request", json={"email": email})
    assert r.status_code == 200
    assert r.json()["data"]["accepted"] is True
    token = r.json()["data"].get("reset_token")
    assert token, "demo mode returns the reset token so the flow can complete"
    done = client.post(
        "/api/v1/auth/password/reset/complete",
        json={"token": token, "new_password": "NewStrongPass456!"},
    )
    assert done.status_code == 200
    # Old sessions revoked; new password works.
    assert client.get("/api/v1/auth/me").status_code == 401
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "NewStrongPass456!"})
    assert login.status_code == 200
    # Token is single-use.
    again = client.post(
        "/api/v1/auth/password/reset/complete",
        json={"token": token, "new_password": "AnotherPass789!"},
    )
    assert again.status_code == 400
