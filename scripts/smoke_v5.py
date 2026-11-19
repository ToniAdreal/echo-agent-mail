#!/usr/bin/env python3
"""Intenda V5 end-to-end smoke test.

Starts the real FastAPI server (uvicorn) against a throwaway SQLite DB,
then exercises the product the way a user would:

  health -> register -> demo mailbox seed -> onboarding READY -> inbox list
  -> agent chat (deterministic fallback, no LLM key) -> delegated task runs
  to the Review Queue gate -> WebSocket hello -> SPA served by FastAPI.

Usage:  python3 scripts/smoke_v5.py [--port 8791]
Exit code 0 only if every step passes.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, "server")
VENV_PY = os.path.join(SERVER, ".venv", "bin", "python")

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> bool:
    RESULTS.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8791)
    args = ap.parse_args()
    base = f"http://127.0.0.1:{args.port}"
    ws_url = f"ws://127.0.0.1:{args.port}/api/v1/ws"

    sys.path.insert(0, os.path.join(SERVER, ".venv", "lib", "python3.12", "site-packages"))
    import httpx  # from server/.venv
    import websockets

    db_path = tempfile.mktemp(suffix="-smoke.db")
    env = dict(os.environ)
    env["DATABASE_URL"] = f"sqlite:///{db_path}"
    env["DEMO_SYNC_DELAY_MS"] = "50"
    env.pop("LLM_API_KEY", None)  # smoke must prove the no-key fallback path
    env.pop("GROQ_API_KEY", None)

    proc = subprocess.Popen(
        [VENV_PY, "-m", "uvicorn", "app.main:app", "--app-dir", SERVER,
         "--host", "127.0.0.1", "--port", str(args.port)],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        # 1. Health (wait for boot)
        healthy = False
        for _ in range(60):
            try:
                with urllib.request.urlopen(base + "/api/v1/health", timeout=2) as r:
                    healthy = r.status == 200
                    if healthy:
                        break
            except Exception:
                time.sleep(0.5)
        if not check("health endpoint", healthy):
            return _finish(proc, db_path)

        c = httpx.Client(base_url=base, timeout=30, trust_env=False)

        # 2. Register
        r = c.post("/api/v1/auth/register", json={
            "name": "Smoke Tester", "email": "smoke@example.com",
            "password": "SmokePass123!", "terms_accepted": True,
        })
        check("register", r.status_code == 201, f"status={r.status_code}")
        csrf = {"x-csrf-token": c.cookies.get("intenda_csrf")}

        # 3. Demo mailbox seed + onboarding READY
        r = c.post("/api/v1/auth/demo-session", json={})
        check("demo session created", r.status_code in (200, 201), f"status={r.status_code}")
        csrf = {"x-csrf-token": c.cookies.get("intenda_csrf")}
        state = None
        for _ in range(40):
            data = c.get("/api/v1/onboarding/status").json()["data"]
            state = data["state"]
            if state == "READY":
                break
            time.sleep(0.5)
        check("onboarding reaches READY", state == "READY", f"state={state}")
        addr = data["mail_accounts"][0]["email_address"] if data.get("mail_accounts") else "?"
        check("demo address labelled", addr == "you@demo.intenda.example", addr)

        # 4. Briefing + inbox
        b = c.get("/api/v1/briefing").json()["data"]
        check("briefing metrics", b["metrics"]["new_mail"] == 8 and b["badges"]["review"] >= 1,
              f"new_mail={b['metrics']['new_mail']} review_badge={b['badges']['review']}")
        inbox = c.get("/api/v1/emails?folder=inbox&limit=5").json()["data"]
        check("inbox lists seeded mail", inbox["total"] >= 20, f"total={inbox['total']}")

        # 5. Agent chat fallback over SSE (no LLM key configured)
        conv = c.post("/api/v1/agent/conversations", json={"title": "Smoke"}, headers=csrf).json()["data"]["conversation"]
        with c.stream("POST", f"/api/v1/agent/conversations/{conv['id']}/messages",
                      json={"content": "Summarize my inbox", "stream": True}, headers=csrf) as resp:
            body = "".join(resp.iter_text())
        check("agent SSE fallback (spec 5.5)",
              "message.error" in body and "temporarily unable to reach the AI model" in body,
              "fallback wording present" if "temporarily unable to reach the AI model" in body else body[:120])

        # 6. Delegated task runs to the Review Queue gate
        thread_id = c.get("/api/v1/threads?limit=1").json()["data"]["items"][0]["id"]
        plan = {"goal": "Smoke delegation", "steps": [
            {"step_type": "read_context", "title": "Read context"},
            {"step_type": "summarize", "title": "Summarize"},
            {"step_type": "draft_email", "title": "Draft reply"},
            {"step_type": "send_email", "title": "Send after approval"},
            {"step_type": "report", "title": "Report"},
        ]}
        r = c.post("/api/v1/tasks", json={
            "goal": "Smoke delegation", "plan": plan,
            "authorization_mode": "confirm_before_send",
            "context_scope": {"thread_ids": [thread_id]},
        }, headers=csrf)
        check("task created", r.status_code == 201, f"status={r.status_code}")
        task = r.json()["data"]["task"]
        status, outputs = None, []
        for _ in range(60):
            detail = c.get(f"/api/v1/tasks/{task['id']}").json()["data"]
            status = detail["task"]["status"]
            outputs = detail["outputs"]
            if status == "waiting_user" and outputs:
                break
            time.sleep(0.5)
        check("task gates at Review Queue with a draft",
              status == "waiting_user" and len(outputs) >= 1,
              f"status={status} outputs={len(outputs)}")

        # 7. WebSocket hello
        async def ws_hello() -> str:
            cookie = "; ".join(f"{k}={v}" for k, v in c.cookies.items())
            async with websockets.connect(ws_url, additional_headers={"Cookie": cookie}) as ws:
                msg = await asyncio.wait_for(ws.recv(), timeout=10)
                return json.loads(msg).get("type", "")
        try:
            hello_type = asyncio.run(ws_hello())
        except Exception as exc:  # noqa: BLE001
            hello_type = f"error: {exc}"
        check("websocket server.hello", hello_type == "server.hello", hello_type)

        # 8. FastAPI serves the built SPA + fallback
        r = c.get("/")
        spa_ok = r.status_code == 200 and "<div id=\"root\">" in r.text
        r2 = c.get("/briefing")
        check("SPA served with fallback", spa_ok and r2.status_code == 200,
              f"/ ={r.status_code} /briefing={r2.status_code}")
        r3 = c.get("/api/v1/does-not-exist")
        check("unknown API route returns envelope 404",
              r3.status_code == 404 and r3.json()["error"]["code"] == "NOT_FOUND",
              f"status={r3.status_code}")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
    return _finish(proc, db_path)


def _finish(proc, db_path: str) -> int:
    try:
        os.unlink(db_path)
    except OSError:
        pass
    failed = [n for n, ok, _ in RESULTS if not ok]
    print(f"\nSMOKE {'FAILED' if failed else 'PASSED'}: "
          f"{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed"
          + (f" — failed: {', '.join(failed)}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
