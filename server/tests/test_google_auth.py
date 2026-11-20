"""Google one-click sign-in (GIS ID token -> session).

The token-verification call to Google is stubbed in every test; nothing
leaves the process. What is covered: the public config endpoint, account
creation on first Google sign-in, sign-in to an existing password
account by verified email, rejection of unverifiable tokens and of
tokens issued for a different client ID, and the not-configured 503.
"""
from __future__ import annotations

import pytest

from .conftest import csrf, register_user

# NOTE: app.* is deliberately NOT imported at module top level (same
# conftest DATABASE_URL freeze concern as test_gmail.py). The fixture
# below imports the auth routes module through the client fixture and
# injects it into this module's globals.


@pytest.fixture(scope="module", autouse=True)
def _app_imported(client):
    from app.routes import auth

    globals().update({"auth": auth})


CLIENT_ID = "test-client-id.apps.googleusercontent.com"


def _claims(email: str, name: str = "Google User") -> dict:
    return {
        "aud": CLIENT_ID,
        "email": email,
        "email_verified": "true",
        "name": name,
        "sub": "google-sub-123",
    }


@pytest.fixture()
def google_configured(monkeypatch):
    monkeypatch.setattr(auth.settings, "GOOGLE_CLIENT_ID", CLIENT_ID)


def test_auth_config_reports_client_id(client, google_configured):
    r = client.get("/api/v1/auth/config")
    assert r.status_code == 200
    assert r.json()["data"]["google_client_id"] == CLIENT_ID


def test_auth_config_empty_when_unconfigured(client, monkeypatch):
    monkeypatch.setattr(auth.settings, "GOOGLE_CLIENT_ID", "")
    r = client.get("/api/v1/auth/config")
    assert r.status_code == 200
    assert r.json()["data"]["google_client_id"] == ""


def test_google_signin_creates_account_and_session(client, google_configured, monkeypatch):
    monkeypatch.setattr(
        auth, "_verify_google_id_token", lambda credential: _claims("gina@example.com", "Gina Google")
    )
    r = client.post("/api/v1/auth/google", json={"credential": "fake-id-token"})
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    assert data["user"]["email"] == "gina@example.com"
    assert data["user"]["name"] == "Gina Google"
    assert data["onboarding_state"] == "ACCOUNT_CREATED"

    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["data"]["user"]["email"] == "gina@example.com"

    out = client.post("/api/v1/auth/logout", json={}, headers=csrf(client))
    assert out.status_code == 200


def test_google_signin_existing_password_account(client, google_configured, monkeypatch):
    email = "linked@example.com"
    register_user(client, email)
    out = client.post("/api/v1/auth/logout", json={}, headers=csrf(client))
    assert out.status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401

    monkeypatch.setattr(auth, "_verify_google_id_token", lambda credential: _claims(email))
    r = client.post("/api/v1/auth/google", json={"credential": "fake-id-token"})
    assert r.status_code == 200, r.text
    assert r.json()["data"]["user"]["email"] == email

    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["data"]["user"]["email"] == email

    out = client.post("/api/v1/auth/logout", json={}, headers=csrf(client))
    assert out.status_code == 200


def test_google_signin_rejects_unverifiable_token(client, google_configured, monkeypatch):
    from app.errors import ApiError

    def _boom(credential):
        raise ApiError(401, "INVALID_CREDENTIALS", "Google sign-in could not be verified.")

    monkeypatch.setattr(auth, "_verify_google_id_token", _boom)
    r = client.post("/api/v1/auth/google", json={"credential": "garbage"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_google_signin_not_configured(client, monkeypatch):
    monkeypatch.setattr(auth.settings, "GOOGLE_CLIENT_ID", "")
    r = client.post("/api/v1/auth/google", json={"credential": "whatever"})
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "PROVIDER_NOT_CONFIGURED"


def test_verify_rejects_wrong_audience(client, google_configured, monkeypatch):
    """The real verifier must reject a token issued for another app."""
    import httpx

    from app.errors import ApiError

    class _Resp:
        status_code = 200

        def json(self):
            return {
                "aud": "someone-elses-client-id",
                "email": "mallory@example.com",
                "email_verified": "true",
            }

    monkeypatch.setattr(httpx, "get", lambda *a, **k: _Resp())
    with pytest.raises(ApiError) as excinfo:
        auth._verify_google_id_token("stolen-token")
    assert excinfo.value.status == 401


def test_verify_rejects_unverified_email(client, google_configured, monkeypatch):
    import httpx

    from app.errors import ApiError

    class _Resp:
        status_code = 200

        def json(self):
            return {"aud": CLIENT_ID, "email": "unv@example.com", "email_verified": "false"}

    monkeypatch.setattr(httpx, "get", lambda *a, **k: _Resp())
    with pytest.raises(ApiError) as excinfo:
        auth._verify_google_id_token("token")
    assert excinfo.value.status == 401
