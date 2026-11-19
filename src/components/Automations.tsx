import { useState } from 'react';
import { Copy, Play, Plus, Trash2 } from 'lucide-react';
import { api, type Automation } from '../lib/api';
import {
  ErrorCard,
  Modal,
  SkeletonRows,
  errorText,
  fmtDateTime,
  useAsync,
  useToast,
} from '../lib/ui';
import { StatusPill } from './TaskProgress';

const TRIGGER_LABEL: Record<string, string> = {
  scheduled: 'Scheduled',
  new_matching_email: 'On matching email',
  manual: 'Manual only',
};

const ACTION_LABEL: Record<string, string> = {
  summarize: 'Summarize matches',
  create_todo: 'Create a to-do',
  prepare_draft: 'Prepare a draft for review',
  notify: 'Notify me',
};

interface RunRecord {
  id: string;
  status: string;
  result: any;
  started_at: string;
}

export default function Automations() {
  const toast = useToast();
  const { data, error, loading, reload } = useAsync(
    () => api<{ items: Automation[] }>('/api/v1/automations'),
    [],
  );
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [runs, setRuns] = useState<RunRecord[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [busy, setBusy] = useState(false);

  const items = data?.items ?? [];
  const selected = items.find((a) => a.id === selectedId) ?? null;

  const loadRuns = async (id: string) => {
    try {
      const d = await api<{ automation: Automation; runs: RunRecord[] }>(`/api/v1/automations/${id}`);
      setRuns(d.runs);
    } catch {
      setRuns([]);
    }
  };

  const pick = (a: Automation) => {
    setSelectedId(a.id);
    loadRuns(a.id);
  };

  const call = async (fn: () => Promise<unknown>, okText?: string) => {
    setBusy(true);
    try {
      await fn();
      if (okText) toast({ text: okText });
      reload();
      if (selectedId) loadRuns(selectedId);
    } catch (e) {
      toast({ text: errorText(e), error: true });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="view">
      <div className="view-head with-pill">
        <div>
          <span className="kicker">AUTOMATIONS</span>
          <h1>Rules that work while you don't</h1>
          <p className="view-sub">
            Automations can summarize, create to-dos, notify you and prepare drafts. They can never send email — drafts always wait in the Review Queue.
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
          <Plus size={15} /> New automation
        </button>
      </div>

      {error != null && <ErrorCard error={error} onRetry={reload} />}
      {loading && <SkeletonRows />}

      {!loading && items.length === 0 && (
        <div className="empty-card">
          <img className="empty-motif only-night" src="assets/empty-automations-dark.png" alt="" />
          <img className="empty-motif only-day" src="assets/empty-automations-light.png" alt="" />
          No automations yet. Create one to keep routine mail work moving.
        </div>
      )}

      <div className="two-col">
        <section className="panel" style={{ padding: '6px 18px' }}>
          <div className="list-rows">
            {items.map((a) => (
              <button key={a.id} className="list-row" onClick={() => pick(a)}>
                <span className="list-row-main">
                  <span className="list-row-title">{a.name}</span>
                  <span className="list-row-meta" style={{ display: 'block' }}>
                    {TRIGGER_LABEL[a.trigger.type] ?? a.trigger.type}
                    {a.trigger.schedule ? ` · ${a.trigger.schedule}` : ''} ·{' '}
                    {a.actions.map((x) => ACTION_LABEL[x.type] ?? x.type).join(', ')}
                  </span>
                  <span className="list-row-meta" style={{ display: 'block' }}>
                    Last run: {a.last_run_at ? `${fmtDateTime(a.last_run_at)} (${a.last_run_status ?? ''})` : 'never'}
                  </span>
                </span>
                {a.enabled ? <span className="pill pill-ok">Enabled</span> : <span className="pill pill-neutral">Disabled</span>}
              </button>
            ))}
          </div>
        </section>

        <section className="panel" style={{ padding: '20px 22px' }}>
          {!selected && <div className="empty-mini">Select an automation to manage it, run it, or see its history.</div>}
          {selected && (
            <>
              <div className="section-head">
                <h2>{selected.name}</h2>
                <button
                  className="switch"
                  role="switch"
                  aria-checked={selected.enabled}
                  aria-label={selected.enabled ? 'Disable automation' : 'Enable automation'}
                  disabled={busy}
                  onClick={() =>
                    call(
                      () => api(`/api/v1/automations/${selected.id}/${selected.enabled ? 'disable' : 'enable'}`, { method: 'POST', body: {} }),
                      selected.enabled ? 'Automation disabled.' : 'Automation enabled.',
                    )
                  }
                />
              </div>
              <dl className="kv-grid">
                <dt>Trigger</dt>
                <dd>
                  {TRIGGER_LABEL[selected.trigger.type] ?? selected.trigger.type}
                  {selected.trigger.schedule ? ` (${selected.trigger.schedule})` : ''}
                </dd>
                <dt>Conditions</dt>
                <dd>
                  {Object.keys(selected.conditions ?? {}).length === 0
                    ? 'Any message'
                    : Object.entries(selected.conditions).map(([k, v]) => `${k}: ${String(v)}`).join(' · ')}
                </dd>
                <dt>Actions</dt>
                <dd>{selected.actions.map((x) => ACTION_LABEL[x.type] ?? x.type).join(', ')}</dd>
                <dt>Sending</dt>
                <dd>Never automatic — drafts go to the Review Queue</dd>
              </dl>
              <div className="btn-row">
                <button
                  className="btn btn-primary"
                  disabled={busy}
                  onClick={() =>
                    call(async () => {
                      const r = await api<{ run: RunRecord }>(`/api/v1/automations/${selected.id}/run`, { method: 'POST', body: {} });
                      if (r.run.status === 'needs_attention') {
                        toast({ text: 'Run finished with no matching messages, so no action was taken.' });
                      }
                    }, 'Automation run finished.')
                  }
                >
                  <Play size={14} /> Run now
                </button>
                <button
                  className="btn btn-dark"
                  disabled={busy}
                  onClick={() => call(() => api(`/api/v1/automations/${selected.id}/duplicate`, { method: 'POST', body: {} }), 'Duplicated (disabled).')}
                >
                  <Copy size={14} /> Duplicate
                </button>
                <button
                  className="btn btn-danger-ghost"
                  disabled={busy}
                  onClick={() =>
                    call(async () => {
                      await api(`/api/v1/automations/${selected.id}`, { method: 'DELETE' });
                      setSelectedId(null);
                    }, 'Automation deleted.')
                  }
                >
                  <Trash2 size={14} /> Delete
                </button>
              </div>
              <div className="section-head" style={{ marginTop: 20 }}>
                <h2>Run history</h2>
              </div>
              {runs.length === 0 && <div className="empty-mini">No runs yet.</div>}
              {runs.map((r) => (
                <div key={r.id} className="feed-item">
                  <span className="feed-text">
                    <StatusPill status={r.status} />{' '}
                    {r.result?.matched !== undefined ? `${r.result.matched} matched` : ''}
                    {r.result?.note ? ` — ${r.result.note}` : ''}
                  </span>
                  <span className="feed-time">{fmtDateTime(r.started_at)}</span>
                </div>
              ))}
            </>
          )}
        </section>
      </div>

      {showCreate && (
        <CreateAutomation
          onClose={() => setShowCreate(false)}
          onCreated={() => {
            setShowCreate(false);
            reload();
          }}
        />
      )}
    </div>
  );
}

function CreateAutomation({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const toast = useToast();
  const [name, setName] = useState('');
  const [triggerType, setTriggerType] = useState('manual');
  const [schedule, setSchedule] = useState('daily');
  const [sender, setSender] = useState('');
  const [subjectContains, setSubjectContains] = useState('');
  const [actions, setActions] = useState<string[]>(['summarize']);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const toggleAction = (a: string) =>
    setActions((prev) => (prev.includes(a) ? prev.filter((x) => x !== a) : [...prev, a]));

  const submit = async () => {
    if (!name.trim()) {
      setError(new Error('Give the automation a name.'));
      return;
    }
    if (actions.length === 0) {
      setError(new Error('Choose at least one action.'));
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const conditions: Record<string, string> = {};
      if (sender.trim()) conditions.sender = sender.trim();
      if (subjectContains.trim()) conditions.subject_contains = subjectContains.trim();
      await api('/api/v1/automations', {
        method: 'POST',
        body: {
          name: name.trim(),
          trigger: triggerType === 'scheduled' ? { type: 'scheduled', schedule } : { type: triggerType },
          conditions,
          actions: actions.map((type) => ({ type })),
        },
      });
      toast({ text: 'Automation created (disabled). Enable it when ready.' });
      onCreated();
    } catch (e) {
      setError(e);
      setBusy(false);
    }
  };

  return (
    <Modal title="New automation" sub="Automations never send email. Drafts they prepare wait in the Review Queue for your approval." onClose={onClose}>
      {error != null && <ErrorCard error={error} />}
      <div className="field">
        <label htmlFor="am-name">Name</label>
        <input id="am-name" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Invoice watcher" />
      </div>
      <div className="field">
        <label htmlFor="am-trigger">Trigger</label>
        <select id="am-trigger" value={triggerType} onChange={(e) => setTriggerType(e.target.value)}>
          <option value="manual">Manual only</option>
          <option value="scheduled">Scheduled</option>
          <option value="new_matching_email">On matching email</option>
        </select>
      </div>
      {triggerType === 'scheduled' && (
        <div className="field">
          <label htmlFor="am-schedule">Schedule</label>
          <select id="am-schedule" value={schedule} onChange={(e) => setSchedule(e.target.value)}>
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
          </select>
        </div>
      )}
      <div className="field">
        <label htmlFor="am-sender">Sender contains (optional)</label>
        <input id="am-sender" value={sender} onChange={(e) => setSender(e.target.value)} placeholder="acme.com" />
      </div>
      <div className="field">
        <label htmlFor="am-subject">Subject contains (optional)</label>
        <input id="am-subject" value={subjectContains} onChange={(e) => setSubjectContains(e.target.value)} placeholder="invoice" />
      </div>
      <div className="field">
        <label>Actions</label>
        <div className="chip-row">
          {Object.entries(ACTION_LABEL).map(([id, label]) => (
            <button
              key={id}
              className="chip"
              style={actions.includes(id) ? { borderColor: 'var(--accent)', color: 'var(--accent-text)' } : undefined}
              onClick={() => toggleAction(id)}
              aria-pressed={actions.includes(id)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
      <div className="btn-row" style={{ justifyContent: 'flex-end' }}>
        <button className="btn btn-ghost" onClick={onClose}>
          Cancel
        </button>
        <button className="btn btn-primary" onClick={submit} disabled={busy}>
          {busy ? 'Creating…' : 'Create automation'}
        </button>
      </div>
    </Modal>
  );
}
