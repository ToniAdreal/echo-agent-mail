"""Gmail connectivity: secret encryption, message parsing, idempotent
sync, token refresh, runner handling of live Google jobs, and real sends.

All Gmail HTTP is mocked with httpx.MockTransport; nothing leaves the
process."""
from __future__ import annotations

import asyncio
import base64
import json
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# NOTE: app.* is deliberately NOT imported at module top level. The shared
# conftest freezes app.config's DATABASE_URL at first import, and its
# client fixture relies on being the first importer (after setting a tmp
# DATABASE_URL). Importing the app here at collection time would poison
# that for every other test module. Instead the module-scoped fixture
# below imports the app (through the client fixture) and injects the
# names the tests use into this module's globals.


@pytest.fixture(scope="module", autouse=True)
def _app_imported(client):
    from app import models
    from app.security import decrypt_secret, encrypt_secret
    from app.services import gmail, runner, tasks_svc

    globals().update({
        "m": models,
        "gmail": gmail,
        "runner": runner,
        "tasks_svc": tasks_svc,
        "encrypt_secret": encrypt_secret,
        "decrypt_secret": decrypt_secret,
    })
    return client


@pytest.fixture()
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    m.User.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()
    yield session
    session.close()


def _b64(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode()).decode().rstrip("=")


