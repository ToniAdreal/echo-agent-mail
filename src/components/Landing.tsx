import { navigate } from '../lib/ui';

// Public product page shown to unauthenticated visitors at /.
// It describes the app for anyone who has not signed in yet (including
// OAuth reviewers) and routes into the existing Auth views.
export default function LandingPage({
  onSignIn,
  onRegister,
}: {
  onSignIn: () => void;
  onRegister: () => void;
}) {
  return (
    <div className="landing">
      <header className="landing-header">
        <div className="landing-brand">
          <img className="only-night" src="assets/logo-lockup-dark.png" alt="Intenda" />
          <img className="only-day" src="assets/logo-lockup-light.png" alt="Intenda" />
        </div>
        <nav className="landing-nav">
          <button type="button" className="link-btn" onClick={() => navigate('/privacy')}>
            Privacy
          </button>
          <button type="button" className="link-btn" onClick={() => navigate('/terms')}>
            Terms
          </button>
          <button type="button" className="btn btn-ghost" onClick={onSignIn}>
            Sign in
          </button>
          <button type="button" className="btn btn-primary" onClick={onRegister}>
            Create account
          </button>
        </nav>
      </header>

      <main className="landing-main">
        <section className="landing-hero">
          <div className="landing-hero-copy">
            <span className="pill pill-accent">Agent Native email</span>
            <h1 className="landing-tagline">From Intent to Done.</h1>
            <p className="landing-lede">
              Intenda is an Agent Native email client. You say the outcome you want; the Agent reads
              your mailbox context, works out a plan, and executes it step by step under the approval
              level you choose. Every draft it prepares waits for your approval before anything is
              sent.
            </p>
            <div className="landing-cta">
              <button type="button" className="btn btn-primary btn-lg" onClick={onRegister}>
                Create account
              </button>
              <button type="button" className="btn btn-dark btn-lg" onClick={onSignIn}>
                Sign in
              </button>
            </div>
            <p className="landing-note">
              Just looking? The sign-in page has a one-click demo account, and the built-in Demo
              Mailbox runs entirely on synthetic data.
            </p>
          </div>
          <div className="landing-hero-art" aria-hidden="true">
            <img className="only-night" src="assets/galaxy-dark.png" alt="" />
            <img className="only-day" src="assets/galaxy-light.png" alt="" />
          </div>
        </section>

        <section className="landing-steps" aria-label="How it works">
          <h2 className="landing-h2">How it works</h2>
          <div className="landing-steps-grid">
            <div className="landing-step">
              <span className="landing-step-num">1</span>
              <h3>Say the outcome</h3>
              <p>Describe the result you want in your own words, not a sequence of clicks.</p>
            </div>
            <div className="landing-step">
              <span className="landing-step-num">2</span>
              <h3>Approve the plan</h3>
              <p>The Agent shows its plan first, then works through it at the pace you set.</p>
            </div>
            <div className="landing-step">
              <span className="landing-step-num">3</span>
              <h3>Review before it sends</h3>
              <p>Drafts land in the Review Queue. Nothing leaves your mailbox without your approval.</p>
            </div>
          </div>
        </section>

        <section className="landing-features" aria-label="Features">
          <h2 className="landing-h2">What Intenda does</h2>
          <div className="landing-grid">
            <article className="landing-card">
              <h3>Daily Briefing</h3>
              <p>
                Start the day with decisions, not an inbox list. The briefing surfaces what needs a
                decision from you, what the Agent has finished, and what is still waiting.
              </p>
            </article>
            <article className="landing-card">
              <h3>Delegate an outcome</h3>
              <p>
                Hand over a goal and the Agent plans before it acts. You choose the approval level:
                ask at every step, approve key milestones, or review only before sending. Pause a
                run, take over manually, or stop it at any time.
              </p>
            </article>
            <article className="landing-card">
              <h3>Review Queue</h3>
              <p>
                Every draft the Agent writes waits here for you. Read it, edit it, approve it, or
                discard it. Nothing is sent without your approval.
              </p>
            </article>
            <article className="landing-card">
              <h3>A full inbox, kept whole</h3>
              <p>
                The traditional inbox is still here. Read, reply, search, and organize mail yourself,
                and hand a thread to the Agent whenever you would rather delegate it.
              </p>
            </article>
            <article className="landing-card">
              <h3>Your mailbox, your choice</h3>
              <p>
                Connect a real Google mailbox and Intenda syncs it through Gmail so the Agent can
                work on your actual mail. Prefer not to? The built-in Demo Mailbox uses synthetic
                data and never touches an external account.
              </p>
              <span className="pill pill-khaki">Google connection is optional</span>
            </article>
            <article className="landing-card">
              <h3>Day and night</h3>
              <p>
                A black-and-white workbench with a single blue accent, in day and night themes. Your
                choice is remembered between visits.
              </p>
            </article>
          </div>
        </section>
      </main>

      <footer className="landing-footer">
        <div className="landing-footer-row">
          <span className="landing-footer-brand">Built by Tokenta</span>
          <div className="landing-footer-links">
            <button type="button" className="link-btn" onClick={() => navigate('/privacy')}>
              Privacy Policy
            </button>
            <button type="button" className="link-btn" onClick={() => navigate('/terms')}>
              Terms of Service
            </button>
            <button type="button" className="link-btn" onClick={onSignIn}>
              Sign in
            </button>
          </div>
        </div>
        <p className="landing-footer-note">
          The Demo Mailbox uses synthetic data. Connecting a Google account is optional; how Intenda
          handles Google data is described in the Privacy Policy.
        </p>
      </footer>
    </div>
  );
}
