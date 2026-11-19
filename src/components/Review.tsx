import { useEffect, useMemo, useState } from 'react';
import { Draft } from '../data';
import { IconMail, IconSparkle } from './icons';

interface Props {
  drafts: Draft[];
  draftAction: (id: string, action: 'send' | 'discard' | 'edit', body?: string) => void;
}

type Filter = 'all' | 'pending' | 'changes' | 'rejected';
type QueueItem = { draft: Draft; kind: 'live' | 'rejected' };

export default function Review({ drafts, draftAction }: Props) {
  const [filter, setFilter] = useState<Filter>('all');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [editText, setEditText] = useState('');
  const [editedIds, setEditedIds] = useState<string[]>([]);
  const [rejected, setRejected] = useState<Draft[]>([]);

  const pending = useMemo(() => drafts.filter((d) => d.status === 'pending'), [drafts]);
  const sent = useMemo(() => drafts.filter((d) => d.status === 'sent'), [drafts]);
  const pendingFresh = useMemo(() => pending.filter((d) => !editedIds.includes(d.id)), [pending, editedIds]);
  const pendingEdited = useMemo(() => pending.filter((d) => editedIds.includes(d.id)), [pending, editedIds]);

  const counts = {
    all: pending.length + sent.length,
    pending: pendingFresh.length,
    changes: pendingEdited.length,
    rejected: rejected.length,
  };

  const list: QueueItem[] = useMemo(() => {
    if (filter === 'pending') return pendingFresh.map((draft) => ({ draft, kind: 'live' as const }));
    if (filter === 'changes') return pendingEdited.map((draft) => ({ draft, kind: 'live' as const }));
    if (filter === 'rejected') return rejected.map((draft) => ({ draft, kind: 'rejected' as const }));
    return [...pending, ...sent].map((draft) => ({ draft, kind: 'live' as const }));
  }, [filter, pending, sent, pendingFresh, pendingEdited, rejected]);

  useEffect(() => {
    if (list.length === 0) {
      if (selectedId !== null) setSelectedId(null);
      return;
    }
    if (!selectedId || !list.some((x) => x.draft.id === selectedId)) {
      setSelectedId(list[0].draft.id);
    }
  }, [list, selectedId]);

  useEffect(() => {
    setEditing(false);
  }, [selectedId, filter]);

  const selected = list.find((x) => x.draft.id === selectedId) ?? null;
  const sel = selected?.draft ?? null;
  const selEdited = sel ? editedIds.includes(sel.id) : false;

  const statusPill = (item: QueueItem) => {
    if (item.kind === 'rejected') return <span className="pill pill-danger">已拒绝</span>;
    if (item.draft.status === 'sent') return <span className="pill pill-ok">已发送</span>;
    if (editedIds.includes(item.draft.id)) return <span className="pill pill-danger">需修改</span>;
    return <span className="pill pill-warn">待批准</span>;
  };

  const doReject = () => {
    if (!sel || selected?.kind !== 'live') return;
    setRejected((prev) => [sel, ...prev]);
    draftAction(sel.id, 'discard');
  };

  const doSaveEdit = () => {
    if (!sel) return;
    draftAction(sel.id, 'edit', editText);
    setEditedIds((prev) => (prev.includes(sel.id) ? prev : [...prev, sel.id]));
    setEditing(false);
  };

  const doSend = () => {
    if (!sel) return;
    draftAction(sel.id, 'send');
    setEditedIds((prev) => prev.filter((x) => x !== sel.id));
  };

  const FILTERS: { key: Filter; label: string; count: number }[] = [
    { key: 'all', label: '全部', count: counts.all },
    { key: 'pending', label: '待批准', count: counts.pending },
    { key: 'changes', label: '需修改', count: counts.changes },
    { key: 'rejected', label: '已拒绝', count: counts.rejected },
  ];

  return (
    <div className="view">
      <header className="view-head">
        <div className="kicker">REVIEW QUEUE / {pending.length} ITEMS</div>
        <h1>待审阅</h1>
        <p className="view-sub">Agent 为你准备的外发邮件与关键决策，都需要最后确认。</p>
      </header>

      <div className="panel filter-bar">
        {FILTERS.map((f) => (
          <button
            key={f.key}
            className={`filter-pill ${filter === f.key ? 'active' : ''}`}
            onClick={() => setFilter(f.key)}
          >
            {f.label} {f.count}
          </button>
        ))}
      </div>

      <div className="review-grid">
        <section className="panel queue-panel">
          <div className="section-head">
            <h2>待处理事项</h2>
            <span className="pill pill-warn">{list.length} 项</span>
          </div>
          <div className="queue-list">
            {list.length === 0 && <div className="empty-mini">这个分类下暂时没有草稿。</div>}
            {list.map((item) => (
              <button
                key={item.draft.id}
                className={`queue-item ${sel?.id === item.draft.id && selected?.kind === item.kind ? 'active' : ''}`}
                onClick={() => setSelectedId(item.draft.id)}
              >
                <span className="queue-icon">
                  <IconMail size={17} />
                </span>
                <span className="queue-main">
                  <span className="queue-title">{item.draft.subject}</span>
                  <span className="queue-meta">{item.draft.to}</span>
                  <span className="queue-foot">
                    {statusPill(item)}
                    <span className="queue-id">{item.draft.id.toUpperCase()}</span>
                  </span>
                </span>
              </button>
            ))}
          </div>
          <div className="panel-foot-note">所有操作会保留来源与审批记录</div>
        </section>

        <section className="panel detail-panel">
          {sel ? (
            <>
              <div className="detail-head">
                <h2 className="detail-subject">{sel.subject}</h2>
                {selected?.kind === 'rejected' ? (
                  <span className="pill pill-danger">已拒绝</span>
                ) : sel.status === 'sent' ? (
                  <span className="pill pill-ok">已发送</span>
                ) : selEdited ? (
                  <span className="pill pill-danger">需修改</span>
                ) : (
                  <span className="pill pill-warn">发送前审批</span>
                )}
              </div>
              <div className="detail-meta">
                <div className="draft-row">
                  <span className="draft-row-label">收件人</span>
                  <span>{sel.to}</span>
                </div>
                <div className="draft-row">
                  <span className="draft-row-label">来源</span>
                  <span>{sel.source}</span>
                </div>
              </div>
              {editing ? (
                <div className="edit-box">
                  <textarea value={editText} onChange={(e) => setEditText(e.target.value)} rows={12} />
                  <div className="btn-row">
                    <button className="btn btn-primary" onClick={doSaveEdit}>
                      保存修改
                    </button>
                    <button className="btn btn-ghost" onClick={() => setEditing(false)}>
                      取消
                    </button>
                  </div>
                </div>
              ) : (
                <pre className="tone-body detail-body">{sel.body}</pre>
              )}
              <div className="agent-hint">
                <IconSparkle size={15} />
                <span>Agent 提示：这封草稿{sel.source}，发送前请再确认收件人与正文内容。</span>
              </div>
              {selected?.kind === 'rejected' ? (
                <div className="state-banner stopped">这封草稿已被你拒绝，不会发送。记录保留在「已拒绝」分类中。</div>
              ) : sel.status === 'sent' ? (
                <div className="state-banner done">已批准发送，审计记录已写入活动日志。</div>
              ) : (
                !editing && (
                  <div className="btn-row detail-actions">
                    <button className="btn btn-primary btn-lg" onClick={doSend}>
                      批准并发送
                    </button>
                    <button
                      className="btn btn-dark btn-lg"
                      onClick={() => {
                        setEditText(sel.body);
                        setEditing(true);
                      }}
                    >
                      修改内容
                    </button>
                    <button className="btn btn-dark btn-lg" onClick={doReject}>
                      拒绝
                    </button>
                  </div>
                )
              )}
            </>
          ) : (
            <div className="empty-mini">从左侧队列选择一封草稿查看详情。</div>
          )}
        </section>
      </div>
    </div>
  );
}
