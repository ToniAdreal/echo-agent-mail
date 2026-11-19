import { useState } from 'react';
import { ActivityEntry, Decision, DoneItem } from '../data';
import { SeededTask } from '../App';
import { TaskState } from './TaskProgress';

interface Props {
  decisions: Decision[];
  resolveDecision: (id: string, action: 'approve' | 'self' | 'ignore', editedDraft?: string) => void;
  seeded: SeededTask[];
  activeTask: TaskState | null;
  doneFeed: DoneItem[];
  activity: ActivityEntry[];
  goTask: () => void;
  goReview: () => void;
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
}: Props) {
  const [leaving, setLeaving] = useState<string | null>(null);
  const [editing, setEditing] = useState<string | null>(null);
  const [editText, setEditText] = useState('');

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

  return (
    <div className="view">
      <header className="view-head">
        <h1>早上好，Toni</h1>
        <p className="view-sub">这是 Agent 在你离线时整理好的今日简报。你只需要做决定，其余的它已经在做了。</p>
      </header>

      <section className="summary-card">
        <div className="summary-text">
          昨夜新到 <strong>23 封</strong>邮件，Agent 已处理完大部分：归档 <strong>14</strong> 封订阅与通知，
          起草 <strong>3</strong> 封回复（在待审阅里），把发票录入了报销表。
          现在有 <strong>{decisions.length} 件</strong>事需要你决定，
          <strong> {seeded.length + (taskRunning ? 1 : 0)} 个</strong>任务正在进行。
        </div>
        <div className="summary-stats">
          <div className="stat">
            <div className="stat-num">23</div>
            <div className="stat-label">昨夜新邮件</div>
          </div>
          <div className="stat">
            <div className="stat-num">14</div>
            <div className="stat-label">已自动归档</div>
          </div>
          <div className="stat">
            <div className="stat-num accent">{decisions.length}</div>
            <div className="stat-label">需要你决定</div>
          </div>
          <div className="stat">
            <div className="stat-num">3</div>
            <div className="stat-label">已起草待审</div>
          </div>
        </div>
      </section>

      <section>
        <div className="section-head">
          <h2>需要你决定</h2>
          <span className="section-note">Agent 给出了建议，你只需确认、修改，或者拿回自己处理</span>
        </div>
        {decisions.length === 0 && (
          <div className="empty-card">全部处理完了。Agent 会继续盯着新邮件，有需要决定的事会放在这里。</div>
        )}
        <div className="card-list">
          {decisions.map((d) => (
            <article key={d.id} className={`decision-card ${leaving === d.id ? 'leaving' : ''}`}>
              <div className="decision-top">
                <h3>{d.title}</h3>
                <span className="tag tag-wait">等待决定</span>
              </div>
              <p className="decision-context">{d.context}</p>
              <p className="decision-rec">
                <span className="rec-label">Agent 建议</span>
                {d.recommendation}
              </p>
              <p className="decision-source">{d.source}</p>
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
                      className="btn btn-soft"
                      onClick={() => {
                        setEditing(d.id);
                        setEditText(d.draft ?? '');
                      }}
                    >
                      编辑草稿
                    </button>
                  )}
                  <button className="btn btn-soft" onClick={() => act(d.id, 'self')}>
                    我自己处理
                  </button>
                  <button className="btn btn-ghost" onClick={() => act(d.id, 'ignore')}>
                    忽略
                  </button>
                </div>
              )}
            </article>
          ))}
        </div>
      </section>

      <section>
        <div className="section-head">
          <h2>进行中</h2>
          <span className="section-note">Agent 正在执行的任务，随时可以暂停或接管</span>
        </div>
        <div className="card-list">
          {taskRunning && activeTask && (
            <article className="task-strip clickable" onClick={goTask}>
              <div className="task-strip-top">
                <span className="task-strip-title">{activeTask.title}</span>
                <span className={`tag ${activeTask.status === 'waiting' ? 'tag-wait' : 'tag-run'}`}>
                  {activeTask.status === 'waiting' ? '等待决定' : activeTask.status === 'paused' ? '已暂停' : '进行中'}
                </span>
              </div>
              <div className="progress">
                <div
                  className="progress-bar"
                  style={{ width: `${Math.round((activeTask.current / activeTask.plan.steps.length) * 100)}%` }}
                />
              </div>
              <div className="task-strip-step">
                当前步骤：{activeTask.plan.steps[Math.min(activeTask.current, activeTask.plan.steps.length - 1)].label}
                （{activeTask.current}/{activeTask.plan.steps.length}）· 点击查看
              </div>
            </article>
          )}
          {seeded.map((s) => (
            <article key={s.id} className="task-strip">
              <div className="task-strip-top">
                <span className="task-strip-title">{s.title}</span>
                <span className="tag tag-run">进行中</span>
              </div>
              <div className="progress">
                <div className="progress-bar" style={{ width: `${s.progress}%` }} />
              </div>
              <div className="task-strip-step">{s.stepLabel} · {s.progress}%</div>
            </article>
          ))}
        </div>
      </section>

      <div className="two-col">
        <section>
          <div className="section-head">
            <h2>已完成</h2>
            <button className="link-btn" onClick={goReview}>
              去待审阅
            </button>
          </div>
          <div className="feed">
            {doneFeed.map((item) => (
              <div key={item.id} className="feed-item">
                <span className="feed-check">✓</span>
                <span className="feed-text">{item.text}</span>
                <span className="feed-link">{item.output}</span>
                <span className="feed-time">{item.time}</span>
              </div>
            ))}
          </div>
        </section>

        <section>
          <div className="section-head">
            <h2>活动日志</h2>
            <span className="section-note">审计记录</span>
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
    </div>
  );
}
