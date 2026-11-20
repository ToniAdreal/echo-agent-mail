"""Microsoft Graph connectivity: message parsing, idempotent sync,
token refresh, runner handling of live Microsoft jobs, and real sends.

All Graph HTTP is mocked with httpx.MockTransport; nothing leaves the
process."""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs

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
    from app.services import graphmail, runner, tasks_svc

    globals().update({
        "m": models,
        "graphmail": graphmail,
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


def _user(db) -> m.User:
    user = m.User(name="Toni Adreal", email="toni@example.com", password_hash="x")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _live_account(db, user, *, expires_at=None) -> m.MailAccount:
    account = m.MailAccount(
        user_id=user.id,
        provider="microsoft",
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
# Canned Microsoft Graph payloads
# ---------------------------------------------------------------------------

FOLDERS = {
    "value": [
        {"id": "folder-inbox", "displayName": "Inbox", "wellKnownName": "inbox"},
        {"id": "folder-drafts", "displayName": "Drafts", "wellKnownName": "drafts"},
        {"id": "folder-sent", "displayName": "Sent Items", "wellKnownName": "sentitems"},
        {"id": "folder-deleted", "displayName": "Deleted Items", "wellKnownName": "deleteditems"},
        {"id": "folder-junk", "displayName": "Junk Email", "wellKnownName": "junkemail"},
    ]
}

MESSAGE_1 = {
    "id": "gm1",
    "conversationId": "conv-1",
    "subject": "Re: Quotation Q-1042 for the spring campaign",
    "bodyPreview": "Hi Toni, attached is quotation Q-1042",
    "isRead": False,
    "isDraft": False,
    "hasAttachments": True,
    "internetMessageId": "<msg-1@acmestudio.example>",
    "parentFolderId": "folder-inbox",
    "receivedDateTime": "2024-10-27T05:33:20Z",
    "sentDateTime": "2024-10-27T05:33:20Z",
    "from": {"emailAddress": {"name": "Maya Chen", "address": "maya@acmestudio.example"}},
    "toRecipients": [
        {"emailAddress": {"name": "Toni Adreal", "address": "toni@example.com"}},
        {"emailAddress": {"name": "", "address": "alex@cedarventures.example"}},
    ],
    "ccRecipients": [
        {"emailAddress": {"name": "June Park", "address": "june@atlasresearch.example"}},
    ],
    "body": {
        "contentType": "html",
        "content": "<p>Hi Toni,</p><script>alert(1)</script><style>.x{color:red}</style>",
    },
}

MESSAGE_2 = {
    "id": "gm2",
    "conversationId": "conv-1",
    "subject": "Re: Re: Quotation Q-1042 for the spring campaign",
    "bodyPreview": "Thanks Maya, reviewing this week",
    "isRead": True,
    "isDraft": False,
    "hasAttachments": False,
    "internetMessageId": "<msg-2@example.com>",
    "parentFolderId": "folder-sent",
    "receivedDateTime": "2024-10-27T06:33:20Z",
    "sentDateTime": "2024-10-27T06:33:20Z",
    "from": {"emailAddress": {"name": "Toni Adreal", "address": "toni@example.com"}},
    "toRecipients": [
        {"emailAddress": {"name": "Maya Chen", "address": "maya@acmestudio.example"}},
    ],
    "ccRecipients": [],
    "body": {"contentType": "text", "content": "Thanks Maya, reviewing this week."},
}

ATTACHMENTS_1 = {
    "value": [{
        "id": "att-1",
        "name": "Quotation-Q-1042.pdf",
        "contentType": "application/pdf",
        "size": 184320,
    }]
}


def _graph_transport(captured: dict | None = None) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if captured is not None:
            captured.setdefault("paths", []).append(path)
        if path == "/v1.0/me/mailFolders":
            return httpx.Response(200, json=FOLDERS)
        if path == "/v1.0/me/messages":
            return httpx.Response(200, json={"value": [MESSAGE_1, MESSAGE_2]})
        if path == "/v1.0/me/messages/gm1/attachments":
            return httpx.Response(200, json=ATTACHMENTS_1)
        return httpx.Response(404, json={"error": {"message": "not found"}})

    return httpx.MockTransport(handler)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def test_parse_graph_message_headers_body_flags():
    parsed = graphmail.parse_graph_message(MESSAGE_1, "inbox")
    assert parsed["provider_message_id"] == "gm1"
    assert parsed["provider_thread_id"] == "conv-1"
    assert parsed["from_name"] == "Maya Chen"
    assert parsed["from_address"] == "maya@acmestudio.example"
    assert parsed["to_recipients"] == [
        {"name": "Toni Adreal", "email": "toni@example.com"},
        {"name": "", "email": "alex@cedarventures.example"},
    ]
    assert parsed["cc_recipients"] == [{"name": "June Park", "email": "june@atlasresearch.example"}]
    assert parsed["subject_normalized"] == "Quotation Q-1042 for the spring campaign"
    assert parsed["internet_message_id"] == "<msg-1@acmestudio.example>"
    assert parsed["body_text"] is None
    assert "<p>Hi Toni,</p>" in parsed["body_html_sanitized"]
    assert "alert" not in parsed["body_html_sanitized"]
    assert "color:red" not in parsed["body_html_sanitized"]
    assert parsed["snippet"] == "Hi Toni, attached is quotation Q-1042"
    assert parsed["is_read"] is False
    assert parsed["is_sent"] is False
    assert parsed["is_draft"] is False
    assert parsed["is_trashed"] is False
    assert parsed["in_inbox"] is True
    assert parsed["has_attachments"] is True
    assert parsed["received_at"] == datetime(2024, 10, 27, 5, 33, 20, tzinfo=timezone.utc)
    assert parsed["sent_at"] is None


def test_parse_graph_message_sent_text_and_folder_flags():
    parsed = graphmail.parse_graph_message(MESSAGE_2, "sentitems")
    assert parsed["is_sent"] is True
    assert parsed["is_read"] is True
    assert parsed["sent_at"] == datetime(2024, 10, 27, 6, 33, 20, tzinfo=timezone.utc)
    assert parsed["received_at"] is None
    assert parsed["body_text"] == "Thanks Maya, reviewing this week."
    assert parsed["body_html_sanitized"] is None
    assert parsed["subject_normalized"] == "Quotation Q-1042 for the spring campaign"

    # Folder membership alone drives the draft / trashed flags.
    as_draft = graphmail.parse_graph_message(MESSAGE_1, "drafts")
    assert as_draft["is_draft"] is True
    assert as_draft["in_inbox"] is False
    as_trashed = graphmail.parse_graph_message(MESSAGE_1, "deleteditems")
    assert as_trashed["is_trashed"] is True
    as_junk = graphmail.parse_graph_message(MESSAGE_1, "junkemail")
    assert as_junk["is_trashed"] is True
    unknown = graphmail.parse_graph_message(MESSAGE_1, None)
    assert unknown["is_sent"] is False
    assert unknown["is_draft"] is False
    assert unknown["is_trashed"] is False
    assert unknown["in_inbox"] is False


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------


def test_sync_upserts_and_is_idempotent(db):
    user = _user(db)
    account = _live_account(db, user)
    transport = _graph_transport()

    fetched, cursor = asyncio.run(
        graphmail.sync_account(db, account, "initial", transport=transport)
    )
    assert (fetched, cursor) == (2, None)
    assert db.query(m.EmailThread).count() == 1
    assert db.query(m.EmailMessage).count() == 2
    assert db.query(m.EmailAttachment).count() == 1
    thread = db.query(m.EmailThread).one()
    assert thread.provider_thread_id == "conv-1"
    assert thread.subject_normalized == "Quotation Q-1042 for the spring campaign"
    assert thread.message_count == 2
    assert thread.is_archived is False
    assert thread.snippet == "Thanks Maya, reviewing this week"
    assert {p["email"] for p in thread.participants} == {
        "maya@acmestudio.example", "toni@example.com",
        "alex@cedarventures.example", "june@atlasresearch.example",
    }
    attachment = db.query(m.EmailAttachment).one()
    assert attachment.filename == "Quotation-Q-1042.pdf"
    assert attachment.mime_type == "application/pdf"
    assert attachment.size_bytes == 184320
    assert attachment.provider_attachment_id == "att-1"
    db.refresh(account)
    assert account.last_sync_at is not None
    assert account.sync_cursor is None

    # Second sync over the same data changes nothing structurally.
    fetched2, _ = asyncio.run(
        graphmail.sync_account(db, account, "incremental", transport=transport)
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
        graphmail.get_access_token(db, account, transport=httpx.MockTransport(handler))
    )
    assert token == "stored-access-token"


def test_get_access_token_refreshes_when_expired(db):
    user = _user(db)
    account = _live_account(db, user, expires_at=m.now() - timedelta(minutes=5))
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["form"] = parse_qs(request.content.decode())
        return httpx.Response(200, json={
            "access_token": "fresh-access",
            "expires_in": 3600,
            "refresh_token": "rotated-refresh",
        })

    token = asyncio.run(
        graphmail.get_access_token(db, account, transport=httpx.MockTransport(handler))
    )
    assert token == "fresh-access"
    assert seen["url"].startswith(
        "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    )
    assert seen["form"]["grant_type"] == ["refresh_token"]
    assert seen["form"]["refresh_token"] == ["stored-refresh-token"]
    scope = seen["form"]["scope"][0]
    assert "Mail.ReadWrite" in scope
    assert "Mail.Send" in scope
    assert "offline_access" in scope
    db.refresh(account)
    assert decrypt_secret(account.access_token_ciphertext) == "fresh-access"
    # Microsoft rotates refresh tokens; the replacement must be persisted.
    assert decrypt_secret(account.refresh_token_ciphertext) == "rotated-refresh"
    assert m.as_utc(account.token_expires_at) > m.now() + timedelta(minutes=50)


def test_get_access_token_invalid_grant_raises_auth_error(db):
    user = _user(db)
    account = _live_account(db, user, expires_at=m.now() - timedelta(minutes=5))

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": "invalid_grant"})

    with pytest.raises(graphmail.GraphAuthError):
        asyncio.run(
            graphmail.get_access_token(db, account, transport=httpx.MockTransport(handler))
        )


# ---------------------------------------------------------------------------
# Runner handling of live Microsoft sync jobs
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


def test_runner_completes_live_microsoft_job(db, monkeypatch):
    user = _user(db)
    account = _live_account(db, user)
    account.status = "syncing"
    db.commit()
    job = _running_job(db, user, account)

    async def fake_sync(db_, account_, mode):
        assert mode == "initial"
        return 5, None

    monkeypatch.setattr(graphmail, "sync_account", fake_sync)
    asyncio.run(runner._advance_syncs(db))
    db.refresh(job)
    db.refresh(account)
    assert job.status == "completed"
    assert job.processed_count == 5
    assert job.total_count == 5
    assert job.cursor_after is None
    assert account.status == "connected"
    ob = db.query(m.OnboardingState).filter_by(user_id=user.id).one()
    assert ob.state == "READY"


def test_runner_fails_live_microsoft_job_on_auth_error(db, monkeypatch):
    user = _user(db)
    account = _live_account(db, user)
    job = _running_job(db, user, account)

    async def failing_sync(db_, account_, mode):
        raise graphmail.GraphAuthError("revoked")

    monkeypatch.setattr(graphmail, "sync_account", failing_sync)
    asyncio.run(runner._advance_syncs(db))
    db.refresh(job)
    db.refresh(account)
    assert job.status == "failed"
    assert job.error_code == "TOKEN_REFRESH_FAILED"
    assert account.status == "action_required"


def test_runner_fails_live_microsoft_job_on_generic_error(db, monkeypatch):
    user = _user(db)
    account = _live_account(db, user)
    job = _running_job(db, user, account)

    async def broken_sync(db_, account_, mode):
        raise RuntimeError("boom")

    monkeypatch.setattr(graphmail, "sync_account", broken_sync)
    asyncio.run(runner._advance_syncs(db))
    db.refresh(job)
    db.refresh(account)
    assert job.status == "failed"
    assert job.error_code == "GRAPH_SYNC_FAILED"
    assert account.status == "connected"


# ---------------------------------------------------------------------------
# Real send on approval
# ---------------------------------------------------------------------------


def _draft_in_thread(db, user, account) -> tuple[m.EmailThread, m.EmailDraft]:
    thread = m.EmailThread(
        user_id=user.id, mail_account_id=account.id, provider_thread_id="conv-1",
        subject_normalized="Quotation Q-1042 for the spring campaign",
        environment="live",
    )
    db.add(thread)
    db.flush()
    db.add(m.EmailMessage(
        user_id=user.id, mail_account_id=account.id, thread_id=thread.id,
        provider_message_id="gm1", internet_message_id="<msg-1@acmestudio.example>",
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


def test_perform_send_live_microsoft_goes_through_graph(db, monkeypatch):
    user = _user(db)
    account = _live_account(db, user)
    _thread, draft = _draft_in_thread(db, user, account)
    captured: dict = {"paths": []}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["paths"].append(request.url.path)
        if request.url.path == "/v1.0/me/messages":
            captured["payload"] = json.loads(request.content)
            return httpx.Response(201, json={"id": "graph-draft-1"})
        if request.url.path == "/v1.0/me/messages/graph-draft-1/send":
            return httpx.Response(202)
        return httpx.Response(404, json={"error": {"message": "not found"}})

    transport = httpx.MockTransport(handler)
    real_send = graphmail.send_draft

    async def send_with_transport(db_, account_, draft_):
        return await real_send(db_, account_, draft_, transport=transport)

    monkeypatch.setattr(graphmail, "send_draft", send_with_transport)
    result = tasks_svc.perform_send(db, user, draft)
    assert result["simulated"] is False
    assert result["provider_message_id"] == "graph-draft-1"
    assert "Microsoft" in result["notice"]
    assert captured["paths"] == [
        "/v1.0/me/messages",
        "/v1.0/me/messages/graph-draft-1/send",
    ]
    payload = captured["payload"]
    assert payload["subject"] == "Re: Quotation Q-1042 for the spring campaign"
    assert payload["body"] == {
        "contentType": "Text",
        "content": "Thanks Maya, confirming this week.",
    }
    assert payload["toRecipients"] == [
        {"emailAddress": {"address": "maya@acmestudio.example", "name": "Maya Chen"}}
    ]
    db.refresh(draft)
    assert draft.status == "sent"
    sent = db.query(m.EmailMessage).filter_by(provider_message_id="graph-draft-1").one()
    assert sent.is_sent is True


def test_perform_send_live_microsoft_failure_raises_and_records_nothing(db, monkeypatch):
    user = _user(db)
    account = _live_account(db, user)
    _thread, draft = _draft_in_thread(db, user, account)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": {"message": "backend error"}})

    transport = httpx.MockTransport(handler)
    real_send = graphmail.send_draft

    async def send_with_transport(db_, account_, draft_):
        return await real_send(db_, account_, draft_, transport=transport)

    monkeypatch.setattr(graphmail, "send_draft", send_with_transport)
    with pytest.raises(graphmail.GraphError):
        tasks_svc.perform_send(db, user, draft)
    db.refresh(draft)
    assert draft.status == "in_review"
    assert db.query(m.EmailMessage).filter_by(is_sent=True).count() == 0
