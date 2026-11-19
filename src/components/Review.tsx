import { useState } from 'react';
import { Draft } from '../data';

interface Props {
  drafts: Draft[];
  draftAction: (id: string, action: 'send' | 'discard' | 'edit', body?: string) => void;
}

export default function Review({ drafts, draftAction }: Props) {
  const [expanded, setExpanded] = useState<string | null>(null);
  const [editing, setEditing] = useState<string | null>(null);
  const [editText, setEditText] = useState('');

  const pending = drafts.filter((d) => d.status === 'pending');
  const sent = drafts.filter((d) => d.status === 'sent');

  return (
    <div className="view">
      <header className="view-head">
        <h1>待审阅</h1>
        <p className="view-sub">
          Agent 写好的草稿都停在这里，一封都不会自己发出去。你批准，它才发送。
        </p>
      </header>

      {pending.length === 0 && <div className="empty-card">没有待审阅的草稿。新草稿会出现在任务完成或简报生成之后。</div>}

      <div className="card-list">
        {pending.map((d) => (
          <article key={d.id} className="draft-card">
            <div className="draft-head">
              <div>
                <div className="draft-subject">{d.subject}</div>
                <div className="draft-meta">收件人：{d.to}</div>
              </div>
              <span className="tag tag-wait">待批准</span>
            </div>
            <div className="draft-source">{d.source}</div>
            {editing === d.id ? (
              <div className="edit-box">
                <textarea value={editText} onChange={(e) => setEditText(e.target.value)} rows={10} />
                <div className="btn-row">
                  <button
                    className="btn btn-primary"
                    onClick={() => {
                      draftAction(d.id, 'edit', editText);
                      setEditing(null);
                    }}
                  >
                    保存修改
                  </button>
                  <button className="btn btn-ghost" onClick={() => setEditing(null)}>
                    取消
                  </button>
                </div>
              </div>
            ) : (
              <>
                <pre className={`draft-body ${expanded === d.id ? 'full' : 'clamp'}`}>{d.body}</pre>
                <div className="btn-row">
                  <button className="btn btn-primary" onClick={() => draftAction(d.id, 'send')}>
                    批准发送
                  </button>
                  <button
                    className="btn btn-soft"
                    onClick={() => {
                      setEditing(d.id);
                      setEditText(d.body);
                    }}
                  >
                    编辑
                  </button>
                  <button className="btn btn-soft" onClick={() => setExpanded(expanded === d.id ? null : d.id)}>
                    {expanded === d.id ? '收起全文' : '展开全文'}
                  </button>
                  <button className="btn btn-ghost" onClick={() => draftAction(d.id, 'discard')}>
                    丢弃
                  </button>
                </div>
              </>
            )}
          </article>
        ))}
      </div>

      {sent.length > 0 && (
        <section>
          <div className="section-head">
            <h2>已发送</h2>
          </div>
          <div className="card-list">
            {sent.map((d) => (
              <article key={d.id} className="draft-card sent">
                <div className="draft-head">
                  <div>
                    <div className="draft-subject">{d.subject}</div>
                    <div className="draft-meta">收件人：{d.to}</div>
                  </div>
                  <span className="tag tag-done">已发送</span>
                </div>
              </article>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
