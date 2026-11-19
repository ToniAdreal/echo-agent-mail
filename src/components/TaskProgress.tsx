import { useState } from 'react';
import { AUTONOMY_LABELS, Autonomy, TaskPlan } from '../data';
import { IconCheck, IconClock, IconShieldCheck } from './icons';

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

const STATUS_META: Record<TaskStatus, { label: string; cls: string; sentence: string }> = {
  running: { label: '进行中', cls: 'pill-accent', sentence: 'Agent 正在执行，步骤完成后自动推进' },
  waiting: { label: '停在决策点', cls: 'pill-warn', sentence: '执行已暂停，等待你的决定' },
  paused: { label: '已暂停', cls: 'pill-neutral', sentence: '任务已暂停，等待你继续' },
  takenover: { label: '已转为手动', cls: 'pill-info', sentence: '已转为手动处理，Agent 已停止' },
  done: { label: '已完成', cls: 'pill-ok', sentence: '全部步骤已完成' },
  cancelled: { label: '已终止', cls: 'pill-danger', sentence: '任务已终止，未发送任何内容' },
};

export default function TaskProgress({ task, resolveGate, control, finalAction, goDelegate, goInbox }: Props) {
  const [editingResult, setEditingResult] = useState(false);
  const [resultText, setResultText] = useState('');

  if (!task) {
    return (
      <div className="view">
        <header className="view-head">
          <div className="kicker">WORKFLOW / NO ACTIVE TASK</div>
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
  const pct = Math.round((task.current / task.plan.steps.length) * 100);
  const draftBody = task.tone === 'formal' ? task.plan.toneFormal : task.plan.toneConcise;
  const active = task.status === 'running' || task.status === 'waiting' || task.status === 'paused';

  return (
    <div className="view">
      <header className="view-head with-pill">
        <div>
          <div className="kicker">WORKFLOW / TASK-{task.id.toUpperCase()}</div>
          <h1>任务进度</h1>
          <p className="view-sub">{task.title}</p>
        </div>
        <span className={`pill pill-lg ${meta.cls}`}>{meta.label}</span>
      </header>

      <section className="panel progress-panel">
        <div className="progress-top">
          <span className="progress-status">
            TASK-{task.id.toUpperCase()} · {meta.sentence} · 授权范围：{AUTONOMY_LABELS[task.autonomy]}
          </span>
          <span className="progress-pct">{pct}%</span>
        </div>
        <div className="progress progress-lg">
          <div className="progress-bar" style={{ width: `${pct}%` }} />
        </div>
      </section>

      {task.status === 'takenover' && (
        <div className="state-banner manual">
          已转为手动处理。Agent 已停止，不会再发送或修改任何内容。相关邮件在收件箱里，你可以自己回复。
          <div className="btn-row" style={{ marginTop: 10 }}>
            <button className="btn btn-dark" onClick={goInbox}>
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

      <div className="task-grid">
        <section className="panel timeline-panel">
          <div className="section-head">
            <h2>执行时间线</h2>
            <span className="pill pill-neutral">{task.plan.steps.length} 个步骤</span>
          </div>
          <ol className="timeline">
            {task.plan.steps.map((s, i) => {
              const state = i < task.current ? 'done' : i === task.current ? 'current' : 'todo';
              return (
                <li key={i} className={`tl-item ${state}`}>
                  <span className="tl-dot">
                    {state === 'done' ? (
                      <IconCheck size={14} />
                    ) : state === 'current' && task.status === 'waiting' ? (
                      <IconShieldCheck size={14} />
                    ) : state === 'current' ? (
                      <span className="tl-pulse" />
                    ) : (
                      <IconClock size={14} />
                    )}
                  </span>
                  <div className="tl-body">
                    <div className="tl-label">{s.label}</div>
                    {(state === 'done' || state === 'current') && <div className="tl-note">{s.note}</div>}
                  </div>
                  {state === 'done' && <span className="pill pill-ok">已完成</span>}
                  {state === 'current' &&
                    (task.status === 'waiting' ? (
                      <span className="pill pill-warn">等待审批</span>
                    ) : task.status === 'running' ? (
                      <span className="pill pill-accent">执行中</span>
                    ) : (
                      <span className="pill pill-neutral">当前步</span>
                    ))}
                  {state === 'todo' && <span className="pill pill-neutral">待执行</span>}
                </li>
              );
            })}
          </ol>
        </section>

        <div className="task-side">
          {task.status === 'waiting' && task.gate === 'tone' && (
            <section className="panel gate-panel">
              <span className="pill pill-warn">需要你选择</span>
              <h2 className="gate-heading">选择跟进方式</h2>
              <div className="tone-card selected">
                <div className="tone-head">
                  <span>方案 A · 正式版</span>
                  <span className="tone-rec">推荐</span>
                </div>
                <p className="tone-desc">措辞完整得体，适合正式对外沟通。</p>
                <pre className="tone-body clamp">{task.plan.toneFormal}</pre>
                <button className="btn btn-primary btn-block" onClick={() => resolveGate({ tone: 'formal' })}>
                  用正式版继续
                </button>
              </div>
              <div className="tone-card">
                <div className="tone-head">
                  <span>方案 B · 简洁版</span>
                </div>
                <p className="tone-desc">更短更直接，适合关系熟悉的对方。</p>
                <pre className="tone-body clamp">{task.plan.toneConcise}</pre>
                <button className="btn btn-dark btn-block" onClick={() => resolveGate({ tone: 'concise' })}>
                  用简洁版继续
                </button>
              </div>
            </section>
          )}

          {task.status === 'waiting' && task.gate === 'send' && (
            <section className="panel gate-panel">
              <span className="pill pill-warn">发送前确认</span>
              <h2 className="gate-heading">全自动模式 · 发送前确认</h2>
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
                <button className="btn btn-dark" onClick={() => resolveGate({ sendAction: 'save' })}>
                  先存草稿
                </button>
              </div>
            </section>
          )}

          {task.status === 'waiting' && task.gate === 'step' && (
            <section className="panel gate-panel">
              <span className="pill pill-warn">需要你确认</span>
              <h2 className="gate-heading">你选择了「每一步问我」</h2>
              <p className="gate-desc">Agent 准备执行下一步：{task.plan.steps[task.current]?.label}。确认后继续。</p>
              <div className="btn-row">
                <button className="btn btn-primary" onClick={() => resolveGate({})}>
                  继续执行
                </button>
              </div>
            </section>
          )}

          {task.status === 'done' ? (
            <section className="panel result-panel">
              <div className="section-head">
                <h2>已产出的结果草稿</h2>
                {task.finalAction === 'sent' ? (
                  <span className="pill pill-ok">已发送</span>
                ) : task.finalAction === 'saved' ? (
                  <span className="pill pill-info">已存入待审阅</span>
                ) : (
                  <span className="pill pill-warn">未发送</span>
                )}
              </div>
              <p className="gate-desc">{task.plan.resultSummary}</p>
              <div className="draft-rows">
                <div className="draft-row">
                  <span className="draft-row-label">收件人</span>
                  <span>{task.plan.draftTo}</span>
                </div>
                <div className="draft-row">
                  <span className="draft-row-label">主题</span>
                  <span>
                    {task.plan.draftSubject}
                    {task.tone && <span className="pill pill-neutral draft-tone-pill">{task.tone === 'formal' ? '正式版' : '简洁版'}</span>}
                  </span>
                </div>
              </div>
              {editingResult ? (
                <textarea
                  className="result-edit"
                  value={resultText}
                  onChange={(e) => setResultText(e.target.value)}
                  rows={9}
                />
              ) : (
                <pre className="tone-body draft-body-box">{draftBody}</pre>
              )}
              {task.finalAction === 'sent' && (
                <div className="state-banner done">已发送。你可以在活动日志里看到这次发送的审计记录。</div>
              )}
              {task.finalAction === 'saved' && (
                <div className="state-banner done">已存入「待审阅」，之后随时可以发送。</div>
              )}
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
                        className="btn btn-dark"
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
                        发送草稿
                      </button>
                      <button
                        className="btn btn-dark"
                        onClick={() => {
                          setResultText(draftBody);
                          setEditingResult(true);
                        }}
                      >
                        查看并修改
                      </button>
                      <button className="btn btn-ghost" onClick={() => finalAction('save')}>
                        存入待审阅
                      </button>
                    </>
                  )}
                </div>
              )}
            </section>
          ) : (
            active && (
              <section className="panel draft-preview-panel">
                <div className="section-head">
                  <h2>已产出的结果草稿</h2>
                  <span className="pill pill-warn">未发送</span>
                </div>
                <div className="draft-rows">
                  <div className="draft-row">
                    <span className="draft-row-label">收件人</span>
                    <span>{task.plan.draftTo}</span>
                  </div>
                  <div className="draft-row">
                    <span className="draft-row-label">主题</span>
                    <span>{task.plan.draftSubject}</span>
                  </div>
                </div>
                <pre className="tone-body clamp draft-body-box">{draftBody}</pre>
                <p className="draft-note">草稿已生成，任务完成后可发送、修改或存入待审阅。</p>
              </section>
            )
          )}

          {active && (
            <section className="panel controls-panel">
              <div className="section-head">
                <h2>任务控制</h2>
              </div>
              <div className="btn-row">
                {task.status === 'paused' ? (
                  <button className="btn btn-primary" onClick={() => control('resume')}>
                    继续
                  </button>
                ) : (
                  <button className="btn btn-dark" onClick={() => control('pause')} disabled={task.status === 'waiting'}>
                    暂停
                  </button>
                )}
                <button className="btn btn-dark" onClick={() => control('takeover')}>
                  接管
                </button>
                <button className="btn btn-danger-ghost" onClick={() => control('cancel')}>
                  终止
                </button>
              </div>
              <p className="draft-note">运行记录已保存 · 可随时暂停或手动接管</p>
            </section>
          )}
        </div>
      </div>
    </div>
  );
}
