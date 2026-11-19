import { useEffect, useState } from 'react';
import { AUTONOMY_DESCS, AUTONOMY_LABELS, Autonomy, PRESET_INTENTS, buildPlan } from '../data';

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
        <h1>委托一件事</h1>
        <p className="view-sub">
          不用再一封封点开邮件。说清你想达成什么结果，Agent 会读上下文、列出计划、在你的授权范围内执行。
        </p>
      </header>

      <section className="delegate-card">
        <label className="delegate-label" htmlFor="intent-input">
          想达成什么结果？
        </label>
        <div className="intent-row">
          <input
            id="intent-input"
            className="intent-input"
            placeholder="例如：跟进上周没回复的客户询价"
            value={intent}
            onChange={(e) => setIntent(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') submit(intent);
            }}
          />
          <button className="btn btn-primary btn-lg" onClick={() => submit(intent)}>
            生成计划
          </button>
        </div>
        <div className="chip-row">
          {PRESET_INTENTS.map((p) => (
            <button key={p} className="chip" onClick={() => submit(p)}>
              {p}
            </button>
          ))}
        </div>
      </section>

      {plan && planned && (
        <section className="plan-card">
          <div className="section-head">
            <h2>Agent 的计划</h2>
            <span className="section-note">目标：{planned}</span>
          </div>
          <ol className="plan-steps">
            {plan.steps.map((s, i) => (
              <li key={i} className="plan-step">
                <span className="plan-num">{i + 1}</span>
                <div>
                  <div className="plan-step-label">
                    {s.label}
                    {s.gate === 'tone' && <span className="tag tag-wait">到这里会问你</span>}
                  </div>
                  <div className="plan-step-note">{s.note}</div>
                </div>
              </li>
            ))}
          </ol>

          <div className="autonomy-select">
            <div className="autonomy-select-title">这次任务的授权范围</div>
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
          </div>

          <div className="btn-row">
            <button className="btn btn-primary btn-lg" onClick={() => onLaunch(planned, autonomy)}>
              启动任务
            </button>
            {hasActiveTask && <span className="warn-text">已有任务在进行中，启动新任务会替换它</span>}
          </div>
        </section>
      )}

      <section className="delegate-explain">
        <h2>委托和传统写邮件有什么不同</h2>
        <div className="explain-grid">
          <div className="explain-item">
            <div className="explain-title">你说结果，它找上下文</div>
            <p>Agent 会自己定位相关邮件、读完整个线程再动手，不需要你先翻出原信转发给它。</p>
          </div>
          <div className="explain-item">
            <div className="explain-title">计划先行，随时可见</div>
            <p>执行前先给出分步计划，执行中每一步都有简短的判断说明，不是黑盒。</p>
          </div>
          <div className="explain-item">
            <div className="explain-title">授权有边界</div>
            <p>每个任务单独设定授权范围。涉及对外承诺的步骤，永远停在你这里。</p>
          </div>
        </div>
      </section>
    </div>
  );
}
