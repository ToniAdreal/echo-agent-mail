# Intenda V5 build brief (full product, per Specification v1.0)

You are building in ~/workspace/tenth-global-agent-mail. The contract is
`Intenda-Product-Specification-v1.0.md` in this directory (3,465 lines, 8 sections).
Read it fully before writing code, then implement it. Where the spec and this brief
differ, this brief wins on process, the spec wins on product behavior.

## Starting point
- The existing frontend (src/, Vite + React + TypeScript, V4 visual system) is the
  base. Evolve it into the API-driven product; do not restart the visual system and
  do not reintroduce purple anywhere. Keep the generated PNG assets in use.
- There is a git stash named "cancelled layout pass WIP (pre-V3)". Do not touch it.
- git identity for commits: user.name "ToniAdreal",
  user.email "184365500+ToniAdreal@users.noreply.github.com".

## What to build
1. Backend in a new `server/` directory: Python + FastAPI, SQLite (schema written
   Postgres-ready), implementing the spec Section 7 REST endpoint inventory and the
   WebSocket event catalogue. Auth per spec: Argon2id password hashing, HttpOnly
   session cookies, CSRF protection.
2. Onboarding per spec Section 3: register, mailbox choice, authorization
   explanation, Demo Mailbox path (the live path for this delivery), simulated sync
   with progress, then entry to Today Briefing. Demo vs Live labelled everywhere.
3. Email per spec Section 4: list, read, search, compose, reply, forward, archive,
   delete, drafts, hand-to-Agent. Seed data per spec: 30-50 synthetic messages and
   the stable demo tasks AG-2048, AG-2051, AG-2054. All seed data fictional.
4. Agent per spec Section 5: OpenAI-compatible chat completions called ONLY from the
   backend, streamed to the frontend via SSE token-by-token. Provider is configured
   purely by environment variables so the key can be dropped in later without code
   changes: LLM_BASE_URL (default https://api.groq.com/openai/v1), LLM_API_KEY,
   LLM_MODEL (default openai/gpt-oss-20b). When LLM_API_KEY is unset or the provider
   errors, use the spec's deterministic fallback behavior and exact fallback wording.
   Never hardcode any key. Keys live only in server/.env (gitignored) or host env.
5. Delegation and tasks per spec Section 6: goal to plan to authorization level
   (three levels, enforced server-side), task lifecycle over WebSocket, pause,
   resume, take over, terminate, generated drafts land in the Review Queue.
6. Frontend per spec Section 2: move the appearance (Day/Night) toggle to the
   sidebar bottom-left where the settings gear currently sits, remove it from the
   top bar, persist via PATCH /api/v1/settings. All eight pages (Today Briefing,
   Delegate Work, Task Progress, Inbox, Review Queue, Automations, Archive,
   Settings) fully wired to the API with real create/read/update/delete behavior,
   empty/loading/error states per spec. No dead buttons anywhere.
7. Single deployable service: FastAPI serves the built frontend static files in
   production mode (keep vite base relative). Add a `render.yaml` (Render free web
   service: build installs Python deps and builds the frontend; start runs uvicorn)
   and document local run + deploy steps in README.

## Process rules
- Work in stages: (1) backend skeleton + auth + seed, (2) email + briefing APIs,
  (3) agent SSE + tasks + WebSocket, (4) frontend API wiring + onboarding + toggle
  move, (5) production serving + render.yaml + tests. Commit after each stage with
  a clear message.
- Tests must pass before you finish: backend pytest covering auth, email CRUD,
  task lifecycle with authorization enforcement, and agent fallback when no key is
  set; frontend production build must succeed; plus a smoke script that boots the
  server on a test port and exercises register, login, seed sync, inbox list,
  agent chat (fallback path), task create + WS connect. Put the smoke script in
  scripts/ and record its output.
- Append a running log to BUILD_V5_LOG.md: stage, what was done, test results,
  known deviations from the spec with reasons.
- No paid services, no real email accounts, no external signups. Do not deploy
  anywhere; local build and tests only. The main agent deploys and verifies.
- If a spec detail is impractical, implement the closest faithful behavior and log
  the deviation in BUILD_V5_LOG.md instead of silently dropping it.
