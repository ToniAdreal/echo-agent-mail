"""Email, thread, draft, search and archive endpoints (spec 7.4.5, 7.4.10)."""
from __future__ import annotations

import re
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session as DbSession

from .. import models as m
from .. import serializers as ser
from ..db import get_db
from ..deps import audit, get_current_user
from ..errors import ApiError, ok
from ..helpers import idempotency_lookup, idempotency_store, paginate
from ..services import tasks_svc

router = APIRouter(prefix="/api/v1", tags=["mail"])

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _norm_recipients(raw) -> list[dict]:
    out = []
    for item in raw or []:
        if isinstance(item, str):
            email = item.strip()
            if email:
                out.append({"name": email.split("@")[0], "email": email})
        elif isinstance(item, dict) and item.get("email"):
            out.append({"name": item.get("name") or item["email"].split("@")[0], "email": item["email"]})
    return out


def _validate_recipients(recipients: list[dict]) -> None:
    for r in recipients:
        if not EMAIL_RE.match(r["email"]):
            raise ApiError(422, "VALIDATION_ERROR", f"Recipient address is not valid: {r['email']}", {"field": "to"})


def _own_message(db: DbSession, user: m.User, message_id: str) -> m.EmailMessage:
    msg = db.get(m.EmailMessage, message_id)
    if msg is None or msg.user_id != user.id:
        raise ApiError(404, "NOT_FOUND", "Message not found.")
    return msg


def _own_thread(db: DbSession, user: m.User, thread_id: str) -> m.EmailThread:
    thread = db.get(m.EmailThread, thread_id)
    if thread is None or thread.user_id != user.id:
        raise ApiError(404, "NOT_FOUND", "Thread not found.")
    return thread


def _own_account(db: DbSession, user: m.User, account_id: str | None) -> m.MailAccount:
    q = db.query(m.MailAccount).filter(
        m.MailAccount.user_id == user.id, m.MailAccount.deleted_at.is_(None)
    )
    if account_id:
        q = q.filter(m.MailAccount.id == account_id)
    account = q.order_by(m.MailAccount.created_at).first()
    if account is None:
        raise ApiError(404, "NOT_FOUND", "Mail account not found. Connect a mailbox or open the Demo Mailbox first.")
    return account


def _folder_filter(q, folder: str | None):
    T = m.EmailThread
    if folder in (None, "", "inbox"):
        return q.filter(
            m.EmailMessage.is_draft.is_(False), m.EmailMessage.is_sent.is_(False),
            m.EmailMessage.is_trashed.is_(False), T.is_archived.is_(False), T.is_trashed.is_(False),
        )
    if folder == "sent":
        return q.filter(m.EmailMessage.is_sent.is_(True), m.EmailMessage.is_trashed.is_(False))
    if folder == "drafts":
        return q.filter(m.EmailMessage.is_draft.is_(True), m.EmailMessage.is_trashed.is_(False))
    if folder == "starred":
        return q.filter(m.EmailMessage.is_starred.is_(True), m.EmailMessage.is_trashed.is_(False),
                        m.EmailMessage.is_draft.is_(False))
    if folder == "archive":
        return q.filter(T.is_archived.is_(True), m.EmailMessage.is_trashed.is_(False),
                        m.EmailMessage.is_draft.is_(False))
    if folder == "trash":
        return q.filter(or_(m.EmailMessage.is_trashed.is_(True), T.is_trashed.is_(True)))
    return q


def _attachment_message_ids(db: DbSession) -> set[str]:
    rows = db.query(m.EmailAttachment.message_id).distinct().all()
    return {r[0] for r in rows}


# ------------------------------------------------------------------ emails

