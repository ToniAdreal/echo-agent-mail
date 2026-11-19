"""Onboarding, mail account and sync endpoints (spec 7.4.2 and 7.4.3)."""
from __future__ import annotations

import base64
import hashlib
import secrets
from datetime import timedelta

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session as DbSession

from .. import models as m
from .. import serializers as ser
from ..config import settings
from ..db import get_db
from ..deps import audit, get_current_user
from ..errors import ApiError, ok
from ..helpers import get_onboarding, set_onboarding_state
from ..security import new_token, sha256_hex
from ..services.syncsvc import start_sync

router = APIRouter(prefix="/api/v1", tags=["onboarding"])

PROVIDERS = {
    "google": {
        "name": "Google",
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "scopes": ["openid", "email", "profile", "https://www.googleapis.com/auth/gmail.modify"],
    },
    "microsoft": {
        "name": "Microsoft",
        "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "scopes": ["openid", "email", "profile", "Mail.ReadWrite", "Mail.Send", "offline_access"],
    },
}


def _provider_configured(provider: str) -> bool:
    if provider == "google":
        return bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)
    if provider == "microsoft":
        return bool(settings.MICROSOFT_CLIENT_ID and settings.MICROSOFT_CLIENT_SECRET)
    return False


def _client_id(provider: str) -> str:
    return settings.GOOGLE_CLIENT_ID if provider == "google" else settings.MICROSOFT_CLIENT_ID


def _client_secret(provider: str) -> str:
    return settings.GOOGLE_CLIENT_SECRET if provider == "google" else settings.MICROSOFT_CLIENT_SECRET


def _authorization_summary(provider: str) -> dict:
    cfg = PROVIDERS[provider]
    return {
        "provider": provider,
        "provider_name": cfg["name"],
        "scopes": cfg["scopes"],
        "can_read": True,
        "can_draft": True,
        "can_send": True,
        "can_archive_delete": True,
        "revocable": "You can revoke access at any time in your provider account settings.",
        "training_use": "Intenda does not use mailbox contents to train a model.",
        "demo_alternative": "You can choose the Demo Mailbox instead; no external account is accessed.",
    }


