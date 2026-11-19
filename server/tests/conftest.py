"""Shared fixtures: a fresh SQLite DB per test module, a TestClient bound to
the real app, and a demo user with a fully seeded mailbox."""
from __future__ import annotations

import os
import sys
import time
import uuid
from pathlib import Path

import pytest

SERVER_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVER_DIR))

os.environ["DEMO_SYNC_DELAY_MS"] = "10"
os.environ.pop("LLM_API_KEY", None)
os.environ.pop("GROQ_API_KEY", None)


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("db") / f"test-{uuid.uuid4().hex[:8]}.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    # Import after env is set so the engine binds to the test database.
    import importlib

    import app.db as db_mod
    importlib.reload(db_mod)
    import app.main as main_mod
    importlib.reload(main_mod)
    from fastapi.testclient import TestClient

    app = main_mod.create_app()
    with TestClient(app) as c:
        yield c


def csrf(client) -> dict:
    token = client.cookies.get("intenda_csrf")
    return {"x-csrf-token": token} if token else {}


def wait_ready(client, timeout=20.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        data = client.get("/api/v1/onboarding/status").json()["data"]
        if data["state"] == "READY":
            return data
        time.sleep(0.2)
    raise AssertionError(f"onboarding did not reach READY: {data}")


@pytest.fixture(scope="module")
def demo_client(client):
    r = client.post("/api/v1/auth/demo-session", json={})
    assert r.status_code in (200, 201), r.text
    wait_ready(client)
    return client


def register_user(client, email: str, password: str = "StrongPass123!") -> None:
    r = client.post(
        "/api/v1/auth/register",
        json={"name": "Test User", "email": email, "password": password, "terms_accepted": True},
    )
    assert r.status_code == 201, r.text
