import { useEffect, useRef, useState } from 'react';
import { FileText, Mail, Send, ShieldCheck, Sparkles } from 'lucide-react';
import {
  api,
  streamAgentMessage,
  type ThreadItem,
} from '../lib/api';
import { useApp } from '../lib/appctx';
import { ErrorCard, errorText, navigate, useToast } from '../lib/ui';

export const AUTH_MODES = [
  {
    id: 'confirm_every_step',
    name: 'Confirm Every Step',
    desc: 'Intenda asks before every meaningful step. Maximum control, more interruptions.',
  },
  {
    id: 'confirm_milestones',
    name: 'Confirm at Key Milestones',
    desc: 'Routine work proceeds automatically. Sending, deleting, changing external state and high-risk choices pause for you.',
  },
  {
    id: 'confirm_before_send',
    name: 'Fully Automatic but Confirm Before Sending',
    desc: 'Internal work runs end to end. Nothing is sent externally until you approve it in the Review Queue.',
  },
] as const;

interface ChatMsg {
  id: string;
  role: 'user' | 'assistant' | 'notice';
  content: string;
  status?: string;
  annotation?: any;
}

const EXAMPLES = [
  'Follow up on the Acme quotation if there is no reply, and draft a polite nudge for my review.',
  'Organize the kickoff with Northstar: collect times and confirm the best slot.',
  'Summarize unread mail from the last two days and list anything that needs a decision.',
];

