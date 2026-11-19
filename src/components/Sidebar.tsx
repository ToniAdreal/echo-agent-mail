import { ViewKey } from '../data';

interface Props {
  view: ViewKey;
  setView: (v: ViewKey) => void;
  counts: { decisions: number; review: number; unread: number; taskActive: number };
}

const NAV: { key: ViewKey; label: string; hint: string }[] = [
  { key: 'briefing', label: '今日简报', hint: 'Briefing' },
  { key: 'delegate', label: '委托', hint: 'Delegate' },
  { key: 'task', label: '任务进度', hint: 'Progress' },
  { key: 'review', label: '待审阅', hint: 'Review' },
  { key: 'inbox', label: '收件箱', hint: 'Inbox' },
];

export default function Sidebar({ view, setView, counts }: Props) {
  const badge = (key: ViewKey): number => {
    if (key === 'briefing') return counts.decisions;
    if (key === 'review') return counts.review;
    if (key === 'inbox') return counts.unread;
    if (key === 'task') return counts.taskActive;
    return 0;
  };

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark" aria-hidden="true">
          <svg width="46" height="30" viewBox="0 0 72 40" fill="none">
            <defs>
              <linearGradient id="intendaMetal" x1="0" y1="0" x2="0" y2="40" gradientUnits="userSpaceOnUse">
                <stop offset="0" stopColor="#EDF1F4" />
                <stop offset="0.45" stopColor="#C5CED3" />
                <stop offset="1" stopColor="#8E9AA1" />
              </linearGradient>
            </defs>
            <polygon points="13,7 25,20 13,33 1,20" fill="url(#intendaMetal)" />
            <polygon points="30,29 38,26 51,4 57,14 68,19 59,22 54,33 49,23 41,27" fill="url(#intendaMetal)" />
          </svg>
        </div>
        <div className="brand-text">
          <div className="brand-name">Intenda</div>
          <div className="brand-sub">意达 · AGENT-NATIVE EMAIL</div>
        </div>
      </div>

      <nav className="nav">
        {NAV.map((item) => (
          <button
            key={item.key}
            className={`nav-item ${view === item.key ? 'active' : ''}`}
            onClick={() => setView(item.key)}
          >
            <span className="nav-label">{item.label}</span>
            <span className="nav-hint">{item.hint}</span>
            {badge(item.key) > 0 && <span className="nav-badge">{badge(item.key)}</span>}
          </button>
        ))}
      </nav>

      <div className="sidebar-foot">
        <div className="autonomy-card">
          <div className="autonomy-title">默认授权范围</div>
          <div className="autonomy-row">
            <span className="dot dot-green" /> 整理类：可自动执行
          </div>
          <div className="autonomy-row">
            <span className="dot dot-amber" /> 起草类：发送前确认
          </div>
          <div className="autonomy-row">
            <span className="dot dot-red" /> 承诺类：必须你决定
          </div>
        </div>
        <div className="user-chip">
          <div className="avatar">T</div>
          <div>
            <div className="user-name">Toni Adreal</div>
            <div className="user-mail">toni@tokenta.space</div>
          </div>
        </div>
      </div>
    </aside>
  );
}
