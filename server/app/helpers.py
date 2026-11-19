"""Shared helpers: sessions, cookies, pagination, idempotency, settings."""
from __future__ import annotations

import base64
import hashlib
import json
from datetime import timedelta

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session as DbSession

from .config import settings
from .deps import SESSION_COOKIE, CSRF_COOKIE, client_ip_hash
from .models import (
    IdempotencyRecord,
    OnboardingState,
    Session as SessionRow,
    User,
    UserSettings,
    now,
)
from .security import new_token, sha256_hex


def create_session(db: DbSession, request: Request, user: User) -> tuple[SessionRow, str, str]:
    token = new_token(32)
    csrf = new_token(24)
    row = SessionRow(
        user_id=user.id,
        session_hash=sha256_hex(token),
        csrf_token_hash=sha256_hex(csrf),
        ip_hash=client_ip_hash(request),
        user_agent=(request.headers.get("user-agent") or "")[:300],
        expires_at=now() + timedelta(days=settings.SESSION_ABSOLUTE_DAYS),
        last_seen_at=now(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row, token, csrf


def apply_session_cookies(resp: JSONResponse, token: str, csrf: str) -> JSONResponse:
    resp.set_cookie(
        SESSION_COOKIE, token, httponly=True, secure=settings.COOKIE_SECURE,
        samesite="lax", path="/", max_age=settings.SESSION_ABSOLUTE_DAYS * 86400,
    )
    # CSRF cookie is readable by JS (double-submit pattern); the session cookie is not.
    resp.set_cookie(
        CSRF_COOKIE, csrf, httponly=False, secure=settings.COOKIE_SECURE,
        samesite="lax", path="/", max_age=settings.SESSION_ABSOLUTE_DAYS * 86400,
    )
    return resp


def clear_session_cookies(resp: JSONResponse) -> JSONResponse:
    resp.delete_cookie(SESSION_COOKIE, path="/")
    resp.delete_cookie(CSRF_COOKIE, path="/")
    return resp


def get_settings_row(db: DbSession, user: User) -> UserSettings:
    row = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
    if row is None:
        row = UserSettings(
            user_id=user.id,
            appearance="night",
            default_authorization_mode="confirm_milestones",
            agent_preferences={
                "response_style": "balanced",
                "context_permission": "selected_only",
                "model_provider": settings.LLM_PROVIDER_NAME,
                "model_id": settings.LLM_MODEL,
            },
            notification_preferences={"in_app": True, "email_digest": False},
            privacy_preferences={"data_use_explained": True},
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def get_onboarding(db: DbSession, user: User) -> OnboardingState:
    row = db.query(OnboardingState).filter(OnboardingState.user_id == user.id).first()
    if row is None:
        row = OnboardingState(user_id=user.id, state="NOT_STARTED", completed_steps=[])
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def set_onboarding_state(db: DbSession, user: User, state: str, step: str | None = None) -> OnboardingState:
    row = get_onboarding(db, user)
    row.state = state
    steps = list(row.completed_steps or [])
    if step and step not in steps:
        steps.append(step)
        row.completed_steps = steps
    db.commit()
    db.refresh(row)
    return row


def encode_cursor(offset: int) -> str:
    return base64.urlsafe_b64encode(f"o:{offset}".encode()).decode()


def decode_cursor(cursor: str | None) -> int:
    if not cursor:
        return 0
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        return max(0, int(raw.split(":", 1)[1]))
    except Exception:
        return 0


def paginate(query, limit: int | None, cursor: str | None):
    """Offset-based opaque cursor pagination over an ordered query."""
    limit = min(max(limit or 50, 1), 200)
    offset = decode_cursor(cursor)
    total = query.count()
    items = query.offset(offset).limit(limit).all()
    next_cursor = encode_cursor(offset + limit) if offset + limit < total else None
    return items, next_cursor, total


def idempotency_lookup(db: DbSession, user_id: str, key: str | None, operation: str) -> dict | None:
    if not key:
        return None
    rec = (
        db.query(IdempotencyRecord)
        .filter(
            IdempotencyRecord.user_id == user_id,
            IdempotencyRecord.idempotency_key == key,
            IdempotencyRecord.operation == operation,
        )
        .first()
    )
    return rec.response_json if rec else None


def idempotency_store(db: DbSession, user_id: str, key: str | None, operation: str, payload, response: dict) -> None:
    if not key:
        return
    req_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
    db.add(
        IdempotencyRecord(
            user_id=user_id,
            idempotency_key=key,
            operation=operation,
            request_hash=req_hash,
            response_json=response,
            expires_at=now() + timedelta(days=1),
        )
    )
    db.commit()
