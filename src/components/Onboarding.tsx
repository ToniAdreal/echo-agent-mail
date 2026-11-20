import { useEffect, useRef, useState } from 'react';
import { Check, Loader2, Mail } from 'lucide-react';
import { api, type OnboardingStatus, type SyncJob } from '../lib/api';
import { ErrorCard, navigate } from '../lib/ui';

const STEP_DEFS = [
  { key: 'initial_sync', label: 'Preparing your mailbox' },
  { key: 'history_import', label: 'Importing recent messages' },
  { key: 'indexing', label: 'Indexing threads and attachments' },
  { key: 'agent_briefing', label: 'Building your first briefing' },
  { key: 'ready', label: 'Ready' },
];

function Steps({ done }: { done: number }) {
  return (
    <div className="onboarding-steps" aria-hidden>
      {[0, 1, 2, 3].map((i) => (
        <span key={i} className={`onboarding-step${i < done ? ' done' : ''}`} />
      ))}
    </div>
  );
}

export default function Onboarding({ onReady }: { onReady: () => void }) {
  const [status, setStatus] = useState<OnboardingStatus | null>(null);
  const [job, setJob] = useState<SyncJob | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const [oauthNote, setOauthNote] = useState<string | null>(null);
  const pollRef = useRef<number | undefined>(undefined);

  const load = async () => {
    try {
      const s = await api<OnboardingStatus>('/api/v1/onboarding/status');
      setStatus(s);
      if (s.state === 'SYNCING' || s.state === 'SYNC_FAILED') {
        const sj = await api<{ jobs: SyncJob[] }>('/api/v1/sync/status').catch(() => null);
        if (sj?.jobs?.length) setJob(sj.jobs[sj.jobs.length - 1]);
      }
      return s;
    } catch (e) {
      setError(e);
      return null;
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (status?.state === 'SYNCING') {
      pollRef.current = window.setInterval(async () => {
        const s = await load();
        if (s && s.state !== 'SYNCING') window.clearInterval(pollRef.current);
      }, 700);
      return () => window.clearInterval(pollRef.current);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status?.state]);

  if (error != null && !status) {
    return (
      <div className="auth-shell">
        <div className="auth-card">
          <ErrorCard error={error} onRetry={load} />
        </div>
      </div>
    );
  }
  if (!status) {
    return (
      <div className="auth-shell">
        <div className="auth-card">
          <div className="skeleton" style={{ height: 240 }} />
        </div>
      </div>
    );
  }

  const demoAddress = status.mail_accounts[0]?.email_address ?? null;
  const percent = status.state === 'READY' ? 100 : (job?.percent ?? 0);

  const chooseDemo = async () => {
    setBusy(true);
    setError(null);
    try {
      await api('/api/v1/onboarding/mailbox-choice', { method: 'POST', body: { choice: 'demo' } });
      await api('/api/v1/onboarding/demo-mailbox', { method: 'POST', body: {} });
      await load();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  const startOAuth = async (provider: string) => {
    setBusy(true);
    setError(null);
    setOauthNote(null);
    try {
      await api('/api/v1/onboarding/mailbox-choice', { method: 'POST', body: { choice: provider } });
      const r = await api<{ authorization_url: string }>(`/api/v1/onboarding/oauth/${provider}/start`, {
        method: 'POST',
        body: { return_to: '/onboarding' },
      });
      window.location.href = r.authorization_url;
    } catch {
      // Provider not configured in this deployment: explain and offer Demo.
      setOauthNote(
        'Live mailbox connection is not configured in this deployment yet. You can explore the full product now with the Demo Mailbox — every workflow runs for real inside Intenda.',
      );
      setBusy(false);
    }
  };

  const retrySync = async () => {
    setBusy(true);
    try {
      await api('/api/v1/onboarding/retry', { method: 'POST', body: {} });
      await load();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  const stepIndex =
    status.state === 'ACCOUNT_CREATED' ? 1 : status.state === 'MAILBOX_SELECTION' ? 2 : status.state === 'READY' ? 4 : 3;

  return (
    <div className="auth-shell">
      <div className="auth-card wide">
        <Steps done={stepIndex} />
        {error != null && <ErrorCard error={error} />}

        {(status.state === 'ACCOUNT_CREATED' || status.state === 'MAILBOX_SELECTION') && (
          <>
            <img className="auth-art only-night" src="assets/mailbox-connect-dark.png" alt="" />
            <img className="auth-art only-day" src="assets/mailbox-connect-light.png" alt="" />
            <h1 className="auth-title">Connect your mailbox</h1>
            <p className="auth-sub">
              Intenda reads only the mailbox you connect, prepares briefings and drafts, and never sends anything without the approval rules you set.
            </p>
            {oauthNote && (
              <div className="state-banner manual" style={{ marginTop: 0, marginBottom: 14 }}>
                {oauthNote}
              </div>
            )}
            <div className="provider-grid">
              <button className="provider-card" onClick={() => startOAuth('google')} disabled={busy}>
                <span className="provider-icon">G</span>
                <span className="provider-main">
                  <span className="provider-name">Google / Gmail <span className="live-label">Live</span></span>
                  <span className="provider-desc">OAuth sign-in. Intenda requests mail read, draft and send scopes; you approve on Google's screen.</span>
                </span>
              </button>
              <button className="provider-card" onClick={() => startOAuth('microsoft')} disabled={busy}>
                <span className="provider-icon">M</span>
                <span className="provider-main">
                  <span className="provider-name">Microsoft / Outlook <span className="live-label">Live</span></span>
                  <span className="provider-desc">OAuth sign-in with Microsoft. Same read, draft and send scopes, approved on Microsoft's screen.</span>
                </span>
              </button>
              <button className="provider-card" onClick={chooseDemo} disabled={busy}>
                <span className="provider-icon">
                  <Mail size={17} />
                </span>
                <span className="provider-main">
                  <span className="provider-name">Demo Mailbox <span className="demo-label">Demo</span></span>
                  <span className="provider-desc">
                    A complete sample mailbox (you@demo.intenda.example) with realistic threads, tasks and decisions. Sends are simulated. No external account needed.
                  </span>
                </span>
              </button>
            </div>
            <p className="hint" style={{ color: 'var(--t4)', fontSize: 12.5, lineHeight: 1.6 }}>
              Intenda never stores your mailbox password. You can disconnect a mailbox at any time in Settings, which revokes access and deletes synced data.
            </p>
            <p className="hint" style={{ color: 'var(--t4)', fontSize: 12.5, lineHeight: 1.6 }}>
              See how Intenda handles your data in our{' '}
              <button type="button" className="link-btn" onClick={() => navigate('/privacy')}>
                Privacy Policy
              </button>{' '}
              and{' '}
              <button type="button" className="link-btn" onClick={() => navigate('/terms')}>
                Terms of Service
              </button>
              .
            </p>
          </>
        )}

        {status.state === 'AUTHORIZATION_PENDING' && (
          <>
            <h1 className="auth-title">Waiting for authorization</h1>
            <p className="auth-sub">Complete the sign-in on your provider's page, then return here. If the window was closed, restart the connection.</p>
            <button className="btn btn-dark btn-block" onClick={() => load()}>
              Check status
            </button>
            <button className="btn btn-ghost btn-block" onClick={chooseDemo} disabled={busy}>
              Use the Demo Mailbox instead
            </button>
          </>
        )}

        {(status.state === 'SYNCING' || status.state === 'SYNC_FAILED') && (
          <>
            <h1 className="auth-title">{status.state === 'SYNC_FAILED' ? 'Sync needs attention' : 'Setting up your mailbox'}</h1>
            <p className="auth-sub">
              {demoAddress ? (
                <>
                  Demo mailbox <strong>{demoAddress}</strong> — simulated data, clearly labelled everywhere.
                </>
              ) : (
                'Importing your mailbox.'
              )}
            </p>
            <span className="progress progress-lg">
              <span className="progress-bar" style={{ width: `${percent}%` }} />
            </span>
            <div className="sync-list">
              {STEP_DEFS.map((s, i) => {
                const done = percent >= (i + 1) * 20;
                const active = !done && percent >= i * 20 && status.state === 'SYNCING';
                return (
                  <div key={s.key} className={`sync-row${done ? ' done' : ''}${active ? ' active' : ''}`}>
                    <span className="sync-ic">
                      {done ? <Check size={13} /> : active ? <Loader2 size={13} className="spin" /> : <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--t4)' }} />}
                    </span>
                    <span>{s.label}</span>
                    {s.key === 'history_import' && (
                      <span className="sync-count">
                        {job?.processed_count ?? 0} / {job?.total_count ?? 0}
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
            {status.state === 'SYNC_FAILED' ? (
              <>
                <div className="state-banner stopped">The sync did not finish. Your account and mailbox choice are saved.</div>
                <div className="btn-row">
                  <button className="btn btn-primary" onClick={retrySync} disabled={busy}>
                    Retry sync
                  </button>
                  <button className="btn btn-ghost" onClick={chooseDemo} disabled={busy}>
                    Switch to Demo Mailbox
                  </button>
                </div>
              </>
            ) : (
              <p className="hint" style={{ color: 'var(--t4)', fontSize: 12.5 }}>
                This usually takes a few seconds for the Demo Mailbox. You can leave this page; sync continues in the background.
              </p>
            )}
          </>
        )}

        {status.state === 'READY' && (
          <>
            <img className="auth-art only-night" src="assets/mailbox-connect-dark.png" alt="" />
            <img className="auth-art only-day" src="assets/mailbox-connect-light.png" alt="" />
            <h1 className="auth-title">Your mailbox is ready</h1>
            <p className="auth-sub">
              {job?.total_count ?? 38} messages imported
              {demoAddress ? ` into ${demoAddress}` : ''}. Your first briefing is ready.
            </p>
            <button
              className="btn btn-primary btn-block btn-lg"
              onClick={() => {
                onReady();
                navigate('/briefing');
              }}
            >
              Open Today Briefing
            </button>
          </>
        )}
      </div>
    </div>
  );
}
