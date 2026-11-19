import { useEffect, useState } from 'react';
import { api, idemKey, type Draft } from '../lib/api';
import type { ComposerOpts } from '../lib/appctx';
import { ErrorCard, Modal, useToast } from '../lib/ui';

function parseEmails(value: string): { email: string }[] {
  return value
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
    .map((email) => ({ email }));
}

function joinEmails(list: { email: string }[]): string {
  return list.map((r) => r.email).join(', ');
}

export default function Composer({
  opts,
  onClose,
}: {
  opts: ComposerOpts;
  onClose: () => void;
}) {
  const toast = useToast();
  const isForward = opts.mode === 'forward';
  const [to, setTo] = useState(opts.initial?.to ?? '');
  const [cc, setCc] = useState('');
  const [subject, setSubject] = useState(opts.initial?.subject ?? '');
  const [body, setBody] = useState(opts.initial?.body ?? '');
  const [draftId, setDraftId] = useState<string | null>(opts.draftId ?? null);
  const [messageId, setMessageId] = useState<string | null>(null);
  const [revision, setRevision] = useState<number>(1);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);

  const adoptDraft = (d: Draft) => {
    setDraftId(d.id);
    setMessageId(d.message_id);
    setRevision(d.revision);
    setTo(joinEmails(d.to_recipients));
    setCc(joinEmails(d.cc_recipients));
    setSubject(d.subject);
    setBody(d.body_text);
  };

  useEffect(() => {
    let alive = true;
    const load = async () => {
      try {
        if (opts.draftId) {
          setLoading(true);
          const d = await api<{ draft: Draft }>(`/api/v1/drafts/${opts.draftId}`);
          if (alive) adoptDraft(d.draft);
        } else if (opts.messageId && (opts.mode === 'reply' || opts.mode === 'reply_all')) {
          // The server creates the reply draft (recipients + quoted context).
          setLoading(true);
          const d = await api<{ draft: Draft }>(`/api/v1/emails/${opts.messageId}/reply`, {
            method: 'POST',
            body: { reply_all: opts.mode === 'reply_all', body: '' },
          });
          if (alive) adoptDraft(d.draft);
        } else if (opts.messageId && opts.mode === 'forward') {
          setLoading(true);
          const d = await api<{ message: any }>(`/api/v1/emails/${opts.messageId}`);
          if (alive) {
            const subj: string = d.message.subject ?? '';
            setSubject(subj.toLowerCase().startsWith('fwd:') ? subj : `Fwd: ${subj}`);
          }
        }
      } catch (e) {
        if (alive) setError(e);
      } finally {
        if (alive) setLoading(false);
      }
    };
    load();
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opts.draftId, opts.messageId, opts.mode]);

  const createDraft = async (): Promise<Draft> => {
    if (isForward && opts.messageId) {
      const d = await api<{ draft: Draft }>(`/api/v1/emails/${opts.messageId}/forward`, {
        method: 'POST',
        body: { to: parseEmails(to), cc: parseEmails(cc), body },
      });
      return d.draft;
    }
    const d = await api<{ draft: Draft }>('/api/v1/drafts', {
      method: 'POST',
      body: { to: parseEmails(to), cc: parseEmails(cc), subject: subject.trim(), body },
    });
    return d.draft;
  };

  const saveDraft = async (): Promise<Draft> => {
    if (draftId) {
      const d = await api<{ draft: Draft }>(`/api/v1/drafts/${draftId}`, {
        method: 'PATCH',
        body: { revision, to: parseEmails(to), cc: parseEmails(cc), subject: subject.trim(), body },
      });
      setRevision(d.draft.revision);
      setMessageId(d.draft.message_id);
      return d.draft;
    }
    const d = await createDraft();
    adoptDraftAfterCreate(d);
    return d;
  };

  const adoptDraftAfterCreate = (d: Draft) => {
    setDraftId(d.id);
    setMessageId(d.message_id);
    setRevision(d.revision);
    if (isForward) {
      // The server composed the full forwarded body; keep the editor in sync.
      setBody(d.body_text);
      setSubject(d.subject);
    }
  };

  const onSave = async () => {
    setBusy(true);
    setError(null);
    try {
      await saveDraft();
      toast({ text: 'Draft saved.' });
      opts.onDone?.();
      onClose();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  const onSend = async () => {
    if (parseEmails(to).length === 0) {
      setError(new Error('Add at least one recipient.'));
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const draft = await saveDraft();
      if (!draft.message_id) throw new Error('Draft has no message to send.');
      const r = await api<{ send_result: { notice: string } }>(`/api/v1/emails/${draft.message_id}/send`, {
        method: 'POST',
        body: { draft_id: draft.id, revision: draft.revision, confirm_send: true },
        idempotencyKey: idemKey(),
      });
      toast({ text: r.send_result.notice });
      opts.onDone?.();
      onClose();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  const onDiscard = async () => {
    if (!draftId) {
      onClose();
      return;
    }
    setBusy(true);
    try {
      await api(`/api/v1/drafts/${draftId}`, { method: 'DELETE' });
      toast({ text: 'Draft discarded.' });
      opts.onDone?.();
      onClose();
    } catch (e) {
      setError(e);
      setBusy(false);
    }
  };

  const title =
    opts.mode === 'reply'
      ? 'Reply'
      : opts.mode === 'reply_all'
        ? 'Reply all'
        : isForward
          ? 'Forward'
          : draftId
            ? 'Edit draft'
            : 'New message';

  return (
    <Modal
      title={title}
      sub={
        isForward && !draftId
          ? 'Add recipients and an optional note. The original message is attached below your note when the draft is created. Demo sends are simulated.'
          : 'Demo mailbox sends are simulated and stored in Sent — no external email is delivered.'
      }
      onClose={onClose}
    >
      {error != null && <ErrorCard error={error} />}
      {loading ? (
        <div className="skeleton" style={{ height: 220 }} />
      ) : (
        <>
          <div className="field">
            <label htmlFor="cmp-to">To</label>
            <input id="cmp-to" value={to} onChange={(e) => setTo(e.target.value)} placeholder="name@example.com, other@example.com" />
          </div>
          <div className="field">
            <label htmlFor="cmp-cc">Cc (optional)</label>
            <input id="cmp-cc" value={cc} onChange={(e) => setCc(e.target.value)} />
          </div>
          {!isForward || draftId ? (
            <div className="field">
              <label htmlFor="cmp-subject">Subject</label>
              <input id="cmp-subject" value={subject} onChange={(e) => setSubject(e.target.value)} />
            </div>
          ) : (
            <div className="field">
              <label>Subject</label>
              <input value={subject} disabled />
            </div>
          )}
          <div className="field">
            <label htmlFor="cmp-body">{isForward && !draftId ? 'Your note (the forwarded message is added when saved)' : 'Message'}</label>
            <textarea id="cmp-body" rows={9} value={body} onChange={(e) => setBody(e.target.value)} />
          </div>
          <div className="btn-row" style={{ justifyContent: 'space-between' }}>
            <button className="btn btn-danger-ghost" onClick={onDiscard} disabled={busy}>
              Discard
            </button>
            <span style={{ display: 'flex', gap: 10 }}>
              <button className="btn btn-dark" onClick={onSave} disabled={busy}>
                Save draft
              </button>
              <button className="btn btn-primary" onClick={onSend} disabled={busy}>
                {busy ? 'Sending…' : 'Send'}
              </button>
            </span>
          </div>
        </>
      )}
    </Modal>
  );
}
