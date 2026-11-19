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
