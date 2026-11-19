"""Sync job creation (demo sync is simulated and labelled; spec 4.9)."""
from __future__ import annotations

from sqlalchemy.orm import Session as DbSession

from .. import models as m


def start_sync(db: DbSession, user: m.User, account: m.MailAccount, mode: str = "incremental") -> m.SyncJob:
    running = (
        db.query(m.SyncJob)
        .filter(m.SyncJob.mail_account_id == account.id, m.SyncJob.status == "running")
        .first()
    )
    if running is not None:
        return running
    total = (
        db.query(m.EmailMessage)
        .filter(m.EmailMessage.mail_account_id == account.id)
        .count()
    )
    job = m.SyncJob(
        user_id=user.id,
        mail_account_id=account.id,
        mode=mode,
        environment=account.environment,
        status="running",
        phase="connecting",
        processed_count=0,
        total_count=total,
        cursor_before=account.sync_cursor,
        started_at=m.now(),
    )
    account.status = "syncing"
    db.add(job)
    db.commit()
    db.refresh(job)
    return job
