import { useState } from 'react';
import { ArchiveRestore, Search } from 'lucide-react';
import { api, type MailMessage } from '../lib/api';
import {
  EnvLabel,
  ErrorCard,
  SkeletonRows,
  errorText,
  fmtTime,
  useAsync,
  useToast,
} from '../lib/ui';

export default function Archive() {
  const toast = useToast();
  const [query, setQuery] = useState('');
  const [submittedQuery, setSubmittedQuery] = useState('');
  const { data, error, loading, reload } = useAsync(
    () =>
      api<{ items: MailMessage[] }>(
        submittedQuery
          ? `/api/v1/archive?q=${encodeURIComponent(submittedQuery)}&limit=100`
          : '/api/v1/archive?limit=100',
      ),
    [submittedQuery],
  );

  const restore = async (msg: MailMessage) => {
    try {
      await api(`/api/v1/archive/${msg.id}/restore`, { method: 'POST', body: { destination: 'inbox' } });
      toast({ text: 'Thread restored to the Inbox.' });
      reload();
    } catch (e) {
      toast({ text: errorText(e), error: true });
    }
  };

  const messages = data?.items ?? [];

  return (
    <div className="view">
      <div className="view-head with-pill">
        <div>
          <span className="kicker">ARCHIVE</span>
          <h1>Everything you put away</h1>
          <p className="view-sub">
            Archived mail stays searchable and restorable. Archiving is not deletion — nothing here is lost.
          </p>
        </div>
        <EnvLabel env={messages[0]?.environment ?? 'demo'} />
      </div>

      <div className="panel" style={{ padding: '14px 16px', marginBottom: 18 }}>
        <form
          className="top-search"
          style={{ width: '100%' }}
          onSubmit={(e) => {
            e.preventDefault();
            setSubmittedQuery(query.trim());
          }}
        >
          <Search size={15} />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search archived mail…"
            aria-label="Search archived mail"
          />
          <button className="btn btn-dark" type="submit">
            Search
          </button>
          {submittedQuery && (
            <button
              className="btn btn-ghost"
              type="button"
              onClick={() => {
                setQuery('');
                setSubmittedQuery('');
              }}
            >
              Clear
            </button>
          )}
        </form>
        {submittedQuery && (
          <div className="empty-mini" style={{ paddingBottom: 0 }}>
            {messages.length} archived message(s) match “{submittedQuery}”.
          </div>
        )}
      </div>

      {error != null && <ErrorCard error={error} onRetry={reload} />}
      {loading && <SkeletonRows />}

      {!loading && messages.length === 0 && !submittedQuery && (
        <div className="empty-card">
          <img className="empty-motif only-night" src="assets/empty-archive-dark.png" alt="" />
          <img className="empty-motif only-day" src="assets/empty-archive-light.png" alt="" />
          Nothing archived yet. Archive a thread from the Inbox and its messages will live here, searchable and restorable.
        </div>
      )}
      {!loading && messages.length === 0 && submittedQuery && (
        <div className="empty-card">No archived messages match “{submittedQuery}”.</div>
      )}

      {!loading && messages.length > 0 && (
        <section className="panel" style={{ padding: '6px 18px' }}>
          <div className="list-rows">
            {messages.map((msg) => (
              <div key={msg.id} className="list-row">
                <span className="list-row-main">
                  <span className="list-row-title">{msg.subject}</span>
                  <span className="list-row-meta" style={{ display: 'block' }}>
                    {msg.from_name ?? msg.from_address} · {fmtTime(msg.created_at)}
                  </span>
                  <span className="list-row-meta" style={{ display: 'block' }}>{msg.snippet}</span>
                </span>
                <button className="btn btn-dark" onClick={() => restore(msg)}>
                  <ArchiveRestore size={14} /> Restore thread
                </button>
              </div>
            ))}
          </div>
        </section>
      )}
      <p className="view-footnote">Restoring a message un-archives its whole thread and returns it to the Inbox.</p>
    </div>
  );
}
