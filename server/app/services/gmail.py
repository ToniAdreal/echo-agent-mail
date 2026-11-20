"""Real Gmail connectivity for live Google mail accounts.

Everything the OAuth callback leaves behind is implemented here:

- access-token lifecycle (decrypt, refresh when expiring, re-encrypt),
- mailbox sync into EmailThread / EmailMessage / EmailAttachment rows,
  idempotent on (mail_account_id, provider_thread_id) and
  (mail_account_id, provider_message_id),
- real sends through the Gmail API for approved drafts.

Demo accounts never touch this module; the runner and perform_send branch
on environment="live" + provider="google" only.

The HTTP layer is httpx (async). Functions accept an optional
``transport`` so tests can inject httpx.MockTransport without network.
"""
from __future__ import annotations

import asyncio
import base64
import re
import threading
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage as MimeMessage
from email.utils import formataddr, getaddresses, parseaddr

import httpx
from sqlalchemy.orm import Session as DbSession

from .. import models as m
from ..config import settings
from ..security import decrypt_secret, encrypt_secret

GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1"
TOKEN_URL = "https://oauth2.googleapis.com/token"

_REFRESH_SKEW = timedelta(seconds=60)


class GmailError(Exception):
    """A Gmail API call failed in a way that is not an auth problem."""


class GmailAuthError(GmailError):
    """The stored credentials can no longer produce a valid access token
    (revoked grant, expired refresh token, ...). The account needs the user
    to reconnect it."""


# ---------------------------------------------------------------------------
# Access tokens
# ---------------------------------------------------------------------------


async def get_access_token(
    db: DbSession, account: m.MailAccount, *, transport: httpx.BaseTransport | None = None
) -> str:
    """Return a valid Gmail access token for the account, refreshing (and
    persisting, encrypted) when the stored one is missing or expiring."""
    expires_at = m.as_utc(account.token_expires_at)
    if (
        account.access_token_ciphertext
        and expires_at is not None
        and expires_at > m.now() + _REFRESH_SKEW
    ):
        return decrypt_secret(account.access_token_ciphertext)
    if not account.refresh_token_ciphertext:
        raise GmailAuthError("No refresh token is stored for this account; reconnect it.")
    refresh_token = decrypt_secret(account.refresh_token_ciphertext)
    async with httpx.AsyncClient(timeout=20.0, transport=transport) as client:
        resp = await client.post(
            TOKEN_URL,
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
    if resp.status_code >= 400:
        error = ""
        try:
            error = str(resp.json().get("error") or "")
        except Exception:
            pass
        if error == "invalid_grant" or resp.status_code in {400, 401}:
            raise GmailAuthError(
                f"Gmail token refresh was rejected ({error or resp.status_code}); reconnect the account."
            )
        raise GmailError(f"Gmail token refresh failed with status {resp.status_code}.")
    data = resp.json()
    access_token = data.get("access_token")
    if not access_token:
        raise GmailError("Gmail token refresh returned no access token.")
    account.access_token_ciphertext = encrypt_secret(access_token)
    expires_in = data.get("expires_in")
    account.token_expires_at = (
        m.now() + timedelta(seconds=int(expires_in)) if expires_in else None
    )
    if data.get("refresh_token"):
        account.refresh_token_ciphertext = encrypt_secret(data["refresh_token"])
    db.commit()
    return access_token


# ---------------------------------------------------------------------------
# Message parsing (pure functions over the Gmail JSON representation)
# ---------------------------------------------------------------------------

_SUBJECT_PREFIX_RE = re.compile(r"^\s*(re|fwd|fw)\s*:\s*", re.IGNORECASE)
_SCRIPT_STYLE_RE = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)


def normalize_subject(subject: str | None) -> str:
    """Strip repeated Re:/Fwd:/Fw: prefixes, matching the seed convention
    where a thread's subject_normalized drops the reply prefixes."""
    text = (subject or "").strip()
    while True:
        stripped = _SUBJECT_PREFIX_RE.sub("", text).strip()
        if stripped == text:
            return text
        text = stripped


def _header_map(payload: dict) -> dict[str, str]:
    headers: dict[str, str] = {}
    for header in payload.get("headers") or []:
        name = str(header.get("name") or "").lower()
        if name and name not in headers:
            headers[name] = str(header.get("value") or "")
    return headers


def _parse_address_list(value: str | None) -> list[dict]:
    out: list[dict] = []
    for name, addr in getaddresses([value or ""]):
        addr = addr.strip()
        if not addr:
            continue
        out.append({"name": name.strip(), "email": addr})
    return out


