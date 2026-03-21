# Admin UI

Web-based admin portal for browsing LLM call logs and replaying individual LLM calls with edited prompts. Built with Next.js, served alongside the FastAPI backend.

## Setup

### Prerequisites

- **Node.js 20+** — install via `brew install node` (Homebrew, recommended) or your preferred method
- **Python backend** installed and configured (see README)

### Install & Run

```bash
# Install frontend dependencies (must run from src/frontend/web/)
cd src/frontend/web
npm install

# Start the backend (in one terminal, from repo root)
uvicorn agent.api:app --reload --reload-dir src

# Start the frontend (in another terminal, from src/frontend/web/)
cd src/frontend/web
npm run dev
```

> **Note:** `npm install` must be run inside `src/frontend/web/` before `npm run dev`. The `node_modules/` directory is gitignored and must be installed locally.

- Backend runs on http://localhost:8000
- Frontend runs on http://localhost:3000
- Frontend proxies `/api/*` requests to the backend via `next.config.js` rewrites

## Features

### LLM Log Viewer

Browse LLM call logs with a 4-level drill-down:

1. **Customer Sessions** (`/admin/logs`) — Table of all customers with logs, sorted by last interaction. Shows total interactions and token usage.

2. **Draft Replies** (`/admin/logs/[customerId]`) — All agent loop invocations for a customer. Shows customer message, draft reply, model, confidence, and token counts.

3. **LLM Calls** (`/admin/logs/[customerId]/[logIndex]`) — Full conversation viewer for a single agent loop invocation. Renders each turn (user, assistant, tool_use, tool_result) with expandable tool call details. Marks LLM call boundaries in multi-turn loops.

4. **Replay** (`/admin/logs/[customerId]/[logIndex]/replay`) — Edit the system prompt and messages from any LLM call, pick a different model, re-fire the call, and see a side-by-side diff of the original vs. replayed response.

### Business Selector

Dropdown in the top bar selects which business's logs to browse. Fetches available businesses from `GET /businesses`.

## Architecture

- **Next.js** is a pure presentation layer — it fetches all data from the FastAPI backend.
- **FastAPI** handles log reading, parsing, and LLM replay via `/admin/*` endpoints.
- Log reading logic lives in `src/agent/log_reader.py`.
- No authentication (future work).

## API Endpoints (FastAPI)

| Endpoint | Description |
|----------|-------------|
| `GET /admin/logs/{biz}/customers` | List customers with logs for a business |
| `GET /admin/logs/{biz}/{customer}` | List log entries for a customer |
| `GET /admin/logs/{biz}/{customer}/{index}` | Get full log entry with LLM call boundaries |
| `POST /admin/replay` | Re-send an edited LLM call and return both responses |
