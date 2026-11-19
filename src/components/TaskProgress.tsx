import { useState } from 'react';
import { AUTONOMY_LABELS, Autonomy, TaskPlan } from '../data';

export type TaskStatus = 'running' | 'waiting' | 'paused' | 'takenover' | 'done' | 'cancelled';

export interface TaskState {
  id: string;
  title: string;
  intent: string;
  autonomy: Autonomy;
  plan: TaskPlan;
  current: number;
  status: TaskStatus;
  gate: 'tone' | 'send' | 'step' | null;
  tone: 'formal' | 'concise' | null;
  finalAction: 'sent' | 'saved' | null;
}

interface Props {
  task: TaskState | null;
  resolveGate: (payload: { tone?: 'formal' | 'concise'; sendAction?: 'send' | 'save' }) => void;
  control: (action: 'pause' | 'resume' | 'takeover' | 'cancel') => void;
  finalAction: (action: 'send' | 'save', editedBody?: string) => void;
  goDelegate: () => void;
  goInbox: () => void;
}

const STATUS_META: Record<TaskStatus, { label: string; cls: string }> = {
  running: { label: '进行中', cls: 'tag-run' },
  waiting: { label: '等待决定', cls: 'tag-wait' },
  paused: { label: '已暂停', cls: 'tag-pause' },
  takenover: { label: '已转为手动', cls: 'tag-manual' },
  done: { label: '已完成', cls: 'tag-done' },
  cancelled: { label: '已终止', cls: 'tag-stop' },
};

