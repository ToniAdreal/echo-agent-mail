"""Agent fallback behavior with no model key configured (spec 5.5, 5.7)."""
from __future__ import annotations

from .conftest import csrf

FALLBACK = (
    "I'm temporarily unable to reach the AI model. Your request has been saved, "
    "but I have not taken any action. Please retry in a moment or continue manually."
)


def test_status_reports_unavailable_without_key(demo_client):
    s = demo_client.get("/api/v1/agent/status").json()["data"]
    assert s["available"] is False
    assert s["model"] == "openai/gpt-oss-20b"


def test_chat_fallback_exact_wording_and_no_side_effects(demo_client):
    tasks_before = demo_client.get("/api/v1/tasks?limit=100").json()["data"]["total"]
    conv = demo_client.post(
        "/api/v1/agent/conversations", json={"title": "Fallback check"}, headers=csrf(demo_client)
    ).json()["data"]["conversation"]
    with demo_client.stream(
        "POST",
        f"/api/v1/agent/conversations/{conv['id']}/messages",
        json={"content": "Please email Maya the signed contract now.", "stream": True},
        headers=csrf(demo_client),
    ) as resp:
        body = "".join(resp.iter_text())
    assert "message.error" in body
    assert FALLBACK in body
    detail = demo_client.get(f"/api/v1/agent/conversations/{conv['id']}").json()["data"]
    statuses = {(m["role"], m["status"]) for m in detail["messages"]}
    assert ("user", "model_unavailable") in statuses
    # The failed request must not have created a task or any side effect.
    tasks_after = demo_client.get("/api/v1/tasks?limit=100").json()["data"]["total"]
    assert tasks_after == tasks_before


def test_non_streaming_chat_also_falls_back(demo_client):
    conv = demo_client.post(
        "/api/v1/agent/conversations", json={"title": "Sync check"}, headers=csrf(demo_client)
    ).json()["data"]["conversation"]
    r = demo_client.post(
        f"/api/v1/agent/conversations/{conv['id']}/messages",
        json={"content": "Summarize my inbox", "stream": False},
        headers=csrf(demo_client),
    )
    assert r.status_code == 200
    data = r.json()["data"]
    # Clean fallback: no assistant answer is fabricated; the reply arrives as
    # a notice carrying the exact spec 5.5 wording.
    assert data["message"] is None
    assert data["notice"]["content"] == FALLBACK