@router.get("/emails")
def list_emails(request: Request, account_id: str | None = None, folder: str | None = "inbox",
                limit: int = 50, cursor: str | None = None, unread: bool | None = None,
                starred: bool | None = None, has_attachment: bool | None = None,
                db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    q = (
        db.query(m.EmailMessage)
        .join(m.EmailThread, m.EmailMessage.thread_id == m.EmailThread.id)
        .filter(m.EmailMessage.user_id == user.id)
    )
    if account_id:
        q = q.filter(m.EmailMessage.mail_account_id == account_id)
    q = _folder_filter(q, folder)
    if unread:
        q = q.filter(m.EmailMessage.is_read.is_(False))
    if starred:
        q = q.filter(m.EmailMessage.is_starred.is_(True))
    if has_attachment:
        ids = _attachment_message_ids(db)
        q = q.filter(m.EmailMessage.id.in_(ids)) if ids else q.filter(False)
    q = q.order_by(m.EmailMessage.created_at.desc())
    items, next_cursor, total = paginate(q, limit, cursor)
    att_ids = _attachment_message_ids(db)
    return ok(request, {
        "items": [ser.message_summary(x, x.id in att_ids) for x in items],
        "next_cursor": next_cursor, "total": total,
    })


@router.get("/emails/{message_id}")
def get_email(message_id: str, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    msg = _own_message(db, user, message_id)
    atts = db.query(m.EmailAttachment).filter(m.EmailAttachment.message_id == msg.id).all()
    thread = db.get(m.EmailThread, msg.thread_id)
    return ok(request, {
        "message": ser.message(msg, atts),
        "attachments": [ser.attachment(a) for a in atts],
        "thread_summary": ser.thread(thread) if thread else None,
    })


class ComposeBody(BaseModel):
    account_id: str | None = None
    to: list = []
    cc: list = []
    bcc: list = []
    subject: str = ""
    body: str = ""
    thread_id: str | None = None


def _create_draft(db, user, account, *, to, cc, bcc, subject, body, thread=None, source_message_id=None):
    if thread is None:
        thread = m.EmailThread(
            user_id=user.id, mail_account_id=account.id,
            subject_normalized=subject or "(no subject)",
            participants=to, environment=account.environment,
        )
        db.add(thread)
        db.flush()
    msg = m.EmailMessage(
        user_id=user.id, mail_account_id=account.id, thread_id=thread.id,
        from_address=account.email_address, from_name=user.name,
        to_recipients=to, cc_recipients=cc, bcc_recipients=bcc,
        subject=subject, body_text=body,
        snippet=(body or "").replace("\n", " ")[:110],
        is_read=True, is_draft=True, environment=account.environment,
    )
    db.add(msg)
    db.flush()
    draft = m.EmailDraft(
        user_id=user.id, mail_account_id=account.id, thread_id=thread.id,
        source_message_id=source_message_id, message_id=msg.id,
        to_recipients=to, cc_recipients=cc, bcc_recipients=bcc,
        subject=subject, body_text=body, status="draft", environment=account.environment,
    )
    db.add(draft)
    thread.message_count = db.query(m.EmailMessage).filter(m.EmailMessage.thread_id == thread.id).count()
    db.commit()
    db.refresh(draft)
    return draft


@router.post("/emails/compose")
def compose(body: ComposeBody, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    account = _own_account(db, user, body.account_id)
    to = _norm_recipients(body.to)
    cc = _norm_recipients(body.cc)
    bcc = _norm_recipients(body.bcc)
    _validate_recipients(to + cc + bcc)
    thread = _own_thread(db, user, body.thread_id) if body.thread_id else None
    draft = _create_draft(db, user, account, to=to, cc=cc, bcc=bcc,
                          subject=body.subject, body=body.body, thread=thread)
    audit(db, user, "email.draft_created", "email_draft", draft.id, request=request, environment=account.environment)
    db.commit()
    return ok(request, {"draft": ser.draft(draft)}, status=201)


class ReplyBody(BaseModel):
    reply_all: bool = False
    body: str = ""
    attachments: list | None = None


@router.post("/emails/{message_id}/reply")
def reply(message_id: str, body: ReplyBody, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    src = _own_message(db, user, message_id)
    account = _own_account(db, user, src.mail_account_id)
    thread = db.get(m.EmailThread, src.thread_id)
    to = [{"name": src.from_name or src.from_address, "email": src.from_address}]
    cc: list[dict] = []
    if body.reply_all:
        seen = {src.from_address, account.email_address}
        for r in (src.to_recipients or []) + (src.cc_recipients or []):
            if r.get("email") and r["email"] not in seen:
                cc.append(r)
                seen.add(r["email"])
    subject = src.subject if src.subject.lower().startswith("re:") else f"Re: {src.subject}"
    quoted = "\n".join(f"> {line}" for line in (src.body_text or "").splitlines())
    full_body = f"{body.body}\n\nOn {src.received_at or src.sent_at or ''}, {src.from_name or src.from_address} wrote:\n{quoted}"
    draft = _create_draft(db, user, account, to=to, cc=cc, bcc=[], subject=subject,
                          body=full_body, thread=thread, source_message_id=src.id)
    return ok(request, {"draft": ser.draft(draft)}, status=201)


class ForwardBody(BaseModel):
    to: list = []
    cc: list = []
    bcc: list = []
    body: str = ""
    include_attachments: bool = False


@router.post("/emails/{message_id}/forward")
def forward(message_id: str, body: ForwardBody, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    src = _own_message(db, user, message_id)
    account = _own_account(db, user, src.mail_account_id)
    to = _norm_recipients(body.to)
    cc = _norm_recipients(body.cc)
    bcc = _norm_recipients(body.bcc)
    _validate_recipients(to + cc + bcc)
    if not to:
        raise ApiError(422, "VALIDATION_ERROR", "Forward needs at least one recipient.", {"field": "to"})
    subject = src.subject if src.subject.lower().startswith("fwd:") else f"Fwd: {src.subject}"
    forwarded = (
        f"{body.body}\n\n---------- Forwarded message ----------\n"
        f"From: {src.from_name or ''} <{src.from_address}>\nSubject: {src.subject}\n\n{src.body_text or ''}"
    )
    draft = _create_draft(db, user, account, to=to, cc=cc, bcc=bcc, subject=subject,
                          body=forwarded, source_message_id=src.id)
    return ok(request, {"draft": ser.draft(draft)}, status=201)


class SendBody(BaseModel):
    draft_id: str
    revision: int
    confirm_send: bool = False
    environment: str | None = None


@router.post("/emails/{message_id}/send")
def send_email(message_id: str, body: SendBody, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    msg = _own_message(db, user, message_id)
    draft = db.get(m.EmailDraft, body.draft_id)
    if draft is None or draft.user_id != user.id or draft.message_id != msg.id:
        raise ApiError(404, "NOT_FOUND", "Draft not found for this message.")
    if not body.confirm_send:
        raise ApiError(422, "CONFIRMATION_REQUIRED", "Sending requires confirm_send=true after reviewing the confirmation.")
    if draft.status == "sent":
        prior = idempotency_lookup(db, user.id, request.headers.get("idempotency-key"), "email.send")
        if prior is not None:
            return ok(request, prior)
        raise ApiError(409, "ALREADY_SENT", "This draft has already been sent.")
    if body.revision != draft.revision:
        raise ApiError(409, "REVISION_CONFLICT", "The draft changed since you loaded it. Reload the latest revision.",
                       {"latest_revision": draft.revision})
    result = tasks_svc.perform_send(db, user, draft)
    payload = {"send_result": result, "message": ser.message(db.get(m.EmailMessage, result["message_id"]))}
    audit(db, user, "email.sent", "email_draft", draft.id, request=request,
          environment=draft.environment, meta={"simulated": result["simulated"]})
    db.commit()
    idempotency_store(db, user.id, request.headers.get("idempotency-key"), "email.send",
                      {"draft_id": draft.id}, payload)
    return ok(request, payload)


@router.post("/emails/{message_id}/archive")
def archive_email(message_id: str, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    msg = _own_message(db, user, message_id)
    thread = db.get(m.EmailThread, msg.thread_id)
    if thread is not None:
        thread.is_archived = True
    audit(db, user, "email.archived", "email_message", msg.id, request=request, environment=msg.environment)
    db.commit()
    return ok(request, {"archived": True})


@router.delete("/emails/{message_id}")
def trash_email(message_id: str, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    msg = _own_message(db, user, message_id)
    msg.is_trashed = True
    audit(db, user, "email.trashed", "email_message", msg.id, request=request, environment=msg.environment)
    db.commit()
    return ok(request, {"trashed": True})


class RestoreBody(BaseModel):
    destination: str = "inbox"


@router.post("/emails/{message_id}/restore")
def restore_email(message_id: str, body: RestoreBody, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    msg = _own_message(db, user, message_id)
    msg.is_trashed = False
    thread = db.get(m.EmailThread, msg.thread_id)
    if thread is not None:
        thread.is_trashed = False
        if body.destination == "inbox":
            thread.is_archived = False
    db.commit()
    return ok(request, {"restored": True})


class ReadStateBody(BaseModel):
    is_read: bool


@router.post("/emails/{message_id}/read-state")
def read_state(message_id: str, body: ReadStateBody, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    msg = _own_message(db, user, message_id)
    msg.is_read = body.is_read
    db.commit()
    return ok(request, {"is_read": msg.is_read})


class StarBody(BaseModel):
    is_starred: bool


@router.post("/emails/{message_id}/star")
def star(message_id: str, body: StarBody, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    msg = _own_message(db, user, message_id)
    msg.is_starred = body.is_starred
    db.commit()
    return ok(request, {"is_starred": msg.is_starred})


class HandOffBody(BaseModel):
    conversation_id: str | None = None
    intent: str | None = None


@router.post("/emails/{message_id}/hand-off")
def hand_off(message_id: str, body: HandOffBody, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    msg = _own_message(db, user, message_id)
    thread = db.get(m.EmailThread, msg.thread_id)
    account = _own_account(db, user, msg.mail_account_id)
    if body.conversation_id:
        conv = db.get(m.AgentConversation, body.conversation_id)
        if conv is None or conv.user_id != user.id:
            raise ApiError(404, "NOT_FOUND", "Conversation not found.")
        scope = dict(conv.context_scope or {})
        tids = list(scope.get("thread_ids") or [])
        if thread.id not in tids:
            tids.append(thread.id)
        scope["thread_ids"] = tids
        conv.context_scope = scope
    else:
        conv = m.AgentConversation(
            user_id=user.id,
            title=f"Re: {thread.subject_normalized}" if thread else "Email handoff",
            context_scope={"thread_ids": [thread.id] if thread else [], "message_ids": [msg.id]},
        )
        db.add(conv)
    db.commit()
    db.refresh(conv)
    atts = db.query(m.EmailAttachment).filter(m.EmailAttachment.message_id == msg.id).count()
    preview = {
        "mailbox": account.email_address,
        "environment": account.environment,
        "thread_id": thread.id if thread else None,
        "subject": thread.subject_normalized if thread else msg.subject,
        "participants": thread.participants if thread else [],
        "message_count": thread.message_count if thread else 1,
        "attachments_included": False,
        "attachment_count": atts,
        "body_sent_to_model": True,
        "intent": body.intent,
    }
    return ok(request, {"conversation": ser.conversation(conv), "context_preview": preview}, status=201)


# ----------------------------------------------------------------- threads

@router.get("/threads")
def list_threads(request: Request, account_id: str | None = None, folder: str | None = "inbox",
                 limit: int = 50, cursor: str | None = None, q: str | None = None,
                 db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    query = db.query(m.EmailThread).filter(m.EmailThread.user_id == user.id)
    if account_id:
        query = query.filter(m.EmailThread.mail_account_id == account_id)
    if folder in (None, "", "inbox"):
        query = query.filter(m.EmailThread.is_archived.is_(False), m.EmailThread.is_trashed.is_(False))
    elif folder == "archive":
        query = query.filter(m.EmailThread.is_archived.is_(True), m.EmailThread.is_trashed.is_(False))
    elif folder == "trash":
        query = query.filter(m.EmailThread.is_trashed.is_(True))
    if q:
        query = query.filter(m.EmailThread.subject_normalized.ilike(f"%{q}%"))
    query = query.order_by(m.EmailThread.last_message_at.desc())
    items, next_cursor, total = paginate(query, limit, cursor)
    out = []
    for t in items:
        latest = (
            db.query(m.EmailMessage)
            .filter(m.EmailMessage.thread_id == t.id, m.EmailMessage.is_draft.is_(False))
            .order_by(m.EmailMessage.created_at.desc())
            .first()
        )
        unread = (
            db.query(m.EmailMessage)
            .filter(m.EmailMessage.thread_id == t.id, m.EmailMessage.is_read.is_(False),
                    m.EmailMessage.is_draft.is_(False))
            .count()
        )
        data = ser.thread(t, latest)
        data["unread_count"] = unread
        out.append(data)
    return ok(request, {"items": out, "next_cursor": next_cursor, "total": total})


@router.get("/threads/{thread_id}")
def get_thread(thread_id: str, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    thread = _own_thread(db, user, thread_id)
    msgs = (
        db.query(m.EmailMessage)
        .filter(m.EmailMessage.thread_id == thread.id)
        .order_by(m.EmailMessage.created_at)
        .all()
    )
    atts = db.query(m.EmailAttachment).filter(
        m.EmailAttachment.message_id.in_([x.id for x in msgs])
    ).all() if msgs else []
    return ok(request, {
        "thread": ser.thread(thread),
        "messages": [ser.message(x, [a for a in atts if a.message_id == x.id]) for x in msgs],
        "attachments": [ser.attachment(a) for a in atts],
    })


@router.post("/threads/{thread_id}/read-state")
def thread_read_state(thread_id: str, body: ReadStateBody, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    thread = _own_thread(db, user, thread_id)
    db.query(m.EmailMessage).filter(m.EmailMessage.thread_id == thread.id).update(
        {"is_read": body.is_read}
    )
    db.commit()
    return ok(request, {"updated": True})


@router.post("/threads/{thread_id}/archive")
def thread_archive(thread_id: str, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    thread = _own_thread(db, user, thread_id)
    thread.is_archived = True
    audit(db, user, "thread.archived", "email_thread", thread.id, request=request, environment=thread.environment)
    db.commit()
    return ok(request, {"archived": True})


# ------------------------------------------------------------------ search

@router.get("/search")
def search(request: Request, q: str = "", account_id: str | None = None,
           from_: str | None = None, to: str | None = None, after: str | None = None,
           before: str | None = None, label: str | None = None, unread: bool | None = None,
           has_attachment: bool | None = None, limit: int = 50, cursor: str | None = None,
           db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    query = (
        db.query(m.EmailMessage)
        .filter(m.EmailMessage.user_id == user.id, m.EmailMessage.is_trashed.is_(False),
                m.EmailMessage.is_draft.is_(False))
    )
    if account_id:
        query = query.filter(m.EmailMessage.mail_account_id == account_id)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            m.EmailMessage.subject.ilike(like),
            m.EmailMessage.from_address.ilike(like),
            m.EmailMessage.from_name.ilike(like),
            m.EmailMessage.body_text.ilike(like),
            m.EmailMessage.snippet.ilike(like),
        ))
    if from_:
        query = query.filter(m.EmailMessage.from_address.ilike(f"%{from_}%"))
    if unread:
        query = query.filter(m.EmailMessage.is_read.is_(False))
    if after:
        try:
            query = query.filter(m.EmailMessage.created_at >= datetime.fromisoformat(after))
        except ValueError:
            raise ApiError(422, "VALIDATION_ERROR", "after must be an ISO 8601 date.")
    if before:
        try:
            query = query.filter(m.EmailMessage.created_at <= datetime.fromisoformat(before))
        except ValueError:
            raise ApiError(422, "VALIDATION_ERROR", "before must be an ISO 8601 date.")
    if has_attachment:
        ids = _attachment_message_ids(db)
        query = query.filter(m.EmailMessage.id.in_(ids)) if ids else query.filter(False)
    query = query.order_by(m.EmailMessage.created_at.desc())
    items, next_cursor, total = paginate(query, limit, cursor)
    att_ids = _attachment_message_ids(db)
    return ok(request, {
        "items": [ser.message_summary(x, x.id in att_ids) for x in items],
        "next_cursor": next_cursor, "total": total, "query": q,
    })


# ------------------------------------------------------------------ drafts

@router.get("/drafts")
def list_drafts(request: Request, status: str | None = None, limit: int = 50, cursor: str | None = None,
                db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    q = db.query(m.EmailDraft).filter(m.EmailDraft.user_id == user.id)
    if status:
        q = q.filter(m.EmailDraft.status == status)
    q = q.order_by(m.EmailDraft.updated_at.desc())
    items, next_cursor, total = paginate(q, limit, cursor)
    return ok(request, {"items": [ser.draft(d) for d in items], "next_cursor": next_cursor, "total": total})


class DraftCreateBody(BaseModel):
    account_id: str | None = None
    thread_id: str | None = None
    to: list = []
    cc: list = []
    bcc: list = []
    subject: str = ""
    body: str = ""


@router.post("/drafts")
def create_draft(body: DraftCreateBody, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    account = _own_account(db, user, body.account_id)
    to = _norm_recipients(body.to)
    _validate_recipients(to)
    thread = _own_thread(db, user, body.thread_id) if body.thread_id else None
    draft = _create_draft(db, user, account, to=to, cc=_norm_recipients(body.cc),
                          bcc=_norm_recipients(body.bcc), subject=body.subject,
                          body=body.body, thread=thread)
    return ok(request, {"draft": ser.draft(draft)}, status=201)


@router.get("/drafts/{draft_id}")
def get_draft(draft_id: str, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    draft = db.get(m.EmailDraft, draft_id)
    if draft is None or draft.user_id != user.id:
        raise ApiError(404, "NOT_FOUND", "Draft not found.")
    return ok(request, {"draft": ser.draft(draft)})


class DraftPatchBody(BaseModel):
    revision: int
    to: list | None = None
    cc: list | None = None
    bcc: list | None = None
    subject: str | None = None
    body: str | None = None


@router.patch("/drafts/{draft_id}")
def patch_draft(draft_id: str, body: DraftPatchBody, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    draft = db.get(m.EmailDraft, draft_id)
    if draft is None or draft.user_id != user.id:
        raise ApiError(404, "NOT_FOUND", "Draft not found.")
    if draft.status == "sent":
        raise ApiError(409, "ALREADY_SENT", "A sent draft can no longer be edited.")
    if body.revision != draft.revision:
        raise ApiError(409, "REVISION_CONFLICT", "The draft changed since you loaded it.",
                       {"latest": ser.draft(draft)})
    if body.to is not None:
        draft.to_recipients = _norm_recipients(body.to)
        _validate_recipients(draft.to_recipients)
    if body.cc is not None:
        draft.cc_recipients = _norm_recipients(body.cc)
    if body.bcc is not None:
        draft.bcc_recipients = _norm_recipients(body.bcc)
    if body.subject is not None:
        draft.subject = body.subject
    if body.body is not None:
        draft.body_text = body.body
    draft.revision += 1
    if draft.message_id:
        msg = db.get(m.EmailMessage, draft.message_id)
        if msg is not None:
            msg.to_recipients = draft.to_recipients
            msg.cc_recipients = draft.cc_recipients
            msg.bcc_recipients = draft.bcc_recipients
            msg.subject = draft.subject
            msg.body_text = draft.body_text
            msg.snippet = (draft.body_text or "").replace("\n", " ")[:110]
    db.commit()
    db.refresh(draft)
    return ok(request, {"draft": ser.draft(draft)})


@router.delete("/drafts/{draft_id}")
def delete_draft(draft_id: str, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    draft = db.get(m.EmailDraft, draft_id)
    if draft is None or draft.user_id != user.id:
        raise ApiError(404, "NOT_FOUND", "Draft not found.")
    if draft.status == "sent":
        raise ApiError(409, "ALREADY_SENT", "A sent draft cannot be deleted.")
    if draft.message_id:
        msg = db.get(m.EmailMessage, draft.message_id)
        if msg is not None:
            db.delete(msg)
    db.delete(draft)
    db.commit()
    return ok(request, {"deleted": True})


# ----------------------------------------------------------------- archive

@router.get("/archive")
def list_archive(request: Request, q: str | None = None, after: str | None = None,
                 before: str | None = None, account_id: str | None = None,
                 limit: int = 50, cursor: str | None = None,
                 db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    query = (
        db.query(m.EmailMessage)
        .join(m.EmailThread, m.EmailMessage.thread_id == m.EmailThread.id)
        .filter(m.EmailMessage.user_id == user.id, m.EmailThread.is_archived.is_(True),
                m.EmailMessage.is_trashed.is_(False), m.EmailMessage.is_draft.is_(False))
    )
    if account_id:
        query = query.filter(m.EmailMessage.mail_account_id == account_id)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(m.EmailMessage.subject.ilike(like),
                                 m.EmailMessage.from_address.ilike(like),
                                 m.EmailMessage.body_text.ilike(like)))
    if after:
        try:
            query = query.filter(m.EmailMessage.created_at >= datetime.fromisoformat(after))
        except ValueError:
            raise ApiError(422, "VALIDATION_ERROR", "after must be an ISO 8601 date.")
    if before:
        try:
            query = query.filter(m.EmailMessage.created_at <= datetime.fromisoformat(before))
        except ValueError:
            raise ApiError(422, "VALIDATION_ERROR", "before must be an ISO 8601 date.")
    query = query.order_by(m.EmailMessage.created_at.desc())
    items, next_cursor, total = paginate(query, limit, cursor)
    att_ids = _attachment_message_ids(db)
    return ok(request, {
        "items": [ser.message_summary(x, x.id in att_ids) for x in items],
        "next_cursor": next_cursor, "total": total,
    })


@router.post("/archive/{message_id}/restore")
def archive_restore(message_id: str, body: RestoreBody, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    msg = _own_message(db, user, message_id)
    thread = db.get(m.EmailThread, msg.thread_id)
    if thread is not None:
        thread.is_archived = False
    audit(db, user, "email.restored", "email_message", msg.id, request=request, environment=msg.environment)
    db.commit()
    return ok(request, {"restored": True})
