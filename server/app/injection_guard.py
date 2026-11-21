"""Prompt-injection guard for untrusted email content.

Email is external input: a sender can write anything into a subject, body,
display name or attachment filename, including text crafted to look like
instructions to the Agent, a fake system turn, or a fake user approval.
This module is the single line of defence that treats that content as data:

- ``detect`` runs heuristic pattern checks over the subject, body, sender
  display name and attachment filenames and returns structured flags.
- ``scan_message`` / ``ensure_scanned`` persist the result on the message
  (``injection_flags`` / ``injection_suspect``) and roll the thread flag up.
- Flagged mail stays fully readable, but it is excluded from every
  automatic processing path (agent auto-context matching, automation
  runs). Nothing here ever blocks the user from reading or acting
  manually; agent outputs still land in the Review Queue as before.
- ``wrap_message_block`` is the only sanctioned way to embed an email in
  an LLM prompt: explicit data delimiters, with delimiter spoofs inside
  the body defanged so content cannot break out of its block.
"""
from __future__ import annotations

import re

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session as DbSession

from . import models as m

# ---------------------------------------------------------------------------
# Prompt delimiters
# ---------------------------------------------------------------------------

DATA_OPEN = "<<<UNTRUSTED_EMAIL_DATA"
DATA_CLOSE = "<<<END_UNTRUSTED_EMAIL_DATA>>>"

_DELIMITER_SPOOF_RE = re.compile(r"<<<\s*(END_)?UNTRUSTED_EMAIL_DATA\s*>>>?", re.IGNORECASE)
_LEGACY_HEADER_RE = re.compile(r"(?m)^--- message\s", re.IGNORECASE)


def defang_body(body: str) -> str:
    """Neutralise text inside an email body that could break the prompt
    framing: our own delimiter markers and the legacy per-message header
    shape, so a body cannot fake the end of its data block or the start
    of a second message."""
    out = _DELIMITER_SPOOF_RE.sub("[delimiter removed]", body or "")
    out = _LEGACY_HEADER_RE.sub("---message ", out)
    return out


def wrap_message_block(msg: "m.EmailMessage", body: str) -> str:
    """Embed one message in an LLM prompt as a delimited data block."""
    sender = f"{msg.from_name or ''} <{msg.from_address}>".strip()
    return (
        f"{DATA_OPEN} message_id={msg.id}>>>\n"
        f"From: {sender}\n"
        f"Subject: {msg.subject or ''}\n"
        f"\n{defang_body(body)}\n"
        f"{DATA_CLOSE}"
    )


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

