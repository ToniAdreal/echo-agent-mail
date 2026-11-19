import { ViewKey } from '../data';
import { IconBell, IconSearch } from './icons';

const CRUMBS: Record<ViewKey, string> = {
  briefing: '今日简报',
  delegate: '委托工作',
  task: '任务进度',
  review: '待审阅',
  inbox: '收件箱',
};

interface Props {
  view: ViewKey;
  query: string;
  onQuery: (q: string) => void;
}

export default function Topbar({ view, query, onQuery }: Props) {
  return (
    <div className="topbar">
      <div className="crumb">
        <span className="crumb-brand">INTENDA</span>
        <span className="crumb-sep">/</span>
        <span className="crumb-here">{CRUMBS[view]}</span>
      </div>
      <div className="topbar-right">
        <label className="top-search">
          <IconSearch size={15} />
          <input
            value={query}
            onChange={(e) => onQuery(e.target.value)}
            placeholder="搜索邮件、任务或联系人"
            aria-label="搜索邮件"
          />
        </label>
        <button className="icon-btn" aria-label="通知">
          <IconBell size={17} />
          <span className="bell-dot" />
        </button>
        <div className="account-chip">
          <span className="account-avatar">T</span>
          <span className="account-label">工作账户</span>
        </div>
      </div>
    </div>
  );
}
