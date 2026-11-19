"""WebSocket endpoint /api/v1/ws (spec 7.5). Auth via the session cookie."""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..db import SessionLocal
from ..deps import SESSION_COOKIE
from ..models import Session as SessionRow, Task, User
from ..security import sha256_hex
from ..ws import manager, utc_iso

router = APIRouter(tags=["ws"])


def _authenticate(ws: WebSocket) -> User | None:
    token = ws.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    db = SessionLocal()
    try:
        row = (
            db.query(SessionRow)
            .filter(SessionRow.session_hash == sha256_hex(token), SessionRow.revoked_at.is_(None))
            .first()
        )
        if row is None:
            return None
        from ..models import as_utc, now

        if as_utc(row.expires_at) < now():
            return None
        return db.get(User, row.user_id)
    finally:
        db.close()


@router.websocket("/api/v1/ws")
async def websocket_endpoint(ws: WebSocket):
    user = _authenticate(ws)
    if user is None:
        await ws.close(code=4401)
        return
    await ws.accept()
    user_id = user.id
    connection_id = str(uuid.uuid4())
    await manager.connect(user_id, ws)
    await ws.send_json({
        "type": "server.hello",
        "event_id": str(uuid.uuid4()),
        "timestamp": utc_iso(datetime.now(timezone.utc)),
        "connection_id": connection_id,
        "server_time": utc_iso(datetime.now(timezone.utc)),
        "resume_from": None,
    })

    async def heartbeat():
        while True:
            await asyncio.sleep(30)
            try:
                await ws.send_json({
                    "type": "server.heartbeat",
                    "event_id": str(uuid.uuid4()),
                    "timestamp": utc_iso(datetime.now(timezone.utc)),
                })
            except Exception:
                return

    hb = asyncio.create_task(heartbeat())
    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except Exception:
                continue
            mtype = msg.get("type")
            if mtype == "client.ping":
                await ws.send_json({
                    "type": "server.heartbeat",
                    "event_id": str(uuid.uuid4()),
                    "timestamp": utc_iso(datetime.now(timezone.utc)),
                })
            elif mtype == "client.hello":
                await ws.send_json({
                    "type": "server.hello",
                    "event_id": str(uuid.uuid4()),
                    "timestamp": utc_iso(datetime.now(timezone.utc)),
                    "connection_id": connection_id,
                    "server_time": utc_iso(datetime.now(timezone.utc)),
                    "resume_from": msg.get("last_event_id"),
                })
            elif mtype == "client.task.watch":
                task_id = msg.get("task_id")
                db = SessionLocal()
                try:
                    task = db.get(Task, task_id) if task_id else None
                    if task is not None and task.user_id == user_id:
                        await ws.send_json({
                            "type": "task.progress",
                            "event_id": str(uuid.uuid4()),
                            "timestamp": utc_iso(datetime.now(timezone.utc)),
                            "task_id": task.id,
                            "percent": task.progress_percent,
                            "summary": f"Task is {task.status}",
                            "current_step_id": task.current_step_id,
                        })
                    else:
                        await ws.send_json({
                            "type": "server.error",
                            "event_id": str(uuid.uuid4()),
                            "timestamp": utc_iso(datetime.now(timezone.utc)),
                            "code": "NOT_FOUND", "message": "Task not found.", "retryable": False,
                        })
                finally:
                    db.close()
            # client.subscribe / unsubscribe / task.ack / sync.request are
            # accepted; all events for owned resources are pushed on the
            # user's channel and REST remains the source of truth.
    except WebSocketDisconnect:
        pass
    finally:
        hb.cancel()
        manager.disconnect(user_id, ws)
