# Intenda 意达 — Agent Native Email

**From Intent to Done.** Intenda is an agent-native email workspace: you state the outcome, the Agent reads the context you approve, proposes a plan, works under the authorization level you choose, and brings drafts back to your Review Queue. Nothing sends without your approval path.

This repository contains the full product (V5): a FastAPI + SQLite backend (`server/`) and a React + TypeScript frontend (project root) that the backend serves in production. The demo mailbox is fully fictional; demo sends are simulated and stored in Sent.

## Quick start (local)

Prerequisites: Python 3.12, Node 20+.

```bash
# 1. Backend deps (venv inside server/)
python3 -m venv server/.venv
server/.venv/bin/pip install -r server/requirements.txt

# 2. Frontend deps + build
npm install
npm run build        # tsc type-check + vite build -> dist/

# 3. Run (single process serves API + SPA on :8000)
server/.venv/bin/python -m uvicorn app.main:app --app-dir server --port 8000
```

Open http://127.0.0.1:8000 — create an account, choose **Try the Demo Mailbox**, watch the simulated sync, and land on the Today Briefing. A one-click demo session is also available on the sign-in page.

Frontend dev mode (hot reload, API proxied to :8000): `npm run dev`.

## Configuration

All configuration is via environment variables (see `server/.env.example`). Key ones:

| Variable | Meaning |
| --- | --- |
| `LLM_BASE_URL` | OpenAI-compatible base URL (default `https://api.groq.com/openai/v1`) |
| `LLM_API_KEY` | Provider API key (falls back to `GROQ_API_KEY`). **Never commit a key.** |
| `LLM_MODEL` | Model id (default `openai/gpt-oss-20b`) |
| `SESSION_SECRET` | Session cookie signing secret (set in production) |
| `DATABASE_URL` | SQLite path (default `sqlite:///./intenda.db` under `server/`) |
| `FRONTEND_DIST` | Built frontend directory served by FastAPI (default `../dist`) |

With no LLM key configured the product still works: the Agent answers with the deterministic spec 5.5 fallback ("I'm temporarily unable to reach the AI model…"), takes no side effects, and all delegation, review and mail flows remain fully usable.

## Tests & smoke

```bash
server/.venv/bin/python -m pytest server/tests -q   # backend suite (22 tests)
python3 scripts/smoke_v5.py                          # boots real uvicorn, 13 end-to-end checks
```

## Deploy (Render free tier)

`render.yaml` defines a single free Web Service:

- **Build:** install Python deps, `npm install`, `npm run build`
- **Start:** `uvicorn app.main:app --app-dir server`
- **Health check:** `/api/v1/health`
- Set `LLM_API_KEY` and `SESSION_SECRET` in the Render dashboard (marked `sync: false`, never stored in the repo).

SQLite lives on the instance filesystem; on the free tier it resets on redeploy/spin-down, which is acceptable for the demo deployment (accounts re-seed via the Demo Mailbox flow).

## Product map

| Page | What it does |
| --- | --- |
| Today Briefing | Overnight summary, decision cards, active tasks, recent mail and activity |
| Delegate | Goal + context selection, Agent conversation (SSE), plan confirmation, authorization level |
| Task Progress | Live task timeline over WebSocket, step gates, pause / take over / terminate, outputs |
| Review Queue | Every Agent draft: edit, approve & send (simulated in Demo), reject, return to task |
| Inbox | Threads and messages, read/star, reply/forward, hand-off to the Agent, compose |
| Archive | Archived messages, searchable, restorable to the Inbox |
| Automations | Scheduled rules (briefing digest, invoice watcher) with run history |
| Settings | Profile, appearance (Day/Night, persisted server-side), Agent defaults, notifications, privacy, mailboxes, sessions, contacts, to-dos |

Authorization levels, enforced server-side per task: **Confirm Every Step**, **Confirm at Key Milestones**, **Fully Automatic but Confirm Before Sending** — and even in the last mode, sending only ever happens from the Review Queue.

## Design system

Black/white base with a single blue accent (#2563EB), macaron khaki for neutral status tints, Inter + Noto Sans SC, Day/Night themes persisted per account. Decorative artwork is generated transparent PNG (galaxy/orbit motifs); no purple anywhere.

All people, companies, amounts and messages in the seed data are fictional.
