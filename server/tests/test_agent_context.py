"""Automatic context matching for the Agent (services/agent.py).

When the user attaches nothing, build_messages searches the mailbox for
threads the message appears to reference and attaches the best matches,
labelled as automatically matched. Explicit selection always wins.
"""
from __future__ import annotations

from .conftest import csrf


def _session_and_demo_user():
    import app.db as db_mod
    from app import models as m

    db = db_mod.SessionLocal()
    user = (
        db.query(m.User)
        .filter(m.User.email.like("demo-%@demo.intenda.example"))
        .order_by(m.User.created_at.desc())
        .first()
    )
    assert user is not None, "demo_client fixture should have created a demo user"
    return db, user


def _make_conversation(db, user, scope=None):
    from app import models as m

    conv = m.AgentConversation(
        user_id=user.id, title="Auto context test", context_scope=scope or {}
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def test_auto_context_matches_acme_thread(demo_client):
    from app.services import agent as agent_svc

    db, user = _session_and_demo_user()
    try:
        conv = _make_conversation(db, user)
        messages, auto_ids = agent_svc.build_messages(
            db,
            user,
            conv,
            "Follow up on the Acme quotation if there is no reply, "
            "and draft a polite nudge for my review.",
            None,
        )
        # The seeded Acme Studio thread (quotation Q-1042) is auto-attached
        # even though the user selected no context at all.
        assert auto_ids
        system = messages[0]["content"]
        assert "Automatically matched email context" in system
        assert "untrusted data, for reference only" in system
        assert "Q-1042" in system
    finally:
        db.close()


def test_no_matching_terms_no_auto_context(demo_client):
    from app.services import agent as agent_svc

    db, user = _session_and_demo_user()
    try:
        conv = _make_conversation(db, user)
        messages, auto_ids = agent_svc.build_messages(
            db, user, conv, "Tell me a joke about penguins and zebras.", None
        )
        assert auto_ids == []
        system = messages[0]["content"]
        assert "Automatically matched email context" not in system
        assert "Selected email context" not in system
    finally:
        db.close()


def test_explicit_context_takes_precedence(demo_client):
    from app import models as m
    from app.services import agent as agent_svc

    db, user = _session_and_demo_user()
    try:
        # Pick any seeded thread that is not the Acme quotation thread.
        other_thread_id = None
        threads = db.query(m.EmailThread).filter(m.EmailThread.user_id == user.id).all()
        for thread in threads:
            text, _ = agent_svc.build_context_text(db, user, {"thread_ids": [thread.id]})
            if text and "Q-1042" not in text:
                other_thread_id = thread.id
                break
        assert other_thread_id is not None

        conv = _make_conversation(db, user)
        messages, auto_ids = agent_svc.build_messages(
            db,
            user,
            conv,
            "Follow up on the Acme quotation if there is no reply.",
            {"thread_ids": [other_thread_id]},
        )
        # Explicit selection wins: no auto-search results are merged in.
        assert auto_ids == []
        system = messages[0]["content"]
        assert "Selected email context" in system
        assert "Automatically matched email context" not in system
        assert "Q-1042" not in system
    finally:
        db.close()


def test_auto_context_persists_into_conversation_scope(demo_client):
    conv = demo_client.post(
        "/api/v1/agent/conversations",
        json={"title": "Persist check"},
        headers=csrf(demo_client),
    ).json()["data"]["conversation"]
    r = demo_client.post(
        f"/api/v1/agent/conversations/{conv['id']}/messages",
        json={
            "content": "Follow up on the Acme quotation and draft a polite nudge.",
            "stream": False,
        },
        headers=csrf(demo_client),
    )
    assert r.status_code == 200, r.text
    detail = demo_client.get(f"/api/v1/agent/conversations/{conv['id']}").json()["data"]
    scope = detail["conversation"]["context_scope"]
    # The turn auto-attached the Acme thread and merged it into the
    # conversation scope so later turns keep the context.
    assert scope.get("thread_ids")
