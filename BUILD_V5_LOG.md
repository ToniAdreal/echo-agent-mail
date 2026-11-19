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
