"""WebSocket connection manager (spec Section 7.5).

Events are persisted in the database before broadcast where the catalogue
requires it (task events); the socket stream is an update signal, never the
sole source of truth.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from fastapi import WebSocket


def utc_iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class ConnectionManager:
    def __init__(self) -> None:
        self._conns: dict[str, set[WebSocket]] = {}
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    async def connect(self, user_id: str, ws: WebSocket) -> None:
        self._conns.setdefault(user_id, set()).add(ws)

    def disconnect(self, user_id: str, ws: WebSocket) -> None:
        conns = self._conns.get(user_id)
        if conns:
            conns.discard(ws)

    async def broadcast(self, user_id: str, event_type: str, payload: dict) -> None:
        message = {
            "type": event_type,
            "event_id": str(uuid.uuid4()),
            "timestamp": utc_iso(datetime.now(timezone.utc)),
            **payload,
        }
        for ws in list(self._conns.get(user_id, set())):
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(user_id, ws)

    def broadcast_threadsafe(self, user_id: str, event_type: str, payload: dict) -> None:
        """For sync (threadpool) route handlers: schedule onto the app loop."""
        if self._loop is None:
            return
        try:
            asyncio.run_coroutine_threadsafe(
                self.broadcast(user_id, event_type, payload), self._loop
            )
        except RuntimeError:
            pass


manager = ConnectionManager()
