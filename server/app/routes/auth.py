"""Authentication and session endpoints (spec Section 7.4.1)."""
from __future__ import annotations

import re
from datetime import timedelta

import httpx
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session as DbSession

from .. import serializers as ser
from ..config import settings
from ..db import get_db
from ..deps import audit, get_current_user, get_session_row, rate_limiter
from ..errors import ApiError, ok
from ..helpers import (
    apply_session_cookies,
    clear_session_cookies,
    create_session,
    get_onboarding,
    get_settings_row,
    idempotency_lookup,
    idempotency_store,
    set_onboarding_state,
)
from ..models import OAuthState, Session as SessionRow, User, now
from ..security import hash_password, new_token, password_policy_error, sha256_hex, verify_password

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegisterBody(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str
    password: str
    terms_accepted: bool = False


class LoginBody(BaseModel):
    email: str
    password: str


class GoogleBody(BaseModel):
    credential: str = Field(min_length=1)


class ResetRequestBody(BaseModel):
    email: str


class ResetCompleteBody(BaseModel):
    token: str
    new_password: str


def _session_payload(db: DbSession, user: User, request: Request) -> dict:
    ob = get_onboarding(db, user)
    return {
        "user": ser.user(user),
        "onboarding_state": ob.state,
    }


@router.post("/register")
def register(body: RegisterBody, request: Request, db: DbSession = Depends(get_db)):
    if not rate_limiter.check(f"register:{request.client.host if request.client else '?'}", 10, 3600):
        raise ApiError(429, "RATE_LIMITED", "Too many registration attempts. Please retry later.")
    email = body.email.strip().lower()
    if not EMAIL_RE.match(email):
        raise ApiError(422, "VALIDATION_ERROR", "Email address is not valid.", {"field": "email"})
    if not body.terms_accepted:
        raise ApiError(422, "VALIDATION_ERROR", "Terms and Privacy acknowledgement is required.", {"field": "terms_accepted"})
    policy_error = password_policy_error(body.password)
    if policy_error:
        raise ApiError(422, "VALIDATION_ERROR", policy_error, {"field": "password"})

    idem_key = request.headers.get("idempotency-key")
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user is not None:
        prior = idempotency_lookup(db, existing_user.id, idem_key, "auth.register")
        if prior is not None:
            return ok(request, prior, status=201)
        raise ApiError(
            409, "ACCOUNT_EXISTS",
            "An account may already exist for this email. Try signing in or resetting your password.",
        )

    user = User(
        name=body.name.strip(),
        email=email,
        password_hash=hash_password(body.password),
        status="active",
        terms_accepted_at=now(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    get_settings_row(db, user)
    set_onboarding_state(db, user, "ACCOUNT_CREATED", step="account")
    row, token, csrf = create_session(db, request, user)
    audit(db, user, "auth.register", "user", user.id, request=request)
    db.commit()
    payload = _session_payload(db, user, request)
    payload["session"] = ser.session(row, row.id)
    idempotency_store(db, user.id, idem_key, "auth.register", body.model_dump(exclude={"password"}), payload)
    return apply_session_cookies(ok(request, payload, status=201), token, csrf)


@router.post("/login")
def login(body: LoginBody, request: Request, db: DbSession = Depends(get_db)):
    email = body.email.strip().lower()
    if not rate_limiter.check(f"login:{email}", 10, 600):
        raise ApiError(429, "RATE_LIMITED", "Too many sign-in attempts. Please retry later.")
    user = db.query(User).filter(User.email == email, User.deleted_at.is_(None)).first()
    if user is None or not verify_password(user.password_hash, body.password):
        raise ApiError(401, "INVALID_CREDENTIALS", "Email or password is incorrect.")
    row, token, csrf = create_session(db, request, user)
    audit(db, user, "auth.login", "user", user.id, request=request)
    db.commit()
    payload = _session_payload(db, user, request)
    payload["session"] = ser.session(row, row.id)
    return apply_session_cookies(ok(request, payload), token, csrf)


@router.get("/config")
def auth_config(request: Request):
    """Public sign-in configuration for the auth pages.

    The Google client ID is a public identifier (it ships in every GIS
    page); the secret never leaves the server. An empty value means
    Google sign-in is not configured in this deployment and the auth
    pages simply do not render the button.
    """
    return ok(request, {"google_client_id": settings.GOOGLE_CLIENT_ID})


def _verify_google_id_token(credential: str) -> dict:
    """Verify a Google Identity Services ID token against Google's
    tokeninfo endpoint and return its claims. Raises ApiError on any
    failure; only tokens issued for this app's client ID with a
    verified email are accepted."""
    try:
        resp = httpx.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": credential},
            timeout=10.0,
        )
    except httpx.HTTPError:
        raise ApiError(502, "PROVIDER_ERROR", "Could not verify the Google sign-in. Please retry.")
    if resp.status_code != 200:
        raise ApiError(401, "INVALID_CREDENTIALS", "Google sign-in could not be verified.")
    claims = resp.json()
    if claims.get("aud") != settings.GOOGLE_CLIENT_ID:
        raise ApiError(401, "INVALID_CREDENTIALS", "Google sign-in could not be verified.")
    if claims.get("email_verified") not in (True, "true"):
        raise ApiError(401, "INVALID_CREDENTIALS", "Your Google email address is not verified.")
    email = (claims.get("email") or "").strip().lower()
    if not EMAIL_RE.match(email):
        raise ApiError(401, "INVALID_CREDENTIALS", "Google sign-in could not be verified.")
    claims["email"] = email
    return claims


@router.post("/google")
def google_signin(body: GoogleBody, request: Request, db: DbSession = Depends(get_db)):
    """One-click sign-in/sign-up with a GIS ID token. Finds the account
    by verified email (creating it on first use, like /register) and
    opens the same session /login would."""
    if not settings.GOOGLE_CLIENT_ID:
        raise ApiError(503, "PROVIDER_NOT_CONFIGURED", "Google sign-in is not configured in this deployment.")
    if not rate_limiter.check(f"google:{request.client.host if request.client else '?'}", 10, 600):
        raise ApiError(429, "RATE_LIMITED", "Too many sign-in attempts. Please retry later.")
    claims = _verify_google_id_token(body.credential)
    email = claims["email"]
    user = db.query(User).filter(User.email == email, User.deleted_at.is_(None)).first()
    created = False
    if user is None:
        name = (claims.get("name") or "").strip()[:120] or email.split("@")[0]
        user = User(
            name=name,
            email=email,
            # No usable password: the account signs in with Google.
            # (Same unusable-random-hash pattern as demo accounts.)
            password_hash=hash_password(new_token(24)),
            status="active",
            terms_accepted_at=now(),
            email_verified_at=now(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        get_settings_row(db, user)
        set_onboarding_state(db, user, "ACCOUNT_CREATED", step="account")
        created = True
    elif user.email_verified_at is None:
        user.email_verified_at = now()
    row, token, csrf = create_session(db, request, user)
    audit(db, user, "auth.google", "user", user.id, request=request)
    db.commit()
    payload = _session_payload(db, user, request)
    payload["session"] = ser.session(row, row.id)
    return apply_session_cookies(ok(request, payload, status=201 if created else 200), token, csrf)


@router.post("/logout")
def logout(request: Request, db: DbSession = Depends(get_db), user: User = Depends(get_current_user)):
    row = get_session_row(request, db)
    if row is not None:
        row.revoked_at = now()
        db.commit()
    resp = ok(request, {"logged_out": True})
    return clear_session_cookies(resp)


@router.get("/me")
def me(request: Request, db: DbSession = Depends(get_db), user: User = Depends(get_current_user)):
    row = get_session_row(request, db)
    payload = _session_payload(db, user, request)
    payload["session"] = ser.session(row, row.id if row else None)
    return ok(request, payload)


class DemoSessionBody(BaseModel):
    display_name: str | None = None


@router.post("/demo-session")
def demo_session(request: Request, body: DemoSessionBody | None = None, db: DbSession = Depends(get_db)):
    """One-click reviewer entry: creates a demo user with a Demo Mailbox."""
    from ..seed import seed_demo_mailbox

    if not settings.DEMO_MODE_ENABLED:
        raise ApiError(503, "DEMO_DISABLED", "The Demo Mailbox is not enabled on this deployment.")
    if not rate_limiter.check(f"demo:{request.client.host if request.client else '?'}", 10, 3600):
        raise ApiError(429, "RATE_LIMITED", "Too many demo sessions. Please retry later.")
    display_name = (body.display_name if body and body.display_name else "Demo Reviewer")[:80]
    suffix = new_token(4).replace("-", "").replace("_", "")[:8].lower()
    user = User(
        name=display_name,
        email=f"demo-{suffix}@demo.intenda.example",
        password_hash=hash_password(new_token(24)),
        status="active",
        terms_accepted_at=now(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    get_settings_row(db, user)
    set_onboarding_state(db, user, "ACCOUNT_CREATED", step="account")
    account = seed_demo_mailbox(db, user)
    from ..services.syncsvc import start_sync

    job = start_sync(db, user, account, mode="initial")
    set_onboarding_state(db, user, "SYNCING", step="demo_mailbox")
    row, token, csrf = create_session(db, request, user)
    audit(db, user, "auth.demo_session", "user", user.id, request=request)
    db.commit()
    payload = {
        "user": ser.user(user),
        "session": ser.session(row, row.id),
        "mail_account": ser.mail_account(account),
        "sync_job": ser.sync_job(job),
        "onboarding_state": "SYNCING",
        "demo": True,
    }
    return apply_session_cookies(ok(request, payload, status=201), token, csrf)


@router.post("/password/reset/request")
def reset_request(body: ResetRequestBody, request: Request, db: DbSession = Depends(get_db)):
    if not rate_limiter.check(f"pwreset:{body.email.strip().lower()}", 5, 3600):
        raise ApiError(429, "RATE_LIMITED", "Too many reset requests. Please retry later.")
    email = body.email.strip().lower()
    user = db.query(User).filter(User.email == email, User.deleted_at.is_(None)).first()
    token = None
    if user is not None:
        token = new_token(24)
        db.add(
            OAuthState(
                user_id=user.id,
                provider="password_reset",
                state_hash=sha256_hex(token),
                redirect_uri="",
                expires_at=now() + timedelta(hours=1),
            )
        )
        audit(db, user, "auth.password_reset_requested", "user", user.id, request=request)
        db.commit()
    # Always accepted: never reveal whether the account exists. In demo mode
    # (no outbound mail channel) the token is returned so the flow can be
    # completed end to end; production deployments email the link instead.
    payload: dict = {"accepted": True}
    if token is not None and settings.DEMO_MODE_ENABLED:
        payload["reset_token"] = token
    return ok(request, payload)


@router.post("/password/reset/complete")
def reset_complete(body: ResetCompleteBody, request: Request, db: DbSession = Depends(get_db)):
    policy_error = password_policy_error(body.new_password)
    if policy_error:
        raise ApiError(422, "VALIDATION_ERROR", policy_error, {"field": "new_password"})
    state = (
        db.query(OAuthState)
        .filter(
            OAuthState.provider == "password_reset",
            OAuthState.state_hash == sha256_hex(body.token),
            OAuthState.consumed_at.is_(None),
        )
        .first()
    )
    from ..models import as_utc

    if state is None or as_utc(state.expires_at) < now():
        raise ApiError(400, "RESET_TOKEN_INVALID", "This reset link is invalid or has expired.")
    user = db.get(User, state.user_id)
    if user is None:
        raise ApiError(400, "RESET_TOKEN_INVALID", "This reset link is invalid or has expired.")
    user.password_hash = hash_password(body.new_password)
    state.consumed_at = now()
    # Revoke all existing sessions after a password change.
    db.query(SessionRow).filter(
        SessionRow.user_id == user.id, SessionRow.revoked_at.is_(None)
    ).update({"revoked_at": now()})
    audit(db, user, "auth.password_reset_completed", "user", user.id, request=request)
    db.commit()
    return ok(request, {"password_updated": True})


@router.get("/sessions")
def list_sessions(request: Request, db: DbSession = Depends(get_db), user: User = Depends(get_current_user)):
    current = get_session_row(request, db)
    rows = (
        db.query(SessionRow)
        .filter(SessionRow.user_id == user.id, SessionRow.revoked_at.is_(None))
        .order_by(SessionRow.created_at.desc())
        .all()
    )
    return ok(request, {"items": [ser.session(r, current.id if current else None) for r in rows]})


@router.delete("/sessions/{session_id}")
def revoke_session(session_id: str, request: Request, db: DbSession = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.get(SessionRow, session_id)
    if row is None or row.user_id != user.id:
        raise ApiError(404, "NOT_FOUND", "Session not found.")
    row.revoked_at = now()
    audit(db, user, "auth.session_revoked", "session", row.id, request=request)
    db.commit()
    return ok(request, {"revoked": True})


@router.post("/sessions/revoke-others")
def revoke_others(request: Request, db: DbSession = Depends(get_db), user: User = Depends(get_current_user)):
    current = get_session_row(request, db)
    q = db.query(SessionRow).filter(
        SessionRow.user_id == user.id, SessionRow.revoked_at.is_(None)
    )
    if current is not None:
        q = q.filter(SessionRow.id != current.id)
    count = q.update({"revoked_at": now()})
    audit(db, user, "auth.sessions_revoked_others", "session", None, request=request, meta={"count": count})
    db.commit()
    return ok(request, {"revoked_count": count})
