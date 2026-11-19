"""Today Briefing aggregate endpoint (spec 7.4.4)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session as DbSession

from .. import models as m
from .. import serializers as ser
from ..db import get_db
from ..deps import get_current_user
from ..errors import ok

router = APIRouter(prefix="/api/v1", tags=["briefing"])

ACTIVE_TASK_STATES = ["queued", "running", "waiting_user", "paused", "takeover", "needs_attention"]


@router.get("/briefing")
def briefing(request: Request, date: str | None = None, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    accounts = (
        db.query(m.MailAccount)
        .filter(m.MailAccount.user_id == user.id, m.MailAccount.deleted_at.is_(None))
        .all()
    )
    environment = "demo" if any(a.environment == "demo" for a in accounts) else (
        "live" if accounts else "none"
    )

    unread = (
        db.query(m.EmailMessage)
        .join(m.EmailThread, m.EmailMessage.thread_id == m.EmailThread.id)
        .filter(
            m.EmailMessage.user_id == user.id,
            m.EmailMessage.is_read.is_(False),
            m.EmailMessage.is_draft.is_(False),
            m.EmailMessage.is_sent.is_(False),
            m.EmailMessage.is_trashed.is_(False),
            m.EmailThread.is_archived.is_(False),
        )
        .count()
    )
    pending_reviews = (
        db.query(m.ReviewItem)
        .filter(m.ReviewItem.user_id == user.id, m.ReviewItem.status.in_(["pending", "modified"]))
        .order_by(m.ReviewItem.created_at)
        .all()
    )
    pending_decisions = (
        db.query(m.Decision)
        .filter(m.Decision.user_id == user.id, m.Decision.status == "pending")
        .order_by(m.Decision.created_at)
        .all()
    )
    active_tasks = (
        db.query(m.Task)
        .filter(m.Task.user_id == user.id, m.Task.status.in_(ACTIVE_TASK_STATES))
        .order_by(m.Task.updated_at.desc())
        .all()
    )
    delivered = (
        db.query(m.Task).filter(m.Task.user_id == user.id, m.Task.status == "completed").count()
    )
    sent_count = (
        db.query(m.EmailMessage)
        .filter(m.EmailMessage.user_id == user.id, m.EmailMessage.is_sent.is_(True))
        .count()
    )

    decision_cards = []
    for item in pending_reviews:
        draft = db.get(m.EmailDraft, item.draft_id)
        task = db.get(m.Task, item.task_id) if item.task_id else None
        decision_cards.append({
            "kind": "review",
            "id": item.id,
            "review_id": item.id,
            "task_id": item.task_id,
            "task_display_id": task.display_id if task else None,
            "subject": draft.subject if draft else "",
            "recipient": (draft.to_recipients or [{}])[0].get("email") if draft else None,
            "recommendation": item.agent_note,
            "status": item.status,
            "created_at": ser.utc_iso(item.created_at),
        })
    for dec in pending_decisions:
        task = db.get(m.Task, dec.task_id)
        decision_cards.append({
            "kind": "decision",
            "id": dec.id,
            "decision_id": dec.id,
            "task_id": dec.task_id,
            "task_display_id": task.display_id if task else None,
            "subject": dec.prompt,
            "recipient": None,
            "recommendation": None,
            "options": dec.options or [],
            "status": dec.status,
            "created_at": ser.utc_iso(dec.created_at),
        })

    recent = (
        db.query(m.EmailMessage)
        .filter(
            m.EmailMessage.user_id == user.id,
            m.EmailMessage.is_draft.is_(False),
            m.EmailMessage.is_sent.is_(False),
            m.EmailMessage.is_trashed.is_(False),
        )
        .order_by(m.EmailMessage.created_at.desc())
        .limit(8)
        .all()
    )
    recent_activity = (
        db.query(m.AuditLog)
        .filter(m.AuditLog.user_id == user.id)
        .order_by(m.AuditLog.created_at.desc())
        .limit(10)
        .all()
    )
    open_todos = (
        db.query(m.Todo)
        .filter(m.Todo.user_id == user.id, m.Todo.status == "open")
        .order_by(m.Todo.due_at)
        .limit(6)
        .all()
    )
    notifications_unread = (
        db.query(m.Notification)
        .filter(m.Notification.user_id == user.id, m.Notification.read_at.is_(None))
        .count()
    )

    return ok(request, {
        "environment": environment,
        "has_mailbox": bool(accounts),
        "metrics": {
            "new_mail": unread,
            "needs_decision": len(pending_reviews) + len(pending_decisions),
            "in_progress": len(active_tasks),
            "delivered": delivered,
            "sent": sent_count,
        },
        "decisions": decision_cards,
        "tasks": [ser.task(t) for t in active_tasks],
        "recent_messages": [ser.message_summary(x) for x in recent],
        "recent_activity": [
            {"id": a.id, "action": a.action, "resource_type": a.resource_type,
             "result": a.result, "created_at": ser.utc_iso(a.created_at)}
            for a in recent_activity
        ],
        "todos": [ser.todo(t) for t in open_todos],
        "badges": {
            "unread": unread,
            "review": len(pending_reviews),
            "decisions": len(pending_decisions),
            "tasks_active": len(active_tasks),
            "notifications": notifications_unread,
        },
    })
