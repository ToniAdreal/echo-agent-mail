"""Real Microsoft (Outlook) connectivity for live Microsoft mail accounts.

Mirrors app/services/gmail.py: everything the provider-generic OAuth
callback leaves behind is implemented here:

- access-token lifecycle (decrypt, refresh when expiring, re-encrypt),
- mailbox sync into EmailThread / EmailMessage / EmailAttachment rows,
  idempotent on (mail_account_id, provider_thread_id) and
  (mail_account_id, provider_message_id),
- real sends through Microsoft Graph for approved drafts.

Demo accounts never touch this module; the runner and perform_send branch
on environment="live" + provider="microsoft" only.

The HTTP layer is httpx (async). Functions accept an optional
``transport`` so tests can inject httpx.MockTransport without network.
"""
from __future__ import annotations

import asyncio
import threading
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.orm import Session as DbSession

from .. import models as m
from ..config import settings
from ..security import decrypt_secret, encrypt_secret
from .gmail import _SCRIPT_STYLE_RE, _recompute_thread, normalize_subject

GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"
TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
REFRESH_SCOPE = "openid email profile Mail.ReadWrite Mail.Send offline_access"

_REFRESH_SKEW = timedelta(seconds=60)

_MESSAGE_SELECT = (
    "id,conversationId,subject,from,toRecipients,ccRecipients,"
    "receivedDateTime,sentDateTime,bodyPreview,isRead,isDraft,"
    "hasAttachments,body,internetMessageId,parentFolderId"
)

_WELL_KNOWN_FOLDERS = {"inbox", "drafts", "sentitems", "deleteditems", "junkemail"}


class GraphError(Exception):
    """A Microsoft Graph call failed in a way that is not an auth problem."""


class GraphAuthError(GraphError):
    """The stored credentials can no longer produce a valid access token
    (revoked grant, expired refresh token, ...). The account needs the user
    to reconnect it."""


# ---------------------------------------------------------------------------
# Access tokens
# ---------------------------------------------------------------------------


async def get_access_token(
    db: DbSession, account: m.MailAccount, *, transport: httpx.BaseTransport | None = None
) -> str:
    """Return a valid Microsoft access token for the account, refreshing
    (and persisting, encrypted) when the stored one is missing or
    expiring. Microsoft rotates refresh tokens, so a replacement refresh
    token in the response is persisted too."""
    expires_at = m.as_utc(account.token_expires_at)
    if (
        account.access_token_ciphertext
        and expires_at is not None
        and expires_at > m.now() + _REFRESH_SKEW
    ):
        return decrypt_secret(account.access_token_ciphertext)
    if not account.refresh_token_ciphertext:
        raise GraphAuthError("No refresh token is stored for this account; reconnect it.")
    refresh_token = decrypt_secret(account.refresh_token_ciphertext)
    async with httpx.AsyncClient(timeout=20.0, transport=transport) as client:
        resp = await client.post(
            TOKEN_URL,
            data={
                "client_id": settings.MICROSOFT_CLIENT_ID,
                "client_secret": settings.MICROSOFT_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
                "scope": REFRESH_SCOPE,
            },
        )
    if resp.status_code >= 400:
        error = ""
        try:
            error = str(resp.json().get("error") or "")
        except Exception:
            pass
        if error == "invalid_grant" or resp.status_code in {400, 401}:
            raise GraphAuthError(
                f"Microsoft token refresh was rejected ({error or resp.status_code}); reconnect the account."
            )
        raise GraphError(f"Microsoft token refresh failed with status {resp.status_code}.")
    data = resp.json()
    access_token = data.get("access_token")
    if not access_token:
        raise GraphError("Microsoft token refresh returned no access token.")
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
# Message parsing (pure functions over the Microsoft Graph JSON shape)
# ---------------------------------------------------------------------------


def _parse_graph_datetime(value) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        stamp = datetime.fromisoformat(text)
    except ValueError:
        return None
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return stamp


def _graph_address(entry) -> dict | None:
    email_address = (entry or {}).get("emailAddress") or {}
    addr = (email_address.get("address") or "").strip()
    if not addr:
        return None
    return {"name": (email_address.get("name") or "").strip(), "email": addr}


