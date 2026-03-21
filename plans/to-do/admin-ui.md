# Plan: Admin UI — LLM Log Viewer & Replayer

## Goal
Build a web-based admin UI for browsing LLM call logs and replaying individual LLM calls with edited prompts. This is the first feature of a broader admin portal that will eventually include usage dashboards, billing, and config management.

## Context
- `logs/llm/{business_id}/{customer_id}.jsonl` — JSONL log files, one line per agent loop invocation
- `docs/llm-logging.md` — log format docs
- `src/agent/loop.py` — agent loop that makes LLM calls and logs them
- `src/agent/api.py` — existing FastAPI backend
- `ARCHITECTURE.md` — system overview

## Architecture Decision: Frontend calls Backend for all data

**Decision: Next.js is a pure presentation layer. All log reading, log parsing, and LLM replay logic lives in the FastAPI backend.**

- The Next.js app lives at `src/frontend/web/` in the repo. It serves both the admin UI (this plan) and the future CS worker UI.
- Next.js pages fetch data from FastAPI endpoints — no direct file access from the frontend.
- New FastAPI endpoints are added for log browsing and replay.
- The existing FastAPI backend stays as the single source of truth for all log format logic, config parsing, and Anthropic API calls.
- For development: FastAPI runs on `:8000`, Next.js runs on `:3000` (proxies API calls to `:8000`).

**Why backend-only for log logic:**
- All JSONL parsing and log format knowledge stays in Python (one place to update if format changes)
- API key management stays server-side
- Next.js stays simple — just UI rendering and data fetching
- The backend already has config/YAML parsing, session logic, etc.

```
Repo structure after this plan:

src/
  agent/                    # Existing Python backend
    api.py                  # FastAPI — existing + new log/replay endpoints
    logging.py              # Existing log writer
    log_reader.py           # NEW: log reading/parsing logic
    ...
  cli.py                    # Existing CLI
  frontend/
    web/                    # Next.js app (admin + future CS worker UI)
      app/
        layout.tsx          # Root layout with business selector
        admin/
          page.tsx          # Admin landing → redirects to log viewer
          logs/
            page.tsx        # Log viewer: customer sessions list
            [customerId]/
              page.tsx      # Draft replies list for a customer
              [logIndex]/
                page.tsx    # LLM calls within a single agent loop invocation
                replay/
                  page.tsx  # Replay: edit prompt, fire LLM call, show diff
      next.config.js        # Proxy /api/* to FastAPI :8000
      package.json
      tsconfig.json
```

## FastAPI Endpoints (new)

### GET /admin/logs/{business_id}/customers
List customers with log files for a business, sorted by last interaction.
```json
[{
  "customer_id": "CUS-001",
  "last_interaction": "2026-03-20T19:30:00Z",
  "total_interactions": 15,
  "total_tokens": {"input": 12000, "output": 3500}
}]
```

### GET /admin/logs/{business_id}/{customer_id}
List all log entries (agent loop invocations) for a customer.
```json
[{
  "index": 0,
  "timestamp": "2026-03-20T19:30:00Z",
  "customer_message": "When is my next appointment?",
  "draft_reply": "Your next appointment is...",
  "model": "claude-sonnet-4-6",
  "confidence": "high",
  "usage": {"input_tokens": 500, "output_tokens": 150},
  "turns_count": 5
}]
```

### GET /admin/logs/{business_id}/{customer_id}/{log_index}
Return the full log entry at the given line index, including all turns, system prompt, tools, and model.

### POST /admin/replay
Re-send an edited single-turn LLM call. The frontend sends the edited prompt and the original response for comparison.
```json
// Request
{
  "model": "claude-sonnet-4-6",
  "system": "You are a customer service agent...",
  "messages": [...],
  "tools": [...],
  "original_response_text": "..."
}

// Response
{
  "original": {"text": "...", "usage": {...}},
  "replayed": {"text": "...", "usage": {...}}
}
```

The existing `GET /businesses` and `GET /businesses/{business_id}/customers` endpoints (added for CLI) are reused by the admin UI.

## UI Layout

### Global
- **Top bar**: Business selector dropdown (top-left). Changing business reloads the page content.
- **Left panel**: Navigation/feature menu. Currently one item: "LLM Log Viewer". Future: "Usage", "Billing", "Config".
- **Right panel**: Main content area (changes based on drill-down level).

### Log Viewer Flow (right panel)

**Level 1 — Customer Sessions List** (`/admin/logs`)
- Table of all customers who have log entries for the selected business
- Columns: Customer ID, Last Interaction Time, Total Interactions, Total Tokens
- Sorted by last interaction time (most recent first)
- Click a row → drill into that customer

