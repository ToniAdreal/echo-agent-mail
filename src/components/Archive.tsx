import { useEffect, useState } from 'react';
import { ArchiveRestore, Search } from 'lucide-react';
import { api, type ThreadItem } from '../lib/api';
import {
  EnvLabel,
  ErrorCard,
  SkeletonRows,
  errorText,
  fmtTime,
  navigate,
  useAsync,
  useToast,
} from '../lib/ui';

export default function Archive() {
  const toast = useToast();
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any | null>(null);
  const [searching, setSearching] = useState(false);
  const { data, error, loading, reload } = useAsync(
    () => api<{ items: ThreadItem[] }>('/api/v1/archive/threads?limit=100'),
    [],
  );

  useEffect(() => {
    if (query.trim().length < 2) {
      setSearchResults(null);
      return;
    }
    const t = window.setTimeout(async () => {
      setSearching(true);
      try {
        const r = await api(`/api/v1/search?q=${encodeURIComponent(query.trim())}&archived=true`);
        setSearchResults(r);
      } catch {
        setSearchResults(null);
      } finally {
        setSearching(false);
      }
    }, 300);
    return () => window.clearTimeout(t);
  }, [query]);

  const restore = async (thread: ThreadItem) => {
    try {
      await api(`/api/v1/archive/threads/${thread.id}/restore`, { method: 'POST', body: {} });
      toast({ text: 'Thread restored to the Inbox.' });
      reload();
    } catch (e) {
      toast({ text: errorText(e), error: true });
    }
  };

  const threads = data?.items ?? [];

  return (
    <div className="view">
      <div className="view-head with-pill">
        <div>
          <span className="kicker">ARCHIVE</span>
          <h1>Everything you put away</h1>
          <p className="view-sub">
            Archived threads stay searchable and restorable. Archiving is not deletion — nothing here is lost.
          </p>
        </div>
        <EnvLabel env={threads[0]?.environment ?? 'demo'} />
      </div>

      <div className="panel" style={{ padding: '14px 16px', marginBottom: 18 }}>
        <div className="top-search" style={{ width: '100%' }}>
          <Search size={15} />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search archived mail…"
            aria-label="Search archived mail"
          />
        </div>
        {searching && <div className="empty-mini">Searching…</div>}
        {searchResults && (
          <div style={{ marginTop: 10 }}>
            {searchResults.messages?.length === 0 && <div className="empty-mini">No archived messages match “{query}”.</div>}
            {searchResults.messages?.map((msg: any) => (
              <button
                key={msg.id}
                className="list-row"
                onClick={() => navigate(`/inbox?message=${msg.id}`)}
              >
                <span className="list-row-main">
                  <span className="list-row-title">{msg.subject}</span>
                  <span className="list-row-meta" style={{ display: 'block' }}>
                    {msg.from.name ?? msg.from.email} · {fmtTime(msg.created_at)}
                  </span>
                </span>
              </button>
            ))}
          </div>
        )}
      </div>

      {error != null && <ErrorCard error={error} onRetry={reload} />}
      {loading && <SkeletonRows />}

      {!loading && threads.length === 0 && (
        <div className="empty-card">
          <img className="empty-motif only-night" src="assets/empty-archive-dark.png" alt="" />
          <img className="empty-motif only-day" src="assets/empty-archive-light.png" alt="" />
          Nothing archived yet. Archive a thread from the Inbox and it will live here, searchable and restorable.
        </div>
      )}

      {!loading && threads.length > 0 && (
        <section className="panel" style={{ padding: '6px 18px' }}>
          <div className="list-rows">
            {threads.map((t) => (
              <div key={t.id} className="list-row">
                <span className="list-row-main">
                  <span className="list-row-title">{t.subject}</span>
                  <span className="list-row-meta" style={{ display: 'block' }}>
                    {t.participants.map((p) => p.name ?? p.email).join(', ')} · {t.message_count} message(s) · last{' '}
                    {fmtTime(t.last_message_at)}
                  </span>
                  <span className="list-row-meta" style={{ display: 'block' }}>{t.latest_snippet}</span>
                </span>
                <button className="btn btn-dark" onClick={() => restore(t)}>
                  <ArchiveRestore size={14} /> Restore
                </button>
              </div>
            ))}
          </div>
        </section>
      )}
      <p className="view-footnote">Archived threads keep their full history and can be restored to the Inbox at any time.</p>
    </div>
  );
}