def _graph_address_list(entries) -> list[dict]:
    out: list[dict] = []
    for entry in entries or []:
        parsed = _graph_address(entry)
        if parsed is not None:
            out.append(parsed)
    return out


def parse_graph_message(raw: dict, folder_kind: str | None = None) -> dict:
    """Convert one Microsoft Graph message resource into the field set
    used by EmailMessage plus thread/attachment side data. ``folder_kind``
    is the well-known name of the folder the message sits in (inbox,
    drafts, sentitems, deleteditems, junkemail) or None when unknown;
    folder membership drives the sent/draft/trashed flags, mirroring how
    the Gmail parser uses labelIds."""
    sender = _graph_address(raw.get("from")) or {"name": "", "email": ""}

    body = raw.get("body") or {}
    content = body.get("content") or ""
    content_type = (body.get("contentType") or "").lower()
    body_text = content if content_type == "text" else None
    body_html = (
        _SCRIPT_STYLE_RE.sub("", content) if content_type == "html" else None
    )

    is_sent = folder_kind == "sentitems"
    received_dt = _parse_graph_datetime(raw.get("receivedDateTime"))
    sent_dt = _parse_graph_datetime(raw.get("sentDateTime"))
    stamp = (sent_dt or received_dt) if is_sent else (received_dt or sent_dt)
    subject = raw.get("subject") or ""
    return {
        "provider_message_id": raw.get("id"),
        "provider_thread_id": raw.get("conversationId"),
        "internet_message_id": raw.get("internetMessageId") or None,
        "in_reply_to": None,
        "references_header": None,
        "from_name": sender["name"] or None,
        "from_address": sender["email"],
        "to_recipients": _graph_address_list(raw.get("toRecipients")),
        "cc_recipients": _graph_address_list(raw.get("ccRecipients")),
        "bcc_recipients": _graph_address_list(raw.get("bccRecipients")),
        "subject": subject,
        "subject_normalized": normalize_subject(subject),
        "body_text": body_text,
        "body_html_sanitized": body_html,
        "snippet": raw.get("bodyPreview") or None,
        "received_at": None if is_sent else stamp,
        "sent_at": stamp if is_sent else None,
        "stamp": stamp,
        "is_read": bool(raw.get("isRead")),
        "is_sent": is_sent,
        "is_draft": bool(raw.get("isDraft")) or folder_kind == "drafts",
        "is_starred": False,
        "is_trashed": folder_kind in {"deleteditems", "junkemail"},
        "in_inbox": folder_kind == "inbox",
        "has_attachments": bool(raw.get("hasAttachments")),
        "attachments": [],
    }


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------


def _upsert_message(db: DbSession, account: m.MailAccount, parsed: dict) -> m.EmailThread:
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
    return thread


def _check(resp: httpx.Response, what: str) -> None:
    if resp.status_code == 401:
        raise GraphAuthError(f"Microsoft Graph rejected the access token during {what}.")
    if resp.status_code >= 400:
        raise GraphError(f"Microsoft Graph {what} failed with status {resp.status_code}.")


async def _fetch_attachments(
    client: httpx.AsyncClient, message_id: str
) -> list[dict]:
    resp = await client.get(
        f"/me/messages/{message_id}/attachments",
        params={"$select": "id,name,contentType,size"},
    )
    if resp.status_code == 404:
        return []  # message deleted between list and attachment fetch
    _check(resp, "attachment fetch")
    out: list[dict] = []
    for entry in resp.json().get("value") or []:
        out.append({
            "filename": entry.get("name") or "attachment",
            "mime_type": entry.get("contentType") or "application/octet-stream",
            "size_bytes": int(entry.get("size") or 0),
            "provider_attachment_id": entry.get("id"),
        })
    return out