export default function TaskProgress({ task, resolveGate, control, finalAction, goDelegate, goInbox }: Props) {
  const [editingResult, setEditingResult] = useState(false);
  const [resultText, setResultText] = useState('');

  if (!task) {
    return (
      <div className="view">
        <header className="view-head">
          <h1>任务进度</h1>
          <p className="view-sub">还没有正在执行的任务。</p>
        </header>
        <div className="empty-card">
          去「委托」页告诉 Agent 你想达成什么结果，任务会在这里实时推进。
          <div className="btn-row" style={{ marginTop: 14 }}>
            <button className="btn btn-primary" onClick={goDelegate}>
              去委托一件事
            </button>
          </div>
        </div>
      </div>
    );
  }

  const meta = STATUS_META[task.status];
  const draftBody = task.tone === 'formal' ? task.plan.toneFormal : task.plan.toneConcise;
  const active = task.status === 'running' || task.status === 'waiting' || task.status === 'paused';

  return (
    <div className="view">
      <header className="view-head">
        <h1>任务进度</h1>
        <p className="view-sub">每一步都留有 Agent 的判断说明。你可以在任何时刻暂停、接管或终止。</p>
      </header>

      <section className="task-card">
        <div className="task-head">
          <div>
            <h2 className="task-title">{task.title}</h2>
            <div className="task-meta">
              授权范围：{AUTONOMY_LABELS[task.autonomy]} · 收件对象：{task.plan.draftTo}
            </div>
          </div>
          <span className={`tag ${meta.cls}`}>{meta.label}</span>
        </div>

        <div className="progress progress-lg">
          <div
            className="progress-bar"
            style={{ width: `${Math.round((task.current / task.plan.steps.length) * 100)}%` }}
          />
        </div>

        <ol className="timeline">
          {task.plan.steps.map((s, i) => {
            const state = i < task.current ? 'done' : i === task.current ? 'current' : 'todo';
            return (
              <li key={i} className={`tl-item ${state}`}>
                <span className="tl-dot">{state === 'done' ? '✓' : i + 1}</span>
                <div className="tl-body">
                  <div className="tl-label">
                    {s.label}
                    {state === 'current' && task.status === 'running' && <span className="pulse-text">执行中…</span>}
                    {state === 'current' && task.status === 'waiting' && <span className="pulse-text amber">等你决定</span>}
                  </div>
                  {(state === 'done' || state === 'current') && <div className="tl-note">{s.note}</div>}
                </div>
              </li>
            );
          })}
        </ol>

        {task.status === 'waiting' && task.gate === 'step' && (
          <div className="gate-card">
            <div className="gate-title">你选择了「每一步问我」</div>
            <p className="gate-desc">
              Agent 准备执行下一步：{task.plan.steps[task.current]?.label}。确认后继续。
            </p>
            <div className="btn-row">
              <button className="btn btn-primary" onClick={() => resolveGate({})}>
                继续执行
              </button>
            </div>
          </div>
        )}

        {task.status === 'waiting' && task.gate === 'tone' && (
          <div className="gate-card">
            <div className="gate-title">Agent 需要你定一个语气</div>
            <p className="gate-desc">草稿已生成两个版本，选一个，Agent 就继续发送并记录跟进。</p>
            <div className="tone-grid">
              <div className="tone-card">
                <div className="tone-head">正式版</div>
                <pre className="tone-body">{task.plan.toneFormal}</pre>
                <button className="btn btn-primary" onClick={() => resolveGate({ tone: 'formal' })}>
                  用正式版继续
                </button>
              </div>
              <div className="tone-card">
                <div className="tone-head">简洁版</div>
                <pre className="tone-body">{task.plan.toneConcise}</pre>
                <button className="btn btn-primary" onClick={() => resolveGate({ tone: 'concise' })}>
                  用简洁版继续
                </button>
              </div>
            </div>
          </div>
        )}

        {task.status === 'waiting' && task.gate === 'send' && (
          <div className="gate-card">
            <div className="gate-title">发送前确认（全自动模式）</div>
            <p className="gate-desc">
              Agent 已自行选定简洁版草稿并完成全部准备。发送对象：{task.plan.draftTo}。
            </p>
            <div className="mail-preview">
              <div className="mail-preview-head">
                <span>主题：{task.plan.draftSubject}</span>
              </div>
              <pre className="tone-body">{task.plan.toneConcise}</pre>
            </div>
            <div className="btn-row">
              <button className="btn btn-primary" onClick={() => resolveGate({ sendAction: 'send' })}>
                确认发送
              </button>
              <button className="btn btn-soft" onClick={() => resolveGate({ sendAction: 'save' })}>
                先存草稿
              </button>
            </div>
          </div>
        )}

        {active && (
          <div className="btn-row task-controls">
            {task.status === 'paused' ? (
              <button className="btn btn-primary" onClick={() => control('resume')}>
                继续
              </button>
            ) : (
              <button className="btn btn-soft" onClick={() => control('pause')} disabled={task.status === 'waiting'}>
                暂停
              </button>
            )}
            <button className="btn btn-soft" onClick={() => control('takeover')}>
              接管
            </button>
            <button className="btn btn-danger-ghost" onClick={() => control('cancel')}>
              终止
            </button>
          </div>
        )}

        {task.status === 'takenover' && (
          <div className="state-banner manual">
            已转为手动处理。Agent 已停止，不会再发送或修改任何内容。相关邮件在收件箱里，你可以自己回复。
            <div className="btn-row" style={{ marginTop: 10 }}>
              <button className="btn btn-soft" onClick={goInbox}>
                打开收件箱
              </button>
              <button className="btn btn-ghost" onClick={goDelegate}>
                重新委托
              </button>
            </div>
          </div>
        )}

        {task.status === 'cancelled' && (
          <div className="state-banner stopped">
            任务已终止。已完成的步骤保留在活动日志里，未发送任何内容。
            <div className="btn-row" style={{ marginTop: 10 }}>
              <button className="btn btn-ghost" onClick={goDelegate}>
                重新委托
              </button>
            </div>
          </div>
        )}

        {task.status === 'done' && (
          <div className="result-card">
            <div className="gate-title">结果</div>
            <p className="gate-desc">{task.plan.resultSummary}</p>
            <div className="mail-preview">
              <div className="mail-preview-head">
                <span>
                  收件人：{task.plan.draftTo} · 主题：{task.plan.draftSubject}
                </span>
                {task.tone && <span className="tag tag-done">{task.tone === 'formal' ? '正式版' : '简洁版'}</span>}
              </div>
              {editingResult ? (
                <textarea
                  className="result-edit"
                  value={resultText}
                  onChange={(e) => setResultText(e.target.value)}
                  rows={9}
                />
              ) : (
                <pre className="tone-body">{draftBody}</pre>
              )}
            </div>
            {task.finalAction === 'sent' && <div className="state-banner done">已发送。你可以在活动日志里看到这次发送的审计记录。</div>}
            {task.finalAction === 'saved' && <div className="state-banner done">已存入「待审阅」，之后随时可以发送。</div>}
            {task.finalAction === null && (
              <div className="btn-row">
                {editingResult ? (
                  <>
                    <button
                      className="btn btn-primary"
                      onClick={() => {
                        finalAction('send', resultText);
                        setEditingResult(false);
                      }}
                    >
                      发送修改版
                    </button>
                    <button
                      className="btn btn-soft"
                      onClick={() => {
                        finalAction('save', resultText);
                        setEditingResult(false);
                      }}
                    >
                      存修改版
                    </button>
                    <button className="btn btn-ghost" onClick={() => setEditingResult(false)}>
                      取消编辑
                    </button>
                  </>
                ) : (
                  <>
                    <button className="btn btn-primary" onClick={() => finalAction('send')}>
                      发送
                    </button>
                    <button
                      className="btn btn-soft"
                      onClick={() => {
                        setResultText(draftBody);
                        setEditingResult(true);
                      }}
                    >
                      再改改
                    </button>
                    <button className="btn btn-ghost" onClick={() => finalAction('save')}>
                      存草稿
                    </button>
                  </>
                )}
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
