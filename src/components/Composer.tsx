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

export default function Composer({
  opts,
  onClose,
}: {
  opts: ComposerOpts;
  onClose: () => void;
}) {
  const toast = useToast();
  const [to, setTo] = useState(opts.initial?.to ?? '');
  const [cc, setCc] = useState('');
  const [subject, setSubject] = useState(opts.initial?.subject ?? '');
  const [body, setBody] = useState(opts.initial?.body ?? '');
  const [draftId, setDraftId] = useState<string | null>(opts.draftId ?? null);
  const [revision, setRevision] = useState<number>(1);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let alive = true;
    const load = async () => {
      try {
        if (opts.draftId) {
          setLoading(true);
          const d = await api<{ draft: Draft }>(`/api/v1/drafts/${opts.draftId}`);
          if (!alive) return;
          setTo(d.draft.to.map((r) => r.email).join(', '));
          setCc(d.draft.cc.map((r) => r.email).join(', '));
          setSubject(d.draft.subject);
          setBody(d.draft.body_text);
          setRevision(d.draft.revision);
        } else if (opts.messageId && opts.mode && opts.mode !== 'new') {
          setLoading(true);
          const d = await api<{ draft: any }>(
            `/api/v1/mail/messages/${opts.messageId}/reply-draft?mode=${opts.mode}`,
          );
          if (!alive) return;
          setTo((d.draft.to ?? []).map((r: any) => r.email).join(', '));
          setCc((d.draft.cc ?? []).map((r: any) => r.email).join(', '));
          setSubject(d.draft.subject ?? '');
          setBody(d.draft.body_text ?? '');
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
  }, [opts.draftId, opts.messageId, opts.mode]);

  const payload = () => ({
    to: parseEmails(to),
    cc: parseEmails(cc),
    subject: subject.trim(),
    body_text: body,
  });

  const saveDraft = async (): Promise<string | null> => {
    if (draftId) {
      const d = await api<{ draft: Draft }>(`/api/v1/drafts/${draftId}`, {
        method: 'PATCH',
        body: { ...payload(), revision },
      });
      setRevision(d.draft.revision);
      return draftId;
    }
    const d = await api<{ draft: Draft }>('/api/v1/drafts', { method: 'POST', body: payload() });
    setDraftId(d.draft.id);
    setRevision(d.draft.revision);
    return d.draft.id;
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
      let notice: string | undefined;
      if (draftId) {
        await saveDraft();
        const r = await api<{ notice: string }>(`/api/v1/drafts/${draftId}/send`, {
          method: 'POST',
          body: { confirm_send: true },
          idempotencyKey: idemKey(),
        });
        notice = r.notice;
      } else {
        const r = await api<{ notice: string }>('/api/v1/mail/compose', {
          method: 'POST',
          body: { ...payload(), confirm_send: true },
          idempotencyKey: idemKey(),
        });
        notice = r.notice;
      }
      toast({ text: notice ?? 'Message sent.' });
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
        : opts.mode === 'forward'
          ? 'Forward'
          : draftId
            ? 'Edit draft'
            : 'New message';

  return (
    <Modal title={title} sub="Demo mailbox sends are simulated and stored in Sent — no external email is delivered." onClose={onClose}>
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
          <div className="field">
            <label htmlFor="cmp-subject">Subject</label>
            <input id="cmp-subject" value={subject} onChange={(e) => setSubject(e.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="cmp-body">Message</label>
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
