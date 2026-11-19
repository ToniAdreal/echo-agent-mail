"""Mail CRUD, drafts, simulated send, search and archive (spec 7.4.5-7.4.10)."""
from __future__ import annotations

from .conftest import csrf


def test_briefing_matches_seed(demo_client):
    b = demo_client.get("/api/v1/briefing").json()["data"]
    assert b["environment"] == "demo"
    assert b["metrics"]["new_mail"] == 8
    assert b["metrics"]["needs_decision"] >= 3
    assert b["badges"]["unread"] == 8


def test_inbox_folders_and_read_state(demo_client):
    inbox = demo_client.get("/api/v1/emails?folder=inbox&limit=100").json()["data"]
    assert inbox["total"] > 0
    msg = inbox["items"][0]
    detail = demo_client.get(f"/api/v1/emails/{msg['id']}").json()["data"]["message"]
    assert detail["body_text"]
    r = demo_client.post(
        f"/api/v1/emails/{msg['id']}/read-state",
        json={"is_read": True},
        headers=csrf(demo_client),
    )
    assert r.status_code == 200
    assert r.json()["data"]["is_read"] is True


def test_search_finds_seeded_invoice(demo_client):
    r = demo_client.get("/api/v1/search?q=invoice").json()["data"]
    assert len(r["items"]) >= 2
    assert r["total"] >= 2


def _make_draft(client, subject="Test hello", body="Hello from the test suite."):
    r = client.post(
        "/api/v1/drafts",
        json={"to": [{"email": "maya@acme.example"}], "subject": subject, "body": body},
        headers=csrf(client),
    )
    assert r.status_code == 201, r.text
    return r.json()["data"]["draft"]


def test_draft_send_simulated_and_idempotent(demo_client):
    before = demo_client.get("/api/v1/emails?folder=sent&limit=100").json()["data"]["total"]
    draft = _make_draft(demo_client)
    r = demo_client.post(
        f"/api/v1/emails/{draft['message_id']}/send",
        json={"draft_id": draft["id"], "revision": draft["revision"], "confirm_send": True},
        headers={**csrf(demo_client), "Idempotency-Key": "test-send-1"},
    )
    assert r.status_code == 200, r.text
    assert "Simulated send" in r.json()["data"]["send_result"]["notice"]
    after = demo_client.get("/api/v1/emails?folder=sent&limit=100").json()["data"]["total"]
    assert after == before + 1
    # Idempotent replay with the same key returns the stored result, no resend.
    replay = demo_client.post(
        f"/api/v1/emails/{draft['message_id']}/send",
        json={"draft_id": draft["id"], "revision": draft["revision"], "confirm_send": True},
        headers={**csrf(demo_client), "Idempotency-Key": "test-send-1"},
    )
    assert replay.status_code == 200
    final = demo_client.get("/api/v1/emails?folder=sent&limit=100").json()["data"]["total"]
    assert final == after


def test_send_requires_confirmation(demo_client):
    draft = _make_draft(demo_client, subject="Needs confirmation")
    r = demo_client.post(
        f"/api/v1/emails/{draft['message_id']}/send",
        json={"draft_id": draft["id"], "revision": draft["revision"], "confirm_send": False},
        headers=csrf(demo_client),
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "CONFIRMATION_REQUIRED"


def test_draft_revision_conflict(demo_client):
    draft = _make_draft(demo_client, subject="Draft v1")
    ok = demo_client.patch(
        f"/api/v1/drafts/{draft['id']}",
        json={"body": "v2", "revision": draft["revision"]},
        headers=csrf(demo_client),
    )
    assert ok.status_code == 200
    assert ok.json()["data"]["draft"]["body_text"] == "v2"
    stale = demo_client.patch(
        f"/api/v1/drafts/{draft['id']}",
        json={"body": "v3", "revision": draft["revision"]},
        headers=csrf(demo_client),
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "REVISION_CONFLICT"


def test_reply_creates_threaded_draft(demo_client):
    inbox = demo_client.get("/api/v1/emails?folder=inbox&limit=5").json()["data"]
    src = inbox["items"][0]
    r = demo_client.post(
        f"/api/v1/emails/{src['id']}/reply",
        json={"reply_all": False, "body": "Thanks!"},
        headers=csrf(demo_client),
    )
    assert r.status_code == 201, r.text
    draft = r.json()["data"]["draft"]
    assert draft["thread_id"] == src["thread_id"]
    assert draft["subject"].startswith("Re:")
    assert "Thanks!" in draft["body_text"]


def test_archive_and_restore_thread(demo_client):
    inbox = demo_client.get("/api/v1/emails?folder=inbox&limit=5").json()["data"]["items"]
    target_id = inbox[0]["thread_id"]
    r = demo_client.post(f"/api/v1/threads/{target_id}/archive", json={}, headers=csrf(demo_client))
    assert r.status_code == 200
    archived = demo_client.get("/api/v1/archive?limit=100").json()["data"]["items"]
    assert any(x["thread_id"] == target_id for x in archived)
    msg_id = next(x["id"] for x in archived if x["thread_id"] == target_id)
    back = demo_client.post(
        f"/api/v1/archive/{msg_id}/restore", json={"destination": "inbox"}, headers=csrf(demo_client)
    )
    assert back.status_code == 200
    remaining = demo_client.get("/api/v1/archive?limit=100").json()["data"]["items"]
    assert not any(x["thread_id"] == target_id for x in remaining)
