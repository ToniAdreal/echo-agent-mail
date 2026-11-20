/* Google Identity Services wiring for the auth pages.
 *
 * The GIS client library is loaded once via a static <script> tag in
 * index.html — never injected dynamically — so there is no load race to
 * lose. This module handles the three things that make the button
 * reliable across mounts:
 *
 * 1. The public client ID comes from the backend (GET /api/v1/auth/config,
 *    sourced from the GOOGLE_CLIENT_ID env value) and is cached per page
 *    load. An empty value means Google sign-in is not configured in this
 *    deployment and the button is not rendered at all.
 * 2. `initialize` is called exactly once per page load (GIS keeps one
 *    configuration per client ID). The credential callback dispatches to
 *    whichever auth page is currently mounted, so client-side navigation
 *    between /login and /register never leaves a stale page holding the
 *    credential.
 * 3. `renderButton` is called on every mount into that mount's own
 *    container node (after clearing it), so React unmount/remount cycles
 *    can never strand the button on a detached DOM node.
 */
import { api } from './api';

declare global {
  interface Window {
    google?: any;
  }
}

let clientIdPromise: Promise<string> | null = null;

export function fetchGoogleClientId(): Promise<string> {
  if (!clientIdPromise) {
    clientIdPromise = api<{ google_client_id: string }>('/api/v1/auth/config')
      .then((c) => c.google_client_id ?? '')
      .catch(() => '');
  }
  return clientIdPromise;
}

let gisReadyPromise: Promise<boolean> | null = null;

function gisReady(): Promise<boolean> {
  if (window.google?.accounts?.id) return Promise.resolve(true);
  if (!gisReadyPromise) {
    gisReadyPromise = new Promise((resolve) => {
      const started = Date.now();
      const timer = window.setInterval(() => {
        if (window.google?.accounts?.id) {
          window.clearInterval(timer);
          resolve(true);
        } else if (Date.now() - started > 10000) {
          window.clearInterval(timer);
          resolve(false);
        }
      }, 50);
    });
  }
  return gisReadyPromise;
}

type CredentialHandler = (credential: string) => void;

let currentHandler: CredentialHandler | null = null;
let initializedFor: string | null = null;

export function setGoogleCredentialHandler(handler: CredentialHandler | null): void {
  currentHandler = handler;
}

export async function renderGoogleButton(
  el: HTMLElement,
  clientId: string,
  opts: { text: 'signin_with' | 'signup_with' | 'continue_with' },
): Promise<void> {
  const ready = await gisReady();
  if (!ready || !window.google?.accounts?.id) return;
  if (initializedFor !== clientId) {
    window.google.accounts.id.initialize({
      client_id: clientId,
      callback: (response: { credential?: string }) => {
        if (response?.credential && currentHandler) currentHandler(response.credential);
      },
    });
    initializedFor = clientId;
  }
  el.innerHTML = '';
  const width = Math.min(400, Math.max(240, el.clientWidth || 320));
  window.google.accounts.id.renderButton(el, {
    type: 'standard',
    theme: 'outline',
    size: 'large',
    text: opts.text,
    shape: 'rectangular',
    logo_alignment: 'left',
    width,
  });
}