async def sync_account(
    db: DbSession,
    account: m.MailAccount,
    mode: str,
    *,
    transport: httpx.BaseTransport | None = None,
) -> tuple[int, str | None]:
    """Sync a live Microsoft account from Microsoft Graph. Returns
    (messages upserted, None): Graph delta sync is out of scope, so no
    cursor is produced and account.sync_cursor is left untouched. Raises
    GraphAuthError when the grant is dead and GraphError for other API
    failures."""
    token = await get_access_token(db, account, transport=transport)
    headers = {"Authorization": f"Bearer {token}"}
    top = 100 if mode == "initial" else 50
    async with httpx.AsyncClient(
        base_url=GRAPH_API_BASE, headers=headers, timeout=30.0, transport=transport
    ) as client:
        folders_resp = await client.get(
            "/me/mailFolders",
            params={"$top": 100, "$select": "id,wellKnownName,displayName"},
        )
        _check(folders_resp, "mail folder list")
        folder_kinds: dict[str, str] = {}
        for folder in folders_resp.json().get("value") or []:
            kind = folder.get("wellKnownName")
            if kind in _WELL_KNOWN_FOLDERS and folder.get("id"):
                folder_kinds[folder["id"]] = kind

        list_resp = await client.get(
            "/me/messages",
            params={
                "$top": top,
                "$orderby": "receivedDateTime desc",
                "$select": _MESSAGE_SELECT,
            },
        )
        _check(list_resp, "message list")

        upserted = 0
        batch_ids: set[str] = set()
        batch_inbox: dict[str, bool] = {}
        touched: dict[str, m.EmailThread] = {}
        for raw in list_resp.json().get("value") or []:
            parsed = parse_graph_message(raw, folder_kinds.get(raw.get("parentFolderId")))
            if parsed["has_attachments"] and parsed["provider_message_id"]:
                parsed["attachments"] = await _fetch_attachments(
                    client, parsed["provider_message_id"]
                )
            thread = _upsert_message(db, account, parsed)
            upserted += 1
            batch_ids.add(parsed["provider_message_id"])
            touched[thread.id] = thread
            batch_inbox[thread.id] = batch_inbox.get(thread.id, False) or parsed["in_inbox"]
        for thread in touched.values():
            _recompute_thread(db, thread, batch_inbox, batch_ids)

    account.last_sync_at = m.now()
    db.commit()
    return upserted, None


# ---------------------------------------------------------------------------
# Sending
# ---------------------------------------------------------------------------


def _graph_recipient(person: dict) -> dict:
    return {
        "emailAddress": {
            "address": person.get("email") or "",
            "name": person.get("name") or "",
        }
    }


async def send_draft(
    db: DbSession,
    account: m.MailAccount,
    draft: m.EmailDraft,
    thread: m.EmailThread | None = None,
    *,
    transport: httpx.BaseTransport | None = None,
) -> str:
    """Send a draft through Microsoft Graph and return the provider
    message id. Graph cannot create a message directly inside an existing
    conversation, so the draft is created as a new message (subject/body/
    recipients from the draft) and then sent; ``thread`` is accepted for
    signature parity with gmail.send_draft and is otherwise unused.
    Raises GraphError/GraphAuthError on failure; callers must not record a
    local send when this raises."""
    token = await get_access_token(db, account, transport=transport)
    payload: dict = {
        "subject": draft.subject or "",
        "body": {"contentType": "Text", "content": draft.body_text or ""},
        "toRecipients": [_graph_recipient(r) for r in (draft.to_recipients or [])],
    }
    if draft.cc_recipients:
        payload["ccRecipients"] = [_graph_recipient(r) for r in draft.cc_recipients]
    if draft.bcc_recipients:
        payload["bccRecipients"] = [_graph_recipient(r) for r in draft.bcc_recipients]
    async with httpx.AsyncClient(
        base_url=GRAPH_API_BASE,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30.0,
        transport=transport,
    ) as client:
        create_resp = await client.post("/me/messages", json=payload)
        if create_resp.status_code == 401:
            raise GraphAuthError("Microsoft Graph rejected the access token while sending.")
        if create_resp.status_code >= 400:
            raise GraphError(
                f"Microsoft Graph draft creation failed with status {create_resp.status_code}."
            )
        new_id = create_resp.json().get("id")
        if not new_id:
            raise GraphError("Microsoft Graph draft creation returned no message id.")
        send_resp = await client.post(f"/me/messages/{new_id}/send")
        if send_resp.status_code == 401:
            raise GraphAuthError("Microsoft Graph rejected the access token while sending.")
        if send_resp.status_code >= 400:
            raise GraphError(
                f"Microsoft Graph send failed with status {send_resp.status_code}."
            )
    return str(new_id)


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
