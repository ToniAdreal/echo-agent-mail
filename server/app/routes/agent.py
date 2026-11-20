"""Agent conversation endpoints with SSE streaming (spec 7.4.6, Section 5)."""
from __future__ import annotations

import json
import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session as DbSession

from .. import models as m
from .. import serializers as ser
from ..config import settings
from ..db import SessionLocal, get_db
from ..deps import audit, get_current_user, rate_limiter
from ..errors import ApiError, ok
from ..helpers import paginate
from ..services import agent as agent_svc

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


def _own_conversation(db: DbSession, user: m.User, conversation_id: str) -> m.AgentConversation:
    conv = db.get(m.AgentConversation, conversation_id)
    if conv is None or conv.user_id != user.id:
        raise ApiError(404, "NOT_FOUND", "Conversation not found.")
    return conv


@router.get("/status")
def agent_status(request: Request, user: m.User = Depends(get_current_user)):
    available = agent_svc.model_available()
    return ok(request, {
        "provider": settings.LLM_PROVIDER_NAME,
        "model": settings.LLM_MODEL,
        "available": available,
        "quota_state": "ok" if available else "unavailable",
    })


@router.get("/conversations")
def list_conversations(request: Request, limit: int = 50, cursor: str | None = None,
                       db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    q = (
        db.query(m.AgentConversation)
        .filter(m.AgentConversation.user_id == user.id, m.AgentConversation.status == "active")
        .order_by(m.AgentConversation.updated_at.desc())
    )
    items, next_cursor, total = paginate(q, limit, cursor)
    return ok(request, {"items": [ser.conversation(c) for c in items], "next_cursor": next_cursor, "total": total})


class ConversationCreateBody(BaseModel):
    title: str | None = None
    context_scope: dict | None = None


@router.post("/conversations")
def create_conversation(body: ConversationCreateBody, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    conv = m.AgentConversation(
        user_id=user.id,
        title=(body.title or "New conversation")[:200],
        context_scope=body.context_scope or {},
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return ok(request, {"conversation": ser.conversation(conv)}, status=201)


@router.get("/conversations/{conversation_id}")
def get_conversation(conversation_id: str, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    conv = _own_conversation(db, user, conversation_id)
    msgs = (
        db.query(m.AgentMessage)
        .filter(m.AgentMessage.conversation_id == conv.id)
        .order_by(m.AgentMessage.created_at)
        .all()
    )
    return ok(request, {
        "conversation": ser.conversation(conv),
        "messages": [ser.agent_message(x) for x in msgs],
    })


@router.delete("/conversations/{conversation_id}")
def archive_conversation(conversation_id: str, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    conv = _own_conversation(db, user, conversation_id)
    conv.status = "archived"
    db.commit()
    return ok(request, {"archived": True})


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _check_agent_limits(db: DbSession, user: m.User) -> None:
    if not rate_limiter.check(f"agent:{user.id}", settings.AGENT_REQUESTS_PER_MINUTE, 60):
        raise ApiError(429, "RATE_LIMITED", "Too many Agent messages. Please wait a moment and retry.")
    day_start = m.now() - timedelta(days=1)
    count = (
        db.query(m.AgentMessage)
        .filter(
            m.AgentMessage.user_id == user.id,
            m.AgentMessage.role == "user",
            m.AgentMessage.created_at >= day_start,
        )
        .count()
    )
    if count >= settings.AGENT_REQUESTS_PER_DAY:
        raise ApiError(429, "RATE_LIMITED", "The daily Agent message limit for this demo has been reached.")


async def _run_turn(conversation_id: str, user_id: str, user_message_id: str, content: str, context: dict | None):
    """Generate SSE events for one Agent turn, persisting as we go."""
    db = SessionLocal()
    try:
        conv = db.get(m.AgentConversation, conversation_id)
        user = db.get(m.User, user_id)
        assistant = m.AgentMessage(
            conversation_id=conversation_id, user_id=user_id, role="assistant",
            content="", status="streaming", attempt_id=str(uuid.uuid4()),
            model_provider=settings.LLM_PROVIDER_NAME, model_id=settings.LLM_MODEL,
        )
        db.add(assistant)
        db.commit()
        db.refresh(assistant)
        yield _sse("message.started", {"conversation_id": conversation_id, "message_id": assistant.id})
        yield _sse("heartbeat", {"conversation_id": conversation_id})

        messages, auto_thread_ids = agent_svc.build_messages(db, user, conv, content, context)
        if auto_thread_ids:
            # Persist auto-matched threads so later turns keep this context.
            scope = dict(conv.context_scope or {})
            merged = list(scope.get("thread_ids") or [])
            for v in auto_thread_ids:
                if v not in merged:
                    merged.append(v)
            scope["thread_ids"] = merged
            conv.context_scope = scope
            db.commit()
        deltas: list[str] = []
        error: agent_svc.ModelUnavailable | None = None
        try:
            async for delta in agent_svc.stream_completion(messages):
                deltas.append(delta)
                yield _sse("message.delta", {"message_id": assistant.id, "delta": delta})
        except agent_svc.ModelUnavailable as exc:
            error = exc

        full = "".join(deltas)
        user_msg = db.get(m.AgentMessage, user_message_id)
        if error is not None and not deltas:
            # Clean fallback (spec 5.5): no fabricated answer, no side effects.
            if user_msg is not None:
                user_msg.status = "model_unavailable"
            assistant.role = "notice"
            assistant.content = agent_svc.FALLBACK_WORDING
            assistant.status = "failed"
            assistant.error_code = error.code
            assistant.completed_at = m.now()
            db.commit()
            yield _sse("message.error", {
                "message_id": assistant.id, "code": error.code,
                "message": agent_svc.FALLBACK_WORDING,
            })
            return
        if error is not None and deltas:
            # Partial stream: keep the partial text as incomplete + fallback notice.
            assistant.content = full
            assistant.status = "incomplete"
            assistant.error_code = error.code
            assistant.completed_at = m.now()
            notice = m.AgentMessage(
                conversation_id=conversation_id, user_id=user_id, role="notice",
                content=agent_svc.FALLBACK_WORDING, status="failed", error_code=error.code,
            )
            db.add(notice)
            db.commit()
            yield _sse("message.error", {
                "message_id": assistant.id, "code": error.code,
                "message": agent_svc.FALLBACK_WORDING,
            })
            return

        assistant.content = full
        assistant.status = "complete"
        assistant.completed_at = m.now()
        plan = agent_svc.extract_plan(full)
        if plan is not None:
            assistant.content_json = {"plan": plan}
            db.commit()
            yield _sse("message.annotation", {
                "message_id": assistant.id, "annotation_type": "plan", "plan": plan,
            })
        else:
            db.commit()
        conv.last_message_at = m.now()
        if conv.title == "New conversation" and content:
            conv.title = content[:60]
        db.commit()
        yield _sse("message.completed", {
            "message_id": assistant.id, "status": "complete",
            "model": settings.LLM_MODEL, "provider": settings.LLM_PROVIDER_NAME,
        })
    finally:
        db.close()


class MessageCreateBody(BaseModel):
    content: str
    context: dict | None = None
    stream: bool = True
    client_message_id: str | None = None


@router.post("/conversations/{conversation_id}/messages")
async def post_message(conversation_id: str, body: MessageCreateBody, request: Request,
                       db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    conv = _own_conversation(db, user, conversation_id)
    content = body.content.strip()
    if not content:
        raise ApiError(422, "VALIDATION_ERROR", "Message content is required.")
    _check_agent_limits(db, user)
    if body.client_message_id:
        existing = (
            db.query(m.AgentMessage)
            .filter(m.AgentMessage.conversation_id == conv.id,
                    m.AgentMessage.client_message_id == body.client_message_id)
            .first()
        )
        if existing is not None:
            return ok(request, {"message": ser.agent_message(existing)})
    user_msg = m.AgentMessage(
        conversation_id=conv.id, user_id=user.id, role="user", content=content,
        status="complete", client_message_id=body.client_message_id,
    )
    db.add(user_msg)
    if body.context:
        scope = dict(conv.context_scope or {})
        for key in ("thread_ids", "message_ids"):
            if key in (body.context or {}):
                merged = list(scope.get(key) or [])
                for v in body.context[key]:
                    if v not in merged:
                        merged.append(v)
                scope[key] = merged
        conv.context_scope = scope
    conv.last_message_at = m.now()
    db.commit()
    db.refresh(user_msg)
    audit(db, user, "agent.message_sent", "agent_conversation", conv.id, request=request)
    db.commit()

    if not body.stream:
        events = []
        async for chunk in _run_turn(conv.id, user.id, user_msg.id, content, body.context):
            events.append(chunk)
        final = (
            db.query(m.AgentMessage)
            .filter(m.AgentMessage.conversation_id == conv.id, m.AgentMessage.role == "assistant")
            .order_by(m.AgentMessage.created_at.desc())
            .first()
        )
        notice = (
            db.query(m.AgentMessage)
            .filter(m.AgentMessage.conversation_id == conv.id, m.AgentMessage.role == "notice")
            .order_by(m.AgentMessage.created_at.desc())
            .first()
        )
        return ok(request, {"message": ser.agent_message(final) if final else None,
                            "notice": ser.agent_message(notice) if notice else None})

    return StreamingResponse(
        _run_turn(conv.id, user.id, user_msg.id, content, body.context),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"},
    )


class RetryBody(BaseModel):
    message_id: str
    attempt_id: str | None = None


@router.post("/conversations/{conversation_id}/retry")
async def retry_message(conversation_id: str, body: RetryBody, request: Request,
                        db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    conv = _own_conversation(db, user, conversation_id)
    msg = db.get(m.AgentMessage, body.message_id)
    if msg is None or msg.conversation_id != conv.id or msg.role != "user":
        raise ApiError(404, "NOT_FOUND", "Message not found.")
    if msg.status not in {"model_unavailable", "complete"}:
        raise ApiError(409, "INVALID_STATE", "Only a message whose model request failed can be retried.")
    _check_agent_limits(db, user)
    msg.status = "complete"  # the retry is a new attempt on the same user message
    db.commit()
    return StreamingResponse(
        _run_turn(conv.id, user.id, msg.id, msg.content, conv.context_scope or {}),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"},
    )