# Each entry: (pattern id, regex, human-readable reason). Patterns are
# deliberately narrow: they target text that addresses the *agent* or the
# mailbox machinery (override commands, fake turns, fake approvals,
# mail-redistribution lures, secrecy lures), not ordinary business asks
# such as "please confirm the total" or "send the contract to legal".
_PATTERNS: list[tuple[str, re.Pattern, str]] = [
    (
        "override_instructions",
        re.compile(
            r"ignore\s+(all\s+|the\s+)?(previous|prior|above|earlier|preceding)\s+"
            r"(instructions?|directions?|prompts?|rules|commands)"
            r"|disregard\s+(all\s+|the\s+|your\s+)?(previous\s+|prior\s+)?"
            r"(instructions?|directions?|prompts?|system\s+prompt)"
            r"|forget\s+(your\s+|all\s+|the\s+)?(instructions?|rules|system\s+prompt)"
            r"|(override|bypass)\s+(your\s+)?(instructions?|safety\s+rules|restrictions)"
            r"|new\s+instructions?\s*(for\s+you\s*)?[:\-]",
            re.IGNORECASE,
        ),
        "Tells the reader to ignore or override prior instructions",
    ),
    (
        "fake_role_turn",
        re.compile(
            r"^\s*(system|assistant|developer)\s*:\s+\S"
            r"|<\s*/?\s*(system|instructions)\s*>"
            r"|\[\s*(system|inst)\s*\]"
            r"|#{2,}\s*(system|instructions?)\b"
            r"|\b(begin|end)\s+of\s+(the\s+)?system\s+prompt\b",
            re.IGNORECASE | re.MULTILINE,
        ),
        "Contains a fake system/assistant turn or prompt marker",
    ),
    (
        "fake_context_boundary",
        re.compile(r"<<<\s*(END_)?UNTRUSTED|^---\s*message\s+\S+\s*\|", re.IGNORECASE | re.MULTILINE),
        "Tries to spoof the prompt's data delimiters or message boundaries",
    ),
    (
        "agent_addressed",
        re.compile(
            r"\b(dear|attention|hey|hello)\s+(ai|agent|assistant|intenda|chatbot|bot)\b"
            r"|\b(ai|intenda)\s+(agent|assistant)\s*[:,]"
            r"|\bimportant\s+instruction\s+for\s+(ai|the\s+agent|assistants?)\b"
            r"|\byou\s+are\s+(now\s+)?(an?\s+)?(ai|assistant|agent|language\s+model)\b"
            r"|\binstruction\s+for\s+(ai\s+)?assistants?\b",
            re.IGNORECASE,
        ),
        "Addresses instructions to an AI agent or assistant",
    ),
    (
        "mailbox_action_lure",
        re.compile(
            r"\b(forward|send|copy|relay|bcc)\s+(this|the|all|every)\s+"
            r"(thread|e-?mail|message|conversation|mailbox|inbox)\b"
            r"|\b(forward|send|copy|relay)\b[^.\n]{0,60}?\bto\s+<?[\w.+-]+@[\w-]+\.[\w.]+"
            r"|\b(delete|archive|erase|wipe|empty)\s+(all|every|the\s+entire|my\s+entire)\s+"
            r"(e-?mails?|messages?|threads?|inbox|mailbox)\b"
            r"|\b(send|reveal|share|leak|exfiltrate|upload)\b[^.\n]{0,50}?"
            r"\b(passwords?|credentials?|api\s*keys?|secret\s*keys?|tokens?|address\s+book|system\s+prompt)\b",
            re.IGNORECASE,
        ),
        "Asks for this mail, the mailbox, or secrets to be sent on or destroyed",
    ),
    (
        "fake_approval",
        re.compile(
            r"\buser\s+(has\s+)?(already\s+)?(approved|confirmed|authorized|authorised)\b"
            r"|\bapproval\s+(has\s+been\s+)?(granted|given|confirmed)\b"
            r"|\b(pre[-\s]?approved|already\s+approved)\b"
            r"|\bskip\s+(the\s+)?(review|approval|confirmation)\b"
            r"|\bno\s+need\s+to\s+(ask|wait|get)\b[^.\n]{0,40}?\b(approv\w+|confirm\w+|permission)\b"
            r"|\bbypass\s+(the\s+)?(review|approval)\b",
            re.IGNORECASE,
        ),
        "Claims the user already approved, or asks to skip review/approval",
    ),
    (
        "secrecy_lure",
        re.compile(
            r"\b(do\s+not|don'?t|never)\s+(tell|inform|notify)\s+(the\s+)?(user|owner|human|anyone)\b"
            r"|\bdo\s+not\s+mention\s+this\s+(to|in)\b"
            r"|\bwithout\s+(telling|informing|notifying)\s+(the\s+)?(user|owner|anyone)\b"
            r"|\bkeep\s+this\s+(secret|hidden)\s+from\b",
            re.IGNORECASE,
        ),
        "Asks for the action to be hidden from the user",
    ),
]

_ZERO_WIDTH_RE = re.compile("[\u200b\u200c\u200d\u2060\ufeff\u202a-\u202e]")
_ZERO_WIDTH_MIN = 3


def _scan_text(field: str, text_value: str | None, flags: list[dict], seen: set) -> None:
    if not text_value:
        return
    for pattern_id, regex, reason in _PATTERNS:
        match = regex.search(text_value)
        if match and (field, pattern_id) not in seen:
            seen.add((field, pattern_id))
            flags.append({
                "field": field,
                "pattern": pattern_id,
                "reason": reason,
                "excerpt": " ".join(match.group(0).split())[:80],
            })


