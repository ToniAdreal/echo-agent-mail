import { useEffect, useState } from 'react';
import { Mail, RotateCcw, ShieldAlert, Sparkles } from 'lucide-react';
import { api, type ReviewItem } from '../lib/api';
import { useApp } from '../lib/appctx';
import {
  EnvLabel,
  ErrorCard,
  SkeletonRows,
  errorText,
  navigate,
  timeAgo,
  useAsync,
  useToast,
} from '../lib/ui';
import { StatusPill } from './TaskProgress';

const FILTERS = [
  { id: 'pending', label: 'Pending' },
  { id: 'modified', label: 'Edited by you' },
  { id: 'approved', label: 'Approved' },
  { id: 'sent', label: 'Sent (simulated)' },
  { id: 'rejected', label: 'Rejected' },
  { id: 'all', label: 'All' },
] as const;

export default function Review() {
  const toast = useToast();
  const { refreshBadges } = useApp();
  const [filter, setFilter] = useState<string>('pending');
  const { data, error, loading, reload } = useAsync(
    () =>
      api<{ items: ReviewItem[] }>(
        filter === 'all' ? '/api/v1/review?limit=100' : `/api/v1/review?status=${filter}&limit=100`,
      ),
    [filter],
  );
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ReviewItem | null>(null);
  const [body, setBody] = useState('');
  const [subject, setSubject] = useState('');
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  const items = data?.items ?? [];
  const selected = items.find((i) => i.id === selectedId) ?? items[0] ?? null;

  useEffect(() => {
    if (!selected) {
      setDetail(null);
      return;
    }
    let alive = true;
    api<{ item: ReviewItem }>(`/api/v1/review/${selected.id}`)
      .then((d) => {
        if (!alive) return;
        setDetail(d.item);
        setBody(d.item.draft.body_text);
        setSubject(d.item.draft.subject);
        setNotice(null);
      })
      .catch((e) => toast({ text: errorText(e), error: true }));
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected?.id]);

  const run = async (fn: () => Promise<unknown>, okText?: string) => {
    setBusy(true);
    try {
      const r: any = await fn();
      if (r?.send_result?.notice) setNotice(r.send_result.notice);
      if (okText) toast({ text: okText });
      refreshBadges();
      reload();
    } catch (e) {
      toast({ text: errorText(e), error: true });
      reload();
    } finally {
      setBusy(false);
    }
  };

  const edited = detail && (body !== detail.draft.body_text || subject !== detail.draft.subject);

  const saveEdits = () =>
    run(async () => {
      if (!detail) return;
      const r = await api<{ item: ReviewItem }>(`/api/v1/review/${detail.id}`, {
        method: 'PATCH',
        body: { revision: detail.revision, subject, body_text: body },
      });
      setDetail(r.item);
    }, 'Your edits were saved. The item is now marked as edited by you.');

  const approve = () =>
    run(async () => {
      if (!detail) return;
      if (edited) {
        const r = await api<{ item: ReviewItem }>(`/api/v1/review/${detail.id}`, {
          method: 'PATCH',
          body: { revision: detail.revision, subject, body_text: body },
        });
        return api(`/api/v1/review/${detail.id}/approve`, {
          method: 'POST',
          body: { revision: r.item.revision, confirm_send: true },
        });
      }
      return api(`/api/v1/review/${detail.id}/approve`, {
        method: 'POST',
        body: { revision: detail.revision, confirm_send: true },
      });
    });

  return (
    <div className="view">
      <div className="view-head with-pill">
        <div>
          <span className="kicker">REVIEW QUEUE</span>
          <h1>Nothing sends without you</h1>
          <p className="view-sub">
            Every Agent draft lands here first. Edit it, approve it, reject it, or hand it back to the task. Demo sends are simulated and stored in Sent.
          </p>
        </div>
        <span className="pill pill-warn pill-lg">{items.filter((i) => i.status === 'pending' || i.status === 'modified').length} waiting</span>
      </div>

      <div className="panel filter-bar">
        {FILTERS.map((f) => (
          <button key={f.id} className={`filter-pill${filter === f.id ? ' active' : ''}`} onClick={() => setFilter(f.id)}>
            {f.label}
          </button>
        ))}
      </div>

      {error != null && <ErrorCard error={error} onRetry={reload} />}
      {loading && <SkeletonRows />}

      {!loading && items.length === 0 && (
        <div className="empty-card">
          <img className="empty-motif only-night" src="assets/empty-review-dark.png" alt="" />
          <img className="empty-motif only-day" src="assets/empty-review-light.png" alt="" />
          No items in this view. When the Agent prepares a draft for a delegated task or an automation, it waits for you here.
        </div>
      )}

      {!loading && items.length > 0 && (
        <div className="review-grid">
          <section className="panel queue-panel">
            <div className="section-head">
              <h2>Queue</h2>
              <span className="section-note">{items.length} item(s)</span>
            </div>
            <div className="queue-list">
              {items.map((item) => (
                <button
                  key={item.id}
                  className={`queue-item${selected?.id === item.id ? ' active' : ''}`}
                  onClick={() => setSelectedId(item.id)}
                >
                  <span className="queue-icon">
                    <Mail size={17} />
                  </span>
                  <span className="queue-main">
                    <span className="queue-title">{item.draft.subject}</span>
                    <span className="queue-meta">
                      To {item.draft.to.map((r) => r.name ?? r.email).join(', ')} · {timeAgo(item.created_at)}
                    </span>
                    <span className="queue-foot">
                      <span className="queue-id">{item.task_display_id ?? 'Manual'}</span>
                      <StatusPill status={item.status} />
                    </span>
                  </span>
                </button>
              ))}
            </div>
          </section>

          <section className="panel detail-panel">
            {!detail && <div className="empty-mini">Select an item to inspect it.</div>}
            {detail && (
              <>
                <div className="detail-head">
                  <div>
                    <h2 className="detail-subject">{detail.draft.subject}</h2>
                    <div style={{ display: 'flex', gap: 8, marginTop: 8, flexWrap: 'wrap' }}>
                      <StatusPill status={detail.status} />
                      <span className="pill pill-neutral">Risk: {detail.risk_level}</span>
                      <EnvLabel env={detail.draft.environment} />
                      {detail.task_display_id && (
                        <button className="pill pill-accent" style={{ border: 'none', cursor: 'pointer' }} onClick={() => navigate(`/tasks/${detail.task_id}`)}>
                          Task {detail.task_display_id}
                        </button>
                      )}
                    </div>
                  </div>
                </div>
                <div className="detail-meta">
                  <div className="draft-rows">
                    <div className="draft-row">
                      <span className="draft-row-label">To</span>
                      <span>{detail.draft.to.map((r) => (r.name ? `${r.name} <${r.email}>` : r.email)).join(', ')}</span>
                    </div>
                    <div className="draft-row">
                      <span className="draft-row-label">Subject</span>
                      <span>{detail.draft.subject}</span>
                    </div>
                  </div>
                </div>

                {(detail.status === 'pending' || detail.status === 'modified') ? (
                  <>
                    <div className="field">
                      <label htmlFor="rv-subject">Subject</label>
                      <input id="rv-subject" value={subject} onChange={(e) => setSubject(e.target.value)} />
                    </div>
                    <div className="field">
                      <label htmlFor="rv-body">Draft body — yours to edit</label>
                      <textarea id="rv-body" className="result-edit" rows={10} value={body} onChange={(e) => setBody(e.target.value)} />
                    </div>
                  </>
                ) : (
                  <div className="detail-body">
                    <pre className="tone-body">{detail.draft.body_text}</pre>
                  </div>
                )}

                {detail.agent_note && (
                  <div className="agent-hint">
                    <Sparkles size={15} />
                    <span>
                      <strong>Why the Agent prepared this:</strong> {detail.agent_note}
                    </span>
                  </div>
                )}
                {detail.risk_level !== 'low' && (
                  <div className="agent-hint" style={{ background: 'var(--warn-bg)', color: 'var(--warn)' }}>
                    <ShieldAlert size={15} />
                    <span>This draft is marked {detail.risk_level} risk. Read it fully before approving.</span>
                  </div>
                )}
                {notice && <div className="state-banner done">{notice}</div>}

                {(detail.status === 'pending' || detail.status === 'modified') && (
                  <div className="btn-row detail-actions">
                    <button className="btn btn-primary" disabled={busy} onClick={approve}>
                      Approve &amp; send
                    </button>
                    {edited ? (
                      <button className="btn btn-dark" disabled={busy} onClick={saveEdits}>
                        Save edits
                      </button>
                    ) : null}
                    <button
                      className="btn btn-ghost"
                      disabled={busy}
                      onClick={() => run(() => api(`/api/v1/review/${detail.id}/reject`, { method: 'POST', body: {} }), 'Draft rejected.')}
                    >
                      Reject
                    </button>
                    {detail.task_id && (
                      <button
                        className="btn btn-ghost"
                        disabled={busy}
                        onClick={() => run(() => api(`/api/v1/review/${detail.id}/return-to-task`, { method: 'POST', body: {} }), 'Returned to the task for revision.')}
                      >
                        <RotateCcw size={14} /> Return to task
                      </button>
                    )}
                  </div>
                )}
                {(detail.status === 'sent' || detail.status === 'approved') && (
                  <div className="state-banner done" style={{ marginTop: 16 }}>
                    {detail.draft.environment === 'demo'
                      ? 'Simulated send — no external email was delivered. The message is stored in Sent.'
                      : 'Sent.'}
                  </div>
                )}
                {detail.status === 'rejected' && (
                  <div className="state-banner stopped" style={{ marginTop: 16 }}>
                    You rejected this draft. Nothing was sent.
                  </div>
                )}
                <p className="draft-note">
                  Approving performs the send for this draft only. The Agent cannot reuse this approval for other messages.
                </p>
              </>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