@router.get("/onboarding/status")
def onboarding_status(request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    ob = get_onboarding(db, user)
    accounts = (
        db.query(m.MailAccount)
        .filter(m.MailAccount.user_id == user.id, m.MailAccount.deleted_at.is_(None))
        .all()
    )
    return ok(request, {
        "state": ob.state,
        "completed_steps": ob.completed_steps or [],
        "mailbox_choice": ob.mailbox_choice,
        "last_error_code": ob.last_error_code,
        "mail_accounts": [ser.mail_account(a) for a in accounts],
    })


@router.post("/onboarding/start")
def onboarding_start(request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    ob = set_onboarding_state(db, user, "ACCOUNT_CREATED", step="account")
    return ok(request, {"state": ob.state})


@router.get("/onboarding/providers")
def onboarding_providers(request: Request, user: m.User = Depends(get_current_user)):
    providers = [
        {"id": "demo", "name": "Demo Mailbox", "available": settings.DEMO_MODE_ENABLED,
         "scopes": ["read", "compose", "send", "archive", "delete"],
         "note": "Seeded sample data. Simulated sync. No email will be sent externally."},
    ]
    for pid, cfg in PROVIDERS.items():
        providers.append({
            "id": pid, "name": cfg["name"], "available": _provider_configured(pid),
            "scopes": cfg["scopes"],
            "note": None if _provider_configured(pid) else "Not configured on this deployment.",
        })
    return ok(request, {"providers": providers})


class MailboxChoiceBody(BaseModel):
    choice: str


@router.post("/onboarding/mailbox-choice")
def mailbox_choice(body: MailboxChoiceBody, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    if body.choice not in {"demo", "google", "microsoft"}:
        raise ApiError(422, "VALIDATION_ERROR", "Choose demo, google or microsoft.")
    ob = get_onboarding(db, user)
    ob.mailbox_choice = body.choice
    if body.choice == "demo":
        ob.state = "DEMO_SELECTED"
        db.commit()
        return ok(request, {"next_step": "demo_mailbox", "authorization_summary": None})
    ob.state = "AUTHORIZATION_EXPLAINED"
    steps = list(ob.completed_steps or [])
    if "mailbox_choice" not in steps:
        steps.append("mailbox_choice")
        ob.completed_steps = steps
    db.commit()
    return ok(request, {"next_step": "provider_auth", "authorization_summary": _authorization_summary(body.choice)})


class OAuthStartBody(BaseModel):
    redirect_uri: str = ""


def _start_oauth(db: DbSession, user: m.User, provider: str, redirect_uri: str) -> dict:
    if provider not in PROVIDERS:
        raise ApiError(422, "VALIDATION_ERROR", "Unknown provider.")
    if not _provider_configured(provider):
        raise ApiError(
            503, "PROVIDER_NOT_CONFIGURED",
            f"{PROVIDERS[provider]['name']} sign-in is not configured on this deployment. "
            "You can use the Demo Mailbox instead, or connect a real account later in Settings once OAuth credentials are configured.",
        )
    state_value = new_token(24)
    verifier = new_token(32)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    db.add(m.OAuthState(
        user_id=user.id, provider=provider, state_hash=sha256_hex(state_value),
        pkce_verifier_ciphertext=verifier,  # demo-grade storage; production must encrypt
        redirect_uri=redirect_uri or f"{settings.OAUTH_REDIRECT_BASE_URL}/api/v1/onboarding/oauth/{provider}/callback",
        expires_at=m.now() + timedelta(minutes=10),
    ))
    db.commit()
    cfg = PROVIDERS[provider]
    params = {
        "client_id": _client_id(provider),
        "redirect_uri": redirect_uri or f"{settings.OAUTH_REDIRECT_BASE_URL}/api/v1/onboarding/oauth/{provider}/callback",
        "response_type": "code",
        "scope": " ".join(cfg["scopes"]),
        "state": state_value,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "access_type": "offline",
        "prompt": "consent",
    }
    from urllib.parse import urlencode

    return {
        "authorization_url": f"{cfg['auth_url']}?{urlencode(params)}",
        "state_expires_at": (m.now() + timedelta(minutes=10)).isoformat(),
    }


@router.post("/onboarding/oauth/{provider}/start")
def oauth_start(provider: str, body: OAuthStartBody, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    result = _start_oauth(db, user, provider, body.redirect_uri)
    ob = get_onboarding(db, user)
    ob.state = "PROVIDER_AUTH_PENDING"
    db.commit()
    return ok(request, result)


@router.get("/onboarding/oauth/{provider}/callback")
def oauth_callback(provider: str, request: Request, db: DbSession = Depends(get_db)):
    params = request.query_params
    code = params.get("code")
    state_value = params.get("state")
    fail_url = f"{settings.APP_BASE_URL}/onboarding?oauth_error="
    if params.get("error"):
        return RedirectResponse(f"{fail_url}cancelled")
    if not code or not state_value:
        return RedirectResponse(f"{fail_url}invalid_request")
    row = (
        db.query(m.OAuthState)
        .filter(
            m.OAuthState.provider == provider,
            m.OAuthState.state_hash == sha256_hex(state_value),
            m.OAuthState.consumed_at.is_(None),
        )
        .first()
    )
    if row is None or m.as_utc(row.expires_at) < m.now():
        return RedirectResponse(f"{fail_url}state_mismatch")
    row.consumed_at = m.now()
    db.commit()
    user = db.get(m.User, row.user_id)
    if user is None:
        return RedirectResponse(f"{fail_url}invalid_request")
    # Exchange the code server-side (only reachable when credentials exist).
    try:
        token_resp = httpx.post(
            PROVIDERS[provider]["token_url"],
            data={
                "client_id": _client_id(provider),
                "client_secret": _client_secret(provider),
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": row.redirect_uri,
                "code_verifier": row.pkce_verifier_ciphertext or "",
            },
            timeout=15.0,
        )
        if token_resp.status_code >= 400:
            raise RuntimeError("token exchange failed")
        tokens = token_resp.json()
    except Exception:
        ob = get_onboarding(db, user)
        ob.state = "AUTH_FAILED"
        ob.last_error_code = "TOKEN_EXCHANGE_FAILED"
        db.commit()
        return RedirectResponse(f"{fail_url}token_exchange")
    # Fetch the mailbox identity from the provider userinfo endpoint.
    email_address = user.email
    display_name = user.name
    try:
        if provider == "google":
            info = httpx.get(
                "https://openidconnect.googleapis.com/v1/userinfo",
                headers={"Authorization": f"Bearer {tokens.get('access_token')}"}, timeout=15.0,
            ).json()
        else:
            info = httpx.get(
                "https://graph.microsoft.com/v1.0/me",
                headers={"Authorization": f"Bearer {tokens.get('access_token')}"}, timeout=15.0,
            ).json()
        email_address = info.get("email") or info.get("mail") or info.get("userPrincipalName") or email_address
        display_name = info.get("name") or info.get("displayName") or display_name
    except Exception:
        pass
    account = m.MailAccount(
        user_id=user.id, provider=provider, email_address=str(email_address).lower(),
        display_name=display_name, environment="live", status="connected",
        scopes=PROVIDERS[provider]["scopes"],
        access_token_ciphertext=tokens.get("access_token"),
        refresh_token_ciphertext=tokens.get("refresh_token"),
        provider_account_id=str(email_address),
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    start_sync(db, user, account, mode="initial")
    set_onboarding_state(db, user, "SYNCING", step="mailbox_choice")
    return RedirectResponse(f"{settings.APP_BASE_URL}/onboarding?connected={provider}")


class DemoMailboxBody(BaseModel):
    seed_profile: str | None = None


def _create_demo_mailbox(db: DbSession, user: m.User, request: Request | None):
    from ..seed import seed_demo_mailbox

    if not settings.DEMO_MODE_ENABLED:
        raise ApiError(503, "DEMO_DISABLED", "The Demo Mailbox is not enabled on this deployment.")
    account = seed_demo_mailbox(db, user)
    job = start_sync(db, user, account, mode="initial")
    ob = get_onboarding(db, user)
    ob.mailbox_choice = "demo"
    ob.state = "SYNCING"
    steps = list(ob.completed_steps or [])
    for s in ("mailbox_choice", "demo_mailbox"):
        if s not in steps:
            steps.append(s)
    ob.completed_steps = steps
    db.commit()
    audit(db, user, "onboarding.demo_mailbox", "mail_account", account.id, request=request)
    db.commit()
    return account, job


@router.post("/onboarding/demo-mailbox")
def demo_mailbox(request: Request, body: DemoMailboxBody | None = None, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    account, job = _create_demo_mailbox(db, user, request)
    return ok(request, {"mail_account": ser.mail_account(account), "sync_job": ser.sync_job(job)}, status=201)


class CompleteBody(BaseModel):
    mail_account_id: str


@router.post("/onboarding/complete")
def onboarding_complete(body: CompleteBody, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    account = db.get(m.MailAccount, body.mail_account_id)
    if account is None or account.user_id != user.id:
        raise ApiError(404, "NOT_FOUND", "Mail account not found.")
    ob = set_onboarding_state(db, user, "READY", step="complete")
    return ok(request, {"completed": True, "redirect": "/app/briefing", "state": ob.state})


class RetryBody(BaseModel):
    step: str


@router.post("/onboarding/retry")
def onboarding_retry(body: RetryBody, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    ob = get_onboarding(db, user)
    if body.step == "sync":
        account = (
            db.query(m.MailAccount)
            .filter(m.MailAccount.user_id == user.id, m.MailAccount.deleted_at.is_(None))
            .order_by(m.MailAccount.created_at.desc())
            .first()
        )
        if account is None:
            raise ApiError(409, "INVALID_STATE", "No mailbox to sync yet.")
        failed = (
            db.query(m.SyncJob)
            .filter(m.SyncJob.mail_account_id == account.id, m.SyncJob.status == "failed")
            .order_by(m.SyncJob.created_at.desc())
            .first()
        )
        if failed is not None:
            failed.status = "running"
            failed.started_at = m.now()
            failed.error_code = None
            db.commit()
            job = failed
        else:
            job = start_sync(db, user, account, mode="incremental")
        ob.state = "SYNCING"
        db.commit()
        return ok(request, {"state": ob.state, "retry_started": True, "sync_job": ser.sync_job(job)})
    if body.step in {"auth", "mailbox_choice"}:
        ob.state = "MAILBOX_CHOICE"
        ob.last_error_code = None
        db.commit()
        return ok(request, {"state": ob.state, "retry_started": True})
    raise ApiError(409, "INVALID_STATE", f"Step {body.step} cannot be retried.")


# ---------------------------------------------------------------- accounts

@router.get("/accounts")
def list_accounts(request: Request, status: str | None = None, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    q = db.query(m.MailAccount).filter(
        m.MailAccount.user_id == user.id, m.MailAccount.deleted_at.is_(None)
    )
    if status:
        q = q.filter(m.MailAccount.status == status)
    return ok(request, {"items": [ser.mail_account(a) for a in q.order_by(m.MailAccount.created_at).all()]})


@router.get("/accounts/{account_id}")
def get_account(account_id: str, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    account = db.get(m.MailAccount, account_id)
    if account is None or account.user_id != user.id or account.deleted_at is not None:
        raise ApiError(404, "NOT_FOUND", "Mail account not found.")
    return ok(request, {"account": ser.mail_account(account)})


class ConnectBody(BaseModel):
    provider: str
    redirect_uri: str = ""


@router.post("/accounts/connect")
def connect_account(body: ConnectBody, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    if body.provider == "demo":
        account, job = _create_demo_mailbox(db, user, request)
        return ok(request, {"mail_account": ser.mail_account(account), "sync_job": ser.sync_job(job)}, status=201)
    result = _start_oauth(db, user, body.provider, body.redirect_uri)
    return ok(request, result)


@router.post("/accounts/{account_id}/reconnect")
def reconnect_account(account_id: str, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    account = db.get(m.MailAccount, account_id)
    if account is None or account.user_id != user.id:
        raise ApiError(404, "NOT_FOUND", "Mail account not found.")
    if account.provider == "demo":
        account.status = "connected"
        db.commit()
        return ok(request, {"account": ser.mail_account(account)})
    result = _start_oauth(db, user, account.provider, "")
    return ok(request, result)


class DisconnectBody(BaseModel):
    confirm_email: str | None = None


@router.delete("/accounts/{account_id}")
def disconnect_account(account_id: str, request: Request, body: DisconnectBody | None = None, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    account = db.get(m.MailAccount, account_id)
    if account is None or account.user_id != user.id or account.deleted_at is not None:
        raise ApiError(404, "NOT_FOUND", "Mail account not found.")
    account.status = "disconnected"
    account.deleted_at = m.now()
    audit(db, user, "account.disconnect", "mail_account", account.id, request=request)
    db.commit()
    return ok(request, {"disconnected": True})


class SyncBody(BaseModel):
    mode: str = "incremental"


@router.post("/accounts/{account_id}/sync")
def sync_account(account_id: str, body: SyncBody, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    account = db.get(m.MailAccount, account_id)
    if account is None or account.user_id != user.id or account.deleted_at is not None:
        raise ApiError(404, "NOT_FOUND", "Mail account not found.")
    running = (
        db.query(m.SyncJob)
        .filter(m.SyncJob.mail_account_id == account.id, m.SyncJob.status == "running")
        .first()
    )
    if running is not None:
        raise ApiError(409, "SYNC_IN_PROGRESS", "A sync is already running for this mailbox.")
    job = start_sync(db, user, account, mode=body.mode if body.mode in {"incremental", "full"} else "incremental")
    return ok(request, {"sync_job": ser.sync_job(job)}, status=201)


@router.get("/sync/status")
def sync_status(request: Request, account_id: str | None = None, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    q = db.query(m.SyncJob).filter(m.SyncJob.user_id == user.id)
    if account_id:
        q = q.filter(m.SyncJob.mail_account_id == account_id)
    jobs = q.order_by(m.SyncJob.created_at.desc()).limit(10).all()
    return ok(request, {"jobs": [ser.sync_job(j) for j in jobs]})


@router.get("/sync/jobs/{job_id}")
def sync_job_detail(job_id: str, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    job = db.get(m.SyncJob, job_id)
    if job is None or job.user_id != user.id:
        raise ApiError(404, "NOT_FOUND", "Sync job not found.")
    return ok(request, {"sync_job": ser.sync_job(job), "progress": ser.sync_job(job)["percent"]})


@router.post("/sync/jobs/{job_id}/retry")
def sync_job_retry(job_id: str, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    job = db.get(m.SyncJob, job_id)
    if job is None or job.user_id != user.id:
        raise ApiError(404, "NOT_FOUND", "Sync job not found.")
    if job.status not in {"failed"}:
        raise ApiError(409, "INVALID_STATE", "Only a failed sync job can be retried.")
    job.status = "running"
    job.started_at = m.now()
    job.error_code = None
    job.phase = "connecting"
    db.commit()
    return ok(request, {"sync_job": ser.sync_job(job)})
