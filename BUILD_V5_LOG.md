# Intenda V5 build log

Build follows BUILD_BRIEF_V5.md (process) and Intenda-Product-Specification-v1.0.md
(product behavior). Deviations are recorded per stage, never silently dropped.

## Environment notes
- Python deps installed into `server/.venv` (fastapi, uvicorn, sqlalchemy,
  argon2-cffi, httpx, pytest, websockets). System Python was left untouched.
- No LLM key exists yet and none was created. The Agent runs on the spec
  Section 5.5 deterministic fallback until a key is dropped into the backend
  environment (LLM_API_KEY, falling back to GROQ_API_KEY).

## Stage 1 — backend skeleton + auth + seed (done)
- `server/` created: config (env-only secrets), SQLAlchemy models for every
  table in spec Sections 4.8 and 7.6, Argon2id password hashing, opaque
  session cookies (HttpOnly) with hashed storage, double-submit CSRF
  (middleware + readable CSRF cookie), standard success/error envelopes with
  request IDs, in-memory rate limits for auth endpoints.
- Auth endpoints: register (with idempotency-key support and the spec's safe
  duplicate-account message), login, logout, me, one-click demo-session,
  password reset request/complete (token stored hashed in oauth_states),
  session list/revoke/revoke-others.
- Onboarding endpoints: status, start, providers, mailbox-choice,
  OAuth start/callback (full PKCE + state validation + server-side token
  exchange; returns 503 PROVIDER_NOT_CONFIGURED when no OAuth credentials are
  configured, which is the case in this deployment), demo-mailbox, complete,
  retry. Account endpoints: list/get/connect/reconnect/disconnect, sync
  start/status/job/retry.
- Demo sync is simulated by the in-process runner with the five spec phases,
  labelled simulated, and completes onboarding (state READY).
- Seed (spec 7.11): Demo Mailbox with 38 messages across 13 threads plus one
  draft message (39 total records), 8 contacts, 6 attachments, tasks AG-2048
  (draft awaiting approval), AG-2051 (waiting on a choose-option decision),
  AG-2054 (in progress), AG-2039 (completed), AG-2041 (failed step,
  recoverable), AG-2044 (completed, second pending review item), 2 pending
  review items, 2 automations (1 enabled, 1 disabled), 3 to-dos,
  2 notifications, and one clearly fictional prompt-injection sample email
  used to test the untrusted-content boundary.
- Verified manually with FastAPI TestClient against a scratch SQLite DB:
  register 201, me 200, mailbox choice, demo mailbox 201, sync completed
  100% (total 38), onboarding READY, CSRF-less mutation blocked 403,
  duplicate register 409 ACCOUNT_EXISTS, bad login 401, short password 422,
  OAuth start without credentials 503, two demo sessions for different users
  coexist (display IDs are unique per user), logout revokes the session.

### Stage 1 deviations / interpretation notes
- Repository layout follows the brief (existing frontend stays at repo root,
  backend in `server/`) instead of spec 7.2's `frontend/` + `backend/` split.
- `tasks.display_id` column added (unique per user) because spec 7.11
  requires stable human-facing task references AG-2048/2051/2054 that the
  7.6 schema does not provide a field for.
- Password reset tokens are stored (hashed) in `oauth_states` with provider
  `password_reset`; the spec schema has no dedicated reset-token table.
- OAuth PKCE verifiers are stored server-side only; with no real provider
  configured the callback path is unreachable in this deployment.
- Database schema is created with SQLAlchemy `create_all` (Postgres-ready
  types/constraints); Alembic migrations are not included in the demo scope.

## Stage 2 — email + briefing APIs (done)
- Email endpoints (spec 7.4.5): list with folder filters (inbox/sent/drafts/
  starred/archive/trash), read with attachments, compose, reply/reply-all,
  forward, send (confirm_send required, revision check 409, idempotency-key
  honored, demo sends simulated and labelled with the exact spec notice),
  archive, trash, restore, read-state, star, hand-off to Agent (creates or
  reuses a conversation with only the selected thread as context and returns
  the handoff preview from spec 4.7).
