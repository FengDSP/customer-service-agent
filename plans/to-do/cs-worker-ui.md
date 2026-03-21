# Plan: CS Worker UI

## Goal
Build a web-based customer service agent view in the existing Next.js admin app. This is the web version of the CLI — a CS agent sees incoming customer messages, gets AI-generated draft replies, and reviews/edits/sends them. The CLI continues to be used for sending test customer messages (simulating the customer side).

## Context
- [ARCHITECTURE.md](../../ARCHITECTURE.md) — overall system
- [docs/admin-ui.md](../../docs/admin-ui.md) — existing admin UI (log viewer, replay)
- [docs/cli.md](../../docs/cli.md) — CLI client
- `src/agent/api.py` — FastAPI endpoints
- `src/agent/session.py` — session/history management
- `src/agent/loop.py` — agent loop (LLM + tool calls)
- `src/frontend/web/src/app/admin/layout.tsx` — admin layout with business selector and left nav
- `configs/beauty_lab.yaml` — business config (data sources)

## Design

### Flow
1. **Customer sends a message** — via CLI or future chat integration. A new `POST /messages` endpoint records the message without running the agent loop.
2. **CS agent opens the web UI** — sees a customer list page with unreplied customers at the top.
3. **CS agent clicks a customer** — sees the conversation history. The system auto-generates a draft reply for the latest unreplied message.
4. **CS agent reviews the draft** — it appears in an editable text area at the bottom.
5. **CS agent sends** — clicks "Send" to approve/send the reply (editable before sending).

### Layout (within existing admin shell)
- **Left nav**: new "Chat With Customers" item (reuses existing admin layout, business selector).
- **Main area (center)**: chat conversation, message input area not needed (CS agent doesn't type customer messages), but a "Send" button + editable draft area at the bottom.
- **Right sidebar**: customer context tables. Unstructured tables showing the customer's rows from CSV files. Which CSVs to show is configured in the business YAML under `cs_view_sources` (list of data source names). For beauty_lab: `customers` and `appointments`.

### Config change
Add `cs_view_sources` to business YAML:
```yaml
cs_view_sources:
  - customers
  - appointments
```
This tells the UI which data sources to show in the right sidebar, filtered to the current customer.

### Backend endpoints (new)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /messages` | POST | Record a customer message (no agent loop). Body: `{business_id, customer_id, message}`. Used by CLI `--as-customer` mode. After recording, notifies SSE clients. |
| `GET /conversations/{biz}/pending` | GET | List all customers with messages, unreplied first. Returns customer_id, name, last_message, last_timestamp, has_unreplied flag. |
| `GET /conversations/{biz}/{customer}/context` | GET | Customer context: for each data source in `cs_view_sources`, return the CSV rows matching this customer_id. Returns `{source_name: {columns: [...], rows: [...]}}`. |
| `POST /conversations/{biz}/{customer}/draft` | POST | Generate a draft reply by running the agent loop on the latest unreplied message. Returns the draft + metadata (confidence, internal note, suggested actions). |
| `POST /conversations/{biz}/{customer}/send` | POST | Record the approved reply in the session. Body: `{reply}`. Also pushes a `reply` SSE event. |
| `GET /conversations/{biz}/events` | GET | SSE endpoint. Streams real-time events: `message` events when customer messages arrive, `reply` events when CS agent sends. Uses `asyncio.Queue` per connection; both `POST /messages` and `POST .../send` push to all connected queues. |

### Real-time updates (SSE)

When a customer message arrives via `POST /messages`, the backend pushes an SSE event to all connected clients for that business. The frontend uses the browser-native `EventSource` API to listen:

- **Customer list page**: on event, re-fetches the pending list to update order and unreplied indicators.
- **Chat view page**: on event matching the current customer, appends the new message to the conversation and auto-triggers draft generation.
- **CLI customer mode** (separate plan: `cli-customer-mode.md`): listens for `reply` events to display CS agent responses.

Implementation: an in-memory dict of `{business_id: list[asyncio.Queue]}`. `POST /messages` pushes to all queues for the business. The SSE endpoint reads from its queue and yields `text/event-stream` lines. Queues are removed on client disconnect.

### Frontend pages (new)

| Page | Route | Description |
|------|-------|-------------|
| Customer list | `/admin/chat` | Table of customers with messages. Unreplied customers sorted to top with visual indicator. Shows customer name, last message preview, timestamp. |
| Chat view | `/admin/chat/[customerId]` | Three-column layout: chat history (center), customer context (right sidebar). Draft area at bottom with editable text + Send button. Auto-generates draft when opened with unreplied message. |

### CLI change
Add `--as-customer` flag to CLI. When set, just calls `POST /messages` to record a customer message without generating a draft. This simulates a customer sending a message that the CS agent will see in the web UI.

## Tasks

### Backend
- [ ] Add `cs_view_sources` field to `BusinessConfig` model and update `beauty_lab.yaml`
- [ ] Add `POST /messages` endpoint — records a customer message in session history (no agent loop)
- [ ] Add `GET /conversations/{biz}/pending` — list customers with messages, unreplied first
- [ ] Add `GET /conversations/{biz}/{customer}/context` — return matching CSV rows for configured sources
- [ ] Add `POST /conversations/{biz}/{customer}/draft` — run agent loop, return draft
- [ ] Add `POST /conversations/{biz}/{customer}/send` — record approved reply in session
- [ ] Add `--as-customer` flag to CLI
- [ ] Add `GET /conversations/{biz}/events` SSE endpoint with in-memory pub/sub

### Frontend
- [ ] Add "Chat With Customers" nav item to admin layout
- [ ] Build customer list page (`/admin/chat`) — table with unreplied indicator, sorted unreplied-first
- [ ] Build chat view page (`/admin/chat/[customerId]`) — conversation history display
- [ ] Build draft area — editable text area with Send button, auto-generates draft on load
- [ ] Build right sidebar — customer context tables from configured CSV sources
- [ ] SSE integration — connect to `/conversations/{biz}/events` via `EventSource`, re-fetch data on events

### Tests
- [ ] Unit tests for new backend endpoints
- [ ] Playwright tests for CS worker UI pages
- [ ] E2e test: CLI sends a customer message via `--as-customer`, verify it appears in the web UI, generate a draft, send the reply, and verify the reply is recorded in session history

### Docs
- [ ] Update `docs/admin-ui.md` with CS worker view section
- [ ] Update `ARCHITECTURE.md` if needed
- [ ] Update `README.md` CLI section for `--as-customer` flag

## Notes
