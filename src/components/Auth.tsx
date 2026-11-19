import { useState } from 'react';
import { api } from '../lib/api';
import { ErrorCard, navigate } from '../lib/ui';

function Brand() {
  return (
    <div className="auth-brand">
      <img className="only-night" src="assets/logo-lockup-dark.png" alt="Intenda" />
      <img className="only-day" src="assets/logo-lockup-light.png" alt="Intenda" />
      <span className="brand-name">Intenda</span>
      <span style={{ color: 'var(--t3)' }}>意达</span>
    </div>
  );
}

export function LoginPage({ onAuthed }: { onAuthed: () => void }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api('/api/v1/auth/login', { method: 'POST', body: { email, password } });
      onAuthed();
    } catch (err) {
      setError(err);
      setBusy(false);
    }
  };

  const demo = async () => {
    setBusy(true);
    setError(null);
    try {
      await api('/api/v1/auth/demo-session', { method: 'POST', body: {} });
      onAuthed();
    } catch (err) {
      setError(err);
      setBusy(false);
    }
  };

  return (
    <div className="auth-shell">
      <form className="auth-card" onSubmit={submit}>
        <Brand />
        <h1 className="auth-title">Welcome back</h1>
        <p className="auth-sub">Sign in to your Agent Native mailbox. Your delegated work picks up right where it left off.</p>
        {error != null && <ErrorCard error={error} />}
        <div className="field">
          <label htmlFor="login-email">Email</label>
          <input id="login-email" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div className="field">
          <label htmlFor="login-password">Password</label>
          <input id="login-password" type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>
        <button className="btn btn-primary btn-block btn-lg" type="submit" disabled={busy}>
          {busy ? 'Signing in…' : 'Sign in'}
        </button>
        <button className="btn btn-dark btn-block" type="button" onClick={demo} disabled={busy}>
          Try the one-click demo account
        </button>
        <div className="auth-links">
          <button type="button" className="link-btn" onClick={() => navigate('/forgot-password')}>
            Forgot password?
          </button>
          <span>
            New to Intenda?{' '}
            <button type="button" className="link-btn" onClick={() => navigate('/register')}>
              Create an account
            </button>
          </span>
        </div>
      </form>
    </div>
  );
}

export function RegisterPage({ onAuthed }: { onAuthed: () => void }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirm) {
      setError(new Error('Passwords do not match.'));
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await api('/api/v1/auth/register', { method: 'POST', body: { name, email, password } });
      onAuthed();
    } catch (err) {
      setError(err);
      setBusy(false);
    }
  };

  return (
    <div className="auth-shell">
      <form className="auth-card" onSubmit={submit}>
        <Brand />
        <h1 className="auth-title">Create your account</h1>
        <p className="auth-sub">
          Intenda turns intent into finished work. Create an account, connect a mailbox, and delegate your first task in minutes.
        </p>
        {error != null && <ErrorCard error={error} />}
        <div className="field">
          <label htmlFor="reg-name">Full name</label>
          <input id="reg-name" autoComplete="name" required value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <div className="field">
          <label htmlFor="reg-email">Email</label>
          <input id="reg-email" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div className="field">
          <label htmlFor="reg-password">Password</label>
          <input id="reg-password" type="password" autoComplete="new-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
          <p className="hint">At least 12 characters, with upper and lower case letters and a number or symbol.</p>
        </div>
        <div className="field">
          <label htmlFor="reg-confirm">Confirm password</label>
          <input id="reg-confirm" type="password" autoComplete="new-password" required value={confirm} onChange={(e) => setConfirm(e.target.value)} />
        </div>
        <button className="btn btn-primary btn-block btn-lg" type="submit" disabled={busy}>
          {busy ? 'Creating account…' : 'Create account'}
        </button>
        <div className="auth-links">
          <span>
            Already have an account?{' '}
            <button type="button" className="link-btn" onClick={() => navigate('/login')}>
              Sign in
            </button>
          </span>
        </div>
      </form>
    </div>
  );
}

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [newPassword, setNewPassword] = useState('');
  const [error, setError] = useState<unknown>(null);
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  const request = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const r = await api<{ reset_token?: string }>('/api/v1/auth/password-reset/request', {
        method: 'POST',
        body: { email },
      });
      setSent(true);
      if (r.reset_token) setToken(r.reset_token);
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  };

  const complete = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setBusy(true);
    setError(null);
    try {
      await api('/api/v1/auth/password-reset/complete', {
        method: 'POST',
        body: { token, new_password: newPassword },
      });
      setDone(true);
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <Brand />
        <h1 className="auth-title">Reset your password</h1>
        <p className="auth-sub">
          Enter your account email. If an account exists, a single-use reset link is created. Existing sessions are revoked when the password changes.
        </p>
        {error != null && <ErrorCard error={error} />}
        {done ? (
          <>
            <div className="state-banner done">Your password has been reset. Sign in with the new password.</div>
            <button className="btn btn-primary btn-block" onClick={() => navigate('/login')}>
              Go to sign in
            </button>
          </>
        ) : !sent ? (
          <form onSubmit={request}>
            <div className="field">
              <label htmlFor="fp-email">Email</label>
              <input id="fp-email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            <button className="btn btn-primary btn-block btn-lg" type="submit" disabled={busy}>
              {busy ? 'Sending…' : 'Send reset link'}
            </button>
          </form>
        ) : (
          <form onSubmit={complete}>
            <div className="state-banner manual" style={{ marginTop: 0, marginBottom: 14 }}>
              Reset requested. In this demo build the reset token is shown here instead of being emailed.
            </div>
            <div className="field">
              <label htmlFor="fp-token">Reset token</label>
              <input id="fp-token" required value={token ?? ''} onChange={(e) => setToken(e.target.value)} />
            </div>
            <div className="field">
              <label htmlFor="fp-new">New password</label>
              <input id="fp-new" type="password" autoComplete="new-password" required value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
              <p className="hint">At least 12 characters, with upper and lower case letters and a number or symbol.</p>
            </div>
            <button className="btn btn-primary btn-block btn-lg" type="submit" disabled={busy}>
              {busy ? 'Resetting…' : 'Set new password'}
            </button>
          </form>
        )}
        <div className="auth-links">
          <button type="button" className="link-btn" onClick={() => navigate('/login')}>
            Back to sign in
          </button>
        </div>
      </div>
    </div>
  );
}