- Threads: list with unread counts, detail with messages + attachments,
  read-state, archive. Search: free text + sender/unread/date/attachment
  filters with ownership enforced. Drafts: list/create/get/PATCH with
  revision conflict 409 returning the latest draft, delete. Archive: list
  with filters + restore.
- Briefing (spec 7.4.4): metrics (new mail, needs decision, in progress,
  delivered, sent), decision cards merged from pending Review Queue items
  and pending task decisions, active tasks, recent messages, recent audit
  activity, open to-dos, and sidebar badge counts.
- Verified with TestClient on a scratch DB: briefing metrics match the seed
  (8 unread, 3 decisions, 3 active tasks, 2 delivered), inbox threads 11,
  Acme thread 4 messages + 1 attachment, search "invoice" 3 hits, compose ->
  send revision conflict 409 then simulated send 200, sent folder grows,
  archive/restore round-trip, draft PATCH conflict 409, hand-off preview,
  cross-user message access returns 404.

### Stage 2 deviations / interpretation notes
- Archiving a message archives its thread (the schema stores archive state
  at thread level, spec 4.8); the Archive page lists messages of archived
  threads.
- Compose/reply/forward create a draft plus a backing draft message so the
  inventory's `POST /emails/{messageId}/send` shape works unchanged.

## Stage 3 — agent SSE + tasks + WebSocket (done)
- Agent endpoints: conversations CRUD, status, retry, and POST messages with
  SSE streaming (message.started/delta/annotation/completed/error/heartbeat).
  The provider is called only from the backend via the OpenAI-compatible API;
  the plan JSON block in a model reply is parsed server-side and emitted as a
  plan annotation. With no key configured, the deterministic Section 5.5
  fallback runs: the user message is stored with status model_unavailable, a
  notice with the exact fallback wording is stored, no task/draft/side effect
  is created. Per-user rate limits (10/min, 100/day, configurable) enforced.
- Tasks: create only from a confirmed plan + one of the three authorization
  modes; list/detail/events (sequence-based replay); pause/resume (resume
  requires acknowledge_summary), takeover/return-control, terminate
  (confirmation required, completed work preserved), retry of failed steps.
  Decisions: list + single-use resolve (repeated resolve returns the original
  result). The in-process runner executes steps with server-side gate
  enforcement: Confirm Every Step gates every step, Confirm at Key
  Milestones gates milestone/high-risk steps, Fully Automatic but Confirm
  Before Sending runs internal steps but a send step can only complete via
  Review Queue approval. Step effects are deterministic operations over the
  user's own mailbox data; drafts land in the Review Queue.
- Review Queue: list/detail, PATCH with revision control (409 with latest on
  conflict, edits mark the item modified), approve (confirm_send required,
  idempotency honored, demo send simulated with the exact notice, linked
  task send step completes), reject (linked task goes to needs_attention),
  return-to-task.
- Automations: CRUD + revision control, enable/disable, duplicate, manual
  run with condition matching; actions summarize/create_todo/prepare_draft/
  notify; runs persisted; a run with no matches is marked needs_attention;
  automations can never send email.
- Settings: GET/PATCH (profile, appearance mode persisted server-side,
  agent preferences + default authorization mode, notifications, privacy),
  JSON data export (job + download), delete demo data, account deletion
  (password + typed DELETE confirmation, sessions revoked). Contacts and
  to-dos CRUD. WebSocket /api/v1/ws with cookie auth, server.hello,
  heartbeat, client.ping, client.task.watch.
- Verified with TestClient: fallback SSE contains the exact Section 5.5
  wording and stores user=model_unavailable + notice=failed; AG-2051
  choose_option resolution completes the choice step, the runner drafts the
  confirmation email into the Review Queue and the task completes; AG-2054
  gates at its milestone; AG-2048 approve performs the simulated send and
  completes the task at 100%; a new Confirm-Every-Step task gates before
  step 1; automation run succeeds; appearance PATCH persists; WS hello and
  heartbeat round-trip.

### Stage 3 deviations / interpretation notes
- Task step side effects (summaries, draft bodies) are produced by the
  deterministic task engine from the approved plan and the selected mailbox
  context, not by the chat model; the model is used for conversation and
  plan generation only. This keeps delegated work inspectable and available
  in the demo while the Section 5.5 rule (no fabricated model answers, no
  side effects from failed model requests) is fully honored for Agent chat.