**Level 2 — Draft Replies List** (`/admin/logs/[customerId]`)
- Breadcrumb: Business > Customer ID
- Table of all agent loop invocations (one per JSONL line)
- Columns: Timestamp, Customer Message (truncated), Draft Reply (truncated), Model, Confidence, Tokens (in/out)
- Sorted by timestamp (most recent first)
- Click a row → drill into the LLM calls

**Level 3 — LLM Calls** (`/admin/logs/[customerId]/[logIndex]`)
- Breadcrumb: Business > Customer ID > Timestamp
- Full agent loop invocation displayed as conversation:
  - System prompt (collapsible)
  - Each turn rendered as a chat message (user, assistant, tool_use, tool_result)
  - Tool calls shown with input/output in expandable blocks
  - Token usage summary
- Each LLM call boundary is marked (the loop may call the LLM multiple times when tools are used)
- "Replay" button on each individual LLM call → opens replay page

**Level 4 — Replay** (`/admin/logs/[customerId]/[logIndex]/replay`)
- Editable fields for the selected single-turn LLM call:
  - **System prompt**: text area
  - **Messages**: the messages array for this specific API call (editable JSON or structured form)
  - **Tools**: read-only, collapsible
  - **Model selector**: dropdown
- "Send" button calls `POST /admin/replay` on the FastAPI backend
- Response display:
  - **Original response** (left or top)
  - **New response** (right or bottom)
  - **Diff view**: highlighted text differences

## Tasks

### Backend: log reader module
- [ ] Create `src/agent/log_reader.py` with functions to:
  - List customers with logs for a business (with summary stats)
  - List log entries for a customer (with summary fields)
  - Get a full log entry by index
  - Extract individual LLM call boundaries from a multi-turn log entry
- [ ] Add endpoints to `src/agent/api.py`:
  - `GET /admin/logs/{business_id}/customers`
  - `GET /admin/logs/{business_id}/{customer_id}`
  - `GET /admin/logs/{business_id}/{customer_id}/{log_index}`
  - `POST /admin/replay`
- [ ] Add tests for log reader functions

### Frontend: project setup
- [ ] Initialize Next.js app in `src/frontend/web/` with TypeScript, Tailwind CSS, App Router
- [ ] Configure `next.config.js` to proxy `/api/*` and `/admin/*` to FastAPI `:8000`
- [ ] Add `node_modules/`, `.next/` to `.gitignore`

### Frontend: UI layout
- [ ] Root layout with top bar (business selector dropdown) and left/right panel structure
- [ ] Left panel navigation menu (just "LLM Log Viewer" for now)
- [ ] Business selector fetches from `/businesses`, stores in URL query param or state

### Frontend: log viewer pages
- [ ] Level 1: Customer sessions table with sorting
- [ ] Level 2: Draft replies table for a customer
- [ ] Level 3: Full conversation viewer with turn-by-turn rendering
  - [ ] Distinct rendering for user/assistant/tool_use/tool_result
  - [ ] Collapsible system prompt
  - [ ] Expandable tool call details
  - [ ] LLM call boundary markers
  - [ ] "Replay" button per LLM call

### Frontend: replay page
- [ ] Editable system prompt text area
- [ ] Editable messages (JSON editor or structured form)
- [ ] Model selector dropdown
- [ ] Read-only tools display (collapsible)
- [ ] "Send" button → `POST /admin/replay`
- [ ] Side-by-side diff view (use `react-diff-viewer` or similar)

### Documentation
- [ ] Create `docs/admin-ui.md` with setup and usage
- [ ] Update `ARCHITECTURE.md` to add Admin UI component
- [ ] Update `README.md` with Next.js dev server instructions

## Notes
- No auth for now. Auth is a future plan for when the CS worker UI is built.
- The `src/frontend/web/` directory is the shared home for both admin UI and future CS worker UI, as separate route groups (`app/admin/`, `app/agent/`).
- Replay supports single-turn LLM calls only (one API request/response). Multi-turn replay (re-running the full agent loop with tool execution) is future work.
- Next.js dev server proxies API calls to FastAPI — in production, both could be behind a reverse proxy.
- The replay endpoint reuses the same `ANTHROPIC_API_KEY` as the agent loop.

## Future Features (not in this plan)
- Usage dashboard (tokens over time, cost estimates)
- Billing management
- Business config editor (edit YAML from the UI)
- CS worker view (human-in-the-loop approval interface)
- Auth and role-based access (admin vs. CS worker)
- Multi-turn replay (re-run full agent loop with tools)
