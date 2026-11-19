import { useState } from 'react';
import { ActivityEntry, Decision, DoneItem } from '../data';
import { SeededTask } from '../App';
import { TaskState } from './TaskProgress';
import { IconArrowRight, IconCheck, OrbitMark } from './icons';

interface Props {
  decisions: Decision[];
  resolveDecision: (id: string, action: 'approve' | 'self' | 'ignore', editedDraft?: string) => void;
  seeded: SeededTask[];
  activeTask: TaskState | null;
  doneFeed: DoneItem[];
  activity: ActivityEntry[];
  goTask: () => void;
  goReview: () => void;
  reviewCount: number;
  mailTotal: number;
  unreadCount: number;
}

const DAYS = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
const MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
const DECISION_TAGS = [
  { label: '待批准', cls: 'pill-warn' },
  { label: '待选时间', cls: 'pill-info' },
  { label: '需修改', cls: 'pill-danger' },
];
const DOT_CLASSES = ['dot-gray', 'dot-accent', 'dot-ok'];

function HeroOrbit() {
  return (
    <svg className="hero-orbit" width="360" height="210" viewBox="0 0 360 210" fill="none" aria-hidden="true">
      <ellipse cx="215" cy="105" rx="150" ry="56" transform="rotate(-16 215 105)" stroke="#7865F0" strokeOpacity="0.4" />
      <ellipse cx="215" cy="105" rx="118" ry="86" transform="rotate(24 215 105)" stroke="#9383FF" strokeOpacity="0.22" />
      <circle cx="215" cy="105" r="34" fill="#2A2542" />
      <circle cx="215" cy="105" r="17" fill="#7865F0" />
      <circle cx="96" cy="140" r="4.5" fill="#F4F3F8" />
      <circle cx="322" cy="58" r="3" fill="#9383FF" />
    </svg>
  );
}