- Extra endpoint POST /automations/{id}/duplicate supports the spec's
  Automations page Duplicate action (not in the 7.4.9 inventory).

## Stage 4 — frontend wired to the API (done)
- New client layer: src/lib/api.ts (envelope-aware fetch with CSRF header,
  SSE parser for Agent streaming, reconnecting WebSocket client, shared
  types), src/lib/ui.tsx (history router, toasts, modal, skeletons,
  formatting), src/lib/appctx.ts (session/theme/badges/composer context).
- Auth pages (login, register, forgot/reset with demo token display) and a
  full onboarding flow (provider choice, OAuth start with graceful
  not-configured explanation, Demo Mailbox, polled sync progress with the
  five spec stages, READY handoff to Today Briefing).
- Shell: Sidebar now routes to all eight pages with live badges from the
  briefing endpoint; the Appearance Day/Night control moved to the sidebar
  bottom-left per spec 1.8 (icon + label + current mode, menu with radio
  semantics, full keyboard support, immediate local apply + PATCH
  /api/v1/settings persistence + localStorage cache; server value wins at
  sign-in). The top bar no longer carries a theme toggle; it has live
  search (messages/tasks/people), sync status, Compose, notifications
  (new backend list/read endpoints) and the account menu.
- All eight pages are API-driven with loading/empty/error states and no
  dead buttons: Briefing (metrics, decision cards with approve/reject/
  choose routing, agent activity, recent mail, to-dos), Delegate (goal,
  context selection, streaming Agent chat with plan annotation, manual
  plan builder, three authorization levels, Start execution), Task
  Progress (list + detail with steps timeline, decision cards incl.
  choose_option and free_text, pause/resume/takeover/return/terminate,
  step retry), Inbox (folders incl. Drafts and Trash, read pane, star,
  archive, reply/reply-all/forward via server reply drafts, hand-off to
  Agent), Review Queue (filters, edit with revision control, approve with
  simulated-send notice, reject, return-to-task), Automations (CRUD-lite,
  enable switch, run now, duplicate, run history), Archive (list, search,
  restore), Settings (profile, appearance, mailboxes, agent defaults,
  notification switches, contacts, sessions, export/delete flows).
- Composer modal handles new/reply/reply-all/forward/draft editing with
  save-draft and confirmed send; demo sends show the simulated-send notice.
- CSS tokens replaced with the exact spec Section 1.7 values (single
  #2563EB accent for fills, hover, focus and accent text; muted status
  colors; khaki accents). Fonts: Inter + Noto Sans SC. First-paint theme
  script now falls back to the OS preference per spec 1.8.
- Removed the V4 local-state modules (src/data.ts, components/icons.tsx);
  icons now come from lucide-react (added to package.json, installed with
  pnpm). Verified: tsc --noEmit clean; vite build succeeds (dist JS
  277 kB / 79 kB gzip, CSS 37 kB).

### Stage 4 deviations / interpretation notes
- UI copy follows the spec's English strings (V4's Chinese top-bar crumbs
  are superseded by the spec's English navigation labels); the 意达 brand
  mark and one bilingual ribbon line remain from V4.
- Routing is a small built-in history router instead of react-router
  (keeps the dependency surface unchanged; routes match spec Section 2.1).
- Two small backend endpoints were added for the top bar: GET
  /api/v1/notifications and POST /api/v1/notifications/{id}/read.
- The seeded demo user's "This session" row and session management are
  fully functional; the demo account shares the same Argon2id + cookie
  session machinery as registered accounts.

---

## Stage 5 — Production packaging, test suite, smoke (complete)

- render.yaml: single Render free Web Service. Build installs Python deps
  into server/.venv, npm install + npm run build; start runs uvicorn with
  --app-dir server; healthCheckPath /api/v1/health; LLM_API_KEY and
  SESSION_SECRET declared sync:false (dashboard-only, never in repo).
- FastAPI serves the built frontend: StaticFiles on FRONTEND_DIST with an
  SPA fallback for non-API routes; unknown /api/v1 routes keep the JSON
  error envelope (verified live: /, /briefing 200; unknown API 404
  envelope; static PNG 200).