export default function Delegate() {
  const toast = useToast();
  const { refreshBadges, agentAvailable } = useApp();
  const [goal, setGoal] = useState('');
  const [threads, setThreads] = useState<ThreadItem[]>([]);
  const [selectedThreads, setSelectedThreads] = useState<string[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [plan, setPlan] = useState<any | null>(null);
  const [mode, setMode] = useState<string>('confirm_milestones');
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const logRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api<{ items: ThreadItem[] }>('/api/v1/threads?limit=6')
      .then((d) => setThreads(d.items))
      .catch(() => {});
    api<any>('/api/v1/settings')
      .then((s) => {
        if (s.agent?.default_authorization_mode) setMode(s.agent.default_authorization_mode);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  const contextScope = () => ({ thread_ids: selectedThreads });

  const sendChat = async (text: string) => {
    const content = text.trim();
    if (!content || streaming) return;
    setError(null);
    let convId = conversationId;
    try {
      if (!convId) {
        const c = await api<{ conversation: any }>('/api/v1/agent/conversations', {
          method: 'POST',
          body: { title: content.slice(0, 60), context_scope: contextScope() },
        });
        convId = c.conversation.id;
        setConversationId(convId);
      }
    } catch (e) {
      setError(e);
      return;
    }
    const userMsg: ChatMsg = { id: `u-${Date.now()}`, role: 'user', content };
    const asstId = `a-${Date.now()}`;
    setMessages((prev) => [...prev, userMsg, { id: asstId, role: 'assistant', content: '', status: 'streaming' }]);
    setStreaming(true);
    let acc = '';
    await streamAgentMessage(convId!, content, contextScope(), {
      onDelta: (delta) => {
        acc += delta;
        setMessages((prev) => prev.map((m) => (m.id === asstId ? { ...m, content: acc } : m)));
      },
      onAnnotation: (annotation) => {
        if (annotation?.type === 'plan') {
          setPlan(annotation.plan);
          if (annotation.plan?.goal) setGoal(annotation.plan.goal);
        }
        setMessages((prev) =>
          prev.map((m) => (m.id === asstId ? { ...m, annotation } : m)),
        );
      },
      onCompleted: (message) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === asstId ? { ...m, content: message?.content ?? acc, status: message?.status ?? 'completed' } : m,
          ),
        );
      },
      onError: (message) => {
        setMessages((prev) => [
          ...prev.filter((m) => m.id !== asstId || acc.length > 0),
          {
            id: `n-${Date.now()}`,
            role: 'notice',
            content: message?.content ?? 'The model is unavailable right now.',
            status: 'model_unavailable',
          },
        ]);
        if (!agentAvailable) {
          toast({
            text: 'The AI model is not connected in this deployment. You can still build a plan manually below and delegate it.',
          });
        }
      },
    });
    setStreaming(false);
  };

  const buildManualPlan = () => {
    if (!goal.trim()) {
      setError(new Error('Describe the outcome you want first.'));
      return;
    }
    const firstThread = threads.find((t) => selectedThreads.includes(t.id)) ?? threads[0];
    setPlan({
      goal: goal.trim(),
      summary: 'Plan prepared from your goal and the selected mailbox context.',
      steps: [
        { step_type: 'read_context', title: `Read the selected context${firstThread ? `: “${firstThread.subject}”` : ''}`, description: 'Read only the threads and messages you selected.' },
        { step_type: 'summarize', title: 'Summarize the current state', description: 'Key facts, open questions and deadlines.' },
        { step_type: 'draft_email', title: 'Draft the follow-up', description: 'Prepared for your review. Nothing is sent automatically.' },
        { step_type: 'send_email', title: 'Send after your approval', description: 'Completes only when you approve the draft in the Review Queue.' },
        { step_type: 'report', title: 'Report the result', description: 'A short completion report with links to evidence.' },
      ],
      risks: ['The draft depends on the thread content being current.'],
      assumptions: ['Selected threads are the full context for this task.'],
      deliverables: ['Summary', 'Reviewed draft', 'Completion report'],
      context_refs: selectedThreads.map((id) => ({ type: 'thread', id })),
    });
  };

  const startExecution = async () => {
    if (!plan) return;
    setStarting(true);
    setError(null);
    try {
      const r = await api<{ task: any }>('/api/v1/tasks', {
        method: 'POST',
        body: {
          goal: plan.goal ?? goal,
          plan,
          authorization_mode: mode,
          context_scope: contextScope(),
          conversation_id: conversationId,
        },
      });
      refreshBadges();
      toast({ text: `Task ${r.task.display_id} created. Watch it run in Task Progress.` });
      navigate(`/tasks/${r.task.id}`);
    } catch (e) {
      setError(e);
      setStarting(false);
    }
  };

  const toggleThread = (id: string) =>
    setSelectedThreads((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));

  return (
    <div className="view">
      <div className="view-head">
        <span className="kicker">DELEGATE WORK</span>
        <h1>What should Intenda take off your plate?</h1>
        <p className="view-sub">
          Describe the outcome. The Agent reads only the context you select, proposes a plan, and works under the authorization level you choose.
        </p>
      </div>

      {error != null && <ErrorCard error={error} />}

      <div className="intent-ribbon">
        <img className="only-night" src="assets/intent-orbit-dark.png" alt="" />
        <img className="only-day" src="assets/intent-orbit-light.png" alt="" />
        <div className="intent-ribbon-text">
          <span className="intent-ribbon-en">FROM INTENT TO DONE</span>
          <span className="intent-ribbon-cn">说清目标，剩下的交给意达</span>
        </div>
      </div>

      <section className="panel intent-card">
        <div className="intent-pills">
          <span className="pill pill-accent">
            <Sparkles size={13} /> New delegation
          </span>
          <span className="pill pill-khaki">
            <ShieldCheck size={13} /> Sends always need your approval path
          </span>
          <span className="intent-hint">The Agent sees only the context you attach below.</span>
        </div>
        <textarea
          className="intent-textarea"
          rows={3}
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          placeholder="e.g. Follow up on the Acme quotation and prepare a reply I can approve…"
          aria-label="Delegation goal"
        />
        <div className="intent-foot">
          <div className="chip-row">
            <span className="ctx-chip">
              <Mail size={13} /> {selectedThreads.length} thread(s) attached
            </span>
            <span className="ctx-chip">
              <FileText size={13} /> Attachments stay in your mailbox
            </span>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button className="btn btn-dark" onClick={buildManualPlan} disabled={!goal.trim()}>
              Build plan
            </button>
            <button
              className="btn btn-primary"
              onClick={() => {
                setChatInput('');
                sendChat(goal);
              }}
              disabled={!goal.trim() || streaming}
            >
              <Sparkles size={15} /> Ask Agent to plan
            </button>
          </div>
        </div>
      </section>

      <div className="example-row chip-row">
        <span className="example-label">Try:</span>
        {EXAMPLES.map((ex) => (
          <button key={ex} className="chip" onClick={() => setGoal(ex)}>
            {ex.length > 64 ? `${ex.slice(0, 64)}…` : ex}
          </button>
        ))}
      </div>

      <section className="panel chat-panel">
        <div className="section-head">
          <h2>Agent conversation</h2>
          <span className="section-note">
            {agentAvailable ? 'Connected model — answers stream in live.' : 'Model not connected — the deterministic fallback answers, and no side effects are taken.'}
          </span>
        </div>
        {messages.length === 0 ? (
          <div className="empty-mini">
            Ask the Agent about your mailbox, or use “Ask Agent to plan” above. When the model proposes a plan, it appears below the conversation for your confirmation.
          </div>
        ) : (
          <div className="chat-log" ref={logRef}>
            {messages.map((m) => (
              <div key={m.id} className={`chat-msg ${m.role}`}>
                <span className={`chat-avatar${m.role === 'user' ? ' user' : ''}`}>
                  {m.role === 'user' ? 'You' : m.role === 'notice' ? '!' : 'IA'}
                </span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className="chat-bubble">
                    {m.content || (m.status === 'streaming' ? 'Thinking…' : '')}
                    {m.annotation?.type === 'plan' && (
                      <div style={{ marginTop: 8, fontSize: 12.5, color: 'var(--t3)' }}>
                        A plan is ready below — review it and choose how much autonomy to grant.
                      </div>
                    )}
                  </div>
                  {m.status && m.status !== 'completed' && m.role !== 'notice' && (
                    <div className="chat-status">{m.status === 'streaming' ? 'Streaming…' : m.status}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
        <div className="chat-input-row">
          <textarea
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                const v = chatInput;
                setChatInput('');
                sendChat(v);
              }
            }}
            placeholder="Message the Agent about the selected context…"
            aria-label="Message the Agent"
          />
          <button className="btn btn-primary" onClick={() => { const v = chatInput; setChatInput(''); sendChat(v); }} disabled={streaming || !chatInput.trim()}>
            <Send size={15} /> Send
          </button>
        </div>
      </section>

      <div className="delegate-grid">
        <section className="panel">
          <div className="section-head">
            <h2>Context the Agent may use</h2>
            <span className="section-note">Recent threads</span>
          </div>
          {threads.length === 0 && <div className="empty-mini">No threads available yet.</div>}
          {threads.map((t) => (
            <label key={t.id} className="ctx-item" style={{ cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={selectedThreads.includes(t.id)}
                onChange={() => toggleThread(t.id)}
                aria-label={`Attach thread ${t.subject}`}
              />
              <span className="ctx-main">
                <span className="ctx-title">{t.subject}</span>
                <span className="ctx-sub">
                  {t.participants.map((p) => p.name ?? p.email).join(', ')} · {t.message_count} message(s)
                  {t.unread_count > 0 ? ` · ${t.unread_count} unread` : ''}
                </span>
              </span>
            </label>
          ))}
        </section>

        <section className="panel">
          <div className="section-head">
            <h2>{plan ? 'Proposed plan' : 'Plan'}</h2>
            {plan && <span className="pill pill-accent">Awaiting your confirmation</span>}
          </div>
          {!plan && (
            <div className="empty-mini">
              No plan yet. Write a goal, then “Ask Agent to plan” or “Build plan”. Execution never starts before you confirm a plan and an authorization level.
            </div>
          )}
          {plan && (
            <>
              <p className="decision-context" style={{ marginBottom: 6 }}>{plan.summary}</p>
              {(plan.steps ?? []).map((s: any, i: number) => (
                <div key={i} className="plan-step">
                  <span className="plan-num">{i + 1}</span>
                  <span className="plan-step-main">
                    <span className="plan-step-label">{s.title}</span>
                    <span className="plan-step-note" style={{ display: 'block' }}>
                      {s.step_type.replace(/_/g, ' ')}
                      {s.description ? ` — ${s.description}` : ''}
                    </span>
                  </span>
                </div>
              ))}
              {plan.risks?.length > 0 && (
                <p className="warn-text" style={{ marginTop: 10 }}>
                  Risks: {plan.risks.join(' ')}
                </p>
              )}
            </>
          )}
        </section>
      </div>

      <section className="panel autonomy-panel">
        <div className="section-head">
          <h2>Authorization level</h2>
          <span className="section-note">Enforced by the server for this task</span>
        </div>
        <p className="autonomy-desc">
          This controls how far the Agent may go before it must stop and ask you. Sending email always ends in the Review Queue unless the task's send step is approved.
        </p>
        <div className="autonomy-options" role="radiogroup" aria-label="Authorization level">
          {AUTH_MODES.map((m) => (
            <button
              key={m.id}
              role="radio"
              aria-checked={mode === m.id}
              className={`autonomy-option${mode === m.id ? ' selected' : ''}`}
              onClick={() => setMode(m.id)}
            >
              <span className="autonomy-option-name">{m.name}</span>
              <span className="autonomy-option-desc">{m.desc}</span>
            </button>
          ))}
        </div>
        <div className="autonomy-foot">
          <span className="section-note">{plan ? 'Plan confirmed by you when you start execution.' : 'Create a plan first.'}</span>
          <button className="btn btn-primary btn-lg" onClick={startExecution} disabled={!plan || starting}>
            {starting ? 'Starting…' : 'Start execution'}
          </button>
        </div>
      </section>

      <p className="view-footnote">
        Demo mailbox: delegated work runs against the sample data, and every send is simulated until you approve it in the Review Queue.
      </p>
    </div>
  );
}