def _user(db) -> m.User:
    user = m.User(name="Toni Adreal", email="toni@example.com", password_hash="x")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _live_account(db, user, *, expires_at=None) -> m.MailAccount:
    account = m.MailAccount(
        user_id=user.id,
        provider="google",
        email_address="toni@example.com",
        display_name="Toni Adreal",
        environment="live",
        status="connected",
        access_token_ciphertext=encrypt_secret("stored-access-token"),
        refresh_token_ciphertext=encrypt_secret("stored-refresh-token"),
        token_expires_at=expires_at or (m.now() + timedelta(hours=1)),
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


# ---------------------------------------------------------------------------
# Canned Gmail payloads
# ---------------------------------------------------------------------------

MESSAGE_1 = {
    "id": "m1",
    "threadId": "t1",
    "labelIds": ["INBOX", "UNREAD", "STARRED"],
    "snippet": "Hi Toni, attached is quotation Q-1042",
    "historyId": "12345",
    "internalDate": "1730000000000",
    "payload": {
        "mimeType": "multipart/mixed",
        "headers": [
            {"name": "From", "value": "Maya Chen <maya@acmestudio.example>"},
            {"name": "To", "value": "Toni Adreal <toni@example.com>, alex@cedarventures.example"},
            {"name": "Cc", "value": "June Park <june@atlasresearch.example>"},
            {"name": "Subject", "value": "Re: Quotation Q-1042 for the spring campaign"},
            {"name": "Date", "value": "Sun, 27 Oct 2024 05:33:20 +0000"},
            {"name": "Message-ID", "value": "<msg-1@acmestudio.example>"},
            {"name": "In-Reply-To", "value": "<msg-0@example.com>"},
            {"name": "References", "value": "<msg-0@example.com>"},
        ],
        "body": {"size": 0},
        "parts": [
            {"mimeType": "text/plain", "body": {"size": 24, "data": _b64("Hi Toni,\n\nAttached is quotation Q-1042.")}},
            {"mimeType": "text/html", "body": {"size": 60, "data": _b64(
                "<p>Hi Toni,</p><script>alert(1)</script><style>.x{color:red}</style>")}},
            {"mimeType": "application/pdf", "filename": "Quotation-Q-1042.pdf",
             "body": {"size": 184320, "attachmentId": "att-1"}},
        ],
    },
}

MESSAGE_2 = {
    "id": "m2",
    "threadId": "t1",
    "labelIds": ["SENT"],
    "snippet": "Thanks Maya, reviewing this week",
    "historyId": "12346",
    "internalDate": "1730003600000",
    "payload": {
        "mimeType": "text/plain",
        "headers": [
            {"name": "From", "value": "Toni Adreal <toni@example.com>"},
            {"name": "To", "value": "Maya Chen <maya@acmestudio.example>"},
            {"name": "Subject", "value": "Re: Re: Quotation Q-1042 for the spring campaign"},
            {"name": "Message-ID", "value": "<msg-2@example.com>"},
            {"name": "In-Reply-To", "value": "<msg-1@acmestudio.example>"},
            {"name": "References", "value": "<msg-0@example.com> <msg-1@acmestudio.example>"},
        ],
        "body": {"size": 30, "data": _b64("Thanks Maya, reviewing this week.")},
    },
}


def _gmail_transport(captured: dict | None = None) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if captured is not None:
            captured.setdefault("paths", []).append(path)
        if path == "/gmail/v1/users/me/profile":
            return httpx.Response(200, json={
                "emailAddress": "toni@example.com", "messagesTotal": 2, "historyId": "12345",
            })
        if path == "/gmail/v1/users/me/messages":
            return httpx.Response(200, json={
                "messages": [{"id": "m1", "threadId": "t1"}, {"id": "m2", "threadId": "t1"}],
                "resultSizeEstimate": 2,
            })
        if path == "/gmail/v1/users/me/messages/m1":
            return httpx.Response(200, json=MESSAGE_1)
        if path == "/gmail/v1/users/me/messages/m2":
            return httpx.Response(200, json=MESSAGE_2)
        return httpx.Response(404, json={"error": {"message": "not found"}})

    return httpx.MockTransport(handler)


# ---------------------------------------------------------------------------
# Encryption
# ---------------------------------------------------------------------------


def test_encrypt_decrypt_round_trip():
    token = "ya29.a-very-secret-access-token"
    encrypted = encrypt_secret(token)
    assert encrypted != token
    assert decrypt_secret(encrypted) == token


def test_decrypt_secret_passes_through_legacy_plaintext():
    assert decrypt_secret("legacy-plain-token") == "legacy-plain-token"
    assert decrypt_secret("") == ""


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def test_parse_gmail_message_headers_body_labels():
    parsed = gmail.parse_gmail_message(MESSAGE_1)
    assert parsed["provider_message_id"] == "m1"
    assert parsed["provider_thread_id"] == "t1"
    assert parsed["from_name"] == "Maya Chen"
    assert parsed["from_address"] == "maya@acmestudio.example"
    assert parsed["to_recipients"] == [
        {"name": "Toni Adreal", "email": "toni@example.com"},
        {"name": "", "email": "alex@cedarventures.example"},
    ]
    assert parsed["cc_recipients"] == [{"name": "June Park", "email": "june@atlasresearch.example"}]
    assert parsed["subject_normalized"] == "Quotation Q-1042 for the spring campaign"
    assert parsed["internet_message_id"] == "<msg-1@acmestudio.example>"
    assert parsed["in_reply_to"] == "<msg-0@example.com>"
    assert parsed["references_header"] == "<msg-0@example.com>"
    assert parsed["body_text"] == "Hi Toni,\n\nAttached is quotation Q-1042."
    assert "<p>Hi Toni,</p>" in parsed["body_html_sanitized"]
    assert "alert" not in parsed["body_html_sanitized"]
    assert "color:red" not in parsed["body_html_sanitized"]
    assert parsed["is_read"] is False
    assert parsed["is_starred"] is True
    assert parsed["is_sent"] is False
    assert parsed["is_draft"] is False
    assert parsed["is_trashed"] is False
    assert parsed["in_inbox"] is True
    assert parsed["received_at"] == datetime.fromtimestamp(1730000000, tz=timezone.utc)
    assert parsed["sent_at"] is None
    assert parsed["attachments"] == [{
        "filename": "Quotation-Q-1042.pdf",
        "mime_type": "application/pdf",
        "size_bytes": 184320,
        "provider_attachment_id": "att-1",
    }]


def test_parse_gmail_message_sent_and_prefix_stripping():
    parsed = gmail.parse_gmail_message(MESSAGE_2)
    assert parsed["is_sent"] is True
    assert parsed["is_read"] is True
    assert parsed["sent_at"] == datetime.fromtimestamp(1730003600, tz=timezone.utc)
    assert parsed["received_at"] is None
    assert parsed["subject_normalized"] == "Quotation Q-1042 for the spring campaign"
    assert gmail.normalize_subject("Fwd: Fw: Re: Hello") == "Hello"


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------


def test_sync_upserts_and_is_idempotent(db):
    user = _user(db)
    account = _live_account(db, user)
    transport = _gmail_transport()

    fetched, history_id = asyncio.run(
        gmail.sync_account(db, account, "initial", transport=transport)
    )
    assert (fetched, history_id) == (2, "12345")
    assert db.query(m.EmailThread).count() == 1
    assert db.query(m.EmailMessage).count() == 2
    assert db.query(m.EmailAttachment).count() == 1
    thread = db.query(m.EmailThread).one()
    assert thread.provider_thread_id == "t1"
    assert thread.subject_normalized == "Quotation Q-1042 for the spring campaign"
    assert thread.message_count == 2
    assert thread.is_archived is False
    assert thread.snippet == "Thanks Maya, reviewing this week"
    assert {p["email"] for p in thread.participants} == {
        "maya@acmestudio.example", "toni@example.com",
        "alex@cedarventures.example", "june@atlasresearch.example",
    }
    db.refresh(account)
    assert account.sync_cursor == "12345"
    assert account.last_sync_at is not None

    # Second sync over the same data changes nothing structurally.
    fetched2, _ = asyncio.run(
        gmail.sync_account(db, account, "incremental", transport=transport)
    )
    assert fetched2 == 2
    assert db.query(m.EmailThread).count() == 1
    assert db.query(m.EmailMessage).count() == 2
    assert db.query(m.EmailAttachment).count() == 1
    assert db.query(m.EmailThread).one().message_count == 2


# ---------------------------------------------------------------------------
# Token lifecycle
# ---------------------------------------------------------------------------


def test_get_access_token_returns_stored_when_fresh(db):
    user = _user(db)
    account = _live_account(db, user)

    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("no HTTP call expected for a fresh token")

    token = asyncio.run(
        gmail.get_access_token(db, account, transport=httpx.MockTransport(handler))
    )
    assert token == "stored-access-token"


def test_get_access_token_refreshes_when_expired(db):
    user = _user(db)
    account = _live_account(db, user, expires_at=m.now() - timedelta(minutes=5))
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        return httpx.Response(200, json={"access_token": "fresh-access", "expires_in": 3600})

    token = asyncio.run(
        gmail.get_access_token(db, account, transport=httpx.MockTransport(handler))
    )
    assert token == "fresh-access"
    assert seen["url"].startswith("https://oauth2.googleapis.com/token")
    db.refresh(account)
    assert decrypt_secret(account.access_token_ciphertext) == "fresh-access"
    assert m.as_utc(account.token_expires_at) > m.now() + timedelta(minutes=50)


def test_get_access_token_invalid_grant_raises_auth_error(db):
    user = _user(db)
    account = _live_account(db, user, expires_at=m.now() - timedelta(minutes=5))

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": "invalid_grant"})

    with pytest.raises(gmail.GmailAuthError):
        asyncio.run(
            gmail.get_access_token(db, account, transport=httpx.MockTransport(handler))
        )


# ---------------------------------------------------------------------------
# Runner handling of live Google sync jobs
# ---------------------------------------------------------------------------


def _running_job(db, user, account) -> m.SyncJob:
    db.add(m.OnboardingState(user_id=user.id, state="SYNCING", completed_steps=[]))
    job = m.SyncJob(
        user_id=user.id, mail_account_id=account.id, mode="initial",
        environment="live", status="running", phase="connecting",
        started_at=m.now(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def test_runner_completes_live_google_job(db, monkeypatch):
    user = _user(db)
    account = _live_account(db, user)
    account.status = "syncing"
    db.commit()
    job = _running_job(db, user, account)

    async def fake_sync(db_, account_, mode):
        assert mode == "initial"
        return 7, "hist-99"

    monkeypatch.setattr(gmail, "sync_account", fake_sync)
    asyncio.run(runner._advance_syncs(db))
    db.refresh(job)
    db.refresh(account)
    assert job.status == "completed"
    assert job.processed_count == 7
    assert job.total_count == 7
    assert job.cursor_after == "hist-99"
    assert account.status == "connected"
    ob = db.query(m.OnboardingState).filter_by(user_id=user.id).one()
    assert ob.state == "READY"


def test_runner_fails_live_google_job_on_auth_error(db, monkeypatch):
    user = _user(db)
    account = _live_account(db, user)
    job = _running_job(db, user, account)

    async def failing_sync(db_, account_, mode):
        raise gmail.GmailAuthError("revoked")

    monkeypatch.setattr(gmail, "sync_account", failing_sync)
    asyncio.run(runner._advance_syncs(db))
    db.refresh(job)
    db.refresh(account)
    assert job.status == "failed"
    assert job.error_code == "TOKEN_REFRESH_FAILED"
    assert account.status == "action_required"


def test_runner_fails_live_google_job_on_generic_error(db, monkeypatch):
    user = _user(db)
    account = _live_account(db, user)
    job = _running_job(db, user, account)

    async def broken_sync(db_, account_, mode):
        raise RuntimeError("boom")

    monkeypatch.setattr(gmail, "sync_account", broken_sync)
    asyncio.run(runner._advance_syncs(db))
    db.refresh(job)
    db.refresh(account)
    assert job.status == "failed"
    assert job.error_code == "GMAIL_SYNC_FAILED"
    assert account.status == "connected"


# ---------------------------------------------------------------------------
# Real send on approval
# ---------------------------------------------------------------------------


def _draft_in_thread(db, user, account) -> tuple[m.EmailThread, m.EmailDraft]:
    thread = m.EmailThread(
        user_id=user.id, mail_account_id=account.id, provider_thread_id="t1",
        subject_normalized="Quotation Q-1042 for the spring campaign",
        environment="live",
    )
    db.add(thread)
    db.flush()
    db.add(m.EmailMessage(
        user_id=user.id, mail_account_id=account.id, thread_id=thread.id,
        provider_message_id="m1", internet_message_id="<msg-1@acmestudio.example>",
        references_header="<msg-0@example.com>",
        from_address="maya@acmestudio.example", from_name="Maya Chen",
        to_recipients=[{"name": "Toni Adreal", "email": "toni@example.com"}],
        subject="Re: Quotation Q-1042 for the spring campaign",
        environment="live",
    ))
    draft = m.EmailDraft(
        user_id=user.id, mail_account_id=account.id, thread_id=thread.id,
        to_recipients=[{"name": "Maya Chen", "email": "maya@acmestudio.example"}],
        subject="Re: Quotation Q-1042 for the spring campaign",
        body_text="Thanks Maya, confirming this week.",
        status="in_review", environment="live",
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return thread, draft


def test_perform_send_live_google_goes_through_gmail(db, monkeypatch):
    user = _user(db)
    account = _live_account(db, user)
    _thread, draft = _draft_in_thread(db, user, account)
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["payload"] = json.loads(request.content)
        return httpx.Response(200, json={"id": "gmail-sent-1", "threadId": "t1"})

    transport = httpx.MockTransport(handler)
    real_send = gmail.send_draft

    async def send_with_transport(db_, account_, draft_):
        return await real_send(db_, account_, draft_, transport=transport)

    monkeypatch.setattr(gmail, "send_draft", send_with_transport)
    result = tasks_svc.perform_send(db, user, draft)
    assert result["simulated"] is False
    assert result["provider_message_id"] == "gmail-sent-1"
    assert captured["path"] == "/gmail/v1/users/me/messages/send"
    assert captured["payload"]["threadId"] == "t1"
    raw = base64.urlsafe_b64decode(captured["payload"]["raw"]).decode()
    assert "In-Reply-To: <msg-1@acmestudio.example>" in raw
    assert "<msg-0@example.com> <msg-1@acmestudio.example>" in raw
    assert "Subject: Re: Quotation Q-1042 for the spring campaign" in raw
    db.refresh(draft)
    assert draft.status == "sent"
    sent = db.query(m.EmailMessage).filter_by(provider_message_id="gmail-sent-1").one()
    assert sent.is_sent is True


def test_perform_send_live_google_failure_raises_and_records_nothing(db, monkeypatch):
    user = _user(db)
    account = _live_account(db, user)
    _thread, draft = _draft_in_thread(db, user, account)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": {"message": "backend error"}})

    transport = httpx.MockTransport(handler)
    real_send = gmail.send_draft

    async def send_with_transport(db_, account_, draft_):
        return await real_send(db_, account_, draft_, transport=transport)

    monkeypatch.setattr(gmail, "send_draft", send_with_transport)
    with pytest.raises(gmail.GmailError):
        tasks_svc.perform_send(db, user, draft)
    db.refresh(draft)
    assert draft.status == "in_review"
    assert db.query(m.EmailMessage).filter_by(is_sent=True).count() == 0