- Backend test suite (server/tests/, pytest): 22 tests covering auth +
  CSRF + password reset, demo seed invariants, mail/drafts/send
  idempotency, revision conflicts, reply threading, archive/restore,
  three authorization modes end to end, task plan requirement,
  pause/resume/terminate, seeded AG-2051 choice resolution, agent SSE +
  non-streaming fallback with the exact spec 5.5 wording, automation run,
  settings round-trip. Result: 22 passed.
- Smoke script (scripts/smoke_v5.py): boots real uvicorn on a throwaway
  DB and checks health, register, demo seed, onboarding READY, briefing
  metrics, inbox, SSE fallback, task gating at the Review Queue,
  WebSocket server.hello, SPA serving, API 404 envelope. Result: 13/13.
- Frontend after the Stage 5 API remapping: tsc --noEmit clean; vite
  build succeeds (dist JS 277 kB / 79 kB gzip, CSS 37 kB).
- README rewritten for the full product: local run, env table, tests,
  Render deploy notes.

### Stage 5 deviations / corrections found while aligning to the real API
- The Stage 1-2 backend implements the spec's own endpoint shapes, which
  differ from early Stage 4 assumptions. Stage 5 remapped the frontend
  and tests onto the real surface rather than changing the backend:
  briefing at GET /api/v1/briefing; mail under /api/v1/emails (+ /compose
  is draft-only, sends go through /emails/{id}/send with confirm_send);
  archive is message-grained (GET /api/v1/archive, restore per message,
  restoring un-archives the whole thread); account disconnect is
  DELETE /api/v1/accounts/{id}; session revoke is
  DELETE /api/v1/auth/sessions/{id}; password reset lives under
  /api/v1/auth/password/reset/*. Authorization modes use the spec names
  confirm_every_step / confirm_milestones / confirm_before_send.
- Search (GET /api/v1/search) returns messages only; the top-bar search
  UI therefore shows message results (no task/contact groups).
- Register requires terms_accepted (spec Section 3 acknowledgement);
  the Register page gained the matching checkbox.
- Demo-mode password reset returns the reset token in the API response
  (DEMO_MODE_ENABLED only): a demo deployment has no outbound mail
  channel, so without this the reset flow could never complete. Live
  deployments must keep DEMO_MODE_ENABLED off for this path.
- Runner bug fixed: the send-step pre-check parked a task at the Review
  Queue gate before earlier plan steps had run (deadlock for any plan
  containing a send step). The gate now applies only once the send step
  is current, and completing a draft step links its review_id into the
  send step's input_refs.
- perform_send bug fixed: it created a new sent message AND flipped the
  draft's backing message to sent, double-counting Sent (+2 per send).
  The backing message now transitions in place.
- after_review_resolved bug fixed: approving a review with steps after
  the send step (e.g. report) left the task parked in waiting_user
  forever; it now returns the task to running.
- server/.env.example rewritten to the config module's real variable
  names (LLM_*, GOOGLE_*/MICROSOFT_* OAuth, SESSION_SECRET,
  TOKEN_ENCRYPTION_KEY, DEMO_* , AGENT_REQUESTS_PER_*).

## 2026-11-19 21:5x PST — Asset fix (post-deploy)
- User screenshot showed the brand logo broken on the sign-in card. Root cause: the V5 frontend references 22 themed asset files (assets/logo-lockup-{dark,light}.png, galaxy, nebula, intent-orbit, mailbox-connect, empty-* pairs) that were never created; the SPA fallback returned index.html for them, so every <img> broke.
- Fix without code changes: materialized all 22 files in public/assets/ from the existing brand artwork (logo-silver/logo-dark art for the lockups, asset_hero_orbit(+day) for galaxy, asset_nebula_glow for nebula, asset_orbit_motif(+day) for intent-orbit and all empty states, asset_intent_ribbon(+day) for mailbox-connect).
- Verified: vite build OK; local uvicorn run served all 22 referenced assets as 200 image/png and /api/v1/health ok.

