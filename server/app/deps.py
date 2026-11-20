"""FastAPI dependencies: current session/user, CSRF, rate limiting, audit."""
from __future__ import annotations

import hashlib
import time
from collections import defaultdict
from datetime import timedelta

from fastapi import Depends, Request
from sqlalchemy.orm import Session as DbSession

from .config import settings
from .db import get_db
from .errors import ApiError
from .models import AuditLog, Session as SessionRow, User, now
from .security import sha256_hex

SESSION_COOKIE = "intenda_session"
CSRF_COOKIE = "intenda_csrf"
CSRF_HEADER = "x-csrf-token"

# Paths that establish a session (no prior cookie auth, so no CSRF token yet).
CSRF_EXEMPT_SUFFIXES = (
    "/auth/register",
    "/auth/login",
    "/auth/google",
    "/auth/demo-session",
    "/auth/password/reset/request",
    "/auth/password/reset/complete",
)


class RateLimiter:
    """In-memory sliding-window limiter (demo scale, single process)."""

    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str, limit: int, window_seconds: int) -> bool:
        t = time.time()
        bucket = [x for x in self._hits[key] if t - x < window_seconds]
        if len(bucket) >= limit:
            self._hits[key] = bucket
            return False
        bucket.append(t)
        self._hits[key] = bucket
        return True


rate_limiter = RateLimiter()


def client_ip_hash(request: Request) -> str:
    ip = request.client.host if request.client else "unknown"
    return hashlib.sha256(f"{settings.SESSION_SECRET}:{ip}".encode()).hexdigest()


def get_session_row(request: Request, db: DbSession) -> SessionRow | None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    row = (
        db.query(SessionRow)
        .filter(SessionRow.session_hash == sha256_hex(token), SessionRow.revoked_at.is_(None))
        .first()
    )
    if row is None:
        return None
    current = now()
    from .models import as_utc

    if as_utc(row.expires_at) < current:
        return None
    if current - as_utc(row.last_seen_at) > timedelta(hours=settings.SESSION_IDLE_HOURS):
        return None
    row.last_seen_at = current
    db.commit()
    return row


def get_current_user(request: Request, db: DbSession = Depends(get_db)) -> User:
    row = get_session_row(request, db)
    if row is None:
        raise ApiError(401, "UNAUTHENTICATED", "Sign in is required.")
    user = db.get(User, row.user_id)
    if user is None or user.deleted_at is not None or user.status == "deleted":
        raise ApiError(401, "UNAUTHENTICATED", "Sign in is required.")
    request.state.session_row = row
    return user


def require_csrf(request: Request) -> None:
    """CSRF check for cookie-authenticated mutations (double-submit token)."""
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return
    if request.url.path.endswith(CSRF_EXEMPT_SUFFIXES):
        return
    row: SessionRow | None = getattr(request.state, "session_row", None)
    token = request.headers.get(CSRF_HEADER)
    if row is None or not token or row.csrf_token_hash != sha256_hex(token):
        raise ApiError(403, "CSRF_FAILED", "CSRF token is missing or invalid.")


def audit(
    db: DbSession,
    user: User,
    action: str,
    resource_type: str = "",
    resource_id: str | None = None,
    actor_type: str = "user",
    environment: str = "demo",
    result: str = "success",
    meta: dict | None = None,
    request: Request | None = None,
) -> None:
    db.add(
        AuditLog(
            user_id=user.id,
            actor_type=actor_type,
            actor_id=user.id if actor_type == "user" else None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            environment=environment,
            result=result,
            meta=meta or {},
            ip_hash=client_ip_hash(request) if request is not None else None,
        )
    )