def detect(
    *,
    subject: str | None = None,
    body: str | None = None,
    from_name: str | None = None,
    attachment_filenames: list[str] | None = None,
) -> list[dict]:
    """Run the heuristic detector over the untrusted fields of a message.
    Returns a list of flags: {field, pattern, reason, excerpt}."""
    flags: list[dict] = []
    seen: set = set()
    _scan_text("subject", subject, flags, seen)
    _scan_text("from_name", from_name, flags, seen)
    _scan_text("body", body, flags, seen)
    if body and len(_ZERO_WIDTH_RE.findall(body)) >= _ZERO_WIDTH_MIN:
        flags.append({
            "field": "body",
            "pattern": "hidden_characters",
            "reason": "Body contains hidden zero-width or direction-override characters",
            "excerpt": "",
        })
    for name in attachment_filenames or []:
        # Filenames smuggle instructions with separators: normalise
        # "ignore_previous_instructions.pdf" before matching.
        normalized = re.sub(r"[_\-]+", " ", name or "")
        _scan_text("attachment", normalized, flags, seen)
    return flags


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def refresh_thread_suspect(db: DbSession, thread_id: str | None) -> None:
    """Roll the message-level flags up to the thread row."""
    if not thread_id:
        return
    thread = db.get(m.EmailThread, thread_id)
    if thread is None:
        return
    hit = (
        db.query(m.EmailMessage.id)
        .filter(
            m.EmailMessage.thread_id == thread_id,
            m.EmailMessage.injection_suspect.is_(True),
        )
        .first()
    )
    thread.injection_suspect = hit is not None


def scan_message(db: DbSession, msg: m.EmailMessage) -> list[dict]:
    """Scan one message now and persist the verdict. First-party mail
    (sent/drafts authored in this workspace) is marked scanned-clean
    without running the detector: it is not external input."""
    if msg.is_sent or msg.is_draft:
        msg.injection_flags = []
        msg.injection_suspect = False
        db.flush()
        refresh_thread_suspect(db, msg.thread_id)
        return []
    filenames = [
        a.filename
        for a in db.query(m.EmailAttachment).filter(
            m.EmailAttachment.message_id == msg.id
        ).all()
    ]
    flags = detect(
        subject=msg.subject,
        body=msg.body_text,
        from_name=msg.from_name,
        attachment_filenames=filenames,
    )
    msg.injection_flags = flags
    msg.injection_suspect = bool(flags)
    db.flush()
    refresh_thread_suspect(db, msg.thread_id)
    return flags


def ensure_scanned(db: DbSession, msg: m.EmailMessage) -> bool:
    """Scan ``msg`` if it has never been scanned (``injection_flags`` is
    NULL). Returns True when the row changed. Used as a lazy backstop for
    mail that predates the guard or arrived through a path that did not
    scan at ingest."""
    if msg.injection_flags is not None:
        return False
    scan_message(db, msg)
    return True


def ensure_thread_scanned(db: DbSession, thread_id: str | None) -> bool:
    """Lazy backstop for a whole thread: scan any unscanned messages and
    refresh the thread flag. Returns True when anything changed."""
    if not thread_id:
        return False
    changed = False
    messages = (
        db.query(m.EmailMessage)
        .filter(m.EmailMessage.thread_id == thread_id)
        .all()
    )
    for msg in messages:
        if ensure_scanned(db, msg):
            changed = True
    refresh_thread_suspect(db, thread_id)
    return changed


# ---------------------------------------------------------------------------
# Schema backstop
# ---------------------------------------------------------------------------


def ensure_columns(engine) -> None:
    """Add the guard columns to pre-existing databases. The schema is
    managed by create_all, which never alters existing tables, so a
    database created before this guard shipped would otherwise lack the
    columns. SQLite-only and idempotent."""
    inspector = inspect(engine)
    if "email_messages" not in inspector.get_table_names():
        return
    msg_cols = {c["name"] for c in inspector.get_columns("email_messages")}
    thread_cols = {c["name"] for c in inspector.get_columns("email_threads")}
    with engine.begin() as conn:
        if "injection_suspect" not in msg_cols:
            conn.execute(text(
                "ALTER TABLE email_messages ADD COLUMN injection_suspect BOOLEAN NOT NULL DEFAULT 0"
            ))
        if "injection_flags" not in msg_cols:
            conn.execute(text("ALTER TABLE email_messages ADD COLUMN injection_flags JSON"))
        if "injection_suspect" not in thread_cols:
            conn.execute(text(
                "ALTER TABLE email_threads ADD COLUMN injection_suspect BOOLEAN NOT NULL DEFAULT 0"
            ))