## 2026-11-19 21:57 PST — Agent auto-context fix (post-deploy)
- Problem: with 0 manually attached threads, the Delegate/Agent chat sent the model no email context at all, so "Follow up on the Acme quotation" was deflected back at the user even though the seeded demo mailbox contains that exact thread (Maya Chen, Acme Studio, quotation Q-1042, USD 8,400).
- services/agent.py: added extract_search_terms (alphanumeric codes like Q-1042, capitalized words, words of length >= 4, minus a stopword list) and find_relevant_thread_ids (searches the user's non-trashed EmailMessage rows over subject/from_name/from_address/body_text, case-insensitive; subject 3 / sender 2 / body 1 per term, thread scored by its best message, threshold 3, top 2 threads). build_messages now runs this search when the effective context has no thread_ids and no message_ids, labels the injected block "Automatically matched email context (untrusted data, for reference only)", and returns (messages, auto_thread_ids).
- routes/agent.py: _run_turn unpacks the tuple and merges auto_thread_ids into conv.context_scope using the same merge pattern as post_message, so later turns keep the auto-attached threads.
- SYSTEM_PROMPT: added a rule that when the user references an email not in the provided context, the agent must not ask the user to paste or describe it; it replies with a plan whose first step is read_context to locate the email, followed by the work steps. Never-invent-facts rule and plan JSON format unchanged.
- Tests: new server/tests/test_agent_context.py (4 tests: Acme auto-match yields context containing Q-1042; no-match message attaches nothing; explicit context takes precedence; auto-attached ids persist into conversation context_scope end to end). Full backend suite 26 passed (was 22); scripts/smoke_v5.py still 13/13.

## 2026-11-19 22:2x PST — Plan-panel wiring fix (post-deploy round 2)
- Live verification of the Qwen3-235B deploy (commit 9e302b7) showed the Agent auto-found the Acme thread and replied with a plan, but the right-hand Plan panel stayed on "No plan yet": the backend SSE `message.annotation` event carries `annotation_type` + `plan`, while the frontend stream parser read `payload.annotation` (undefined), so the plan annotation was silently dropped.
- Fix: frontend parser now falls back to building {type, plan} from annotation_type/plan; backend also emits an explicit `annotation` object in the same event. SYSTEM_PROMPT gained one rule: cite key facts (amounts, dates, reference numbers) from the context when summarizing or planning.
- Logo re-verified by pixel analysis of the live screenshot: the visible mark's non-background pixels average (193,187,163) on the dark card, i.e. the silver lockup renders correctly in night mode; the earlier "dark-on-dark" reading came from inspecting the hidden day-variant file.
- Verified: pytest 26 passed, smoke 13/13, vite build OK.

## 2026-11-19 22:3x PST — Combined logo lockup (user-supplied ChatGPT artwork)
- User had ChatGPT (original brand thread) generate a combined lockup: comet icon + "Intenda" wordmark in one image, and supplied the PNG directly (white art, transparent background, 2172x724).
- Processed locally: trimmed to content, saved as public/assets/logo-lockup-dark.png (light art, night mode). Derived the day version from the same alpha with flat near-black (26,27,32) art as logo-lockup-light.png.
- Removed the HTML brand text next to the logo in both places per user instruction: Sidebar brand row (the 意达 span) and the sign-in card brand (Intenda + 意达 spans). Lockup display heights adjusted (sidebar 34px, auth 46px). Favicon stays the icon-only mark.
- Verified: vite build OK; dist lockups' opaque-pixel averages match expectations (251,251,252) / (26,27,32).

## 2026-11-19 22:5x PST — Real Gmail connectivity (live Google accounts)
- Problem: the OAuth PKCE scaffolding worked, but everything after the callback was a stub. Tokens were stored as plaintext, and the runner completed every sync job (live included) with the time-based simulation, so a connected Google account synced zero real messages. Live sends were recorded locally with a "no provider confirmed" notice.
- Token encryption (app/security.py): encrypt_secret/decrypt_secret using Fernet; key = base64url(sha256(TOKEN_ENCRYPTION_KEY or SESSION_SECRET)). decrypt_secret returns the raw value when Fernet decryption fails, so pre-encryption rows keep working. Added cryptography>=42 to server/requirements.txt (installed 50.0.2 into server/.venv).
- Onboarding wiring (routes/onboarding.py): the PKCE verifier is encrypted in OAuthState and decrypted for the token exchange; access/refresh tokens are encrypted when the MailAccount is created, and token_expires_at is set from the token response's expires_in.
- New app/services/gmail.py (async httpx; functions accept an optional transport for MockTransport tests):
  - get_access_token: returns the decrypted stored token when it has >60s left; otherwise refreshes against oauth2.googleapis.com/token, persists the new token encrypted plus the new expiry (and a rotated refresh token when returned). invalid_grant (or 400/401) raises the typed GmailAuthError; other failures raise GmailError.
  - sync_account: GET profile (captures historyId), lists message ids (initial 100 / incremental 50), fetches format=full, and upserts threads/messages keyed by (mail_account_id, provider_thread_id) / (mail_account_id, provider_message_id), so re-syncs are idempotent (attachment rows are replaced per message). Parsing: case-insensitive headers; From split into from_name/from_address; To/Cc/Bcc as {"name","email"} lists matching seed.py shapes; MIME walk with base64url decode, text/plain -> body_text, text/html -> body_html_sanitized with <script>/<style> blocks stripped; snippet from the API response; dates from internalDate (received_at, or sent_at for SENT). labelIds map to flags (UNREAD/SENT/DRAFT/STARRED/TRASH/SPAM). Thread fields recomputed from stored messages (message_count, last_message_at, participants, latest snippet, subject_normalized with repeated Re:/Fwd:/Fw: stripped). is_archived clears whenever a batch message carries INBOX and is set only when the batch covered every stored message of the thread and none was in the inbox. Attachments recorded without content download (filename, mime type, size, provider_attachment_id). Sets account.last_sync_at and account.sync_cursor=historyId; returns (upserted count, historyId).
  - Sending: build_raw_message builds an RFC 822 MIME message from a draft (In-Reply-To/References anchored on the thread's latest stored internet Message-ID, Gmail threadId included); send_draft POSTs users/me/messages/send and returns the provider message id, raising on any failure; send_draft_sync bridges the sync perform_send path.
- Runner (services/runner.py): _advance_syncs branches live+google jobs to _advance_live_google_sync BEFORE the time-based simulation. Success completes the job like the demo path (processed=total=fetched, cursor_after=historyId, account connected, onboarding SYNCING->READY, sync.completed broadcast with simulated=False). GmailAuthError -> job failed with TOKEN_REFRESH_FAILED and account action_required; any other exception -> job failed with GMAIL_SYNC_FAILED and account back to connected. Demo jobs and live Microsoft jobs keep the simulated path untouched.
- Real send on approval (services/tasks_svc.py perform_send): for a live Google account the Gmail send runs FIRST, before any local state changes; on success the returned provider message id is stored on the sent message and the result reports simulated=False with the provider id. A Gmail failure raises, so the review/mail send endpoints surface an error instead of recording a send that never happened. Demo behavior unchanged; live Microsoft keeps the honest local-only notice.
- Tests: new server/tests/test_gmail.py, 13 tests, all Gmail HTTP mocked with httpx.MockTransport (no network): encrypt/decrypt round-trip and legacy plaintext passthrough; canned-payload parsing (headers, multipart body, script/style stripping, labels -> flags, thread fields); sync upsert idempotency (two syncs, counts stable); fresh-token reuse without HTTP; refresh when expired; invalid_grant -> GmailAuthError; runner completes a live job via a mocked sync_account, fails it with TOKEN_REFRESH_FAILED on GmailAuthError and GMAIL_SYNC_FAILED on a generic error; perform_send sends through Gmail (threadId + In-Reply-To/References asserted on the decoded raw MIME) and, on a Gmail 500, raises and records nothing.
- Test-infrastructure note: test_gmail.py must not import app.* at module top level. The shared conftest freezes app.config's DATABASE_URL at first import and its client fixture relies on being the first importer (after setting a tmp DATABASE_URL); a collection-time import in this module broke the other modules' reload-based fixtures (observed as "no such table: users" in test_tasks). The module therefore imports the app through a module-scoped autouse fixture that depends on conftest's client fixture and injects the names into module globals.
- Verified: full backend suite 39 passed (26 baseline + 13 new); scripts/smoke_v5.py 13/13. No frontend changes.
- Not yet live-verified: the deployment still needs GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET (and ideally a dedicated TOKEN_ENCRYPTION_KEY) in the Render environment, plus one real connect + sync + approve-send pass against a real Gmail account, before this can be called proven end to end.

## 2026-11-19 — Public Privacy Policy and Terms pages (for Google OAuth verification)
- New src/components/Legal.tsx: PrivacyPage (/privacy) and TermsPage (/terms) in a shared LegalShell (auth-shell + wide legal-card, brand lockup, cross-links and a Back to sign in link in the footer). App.tsx routes both paths BEFORE the boot-state branches, so they render in every state, signed in or not. The FastAPI SPA fallback already serves index.html for unknown paths; verified locally that GET /privacy and GET /terms return 200 text/html and that the built bundle contains both pages.
- Privacy Policy (dated November 19, 2026; contact team@tokenta.space; no company address): what Intenda is (Agent Native email client by Tokenta, Google connection optional, Demo Mailbox alternative); data accessed with Google sign-in (openid/email/profile basics plus the gmail.modify scope, with Google's own characterization that the scope does not allow immediate permanent deletion bypassing trash; mail is sent only after explicit approval in the Review queue); use limited to the mailbox features the user invokes; a dedicated Google API Limited Use section (adherence to the Google API Services User Data Policy including Limited Use; no model training, no sale, no advertising, no human reading except to operate a triggered feature, security, or legal reasons); storage and security (Fernet-encrypted OAuth tokens, synced data in the app database, honest note that the current Render free-tier deployment has an ephemeral database); retention and deletion (disconnect in Settings deletes synced data and discards tokens, revoke anytime at myaccount.google.com/permissions, deletion requests via the contact email); sharing limited to the processors needed to run the service (hosting provider, and the configured language-model provider when the user asks the Agent to draft or summarize).
- Terms of Service: short standard demo terms (as-is evaluation service, user responsibility for reviewed/approved sends, acceptable use, no warranty, changes, contact).
- Links: shared LegalLinks footer added to the Login and Register pages; a Privacy/Terms line added under the data hint on the Onboarding connect step; links added to the Privacy & data section of Settings. Auth.tsx now exports Brand (reused by LegalShell) and LegalLinks.
- Styles: .auth-legal, .legal-card (max-width 780px), .legal-body prose rules, .legal-meta, .legal-footer in src/styles.css, using the existing theme variables so both day and night themes work.
- Verified: npm run build clean (bundle grep confirms Privacy Policy / Terms of Service / Limited Use / gmail.modify strings present); backend suite 39 passed (unchanged); scripts/smoke_v5.py 13/13. Frontend-only change plus this log.

## 2026-11-19 23:2x PST — Real Microsoft (Outlook) connectivity (live Microsoft accounts)
- Problem: the provider-generic OAuth layer already handled microsoft (callback, encrypted token storage, token_expires_at), but everything after it was missing: the runner's live branch only implemented the real path for google, so a connected Microsoft account's sync jobs fell through to the time-based simulation and synced zero real messages, and live Microsoft sends were recorded locally with a "no provider confirmed" notice.
- New app/services/graphmail.py (async httpx; optional transport for MockTransport tests; mirrors gmail.py's structure and conventions, reusing its normalize_subject, script/style stripper, and thread-recompute helpers so both providers share identical idempotency and thread rules):
  - get_access_token: decrypt, refresh via login.microsoftonline.com/common/oauth2/v2.0/token with scope "openid email profile Mail.ReadWrite Mail.Send offline_access" when the stored token is missing or within 60s of expiry; persists the new access token encrypted and, because Microsoft rotates refresh tokens, any replacement refresh token too. invalid_grant (or HTTP 400/401) -> GraphAuthError; other failures -> GraphError.
  - sync_account: fetches well-known folder ids from GET /v1.0/me/mailFolders (inbox, drafts, sentitems, deleteditems, junkemail), then lists GET /v1.0/me/messages ($top 100 initial / 50 incremental, $orderby receivedDateTime desc, $select covering id/conversationId/subject/from/to/cc/dates/bodyPreview/isRead/isDraft/hasAttachments/body/internetMessageId/parentFolderId). Upserts threads keyed by (mail_account_id, provider_thread_id=conversationId) and messages by (mail_account_id, provider_message_id=id); re-syncs are idempotent (attachment rows replaced per message). Parsing: Graph emailAddress {name, address} -> the seed's {"name","email"} recipient shape; body contentType "text" -> body_text, "html" -> body_html_sanitized with script/style stripped; snippet from bodyPreview; dates from receivedDateTime/sentDateTime (sent folder messages stamp sent_at, others received_at). Flags come from folder membership + message fields: isRead -> is_read; isDraft or drafts folder -> is_draft; sentitems folder -> is_sent; deleteditems/junkemail -> is_trashed; thread.is_archived when no synced message sits in the inbox folder, with the same partial-batch care as Gmail (a batch showing an inbox message always clears it; it is only set when the batch covered every stored message of the thread). Attachments: for hasAttachments messages, GET /v1.0/me/messages/{id}/attachments ($select id,name,contentType,size) recorded without content download. Sets account.last_sync_at; returns (upserted count, None) — Graph delta sync is out of scope, so sync_cursor is left untouched.
  - Sending: send_draft creates the message via POST /v1.0/me/messages (subject, Text body, to/cc/bcc recipients) and then POSTs /v1.0/me/messages/{new_id}/send, returning the created message id as the provider id; any HTTP failure raises before callers record anything. Graph cannot create a message directly inside an existing conversation, so no thread linkage is sent; send_draft accepts a thread argument for signature parity with gmail.send_draft and ignores it. send_draft_sync bridges the sync perform_send path exactly like gmail's.
- Runner (services/runner.py): the live-sync bookkeeping was factored into _run_live_sync (identical completion/failure handling: processed=total=fetched, cursor_after, account connected, onboarding SYNCING->READY, sync.completed broadcast with simulated=False; auth error -> job failed TOKEN_REFRESH_FAILED + account action_required; other failure -> provider code + account back to connected), with _advance_live_google_sync and the new _advance_live_microsoft_sync as thin wrappers. _advance_syncs now branches live+microsoft jobs to the real Graph sync before the simulation; Google and demo behavior unchanged (all pre-existing runner tests still pass).
- Real send on approval (services/tasks_svc.py perform_send): live Microsoft drafts now send through Graph FIRST, before any local state changes, mirroring the Google branch; the returned provider message id is stored on the sent message and the result reports simulated=False with a provider-aware notice ("Sent through your connected Microsoft account."). A Graph failure raises, so the endpoints surface an error instead of recording a send that never happened. Demo behavior unchanged.
- Tests: new server/tests/test_graphmail.py, 11 tests, all Graph HTTP mocked with httpx.MockTransport (no network): canned-payload parsing (emailAddress shapes, html script/style stripping, folder-driven flags incl. drafts/deleteditems/junkemail overrides, sent-folder timestamps, subject prefix stripping); sync upsert idempotency (two syncs, counts stable, attachment fields, cursor stays None); fresh-token reuse without HTTP; refresh when expired (form body asserted: grant_type, stored refresh token, Mail.ReadWrite/Mail.Send/offline_access in scope; rotated refresh token persisted); invalid_grant -> GraphAuthError; runner completes a live Microsoft job via a mocked sync_account, fails it with TOKEN_REFRESH_FAILED on GraphAuthError and GRAPH_SYNC_FAILED on a generic error; perform_send sends through Graph (create + send call order and payload asserted) and, on a Graph 500, raises and records nothing. The module follows test_gmail.py's import pattern (app imported through a module-scoped fixture tied to conftest's client fixture, never at collection time).
- Verified: full backend suite 50 passed (39 baseline + 11 new); scripts/smoke_v5.py 13/13. No frontend changes.
- Not yet live-verified: the deployment still needs MICROSOFT_CLIENT_ID/MICROSOFT_CLIENT_SECRET in the Render environment (the Azure app registration must allow the /common tenant + personal accounts for Outlook.com mailboxes), plus one real connect + sync + approve-send pass against a real Outlook account, before this can be called proven end to end.
