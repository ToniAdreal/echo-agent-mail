import { useEffect, useRef, useState } from 'react';
import { Bell, LogOut, PenLine, RefreshCw, Search, Settings } from 'lucide-react';
import { api, type MailAccount } from '../lib/api';
import { useApp } from '../lib/appctx';
import { fmtTime, initials, navigate, timeAgo, useRoute } from '../lib/ui';

const CRUMBS: Record<string, string> = {
  '/briefing': 'Today Briefing',
  '/delegate': 'Delegate Work',
  '/tasks': 'Task Progress',
  '/inbox': 'Inbox',
  '/review': 'Review Queue',
  '/automations': 'Automations',
  '/archive': 'Archive',
  '/settings': 'Settings',
};

interface Notification {
  id: string;
  title: string;
  body: string | null;
  read_at: string | null;
  created_at: string;
  resource_type: string | null;
  resource_id: string | null;
}

export default function Topbar() {
  const route = useRoute();
  const { me, logout, openComposer, environment } = useApp();
  const [accounts, setAccounts] = useState<MailAccount[]>([]);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any | null>(null);
  const [searchFocus, setSearchFocus] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [bellOpen, setBellOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unread, setUnread] = useState(0);
  const menuRef = useRef<HTMLDivElement>(null);
  const bellRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLDivElement>(null);

  const loadAccounts = () =>
    api<{ items: MailAccount[] }>('/api/v1/mail-accounts')
      .then((d) => setAccounts(d.items))
      .catch(() => {});
  const loadNotifications = () =>
    api<{ items: Notification[]; unread_count: number }>('/api/v1/notifications')
      .then((d) => {
        setNotifications(d.items);
        setUnread(d.unread_count);
      })
      .catch(() => {});

  useEffect(() => {
    loadAccounts();
    loadNotifications();
    const t = window.setInterval(() => {
      loadAccounts();
      loadNotifications();
    }, 30000);
    return () => window.clearInterval(t);
  }, []);

  useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      if (!menuRef.current?.contains(e.target as Node)) setMenuOpen(false);
      if (!bellRef.current?.contains(e.target as Node)) setBellOpen(false);
      if (!searchRef.current?.contains(e.target as Node)) setSearchFocus(false);
    };
    document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, []);

  useEffect(() => {
    if (query.trim().length < 2) {
      setResults(null);
      return;
    }
    const t = window.setTimeout(() => {
      api(`/api/v1/search?q=${encodeURIComponent(query.trim())}`)
        .then(setResults)
        .catch(() => setResults(null));
    }, 300);
    return () => window.clearTimeout(t);
  }, [query]);

  const account = accounts[0];
  const syncing = account?.sync_status === 'syncing';
  const crumb = CRUMBS[route] ?? (route.startsWith('/tasks/') ? 'Task Progress' : 'Intenda');

  const openNotification = (n: Notification) => {
    api(`/api/v1/notifications/${n.id}/read`, { method: 'POST', body: {} })
      .then(loadNotifications)
      .catch(() => {});
    setBellOpen(false);
    if (n.resource_type === 'task' && n.resource_id) navigate(`/tasks/${n.resource_id}`);
    else if (n.resource_type === 'review_item') navigate('/review');
    else if (n.resource_type === 'automation') navigate('/automations');
  };

  return (
    <header className="topbar">
      <div className="crumb">
        <span className="crumb-brand">INTENDA</span>
        <span className="crumb-sep">/</span>
        <span className="crumb-here">{crumb}</span>
        {environment === 'demo' && (
          <span className="demo-label" style={{ marginLeft: 8 }}>
            Demo data
          </span>
        )}
      </div>
      <div className="topbar-right">
        <span className="pill pill-neutral" title={account ? `Last synced ${timeAgo(account.last_sync_at)}` : ''}>
          {syncing ? <RefreshCw size={13} className="spin" /> : null}
          {account ? (syncing ? 'Syncing…' : `Synced ${timeAgo(account.last_sync_at)}`) : 'No mailbox'}
        </span>
        <div className="search-wrap" ref={searchRef}>
          <div className="top-search">
            <Search size={15} />
            <input
              placeholder="Search mail, tasks, people…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => setSearchFocus(true)}
              aria-label="Search mail, tasks and people"
            />
          </div>
          {searchFocus && results && (
            <div className="search-results">
              {results.messages?.length > 0 && (
                <>
                  <div className="pane-title">Messages</div>
                  {results.messages.slice(0, 5).map((msg: any) => (
                    <button
                      key={msg.id}
                      className="menu-item"
                      onClick={() => {
                        setSearchFocus(false);
                        setQuery('');
                        navigate(`/inbox?message=${msg.id}`);
                      }}
                    >
                      <span style={{ flex: 1, minWidth: 0 }}>
                        <span style={{ display: 'block', fontWeight: 600 }}>{msg.subject}</span>
                        <span style={{ display: 'block', fontSize: 12, color: 'var(--t3)' }}>
                          {msg.from.name ?? msg.from.email} · {fmtTime(msg.created_at)}
                        </span>
                      </span>
                    </button>
                  ))}
                </>
              )}
              {results.tasks?.length > 0 && (
                <>
                  <div className="pane-title">Tasks</div>
                  {results.tasks.slice(0, 5).map((t: any) => (
                    <button
                      key={t.id}
                      className="menu-item"
                      onClick={() => {
                        setSearchFocus(false);
                        setQuery('');
                        navigate(`/tasks/${t.id}`);
                      }}
                    >
                      <span className="mono" style={{ fontSize: 12 }}>
                        {t.display_id}
                      </span>
                      <span style={{ flex: 1 }}>{t.title}</span>
                    </button>
                  ))}
                </>
              )}
              {results.contacts?.length > 0 && (
                <>
                  <div className="pane-title">People</div>
                  {results.contacts.slice(0, 5).map((c: any) => (
                    <div key={c.id} className="menu-item" style={{ cursor: 'default' }}>
                      <span style={{ flex: 1 }}>
                        {c.name} <span style={{ color: 'var(--t3)' }}>{c.email}</span>
                      </span>
                    </div>
                  ))}
                </>
              )}
              {!results.messages?.length && !results.tasks?.length && !results.contacts?.length && (
                <div className="empty-mini">No results for “{query}”.</div>
              )}
            </div>
          )}
        </div>
        <button className="btn btn-primary" onClick={() => openComposer({ mode: 'new' })}>
          <PenLine size={15} /> Compose
        </button>
        <div className="account-menu-wrap" ref={bellRef}>
          <button className="icon-btn" aria-label="Notifications" onClick={() => setBellOpen((v) => !v)}>
            <Bell size={17} />
            {unread > 0 && <span className="bell-dot" />}
          </button>
          {bellOpen && (
            <div className="account-menu" style={{ width: 340 }}>
              <div className="account-menu-head">
                <div className="nm">Notifications</div>
                <div className="em">{unread} unread</div>
              </div>
              {notifications.length === 0 && <div className="empty-mini">No notifications yet.</div>}
              {notifications.slice(0, 10).map((n) => (
                <button key={n.id} className="menu-item" onClick={() => openNotification(n)}>
                  <span style={{ flex: 1, minWidth: 0 }}>
                    <span style={{ display: 'block', fontWeight: n.read_at ? 500 : 700 }}>{n.title}</span>
                    {n.body && (
                      <span style={{ display: 'block', fontSize: 12, color: 'var(--t3)' }}>{n.body}</span>
                    )}
                    <span style={{ display: 'block', fontSize: 11.5, color: 'var(--t4)' }}>
                      {timeAgo(n.created_at)}
                    </span>
                  </span>
                  {!n.read_at && <span className="unread-dot" />}
                </button>
              ))}
            </div>
          )}
        </div>
        <div className="account-menu-wrap" ref={menuRef}>
          <button
            className="account-chip"
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit' }}
            aria-haspopup="menu"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((v) => !v)}
          >
            <span className="account-avatar">{initials(me.name)}</span>
            <span>{me.name}</span>
          </button>
          {menuOpen && (
            <div className="account-menu" role="menu">
              <div className="account-menu-head">
                <div className="nm">{me.name}</div>
                <div className="em">{me.email}</div>
              </div>
              <button
                className="menu-item"
                onClick={() => {
                  setMenuOpen(false);
                  navigate('/settings');
                }}
              >
                <Settings size={15} /> Settings
              </button>
              <button
                className="menu-item danger"
                onClick={() => {
                  setMenuOpen(false);
                  logout();
                }}
              >
                <LogOut size={15} /> Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
