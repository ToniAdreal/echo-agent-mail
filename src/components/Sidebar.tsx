import { ViewKey } from '../data';
import {
  IconArchive,
  IconBolt,
  IconGear,
  IconGrid,
  IconList,
  IconMail,
  IconPlus,
  IconShieldCheck,
  IconSparkle,
} from './icons';

interface Props {
  view: ViewKey;
  setView: (v: ViewKey) => void;
  counts: { decisions: number; review: number; unread: number; taskActive: number };
}

const WORKSPACE: { key: ViewKey; label: string; Icon: (p: { size?: number }) => JSX.Element }[] = [
  { key: 'briefing', label: '今日简报', Icon: IconGrid },
  { key: 'delegate', label: '委托工作', Icon: IconSparkle },
  { key: 'task', label: '任务进度', Icon: IconList },
];

export default function Sidebar({ view, setView, counts }: Props) {
  const item = (key: ViewKey, label: string, Icon: (p: { size?: number }) => JSX.Element, badge = 0) => (
    <button key={key} className={`nav-item ${view === key ? 'active' : ''}`} onClick={() => setView(key)}>
      <Icon size={17} />
      <span className="nav-label">{label}</span>
      {badge > 0 && <span className="nav-badge">{badge}</span>}
    </button>
  );

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-row">
          {/* public/logo-silver.png，相对路径以适配 ./ base 部署 */}
          <img className="brand-logo" src="logo-silver.png" alt="Intenda 标记" />
          <span className="brand-name">Intenda</span>
          <span className="brand-cn">意达</span>
        </div>
        <div className="brand-sub">AGENT-NATIVE EMAIL</div>
      </div>

      <button className="new-delegate-btn" onClick={() => setView('delegate')}>
        <IconPlus size={16} />
        新建委托
      </button>

      <nav className="nav">
        <div className="nav-group">WORKSPACE</div>
        {WORKSPACE.map((n) => item(n.key, n.label, n.Icon))}
        <div className="nav-group">COMMUNICATION</div>
        {item('inbox', '收件箱', IconMail, counts.unread)}
        {item('review', '待审阅', IconShieldCheck, counts.review)}
        <div className="nav-item static">
          <IconBolt size={17} />
          <span className="nav-label">自动化</span>
        </div>
        <div className="nav-item static">
          <IconArchive size={17} />
          <span className="nav-label">归档</span>
        </div>
      </nav>

      <div className="sidebar-foot">
        <div className="nav-item static">
          <IconGear size={17} />
          <span className="nav-label">设置</span>
        </div>
        <div className="agent-status">
          <span className="status-dot" />
          Agent 已连接
        </div>
      </div>
    </aside>
  );
}
