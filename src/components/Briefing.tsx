import { useState } from 'react';
import { ArrowRight, Check, ChevronDown, Plus } from 'lucide-react';
import { api, type Briefing as BriefingData } from '../lib/api';
import { useApp } from '../lib/appctx';
import {
  EnvLabel,
  ErrorCard,
  SkeletonRows,
  errorText,
  fmtTime,
  navigate,
  timeAgo,
  useAsync,
  useToast,
} from '../lib/ui';

const DOT: Record<string, string> = {
  running: 'dot-accent',
  waiting_user: 'dot-khaki',
  completed: 'dot-ok',
  failed: 'dot-gray',
};

export default function Briefing() {
  const { me, refreshBadges } = useApp();
  const toast = useToast();
  const { data, error, loading, reload } = useAsync(() => api<BriefingData>('/api/v1/briefing/today'), []);
  const [openId, setOpenId] = useState<string | null>(null);
  const [acting, setActing] = useState<string | null>(null);
  const [newTodo, setNewTodo] = useState('');

  if (loading) {
    return (
      <div className="view">
        <SkeletonRows rows={5} />
      </div>
    );
  }
  if (error || !data) {
    return (
      <div className="view">
        <ErrorCard error={error ?? new Error('Briefing unavailable.')} onRetry={reload} />
      </div>
    );
  }

  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';
  const firstName = me.name.split(' ')[0];

  const actOnDecision = async (d: BriefingData['decisions'][number], action: 'approve' | 'reject' | 'choose', choice?: string) => {
    setActing(d.id);
    try {
      if (d.kind === 'review_item') {
        if (action === 'approve') {
          const detail = await api<any>(`/api/v1/review/${d.id}`);
          await api(`/api/v1/review/${d.id}/approve`, {
            method: 'POST',
            body: { revision: detail.item.revision, confirm_send: true },
          });
          toast({ text: 'Approved. Simulated send completed — the message is in Sent.' });
        } else {
          await api(`/api/v1/review/${d.id}/reject`, { method: 'POST', body: {} });
          toast({ text: 'Draft rejected. The task was flagged for your attention.' });
        }
      } else {
        await api(`/api/v1/decisions/${d.id}/resolve`, {
          method: 'POST',
          body: action === 'choose' ? { choice } : { action },
        });
        toast({ text: action === 'reject' ? 'Declined. The task is paused.' : 'Decision recorded. The task continues.' });
      }
      refreshBadges();
      reload();
    } catch (e) {
      toast({ text: errorText(e), error: true });
    } finally {
      setActing(null);
    }
  };

  const addTodo = async () => {
    if (!newTodo.trim()) return;
    try {
      await api('/api/v1/todos', { method: 'POST', body: { title: newTodo.trim() } });
      setNewTodo('');
      reload();
    } catch (e) {
      toast({ text: errorText(e), error: true });
    }
  };

  const toggleTodo = async (t: BriefingData['todos'][number]) => {
    try {
      await api(`/api/v1/todos/${t.id}`, {
        method: 'PATCH',
        body: { status: t.status === 'completed' ? 'open' : 'completed' },
      });
      reload();
    } catch (e) {
      toast({ text: errorText(e), error: true });
    }
  };

  return (
    <div className="view">
      <section className="hero">
        <img className="hero-nebula only-night" src="assets/nebula-dark.png" alt="" />
        <img className="hero-nebula only-day" src="assets/nebula-light.png" alt="" />
        <img className="hero-art only-night" src="assets/galaxy-dark.png" alt="" />
        <img className="hero-art only-day" src="assets/galaxy-light.png" alt="" />
        <div className="hero-content">
          <div className="hero-kicker">TODAY BRIEFING · {new Date().toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' }).toUpperCase()}</div>
          <h1 className="hero-title">
            {greeting}, {firstName}
          </h1>
          <p className="hero-sub">
            {data.metrics.pending_decisions > 0
              ? `${data.metrics.pending_decisions} item(s) need your decision, ${data.metrics.active_tasks} delegated task(s) are in motion, and ${data.metrics.unread_count} messages are unread.`
              : 'Nothing is waiting on you. Your delegated work is in motion.'}
          </p>
          <div className="hero-actions">
            <button className="btn btn-primary btn-lg" onClick={() => navigate('/delegate')}>
              Delegate new work
            </button>
            <button className="btn btn-dark btn-lg" onClick={() => navigate('/review')}>
              Review pending items
            </button>
          </div>
        </div>
      </section>

      <section className="stats-strip panel">
        <div className="stat-cell">
          <div>
            <div className="stat-num">{data.metrics.unread_count}</div>
          </div>
          <div>
            <div className="stat-label">Unread</div>
            <div className="stat-sub">Across your mailbox</div>
          </div>
        </div>
        <div className="stat-cell">
          <div className="stat-num">{data.metrics.pending_decisions}</div>
          <div>
            <div className="stat-label">Need your decision</div>
            <div className="stat-sub">Approvals and choices</div>
          </div>
        </div>
        <div className="stat-cell">
          <div className="stat-num">{data.metrics.active_tasks}</div>
          <div>
            <div className="stat-label">Tasks in progress</div>
            <div className="stat-sub">Delegated to the Agent</div>
          </div>
        </div>
        <div className="stat-cell">
          <div className="stat-num">{data.metrics.completed_today}</div>
          <div>
            <div className="stat-label">Delivered</div>
            <div className="stat-sub">Completed tasks</div>
          </div>
        </div>
      </section>

      <div className="brief-grid">
        <section>
          <div className="section-head">
            <h2>Needs your decision</h2>
            <EnvLabel env={data.environment} />
          </div>
          {data.decisions.length === 0 ? (
            <div className="empty-card">
              <img className="empty-motif only-night" src="assets/empty-decisions-dark.png" alt="" />
              <img className="empty-motif only-day" src="assets/empty-decisions-light.png" alt="" />
              Nothing needs your decision right now. New approvals and choices will appear here.
            </div>
          ) : (
            <div className="card-list">
              {data.decisions.map((d) => {
                const open = openId === d.id;
                return (
                  <article key={d.id} className="decision-card">
                    <button className="decision-main" onClick={() => setOpenId(open ? null : d.id)} aria-expanded={open}>
                      <img className="decision-motif only-night" src="assets/empty-decisions-dark.png" alt="" />
                      <img className="decision-motif only-day" src="assets/empty-decisions-light.png" alt="" />
                      <span className="decision-main-text">
                        <span className="decision-title">{d.title}</span>
                        <span className="decision-desc">{d.description}</span>
                        <span className="decision-source">
                          {d.source_label} · {timeAgo(d.created_at)}
                        </span>
                      </span>
                      <span className={`decision-arrow${open ? ' up' : ''}`}>
                        <ChevronDown size={17} />
                      </span>
                    </button>
                    {open && (
                      <div className="decision-detail">
                        <p className="decision-context">{d.description}</p>
                        <div className="btn-row">
                          {d.kind === 'choose_option' ? (
                            <>
                              <button
                                className="btn btn-primary"
                                disabled={acting === d.id}
                                onClick={() => navigate(`/tasks/${d.task_id}`)}
                              >
                                Choose in Task Progress <ArrowRight size={14} />
                              </button>
                              <button
                                className="btn btn-ghost"
                                disabled={acting === d.id}
                                onClick={() => actOnDecision(d, 'reject')}
                              >
                                Pause task
                              </button>
                            </>
                          ) : (
                            <>
                              <button className="btn btn-primary" disabled={acting === d.id} onClick={() => actOnDecision(d, 'approve')}>
                                {d.kind === 'review_item' ? 'Approve & send' : 'Approve'}
                              </button>
                              <button className="btn btn-dark" disabled={acting === d.id} onClick={() => navigate(d.kind === 'review_item' ? '/review' : `/tasks/${d.task_id}`)}>
                                Review first
                              </button>
                              <button className="btn btn-ghost" disabled={acting === d.id} onClick={() => actOnDecision(d, 'reject')}>
                                Reject
                              </button>
                            </>
                          )}
                        </div>
                      </div>
                    )}
                  </article>
                );
              })}
            </div>
          )}
        </section>

        <section className="panel agent-panel">
          <div className="section-head">
            <h2>Agent is handling</h2>
            <button className="link-btn" onClick={() => navigate('/tasks')}>
              View all
            </button>
          </div>
          <div className="agent-rows">
            {data.active_tasks.length === 0 && <div className="empty-mini">No active tasks. Delegate something new.</div>}
            {data.active_tasks.map((t) => (
              <button key={t.id} className="agent-row clickable" onClick={() => navigate(`/tasks/${t.id}`)}>
                <span className={`agent-dot ${DOT[t.status] ?? 'dot-gray'}`} />
                <span className="agent-row-main">
                  <span className="agent-row-title">{t.title}</span>
                  <span className="agent-row-meta">
                    <span className="mono">{t.display_id}</span> · {t.status.replace(/_/g, ' ')}
                  </span>
                  <span className="progress">
                    <span className="progress-bar" style={{ width: `${t.progress_percent}%` }} />
                  </span>
                </span>
                <span className="agent-pct">{t.progress_percent}%</span>
              </button>
            ))}
          </div>
        </section>
      </div>

      <div className="brief-bottom">
        <section className="panel feed-panel">
          <div className="section-head">
            <h2>Recent mail</h2>
            <button className="link-btn" onClick={() => navigate('/inbox')}>
              Open inbox
            </button>
          </div>
          {data.recent_messages.length === 0 && <div className="empty-mini">No recent messages.</div>}
          {data.recent_messages.map((msg) => (
            <div key={msg.id} className="feed-item">
              <span className="feed-check" style={msg.is_read ? { background: 'var(--s2)', color: 'var(--t4)' } : undefined}>
                <Check size={12} />
              </span>
              <span className="feed-text">
                <strong>{msg.from.name ?? msg.from.email}</strong> — {msg.subject}
              </span>
              <button className="feed-link" onClick={() => navigate(`/inbox?message=${msg.id}`)}>
                View
              </button>
              <span className="feed-time">{fmtTime(msg.created_at)}</span>
            </div>
          ))}
        </section>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <section className="panel feed-panel">
            <div className="section-head">
              <h2>Completed &amp; activity</h2>
            </div>
            {data.activity.length === 0 && <div className="empty-mini">No activity yet.</div>}
            {data.activity.slice(0, 6).map((a) => (
              <div key={a.id} className="feed-item">
                <span className="feed-check">
                  <Check size={12} />
                </span>
                <span className="feed-text">{a.text}</span>
                <span className="feed-time">{timeAgo(a.created_at)}</span>
              </div>
            ))}
          </section>

          <section className="panel feed-panel">
            <div className="section-head">
              <h2>Your to-dos</h2>
              <span className="section-note">{data.todos.filter((t) => t.status === 'open').length} open</span>
            </div>
            {data.todos.map((t) => (
              <div key={t.id} className="feed-item">
                <button
                  className="feed-check"
                  style={t.status === 'completed' ? undefined : { background: 'var(--s2)', color: 'var(--t4)' }}
                  onClick={() => toggleTodo(t)}
                  aria-label={t.status === 'completed' ? 'Reopen to-do' : 'Complete to-do'}
                >
                  <Check size={12} />
                </button>
                <span className="feed-text" style={t.status === 'completed' ? { textDecoration: 'line-through', color: 'var(--t4)' } : undefined}>
                  {t.title}
                </span>
                {t.due_at && <span className="feed-time">{fmtTime(t.due_at)}</span>}
              </div>
            ))}
            <div className="inline-form" style={{ marginTop: 12 }}>
              <div className="field">
                <input
                  value={newTodo}
                  onChange={(e) => setNewTodo(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addTodo()}
                  placeholder="Add a to-do…"
                  aria-label="New to-do"
                />
              </div>
              <button className="btn btn-dark" onClick={addTodo}>
                <Plus size={14} /> Add
              </button>
            </div>
          </section>
        </div>
      </div>

      <p className="view-footnote">
        {data.environment === 'demo'
          ? 'Demo mailbox data — realistic sample content. Sends are simulated and stored in Sent.'
          : 'Live mailbox data.'}{' '}
        Briefing generated {timeAgo(data.generated_at)}.
      </p>
    </div>
  );
}
