"""Task lifecycle and server-side authorization gates (spec Sections 5-6)."""
from __future__ import annotations

import time

from .conftest import csrf

PLAN = {
    "goal": "Summarize a thread and prepare a reply",
    "steps": [
        {"step_type": "read_context", "title": "Read context"},
        {"step_type": "summarize", "title": "Summarize"},
        {"step_type": "draft_email", "title": "Draft reply"},
        {"step_type": "send_email", "title": "Send after approval"},
        {"step_type": "report", "title": "Report"},
    ],
}


def _thread_id(client) -> str:
    items = client.get("/api/v1/threads?limit=5").json()["data"]["items"]
    return items[0]["id"]


def _create_task(client, mode: str) -> dict:
    r = client.post(
        "/api/v1/tasks",
        json={
            "goal": PLAN["goal"],
            "plan": PLAN,
            "authorization_mode": mode,
            "context_scope": {"thread_ids": [_thread_id(client)]},
        },
        headers=csrf(client),
    )
    assert r.status_code == 201, r.text
    return r.json()["data"]["task"]


def _wait_status(client, task_id: str, statuses: set[str], timeout=25.0) -> dict:
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        last = client.get(f"/api/v1/tasks/{task_id}").json()["data"]["task"]
        if last["status"] in statuses:
            return last
        time.sleep(0.25)
    raise AssertionError(f"task did not reach {statuses}: {last}")


def test_mode_a_gates_every_step(demo_client):
    task = _create_task(demo_client, "confirm_every_step")
    gated = _wait_status(demo_client, task["id"], {"waiting_user"})
    assert gated["progress_percent"] == 0
    decisions = demo_client.get("/api/v1/decisions?status=pending").json()["data"]["items"]
    mine = [d for d in decisions if d["task_id"] == task["id"]]
    assert mine and mine[0]["decision_type"] == "approve_step"
    r = demo_client.post(
        f"/api/v1/decisions/{mine[0]['id']}/resolve",
        json={"choice": "approve"},
        headers=csrf(demo_client),
    )
    assert r.status_code == 200
    # Single-use: resolving again returns the original result, not an error.
    again = demo_client.post(
        f"/api/v1/decisions/{mine[0]['id']}/resolve",
        json={"choice": "approve"},
        headers=csrf(demo_client),
    )
    assert again.status_code == 200
    assert again.json()["data"]["decision"]["status"] == "approved"


def test_mode_c_runs_to_review_and_completes_on_approval(demo_client):
    task = _create_task(demo_client, "confirm_before_send")
    gated = _wait_status(demo_client, task["id"], {"waiting_user"})
    assert gated["progress_percent"] >= 60  # internal steps ran automatically
    detail = demo_client.get(f"/api/v1/tasks/{task['id']}").json()["data"]
    pending_reviews = [r for r in detail["outputs"] if r["status"] == "pending"]
    assert pending_reviews, "a draft must wait in the Review Queue before sending"
    item = demo_client.get(f"/api/v1/review/{pending_reviews[0]['id']}").json()["data"]["review_item"]
    r = demo_client.post(
        f"/api/v1/review/{item['id']}/approve",
        json={"revision": item["revision"], "confirm_send": True},
        headers=csrf(demo_client),
    )
    assert r.status_code == 200, r.text
    assert "Simulated send" in r.json()["data"]["send_result"]["notice"]
    done = _wait_status(demo_client, task["id"], {"completed"})
    assert done["progress_percent"] == 100


def test_task_requires_confirmed_plan(demo_client):
    r = demo_client.post(
        "/api/v1/tasks",
        json={"goal": "x", "authorization_mode": "confirm_milestones"},
        headers=csrf(demo_client),
    )
    assert r.status_code == 422


def test_pause_resume_terminate(demo_client):
    task = _create_task(demo_client, "confirm_milestones")
    _wait_status(demo_client, task["id"], {"running", "waiting_user"})
    p = demo_client.post(f"/api/v1/tasks/{task['id']}/pause", json={}, headers=csrf(demo_client))
    assert p.json()["data"]["task"]["status"] == "paused"
    # Resume requires acknowledging the progress summary (spec 6.4).
    bad = demo_client.post(
        f"/api/v1/tasks/{task['id']}/resume", json={}, headers=csrf(demo_client)
    )
    assert bad.status_code == 422
    ok = demo_client.post(
        f"/api/v1/tasks/{task['id']}/resume",
        json={"acknowledge_summary": True},
        headers=csrf(demo_client),
    )
    assert ok.status_code == 200
    t = demo_client.post(
        f"/api/v1/tasks/{task['id']}/terminate",
        json={"confirmation": True},
        headers=csrf(demo_client),
    )
    assert t.json()["data"]["task"]["status"] == "cancelled"


def test_seeded_ag2051_choice_completes_task(demo_client):
    tasks = demo_client.get("/api/v1/tasks?limit=100").json()["data"]["items"]
    t51 = next(t for t in tasks if t["display_id"] == "AG-2051")
    decisions = demo_client.get("/api/v1/decisions?status=pending").json()["data"]["items"]
    choice = next(d for d in decisions if d["task_id"] == t51["id"] and d["decision_type"] == "choose_option")
    r = demo_client.post(
        f"/api/v1/decisions/{choice['id']}/resolve",
        json={"choice": "wed-1400"},
        headers=csrf(demo_client),
    )
    assert r.status_code == 200, r.text
    assert r.status_code == 200
    done = _wait_status(demo_client, t51["id"], {"completed"})
    assert done["progress_percent"] == 100