export default function Briefing({
  decisions,
  resolveDecision,
  seeded,
  activeTask,
  doneFeed,
  activity,
  goTask,
  goReview,
  reviewCount,
  mailTotal,
  unreadCount,
}: Props) {
  const [leaving, setLeaving] = useState<string | null>(null);
  const [editing, setEditing] = useState<string | null>(null);
  const [editText, setEditText] = useState('');
  const [openId, setOpenId] = useState<string | null>(null);

  const act = (id: string, action: 'approve' | 'self' | 'ignore', editedDraft?: string) => {
    setLeaving(id);
    window.setTimeout(() => {
      resolveDecision(id, action, editedDraft);
      setLeaving(null);
      setEditing(null);
    }, 320);
  };

  const taskRunning =
    activeTask && (activeTask.status === 'running' || activeTask.status === 'waiting' || activeTask.status === 'paused');
  const runningCount = seeded.length + (taskRunning ? 1 : 0);
  const now = new Date();

  const stats = [
    { num: mailTotal, label: '新邮件', sub: `其中 ${unreadCount} 封未读` },
    { num: decisions.length, label: '待决策', sub: '待用户处理' },
    { num: runningCount, label: '进行中', sub: 'Agent 执行中' },
    { num: doneFeed.length, label: '已交付', sub: '今日成果' },
  ];

  return (
    <div className="view">
      <header className="view-head">
        <div className="kicker">TODAY / {DAYS[now.getDay()]} {now.getDate()} {MONTHS[now.getMonth()]}</div>
        <h1>今日简报</h1>
        <p className="view-sub">Agent 已筛选今日来信与待办，优先呈现需要你决策的事项。</p>
      </header>

      <section className="hero">
        <div className="hero-content">
          <div className="hero-kicker">WORK BRIEF · {MONTHS[now.getMonth()]} {now.getDate()}</div>
          <h2 className="hero-title">
            {decisions.length > 0 ? `今天只有 ${decisions.length} 项需要你做决定` : '今天没有待决定的事项'}
          </h2>
          <p className="hero-sub">
            其余工作由 Agent 持续推进。{reviewCount} 封邮件待审核，{runningCount} 项任务运行中。
          </p>
          <div className="hero-actions">
            <button className="btn btn-primary btn-lg" onClick={goReview}>
              处理待审阅
            </button>
            <button className="btn btn-dark btn-lg" onClick={goTask}>
              查看任务进度
            </button>
          </div>
        </div>
        <HeroOrbit />
      </section>

      <section className="stats-strip panel">
        {stats.map((s) => (
          <div key={s.label} className="stat-cell">
            <div className="stat-num">{String(s.num).padStart(2, '0')}</div>
            <div className="stat-meta">
              <div className="stat-label">{s.label}</div>
              <div className="stat-sub">{s.sub}</div>
            </div>
          </div>
        ))}
      </section>

      <div className="brief-grid">
        <section>
          <div className="section-head">
            <h2>需要你决策</h2>
            {decisions.length > 0 && <span className="pill pill-warn">{decisions.length} 项需确认</span>}
          </div>
          {decisions.length === 0 && (
            <div className="empty-card">全部处理完了。Agent 会继续盯着新邮件，有需要决定的事会放在这里。</div>
          )}
          <div className="card-list">
            {decisions.map((d, i) => {
              const tag = DECISION_TAGS[i % DECISION_TAGS.length];
              const open = openId === d.id;
              return (
                <article key={d.id} className={`decision-card ${leaving === d.id ? 'leaving' : ''} ${open ? 'open' : ''}`}>
                  <button className="decision-main" onClick={() => setOpenId(open ? null : d.id)}>
                    <span className="decision-icon">
                      <OrbitMark size={32} />
                    </span>
                    <span className="decision-main-text">
                      <span className="decision-title">{d.title}</span>
                      <span className="decision-desc">{d.recommendation}</span>
                      <span className="decision-source">{d.source}</span>
                    </span>
                    <span className={`pill ${tag.cls}`}>{tag.label}</span>
                    <span className={`decision-arrow ${open ? 'up' : ''}`}>
                      <IconArrowRight size={16} />
                    </span>
                  </button>
                  {open && (
                    <div className="decision-detail">
                      <p className="decision-context">{d.context}</p>
                      {d.draft && (
                        <div className="mail-preview">
                          <div className="mail-preview-head">
                            <span>Agent 草稿</span>
                          </div>
                          <pre className="tone-body">{d.draft}</pre>
                        </div>
                      )}
                      {editing === d.id ? (
                        <div className="edit-box">
                          <textarea value={editText} onChange={(e) => setEditText(e.target.value)} rows={8} />
                          <div className="btn-row">
                            <button className="btn btn-primary" onClick={() => act(d.id, 'approve', editText)}>
                              保存并发送
                            </button>
                            <button className="btn btn-ghost" onClick={() => setEditing(null)}>
                              取消
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="btn-row">
                          <button className="btn btn-primary" onClick={() => act(d.id, 'approve')}>
                            批准发送
                          </button>
                          {d.draft && (
                            <button
                              className="btn btn-dark"
                              onClick={() => {
                                setEditing(d.id);
                                setEditText(d.draft ?? '');
                              }}
                            >
                              编辑草稿
                            </button>
                          )}
                          <button className="btn btn-dark" onClick={() => act(d.id, 'self')}>
                            我自己处理
                          </button>
                          <button className="btn btn-ghost" onClick={() => act(d.id, 'ignore')}>
                            忽略
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </article>
              );
            })}
          </div>
        </section>

        <section className="panel agent-panel">
          <div className="section-head">
            <h2>Agent 正在推进</h2>
            <span className="pill pill-accent live-pill">LIVE</span>
          </div>
          <div className="agent-rows">
            {taskRunning && activeTask && (
              <button className="agent-row clickable" onClick={goTask}>
                <span className="agent-dot dot-accent" />
                <span className="agent-row-main">
                  <span className="agent-row-title">{activeTask.title}</span>
                  <span className="agent-row-meta">
                    当前步骤：{activeTask.plan.steps[Math.min(activeTask.current, activeTask.plan.steps.length - 1)].label}
                  </span>
                  <span className="progress">
                    <span
                      className="progress-bar"
                      style={{ width: `${Math.round((activeTask.current / activeTask.plan.steps.length) * 100)}%` }}
                    />
                  </span>
                </span>
                <span className="agent-pct">
                  {Math.round((activeTask.current / activeTask.plan.steps.length) * 100)}%
                </span>
              </button>
            )}
            {seeded.map((s, i) => (
              <div key={s.id} className="agent-row">
                <span className={`agent-dot ${DOT_CLASSES[i % DOT_CLASSES.length]}`} />
                <span className="agent-row-main">
                  <span className="agent-row-title">{s.title}</span>
                  <span className="agent-row-meta">{s.stepLabel} · 正在执行</span>
                  <span className="progress">
                    <span
                      className={`progress-bar ${DOT_CLASSES[i % DOT_CLASSES.length]}`}
                      style={{ width: `${s.progress}%` }}
                    />
                  </span>
                </span>
                <span className="agent-pct">{s.progress}%</span>
              </div>
            ))}
            {!taskRunning && seeded.length === 0 && <div className="empty-mini">暂无进行中的任务</div>}
          </div>
          <div className="panel-foot-note">所有外发操作需你批准 · 可随时手动接管</div>
        </section>
      </div>

      <div className="brief-bottom">
        <section className="panel feed-panel">
          <div className="section-head">
            <h2>已完成</h2>
            <button className="link-btn" onClick={goReview}>
              去待审阅
            </button>
          </div>
          <div className="feed">
            {doneFeed.map((item) => (
              <div key={item.id} className="feed-item">
                <span className="feed-check">
                  <IconCheck size={13} />
                </span>
                <span className="feed-text">{item.text}</span>
                <span className="feed-link">{item.output}</span>
                <span className="feed-time">{item.time}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="panel feed-panel">
          <div className="section-head">
            <h2>审计日志</h2>
            <span className="section-note">全部动作可追溯</span>
          </div>
          <div className="feed">
            {activity.slice(0, 6).map((a) => (
              <div key={a.id} className="feed-item">
                <span className="feed-time mono">{a.time}</span>
                <span className="feed-text">{a.text}</span>
              </div>
            ))}
          </div>
        </section>
      </div>

      <div className="view-footnote">任务记录已同步 · 所有外发操作在授权范围内执行</div>
    </div>
  );
}