def _parse_from(value: str | None) -> tuple[str | None, str]:
    name, addr = parseaddr(value or "")
    addr = addr.strip()
    if not addr:
        # Malformed From header: keep the raw value as the address so the
        # message still renders instead of failing the whole sync.
        addr = (value or "").strip()
    return (name.strip() or None), addr


def _b64url_decode(data: str) -> str:
    padded = data + "=" * (-len(data) % 4)
    raw = base64.urlsafe_b64decode(padded.encode("ascii"))
    return raw.decode("utf-8", errors="replace")


def _walk_parts(part: dict):
    yield part
    for sub in part.get("parts") or []:
        yield from _walk_parts(sub)


def parse_gmail_message(raw: dict) -> dict:
    """Convert one Gmail API message resource (format=full) into the field
    set used by EmailMessage plus thread/attachment side data."""
    payload = raw.get("payload") or {}
    headers = _header_map(payload)
    from_name, from_address = _parse_from(headers.get("from"))

    body_text: str | None = None
    body_html: str | None = None
    attachments: list[dict] = []
    for part in _walk_parts(payload):
        mime = str(part.get("mimeType") or "")
        filename = part.get("filename") or ""
        body = part.get("body") or {}
        if filename:
            attachments.append({
                "filename": filename,
                "mime_type": mime or "application/octet-stream",
                "size_bytes": int(body.get("size") or 0),
                "provider_attachment_id": body.get("attachmentId"),
            })
            continue
        data = body.get("data")
        if not data:
            continue
        if mime == "text/plain" and body_text is None:
            body_text = _b64url_decode(data)
        elif mime == "text/html" and body_html is None:
            body_html = _SCRIPT_STYLE_RE.sub("", _b64url_decode(data))

    labels = set(raw.get("labelIds") or [])
    internal_ms = raw.get("internalDate")
    stamp = (
        datetime.fromtimestamp(int(internal_ms) / 1000, tz=timezone.utc)
        if internal_ms
        else None
    )
    is_sent = "SENT" in labels
    subject = headers.get("subject", "")
    return {
        "provider_message_id": raw.get("id"),
        "provider_thread_id": raw.get("threadId"),
        "internet_message_id": headers.get("message-id") or None,
        "in_reply_to": headers.get("in-reply-to") or None,
        "references_header": headers.get("references") or None,
        "from_name": from_name,
        "from_address": from_address,
        "to_recipients": _parse_address_list(headers.get("to")),
        "cc_recipients": _parse_address_list(headers.get("cc")),
        "bcc_recipients": _parse_address_list(headers.get("bcc")),
        "subject": subject,
        "subject_normalized": normalize_subject(subject),
        "body_text": body_text,
        "body_html_sanitized": body_html,
        "snippet": raw.get("snippet") or None,
        "received_at": None if is_sent else stamp,
        "sent_at": stamp if is_sent else None,
        "stamp": stamp,
        "is_read": "UNREAD" not in labels,
        "is_sent": is_sent,
        "is_draft": "DRAFT" in labels,
        "is_starred": "STARRED" in labels,
        "is_trashed": bool(labels & {"TRASH", "SPAM"}),
        "in_inbox": "INBOX" in labels,
        "attachments": attachments,
    }


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------


def _upsert_message(db: DbSession, account: m.MailAccount, raw: dict) -> tuple[m.EmailThread, dict]:
    parsed = parse_gmail_message(raw)
    thread = (
        db.query(m.EmailThread)
        .filter(
            m.EmailThread.mail_account_id == account.id,
            m.EmailThread.provider_thread_id == parsed["provider_thread_id"],
        )
        .first()
    )
    if thread is None:
        thread = m.EmailThread(
            user_id=account.user_id,
            mail_account_id=account.id,
            provider_thread_id=parsed["provider_thread_id"],
            subject_normalized=parsed["subject_normalized"],
            environment=account.environment,
        )
        db.add(thread)
        db.flush()
    msg = (
        db.query(m.EmailMessage)
        .filter(
            m.EmailMessage.mail_account_id == account.id,
            m.EmailMessage.provider_message_id == parsed["provider_message_id"],
        )
        .first()
    )
    if msg is None:
        msg = m.EmailMessage(
            user_id=account.user_id,
            mail_account_id=account.id,
            thread_id=thread.id,
            provider_message_id=parsed["provider_message_id"],
            environment=account.environment,
        )
        db.add(msg)
    msg.thread_id = thread.id
    for field in (
        "internet_message_id", "in_reply_to", "references_header",
        "from_address", "from_name", "to_recipients", "cc_recipients",
        "bcc_recipients", "subject", "body_text", "body_html_sanitized",
        "snippet", "received_at", "sent_at",
        "is_read", "is_starred", "is_draft", "is_sent", "is_trashed",
    ):
        setattr(msg, field, parsed[field])
    db.flush()
    # Attachments: replace the stored set so re-syncs stay idempotent.
    db.query(m.EmailAttachment).filter(m.EmailAttachment.message_id == msg.id).delete()
    for att in parsed["attachments"]:
        db.add(m.EmailAttachment(message_id=msg.id, **att))
    db.flush()
    return thread, parsed


