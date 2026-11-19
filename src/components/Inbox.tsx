import { useMemo, useState } from 'react';
import { Email } from '../data';

interface Props {
  emails: Email[];
  markRead: (id: string) => void;
  delegateFromEmail: (e: Email) => void;
  log: (text: string) => void;
}

export default function Inbox({ emails, markRead, delegateFromEmail, log }: Props) {
  const [query, setQuery] = useState('');
  const [selectedId, setSelectedId] = useState<string>(emails[0]?.id ?? '');
  const [composing, setComposing] = useState(false);
  const [replyText, setReplyText] = useState('');
  const [sentNote, setSentNote] = useState(false);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return emails;
    return emails.filter(
      (e) =>
        e.subject.toLowerCase().includes(q) ||
        e.from.toLowerCase().includes(q) ||
        e.preview.toLowerCase().includes(q) ||
        e.body.join(' ').toLowerCase().includes(q),
    );
  }, [emails, query]);

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

  return (
    <div className="view">
      <header className="view-head">
        <h1>收件箱</h1>
        <p className="view-sub">
          传统模式完整保留：所有邮件都在这里，你可以像过去一样逐封阅读和回复。想省事时，把任意一封交给 Agent。
        </p>
      </header>

      <div className="inbox-layout">
        <div className="inbox-list-pane">
          <input
            className="search-input"
            placeholder="搜索邮件（发件人、主题、内容）"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <div className="inbox-list">
            {filtered.length === 0 && <div className="empty-mini">没有匹配的邮件</div>}
            {filtered.map((e) => (
              <button
                key={e.id}
                className={`mail-row ${selected?.id === e.id ? 'active' : ''} ${e.unread ? 'unread' : ''}`}
                onClick={() => openEmail(e)}
              >
                <div className="mail-row-top">
                  <span className="mail-from">{e.from}</span>
                  <span className="mail-time">{e.time}</span>
                </div>
                <div className="mail-subject">{e.subject}</div>
                <div className="mail-preview">{e.preview}</div>
                <div className="mail-row-foot">
                  <span className="tag tag-plain">{e.tag}</span>
                  {e.unread && <span className="unread-dot" />}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="inbox-read-pane">
          {selected ? (
            <>
              <div className="read-head">
                <h2>{selected.subject}</h2>
                <div className="read-meta">
                  <span className="avatar avatar-sm">{selected.from.slice(0, 1)}</span>
                  <span>
                    {selected.from} · {selected.role}
                  </span>
                  <span className="read-time">{selected.time}</span>
                </div>
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
                  <button className="btn btn-primary" onClick={() => delegateFromEmail(selected)}>
                    交给 Agent
                  </button>
                  <button className="btn btn-soft" onClick={() => setComposing(true)}>
                    回复
                  </button>
                </div>
              )}
              <p className="read-note">
                「交给 Agent」会把你的目标预填到委托页，Agent 读完这封邮件的上下文再列计划；「回复」是你熟悉的手动写信。
              </p>
            </>
          ) : (
            <div className="empty-mini">选择一封邮件阅读</div>
          )}
        </div>
      </div>
    </div>
  );
}
