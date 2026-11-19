import { useEffect, useState } from 'react';
import { AUTONOMY_DESCS, AUTONOMY_LABELS, Autonomy, PRESET_INTENTS, buildPlan } from '../data';
import { IconCalendar, IconFile, IconMail, IconPaperclip, IconShieldCheck } from './icons';

interface Props {
  prefill: string;
  onLaunch: (intent: string, autonomy: Autonomy) => void;
  hasActiveTask: boolean;
}

export default function Delegate({ prefill, onLaunch, hasActiveTask }: Props) {
  const [intent, setIntent] = useState('');
  const [autonomy, setAutonomy] = useState<Autonomy>('keypoints');
  const [planned, setPlanned] = useState<string | null>(null);

  useEffect(() => {
    if (prefill) {
      setIntent(prefill);
      setPlanned(prefill);
    }
  }, [prefill]);

  const plan = planned ? buildPlan(planned) : null;

  const submit = (text: string) => {
    const t = text.trim();
    if (!t) return;
    setIntent(t);
    setPlanned(t);
  };

  return (
    <div className="view">
      <header className="view-head">
        <div className="kicker">DELEGATE / TASK CREATION</div>
        <h1>委托工作</h1>
        <p className="view-sub">像给同事交代工作一样告诉 Intenda 你的目标。</p>
      </header>

      <section className="panel intent-card">
        <div className="intent-pills">
          <span className="pill pill-accent">自然语言委托</span>
          {planned && <span className="pill pill-neutral">计划已生成</span>}
          <span className="intent-hint">Agent 将自动理解历史邮件和关联上下文</span>
        </div>
        <textarea
          id="intent-input"
          className="intent-textarea"
          rows={3}
          placeholder="告诉 Agent 你想完成什么…"
          value={intent}
          onChange={(e) => setIntent(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              submit(intent);
            }
          }}
        />
        <div className="intent-foot">
          <div className="chip-row">
            <span className="ctx-chip">
              <IconPaperclip size={14} />
              {plan ? `收件对象：${plan.draftTo}` : '发送后自动关联上下文'}
            </span>
            {plan && <span className="ctx-chip">主题：{plan.draftSubject}</span>}
          </div>
          <button className="btn btn-primary btn-lg" onClick={() => submit(intent)}>
            {planned ? '重新生成计划' : '发送指令'}
          </button>
        </div>
        <div className="chip-row example-row">
          <span className="example-label">快捷示例：</span>
          {PRESET_INTENTS.map((p) => (
            <button key={p} className="chip" onClick={() => submit(p)}>
              {p}
            </button>
          ))}
        </div>
      </section>

      {plan && planned && (
        <>
          <div className="delegate-grid">
            <section className="panel">
              <div className="section-head">
                <h2>Agent 读取的上下文</h2>
                <span className="pill pill-accent">来源可追溯</span>
              </div>
              <div className="ctx-list">
                <div className="ctx-item">
                  <span className="ctx-icon">
                    <IconMail size={17} />
                  </span>
                  <span className="ctx-main">
                    <span className="ctx-title">{plan.draftTo} · 相关邮件线程</span>
                    <span className="ctx-sub">{plan.steps[0].note}</span>
                  </span>
                </div>
                <div className="ctx-item">
                  <span className="ctx-icon">
                    <IconFile size={17} />
                  </span>
                  <span className="ctx-main">
                    <span className="ctx-title">{plan.draftSubject}</span>
                    <span className="ctx-sub">{plan.steps[1].note}</span>
                  </span>
                </div>
                <div className="ctx-item">
                  <span className="ctx-icon">
                    <IconCalendar size={17} />
                  </span>
                  <span className="ctx-main">
                    <span className="ctx-title">日程与既有承诺</span>
                    <span className="ctx-sub">涉及时间与承诺的表述会与邮件原文逐项核对，不凭空添加。</span>
                  </span>
                </div>
                <div className="ctx-item">
                  <span className="ctx-icon">
                    <IconShieldCheck size={17} />
                  </span>
                  <span className="ctx-main">
                    <span className="ctx-title">授权边界</span>
                    <span className="ctx-sub">外发动作将遵循下方所选的授权档位，超出范围立即停下。</span>
                  </span>
                </div>
              </div>
            </section>

            <section className="panel">
              <div className="section-head">
                <h2>执行计划</h2>
                <span className="pill pill-neutral">{plan.steps.length} 个步骤</span>
              </div>
              <ol className="plan-steps">
                {plan.steps.map((s, i) => (
                  <li key={i} className="plan-step">
                    <span className="plan-num">{String(i + 1).padStart(2, '0')}</span>
                    <div className="plan-step-main">
                      <div className="plan-step-label">{s.label}</div>
                      <div className="plan-step-note">{s.note}</div>
                    </div>
                    {s.gate ? (
                      <span className="pill pill-warn">等待授权</span>
                    ) : (
                      <span className="pill pill-neutral">待执行</span>
                    )}
                  </li>
                ))}
              </ol>
            </section>
          </div>

          <section className="panel autonomy-panel">
            <div className="autonomy-head">
              <div>
                <h2>授权范围</h2>
                <p className="autonomy-desc">为当前委托设定 Agent 的执行权限，所选档位会真实决定任务在哪些节点停下。</p>
              </div>
            </div>
            <div className="autonomy-options">
              {(Object.keys(AUTONOMY_LABELS) as Autonomy[]).map((key) => (
                <button
                  key={key}
                  className={`autonomy-option ${autonomy === key ? 'selected' : ''}`}
                  onClick={() => setAutonomy(key)}
                >
                  <span className="autonomy-option-name">{AUTONOMY_LABELS[key]}</span>
                  <span className="autonomy-option-desc">{AUTONOMY_DESCS[key]}</span>
                </button>
              ))}
            </div>
            <div className="autonomy-foot">
              {hasActiveTask && <span className="warn-text">已有任务在进行中，启动新任务会替换它</span>}
              <button className="btn btn-primary btn-lg" onClick={() => onLaunch(planned, autonomy)}>
                开始执行
              </button>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