def _message_stamp(msg: m.EmailMessage) -> datetime:
    return m.as_utc(msg.received_at) or m.as_utc(msg.sent_at) or m.as_utc(msg.created_at) or m.now()


def _recompute_thread(
    db: DbSession, thread: m.EmailThread, batch_stamps: dict[str, bool], batch_ids: set[str]
) -> None:
    """Refresh derived thread fields from the stored messages.

    ``batch_stamps`` maps thread id -> whether any message in this sync
    batch carried INBOX; ``batch_ids`` holds the provider ids seen in the
    batch. is_archived flips to True only when the batch covered every
    stored message of the thread and none was in the inbox; a batch that
    shows an inbox message always clears it.
    """
    messages = (
        db.query(m.EmailMessage)
        .filter(m.EmailMessage.thread_id == thread.id)
        .all()
    )
    if not messages:
        return
    messages.sort(key=_message_stamp)
    latest = messages[-1]
    thread.message_count = len(messages)
    thread.last_message_at = _message_stamp(latest)
    thread.snippet = latest.snippet
    if latest.subject:
        thread.subject_normalized = normalize_subject(latest.subject)
    seen: dict[str, dict] = {}
    for msg in messages:
        people = [{"name": msg.from_name or "", "email": msg.from_address}]
        people += list(msg.to_recipients or []) + list(msg.cc_recipients or [])
        for person in people:
            email = (person.get("email") or "").strip()
            if email and email not in seen:
                seen[email] = {"name": person.get("name") or "", "email": email}
    thread.participants = list(seen.values())
    thread.is_trashed = all(msg.is_trashed for msg in messages)
    saw_inbox = batch_stamps.get(thread.id, False)
    covered = all(msg.provider_message_id in batch_ids for msg in messages)
    if saw_inbox:
        thread.is_archived = False
    elif covered:
        thread.is_archived = True


async def sync_account(
    db: DbSession,
    account: m.MailAccount,
    mode: str,
    *,
    transport: httpx.BaseTransport | None = None,
) -> tuple[int, str | None]:
    """Sync a live Google account from Gmail. Returns (messages upserted,
    historyId). Raises GmailAuthError when the grant is dead and GmailError
    for other API failures."""
    token = await get_access_token(db, account, transport=transport)
    headers = {"Authorization": f"Bearer {token}"}
    max_results = 100 if mode == "initial" else 50
    async with httpx.AsyncClient(
        base_url=GMAIL_API_BASE, headers=headers, timeout=30.0, transport=transport
    ) as client:
        profile_resp = await client.get("/users/me/profile")
        if profile_resp.status_code == 401:
            raise GmailAuthError("Gmail rejected the access token during sync.")
        if profile_resp.status_code >= 400:
            raise GmailError(f"Gmail profile request failed with status {profile_resp.status_code}.")
        history_id = profile_resp.json().get("historyId")
        history_id = str(history_id) if history_id is not None else None

        list_resp = await client.get("/users/me/messages", params={"maxResults": max_results})
        if list_resp.status_code == 401:
            raise GmailAuthError("Gmail rejected the access token during sync.")
        if list_resp.status_code >= 400:
            raise GmailError(f"Gmail message list failed with status {list_resp.status_code}.")
        ids = [entry.get("id") for entry in list_resp.json().get("messages") or []]
        ids = [i for i in ids if i]

        upserted = 0
        batch_ids: set[str] = set()
        batch_inbox: dict[str, bool] = {}
        touched: dict[str, m.EmailThread] = {}
        for message_id in ids:
            resp = await client.get(f"/users/me/messages/{message_id}", params={"format": "full"})
            if resp.status_code == 404:
                continue  # deleted between list and fetch
            if resp.status_code == 401:
                raise GmailAuthError("Gmail rejected the access token during sync.")
            if resp.status_code >= 400:
                raise GmailError(f"Gmail message fetch failed with status {resp.status_code}.")
            thread, parsed = _upsert_message(db, account, resp.json())
            upserted += 1
            batch_ids.add(message_id)
            touched[thread.id] = thread
            batch_inbox[thread.id] = batch_inbox.get(thread.id, False) or parsed["in_inbox"]
        for thread in touched.values():
            _recompute_thread(db, thread, batch_inbox, batch_ids)

    account.last_sync_at = m.now()
    account.sync_cursor = history_id
    db.commit()
    return upserted, history_id


