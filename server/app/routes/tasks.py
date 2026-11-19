"""Task and decision endpoints (spec 7.4.7, Section 6)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session as DbSession

from .. import models as m
from .. import serializers as ser
from ..db import get_db
from ..deps import audit, get_current_user
from ..errors import ApiError, ok
from ..helpers import idempotency_lookup, idempotency_store, paginate
from ..services import tasks_svc

router = APIRouter(prefix="/api/v1", tags=["tasks"])

AUTH_MODES = {"confirm_every_step", "confirm_milestones", "confirm_before_send"}
TERMINAL = {"completed", "failed", "cancelled"}


def _own_task(db: DbSession, user: m.User, task_id: str) -> m.Task:
    task = db.get(m.Task, task_id)
    if task is None or task.user_id != user.id:
        raise ApiError(404, "NOT_FOUND", "Task not found.")
    return task


def _steps(db: DbSession, task: m.Task) -> list[m.TaskStep]:
    return (
        db.query(m.TaskStep)
        .filter(m.TaskStep.task_id == task.id)
        .order_by(m.TaskStep.sequence)
        .all()
    )


@router.get("/tasks")
def list_tasks(request: Request, status: str | None = None, limit: int = 50, cursor: str | None = None,
               db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    q = db.query(m.Task).filter(m.Task.user_id == user.id)
    if status:
        q = q.filter(m.Task.status == status)
    q = q.order_by(m.Task.updated_at.desc())
    items, next_cursor, total = paginate(q, limit, cursor)
    return ok(request, {"items": [ser.task(t) for t in items], "next_cursor": next_cursor, "total": total})


class TaskCreateBody(BaseModel):
    conversation_id: str | None = None
    goal: str
    plan: dict
    authorization_mode: str
    context_scope: dict | None = None


@router.post("/tasks")
def create_task(body: TaskCreateBody, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    if body.authorization_mode not in AUTH_MODES:
        raise ApiError(422, "VALIDATION_ERROR", "authorization_mode must be one of confirm_every_step, confirm_milestones, confirm_before_send.")
    plan_steps = (body.plan or {}).get("steps")
    if not isinstance(plan_steps, list) or not plan_steps:
        raise ApiError(422, "VALIDATION_ERROR", "A confirmed plan with at least one step is required. Tasks are never created from an unconfirmed plan.")
    if body.conversation_id:
        conv = db.get(m.AgentConversation, body.conversation_id)
        if conv is None or conv.user_id != user.id:
            raise ApiError(404, "NOT_FOUND", "Conversation not found.")
    idem_key = request.headers.get("idempotency-key")
    prior = idempotency_lookup(db, user.id, idem_key, "task.create")
    if prior is not None:
        return ok(request, prior, status=201)
    account = (
        db.query(m.MailAccount)
        .filter(m.MailAccount.user_id == user.id, m.MailAccount.deleted_at.is_(None))
        .order_by(m.MailAccount.created_at)
        .first()
    )
    task = m.Task(
        display_id=tasks_svc.next_display_id(db, user),
        user_id=user.id,
        conversation_id=body.conversation_id,
        goal=body.goal.strip(),
        status="queued",
        authorization_mode=body.authorization_mode,
        plan_json=body.plan,
        context_scope=body.context_scope or {},
        environment=account.environment if account else "demo",
    )
    db.add(task)
    db.flush()
    steps = []
    for i, s in enumerate(plan_steps[:20], start=1):
        if not isinstance(s, dict):
            continue
        input_refs = dict(s.get("input_refs") or {})
        if s.get("milestone"):
            input_refs["milestone"] = True
        step = m.TaskStep(
            task_id=task.id,
            sequence=i,
            step_type=str(s.get("step_type") or "custom_internal"),
            title=str(s.get("title") or "Step")[:200],
            description=str(s.get("description") or "")[:500],
            input_refs=input_refs,
            status="pending",
            risk_level=s.get("risk_level") if s.get("risk_level") in {"low", "medium", "high"} else "low",
            requires_approval=bool(s.get("requires_approval", False)),
            idempotency_key=f"{task.display_id}-{i}",
        )
        db.add(step)
        steps.append(step)
    db.commit()
    db.refresh(task)
    tasks_svc.emit_task_event(db, task, "task.created", {"status": "queued", "goal": task.goal})
    tasks_svc.emit_task_event(db, task, "task.queued", {"position": 1})
    audit(db, user, "task.created", "task", task.id, request=request, environment=task.environment)
    db.commit()
    payload = {"task": ser.task(task), "steps": [ser.task_step(s) for s in steps]}
    idempotency_store(db, user.id, idem_key, "task.create", {"goal": task.goal}, payload)
    return ok(request, payload, status=201)


@router.get("/tasks/{task_id}")
def get_task(task_id: str, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    task = _own_task(db, user, task_id)
    steps = _steps(db, task)
    events = (
        db.query(m.TaskEvent)
        .filter(m.TaskEvent.task_id == task.id)
        .order_by(m.TaskEvent.sequence.desc())
        .limit(50)
        .all()
    )
    outputs = (
        db.query(m.ReviewItem).filter(m.ReviewItem.task_id == task.id).all()
    )
    return ok(request, {
        "task": ser.task(task),
        "steps": [ser.task_step(s) for s in steps],
        "latest_events": [ser.task_event(e) for e in reversed(events)],
        "outputs": [ser.review_item(o) for o in outputs],
    })


@router.get("/tasks/{task_id}/events")
def task_events(task_id: str, request: Request, after_sequence: int = 0, limit: int = 100,
                db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    task = _own_task(db, user, task_id)
    events = (
        db.query(m.TaskEvent)
        .filter(m.TaskEvent.task_id == task.id, m.TaskEvent.sequence > after_sequence)
        .order_by(m.TaskEvent.sequence)
        .limit(min(limit, 500))
        .all()
    )
    next_seq = events[-1].sequence if events else after_sequence
    return ok(request, {"items": [ser.task_event(e) for e in events], "next_sequence": next_seq})


@router.post("/tasks/{task_id}/pause")
def pause_task(task_id: str, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    task = _own_task(db, user, task_id)
    if task.status not in {"queued", "running", "waiting_user"}:
        raise ApiError(409, "INVALID_TRANSITION", f"A task in state {task.status} cannot be paused.")
    task.status = "paused"
    db.commit()
    tasks_svc.emit_task_event(db, task, "task.paused", {"reason": "user"})
    audit(db, user, "task.paused", "task", task.id, request=request, environment=task.environment)
    db.commit()
    return ok(request, {"task": ser.task(task)})


class ResumeBody(BaseModel):
    acknowledge_summary: bool = False


@router.post("/tasks/{task_id}/resume")
def resume_task(task_id: str, body: ResumeBody, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    task = _own_task(db, user, task_id)
    if task.status not in {"paused", "needs_attention"}:
        raise ApiError(409, "INVALID_TRANSITION", f"A task in state {task.status} cannot be resumed.")
    if not body.acknowledge_summary:
        raise ApiError(422, "VALIDATION_ERROR", "acknowledge_summary=true is required so the resume summary is confirmed.")
    task.status = "running"
    db.commit()
    tasks_svc.emit_task_event(db, task, "task.resumed", {"resumed_at": m.now().isoformat()})
    audit(db, user, "task.resumed", "task", task.id, request=request, environment=task.environment)
    db.commit()
    return ok(request, {"task": ser.task(task)})


@router.post("/tasks/{task_id}/takeover")
def takeover_task(task_id: str, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    task = _own_task(db, user, task_id)
    if task.status not in {"running", "waiting_user", "paused"}:
        raise ApiError(409, "INVALID_TRANSITION", f"A task in state {task.status} cannot be taken over.")
    task.status = "takeover"
    task.execution_lock = "user"
    db.commit()
    tasks_svc.emit_task_event(db, task, "task.takeover", {"lock_owner": "user"})
    audit(db, user, "task.takeover", "task", task.id, request=request, environment=task.environment)
    db.commit()
    return ok(request, {"task": ser.task(task), "edit_lock": "user"})


class ReturnControlBody(BaseModel):
    resume_with_updated_context: bool = True
    change_summary: str | None = None


@router.post("/tasks/{task_id}/return-control")
def return_control(task_id: str, body: ReturnControlBody, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    task = _own_task(db, user, task_id)
    if task.status != "takeover":
        raise ApiError(409, "INVALID_TRANSITION", "Only a task in takeover can return control to the Agent.")
    task.execution_lock = None
    task.status = "running" if body.resume_with_updated_context else "paused"
    db.commit()
    tasks_svc.emit_task_event(db, task, "task.log.appended", {
        "level": "info",
        "message": f"Control returned to the Agent. Manual changes: {body.change_summary or 'none reported'}",
    })
    if body.resume_with_updated_context:
        tasks_svc.emit_task_event(db, task, "task.resumed", {"resumed_at": m.now().isoformat()})
    audit(db, user, "task.return_control", "task", task.id, request=request, environment=task.environment)
    db.commit()
    return ok(request, {"task": ser.task(task)})


class TerminateBody(BaseModel):
    confirmation: bool = False
    reason: str | None = None


@router.post("/tasks/{task_id}/terminate")
def terminate_task(task_id: str, body: TerminateBody, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    task = _own_task(db, user, task_id)
    if task.status in TERMINAL:
        raise ApiError(409, "INVALID_TRANSITION", f"A task in state {task.status} cannot be terminated.")
    if not body.confirmation:
        raise ApiError(422, "VALIDATION_ERROR", "confirmation=true is required to terminate a task.")
    steps = _steps(db, task)
    completed = [s.sequence for s in steps if s.status == "completed"]
    for s in steps:
        if s.status in {"pending", "ready", "waiting_user", "running"}:
            s.status = "cancelled"
    task.status = "cancelled"
    task.execution_lock = None
    db.commit()
    summary = {"completed_steps": completed, "side_effects": ["Drafts and to-dos already created remain available."]}
    tasks_svc.emit_task_event(db, task, "task.terminated", summary)
    audit(db, user, "task.terminated", "task", task.id, request=request, environment=task.environment,
          meta={"reason": body.reason})
    db.commit()
    return ok(request, {"task": ser.task(task), "side_effect_summary": summary})


class RetryBody(BaseModel):
    step_id: str | None = None
    confirm_retry: bool = False


@router.post("/tasks/{task_id}/retry")
def retry_task(task_id: str, body: RetryBody, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    task = _own_task(db, user, task_id)
    if not body.confirm_retry:
        raise ApiError(422, "VALIDATION_ERROR", "confirm_retry=true is required.")
    steps = _steps(db, task)
    target = None
    for s in steps:
        if body.step_id and s.id == body.step_id:
            target = s
            break
        if target is None and s.status == "failed":
            target = s
    if target is None or target.status != "failed":
        raise ApiError(409, "INVALID_TRANSITION", "No failed step is available to retry.")
    target.status = "pending"
    target.retry_count += 1
    target.error_code = None
    target.started_at = None
    target.completed_at = None
    if task.status == "failed":
        task.status = "running"
        task.error_code = None
    db.commit()
    tasks_svc.emit_task_event(db, task, "task.log.appended",
                              {"level": "info", "message": f"Step {target.sequence} ({target.title}) queued for retry."})
    audit(db, user, "task.step_retried", "task", task.id, request=request, environment=task.environment)
    db.commit()
    return ok(request, {"task": ser.task(task), "step": ser.task_step(target)})


# --------------------------------------------------------------- decisions

@router.get("/decisions")
def list_decisions(request: Request, status: str | None = None, task_id: str | None = None,
                   db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    q = db.query(m.Decision).filter(m.Decision.user_id == user.id)
    if status:
        q = q.filter(m.Decision.status == status)
    if task_id:
        q = q.filter(m.Decision.task_id == task_id)
    items = q.order_by(m.Decision.created_at.desc()).limit(100).all()
    return ok(request, {"items": [ser.decision(d) for d in items]})


class ResolveBody(BaseModel):
    choice: str
    comment: str | None = None
    revision: int | None = None


@router.post("/decisions/{decision_id}/resolve")
def resolve_decision(decision_id: str, body: ResolveBody, request: Request, db: DbSession = Depends(get_db), user: m.User = Depends(get_current_user)):
    decision = db.get(m.Decision, decision_id)
    if decision is None or decision.user_id != user.id:
        raise ApiError(404, "NOT_FOUND", "Decision not found.")
    task = db.get(m.Task, decision.task_id)
    if decision.status != "pending":
        # Single-use decisions: repeated resolution returns the original result.
        return ok(request, {"decision": ser.decision(decision), "task": ser.task(task) if task else None})
    step = db.get(m.TaskStep, decision.step_id) if decision.step_id else None
    choice = body.choice

    if decision.decision_type == "choose_option":
        options = decision.options or []
        match = next((o for o in options if o.get("value") == choice), None)
        if match is None:
            raise ApiError(422, "VALIDATION_ERROR", "Choice must be one of the decision options.")
        decision.status = "approved"
        decision.response = {"choice": choice, "label": match.get("label"), "comment": body.comment}
        decision.resolved_at = m.now()
        if step is not None:
            step.status = "completed"
            step.completed_at = m.now()
            step.output_refs = {**(step.output_refs or {}), "choice": choice, "chosen_option_label": match.get("label")}
            # Pass the choice forward so the draft step can use it.
            steps = _steps(db, task) if task else []
            for later in steps:
                if later.sequence > step.sequence and later.step_type == "draft_email":
                    later.input_refs = {**(later.input_refs or {}), "chosen_option_label": match.get("label")}
        if task is not None and task.status == "waiting_user":
            task.status = "running"
        db.commit()
        if task is not None:
            tasks_svc.emit_task_event(db, task, "task.log.appended",
                                      {"level": "info", "message": f"Decision made: {match.get('label')}"})
            tasks_svc.emit_task_event(db, task, "task.resumed", {"resumed_at": m.now().isoformat()})
    elif choice in {"approve", "approved"}:
        decision.status = "approved"
        decision.response = {"choice": "approved", "comment": body.comment}
        decision.resolved_at = m.now()
        if task is not None and task.status == "waiting_user":
            task.status = "running"
        db.commit()
        if task is not None:
            tasks_svc.emit_task_event(db, task, "task.log.appended",
                                      {"level": "info", "message": "Step approved by user."})
            tasks_svc.emit_task_event(db, task, "task.resumed", {"resumed_at": m.now().isoformat()})
    elif choice in {"reject", "rejected"}:
        decision.status = "rejected"
        decision.response = {"choice": "rejected", "comment": body.comment}
        decision.resolved_at = m.now()
        if step is not None:
            step.status = "pending"
            step.approval_id = None
        if task is not None and task.status not in TERMINAL:
            # Rejecting a step pauses the task (spec 6.2 Mode A).
            task.status = "paused"
        db.commit()
        if task is not None:
            tasks_svc.emit_task_event(db, task, "task.paused", {"reason": "step_rejected"})
    else:
        raise ApiError(422, "VALIDATION_ERROR", "Choice must be approve or reject for this decision.")
    audit(db, user, "decision.resolved", "decision", decision.id, request=request,
          environment=task.environment if task else "demo", meta={"status": decision.status})
    db.commit()
    db.refresh(decision)
    return ok(request, {"decision": ser.decision(decision), "task": ser.task(task) if task else None})
