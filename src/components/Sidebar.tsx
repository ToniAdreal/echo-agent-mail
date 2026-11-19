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
        <div className="brand-mark">回</div>
        <div className="brand-text">
          <div className="brand-name">回声 Echo</div>
          <div className="brand-sub">Agent Native 邮箱</div>
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