# ---------------------------------------------------------------------------
# Sending
# ---------------------------------------------------------------------------


def build_raw_message(db: DbSession, account: m.MailAccount, draft: m.EmailDraft) -> tuple[str, str | None]:
    """Build the base64url RFC 822 payload for a draft. Returns (raw,
    provider_thread_id). Threading headers point at the latest stored
    message of the draft's thread that carries an internet Message-ID."""
    mime = MimeMessage()
    mime["From"] = formataddr((account.display_name or "", account.email_address))
    mime["To"] = ", ".join(
        formataddr((r.get("name") or "", r.get("email") or ""))
        for r in (draft.to_recipients or [])
    )
    if draft.cc_recipients:
        mime["Cc"] = ", ".join(
            formataddr((r.get("name") or "", r.get("email") or ""))
            for r in draft.cc_recipients
        )
    mime["Subject"] = draft.subject or ""
    provider_thread_id: str | None = None
    thread = db.get(m.EmailThread, draft.thread_id) if draft.thread_id else None
    if thread is not None:
        provider_thread_id = thread.provider_thread_id
        anchor = (
            db.query(m.EmailMessage)
            .filter(
                m.EmailMessage.thread_id == thread.id,
                m.EmailMessage.internet_message_id.is_not(None),
            )
            .order_by(m.EmailMessage.created_at.desc())
            .first()
        )
        if anchor is not None and anchor.internet_message_id:
            mime["In-Reply-To"] = anchor.internet_message_id
            references = (anchor.references_header or "").strip()
            mime["References"] = (
                f"{references} {anchor.internet_message_id}".strip()
            )
    mime.set_content(draft.body_text or "")
    raw = base64.urlsafe_b64encode(mime.as_bytes()).decode("ascii")
    return raw, provider_thread_id


async def send_draft(
    db: DbSession,
    account: m.MailAccount,
    draft: m.EmailDraft,
    *,
    transport: httpx.BaseTransport | None = None,
) -> str:
    """Send a draft through Gmail and return the provider message id.
    Raises GmailError/GmailAuthError on failure; callers must not record a
    local send when this raises."""
    token = await get_access_token(db, account, transport=transport)
    raw, provider_thread_id = build_raw_message(db, account, draft)
    payload: dict = {"raw": raw}
    if provider_thread_id:
        payload["threadId"] = provider_thread_id
    async with httpx.AsyncClient(
        base_url=GMAIL_API_BASE,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30.0,
        transport=transport,
    ) as client:
        resp = await client.post("/users/me/messages/send", json=payload)
    if resp.status_code == 401:
        raise GmailAuthError("Gmail rejected the access token while sending.")
    if resp.status_code >= 400:
        raise GmailError(f"Gmail send failed with status {resp.status_code}.")
    provider_id = resp.json().get("id")
    if not provider_id:
        raise GmailError("Gmail send returned no message id.")
    return str(provider_id)


def send_draft_sync(db: DbSession, account: m.MailAccount, draft: m.EmailDraft) -> str:
    """Synchronous bridge for send_draft, used by the sync perform_send
    path (threadpool route handlers, where no event loop is running)."""
    coro = send_draft(db, account, draft)
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    # A loop is already running in this thread: run the coroutine on a
    # helper thread with its own loop. The calling thread blocks on join,
    # so the shared session is never used concurrently.
    outcome: dict = {}

    def _target() -> None:
        try:
            outcome["value"] = asyncio.run(coro)
        except BaseException as exc:  # noqa: BLE001 - re-raised below
            outcome["error"] = exc

    worker = threading.Thread(target=_target)
    worker.start()
    worker.join()
    if "error" in outcome:
        raise outcome["error"]
    return outcome["value"]
