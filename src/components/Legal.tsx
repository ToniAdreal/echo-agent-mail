import type { ReactNode } from 'react';
import { navigate } from '../lib/ui';
import { Brand } from './Auth';

function LegalShell({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="auth-shell">
      <div className="auth-card legal-card">
        <Brand />
        <h1 className="auth-title">{title}</h1>
        <div className="legal-body">{children}</div>
        <div className="legal-footer">
          <button type="button" className="link-btn" onClick={() => navigate('/privacy')}>
            Privacy Policy
          </button>
          <button type="button" className="link-btn" onClick={() => navigate('/terms')}>
            Terms of Service
          </button>
          <button type="button" className="link-btn" onClick={() => navigate('/login')}>
            Back to sign in
          </button>
        </div>
      </div>
    </div>
  );
}

export function PrivacyPage() {
  return (
    <LegalShell title="Intenda Privacy Policy">
      <p className="legal-meta">Last updated: November 19, 2026</p>

      <h2>What Intenda is</h2>
      <p>
        Intenda is an Agent Native email client built by Tokenta. It helps you read, organize and act on
        email: an AI agent prepares briefings, searches your mailbox, drafts replies and, only with your
        approval, sends them. Connecting a Google account is optional. If you would rather not connect a
        real mailbox, you can explore the product with the built-in Demo Mailbox, which uses sample data
        and never touches an external account.
      </p>

      <h2>Data we access when you connect Google</h2>
      <p>When you choose to connect a Google account, Intenda requests these permissions:</p>
      <ul>
        <li>
          <strong>Basic profile (openid, email, profile)</strong> — your name and email address, used to
          identify and label the connected mailbox inside the app.
        </li>
        <li>
          <strong>Gmail access (https://www.googleapis.com/auth/gmail.modify)</strong> — used to read your
          mailbox messages and threads, create drafts, and send mail. Intenda sends a message only after
          you explicitly approve it in the Review queue inside the app. This scope does not allow
          immediate, permanent deletion of threads or messages, bypassing the trash.
        </li>
      </ul>
      <p>
        Intenda never sees or stores your Google password. Sign-in happens on Google&apos;s own pages and
        Intenda receives OAuth tokens only.
      </p>

      <h2>How we use your data</h2>
      <p>
        Your mailbox data is used solely to operate the mailbox features you invoke: showing your inbox
        and threads, preparing your daily briefing, searching messages, letting the Agent draft and
        summarize, and sending the drafts you approve. We do not use mailbox contents for any other
        purpose.
      </p>

      <h2>Google API Limited Use</h2>
      <p>
        Intenda&apos;s use and transfer of information received from Google APIs adheres to the{' '}
        <a
          href="https://developers.google.com/terms/api-services-user-data-policy"
          target="_blank"
          rel="noreferrer"
        >
          Google API Services User Data Policy
        </a>
        , including the Limited Use requirements. In particular:
      </p>
      <ul>
        <li>
          Mailbox contents are <strong>not</strong> used to train, retrain or improve machine-learning or
          AI models.
        </li>
        <li>
          Mailbox contents are <strong>not</strong> sold to anyone and are <strong>not</strong> used for
          advertising.
        </li>
        <li>
          Humans do not read your mailbox contents, except as required to operate a feature you
          triggered, to investigate a security issue, or to comply with applicable law.
        </li>
      </ul>

      <h2>Storage and security</h2>
      <p>
        OAuth access and refresh tokens are stored server-side and encrypted at rest (Fernet). Synced
        mailbox data — messages, threads and drafts — is stored in the application&apos;s database so
        Intenda can present your mailbox, briefings and history without re-reading Gmail on every
        screen. The current deployment is a demonstration instance hosted on Render&apos;s free tier;
        its database is ephemeral and is reset when the service restarts or is redeployed.
      </p>

      <h2>Retention and deletion</h2>
      <ul>
        <li>
          Disconnecting a mailbox in Settings deletes the synced data stored for that account and
          discards the stored tokens for it.
        </li>
        <li>
          You can revoke Intenda&apos;s access at any time from your Google Account at{' '}
          <a href="https://myaccount.google.com/permissions" target="_blank" rel="noreferrer">
            myaccount.google.com/permissions
          </a>
          .
        </li>
        <li>
          To request deletion of any remaining data associated with your account, contact us at{' '}
          <a href="mailto:team@tokenta.space">team@tokenta.space</a>.
        </li>
      </ul>

      <h2>Sharing</h2>
      <p>
        We do not sell your data, and we do not share mailbox contents with third parties other than the
        processors needed to run the service: our hosting provider, and the configured language-model
        provider, which processes message content only when you ask the Agent to draft, summarize or
        otherwise act on it. We may disclose data where required by law.
      </p>

      <h2>Contact</h2>
      <p>
        Questions about this policy or your data: <a href="mailto:team@tokenta.space">team@tokenta.space</a>.
      </p>
    </LegalShell>
  );
}

export function TermsPage() {
  return (
    <LegalShell title="Intenda Terms of Service">
      <p className="legal-meta">Last updated: November 19, 2026</p>

      <h2>The service</h2>
      <p>
        Intenda is an Agent Native email client built by Tokenta and provided for evaluation as a
        demonstration product. Features may change, break or be withdrawn at any time, and the demo
        deployment may reset its data without notice.
      </p>

      <h2>Your account and mailbox</h2>
      <p>
        You are responsible for activity under your account. Connecting a mailbox is optional and always
        your choice; you can disconnect it at any time in Settings or revoke access from your provider
        account. Intenda acts only within the permissions you grant.
      </p>

      <h2>Agent actions and approvals</h2>
      <p>
        The Agent prepares drafts and proposed actions, but email is sent only after your explicit
        approval inside the app. You are responsible for reviewing and approving anything the Agent
        sends or files on your behalf, and for the content of messages sent from your mailbox.
      </p>

      <h2>Acceptable use</h2>
      <p>
        Do not use Intenda to send spam or unlawful content, to harass or defraud others, to access a
        mailbox you are not authorized to use, or to interfere with the service or its providers.
      </p>

      <h2>No warranty</h2>
      <p>
        Intenda is provided &quot;as is&quot; and &quot;as available&quot;, without warranties of any
        kind, express or implied, including fitness for a particular purpose. To the maximum extent
        permitted by law, Tokenta is not liable for any indirect or consequential damages arising from
        use of the service, including lost or misdirected email.
      </p>

      <h2>Changes</h2>
      <p>
        We may update these terms; the current version will always be available on this page, with the
        date above revised when it changes.
      </p>

      <h2>Contact</h2>
      <p>
        Questions about these terms: <a href="mailto:team@tokenta.space">team@tokenta.space</a>.
      </p>
    </LegalShell>
  );
}
