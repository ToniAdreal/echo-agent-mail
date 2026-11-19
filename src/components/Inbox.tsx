import { useMemo, useState } from 'react';
import { Email } from '../data';
import { IconMail, IconSparkle } from './icons';

interface Props {
  emails: Email[];
  markRead: (id: string) => void;
  delegateFromEmail: (e: Email) => void;
  log: (text: string) => void;
  query: string;
}

const TAG_LABELS: Record<string, string> = {
  客户: '客户合作',
  会议: '会议与日程',
  财务: '财务账单',
  招聘: '招聘',
  纪要: '会议纪要',
  订阅: '订阅通知',
};

function initials(from: string): string {
  const ascii = from.replace(/[^A-Za-z ]/g, '').trim();
  if (ascii) {
    const parts = ascii.split(/\s+/);
    return (parts[0][0] + (parts[1]?.[0] ?? '')).toUpperCase();
  }
  return from.slice(0, 1);
}

export default function Inbox({ emails, markRead, delegateFromEmail, log, query }: Props) {
  const [folder, setFolder] = useState<string>('all');
  const [selectedId, setSelectedId] = useState<string>(emails[0]?.id ?? '');
  const [composing, setComposing] = useState(false);
  const [replyText, setReplyText] = useState('');
  const [sentNote, setSentNote] = useState(false);

  const unread = emails.filter((e) => e.unread).length;

  const tagFolders = useMemo(() => {
    const seen: { tag: string; count: number }[] = [];
    for (const e of emails) {
      const f = seen.find((x) => x.tag === e.tag);
      if (f) f.count += 1;
      else seen.push({ tag: e.tag, count: 1 });
    }
    return seen;
  }, [emails]);

  const filtered = useMemo(() => {
    let list = emails;
    if (folder === 'unread') list = list.filter((e) => e.unread);
    else if (folder.startsWith('tag:')) list = list.filter((e) => e.tag === folder.slice(4));
    const q = query.trim().toLowerCase();
    if (q) {
      list = list.filter(
        (e) =>
          e.subject.toLowerCase().includes(q) ||
          e.from.toLowerCase().includes(q) ||
          e.preview.toLowerCase().includes(q) ||
          e.body.join(' ').toLowerCase().includes(q),
      );
    }
    return list;
  }, [emails, folder, query]);

  const selected = emails.find((e) => e.id === selectedId) ?? filtered[0];

  const openEmail = (e: Email) => {
    setSelectedId(e.id);
    markRead(e.id);
    setComposing(false);
    setSentNote(false);
  };

  const sendReply = () => {
    if (!selected || !replyText.trim()) return;
    log(`你在收件箱手动回复了 ${selected.from} 的邮件「${selected.subject}」`);
    setReplyText('');
    setComposing(false);
    setSentNote(true);
  };

  const folderLabel =
    folder === 'all' ? '全部' : folder === 'unread' ? '未读' : TAG_LABELS[folder.slice(4)] ?? folder.slice(4);
  const now = new Date();
  const syncTime = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

  const folderBtn = (key: string, label: string, count: number) => (
    <button key={key} className={`folder-item ${folder === key ? 'active' : ''}`} onClick={() => setFolder(key)}>
      <IconMail size={16} />
      <span className="folder-label">{label}</span>
      <span className="folder-count">{count}</span>
    </button>
  );

  return (
    <div className="view">
      <header className="view-head">
        <div className="kicker">MAIL / YOUR WORKSPACE</div>
        <h1>收件箱</h1>
        <p className="view-sub">
          共 {emails.length} 封 · 未读 {unread} 封 · 最近同步 {syncTime}
        </p>
      </header>

      <div className="inbox-layout">
        <section className="panel folder-pane">
          <div className="pane-title">邮箱</div>
          {folderBtn('all', '收件箱', emails.length)}
          {folderBtn('unread', '未读邮件', unread)}
          {tagFolders.map((f) => folderBtn(`tag:${f.tag}`, TAG_LABELS[f.tag] ?? f.tag, f.count))}
          <div className="pane-divider" />
          <div className="pane-title">标签</div>
          <button className={`tag-row ${folder === 'unread' ? 'active' : ''}`} onClick={() => setFolder('unread')}>
            <span className="tag-dot dot-warn" />
            需要答复
            <span className="folder-count">{unread}</span>
          </button>
          <button
            className={`tag-row ${folder === 'tag:客户' ? 'active' : ''}`}
            onClick={() => setFolder('tag:客户')}
          >
            <span className="tag-dot dot-accent" />
            客户合作
            <span className="folder-count">{emails.filter((e) => e.tag === '客户').length}</span>
          </button>
          <button
            className={`tag-row ${folder === 'tag:财务' ? 'active' : ''}`}
            onClick={() => setFolder('tag:财务')}
          >
            <span className="tag-dot dot-info" />
            财务账单
            <span className="folder-count">{emails.filter((e) => e.tag === '财务').length}</span>
          </button>
        </section>

        <section className="panel list-pane">
          <div className="section-head">
            <h2>邮件列表</h2>
            <span className="pill pill-neutral">
              {folderLabel} {filtered.length}
            </span>
          </div>
          <div className="mail-list">
            {filtered.length === 0 && <div className="empty-mini">没有匹配的邮件</div>}
            {filtered.map((e) => (
              <button
                key={e.id}
                className={`mail-row ${selected?.id === e.id ? 'active' : ''}`}
                onClick={() => openEmail(e)}
              >
                <span className={`mail-avatar ${selected?.id === e.id ? 'accent' : ''}`}>{initials(e.from)}</span>
                <span className="mail-main">
                  <span className="mail-row-top">
                    <span className="mail-from">{e.from}</span>
                    <span className="mail-time">{e.time}</span>
                  </span>
                  <span className="mail-subject">{e.subject}</span>
                  <span className="mail-snippet">{e.preview}</span>
                </span>
                {e.unread && <span className="unread-dot" />}
              </button>
            ))}
          </div>
        </section>

        <section className="panel read-pane">
          {selected ? (
            <>
              <h2 className="read-subject">{selected.subject}</h2>
              <div className="read-pills">
                <span className="pill pill-accent">{TAG_LABELS[selected.tag] ?? selected.tag}</span>
                {selected.unread && <span className="pill pill-warn">未读</span>}
              </div>
              <div className="read-meta">
                <span className="mail-avatar accent">{initials(selected.from)}</span>
                <span className="read-meta-main">
                  <span className="read-from">
                    {selected.from} · {selected.role}
                  </span>
                  <span className="read-sub">收件人：Toni · {selected.time}</span>
                </span>
              </div>
              <div className="read-body">
                {selected.body.map((p, i) => (
                  <p key={i}>{p}</p>
                ))}
              </div>
              {sentNote && <div className="state-banner done">回复已发送（手动模式）。</div>}
              {composing ? (
                <div className="composer">
                  <div className="composer-head">回复 {selected.from}</div>
                  <textarea
                    value={replyText}
                    onChange={(e) => setReplyText(e.target.value)}
                    rows={6}
                    placeholder="写下你的回复…"
                  />
                  <div className="btn-row">
                    <button className="btn btn-primary" onClick={sendReply}>
                      发送
                    </button>
                    <button className="btn btn-ghost" onClick={() => setComposing(false)}>
                      取消
                    </button>
                  </div>
                </div>
              ) : (
                <div className="btn-row read-actions">
                  <button className="btn btn-dark" onClick={() => setComposing(true)}>
                    回复邮件
                  </button>
                </div>
              )}
              <div className="agent-cta">
                <span className="agent-cta-icon">
                  <IconSparkle size={17} />
                </span>
                <span className="agent-cta-main">
                  <span className="agent-cta-title">交给 Agent 处理</span>
                  <span className="agent-cta-desc">Agent 将起草回复并等待你的批准</span>
                </span>
                <button className="btn btn-primary" onClick={() => delegateFromEmail(selected)}>
                  开始委托
                </button>
              </div>
            </>
          ) : (
            <div className="empty-mini">选择一封邮件阅读</div>
          )}
        </section>
      </div>
    </div>
  );
}
