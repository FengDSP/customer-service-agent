# Plan: CLI Customer Mode

## Goal
Make the CLI default to **customer mode** — simulating the customer side of a conversation. The customer sends messages and receives approved replies from the CS agent (via the admin UI). The current CS agent mode (draft review) becomes opt-in via `--cs-mode`.

## Context
- [docs/cli.md](../../docs/cli.md) — CLI client
- `src/cli.py` — current CLI implementation
- `plans/to-do/cs-worker-ui.md` — CS worker UI plan (dependency: `POST /messages`, SSE, `POST /conversations/{biz}/{customer}/send`)

## Dependency
This plan depends on the **CS Worker UI** plan for:
- `POST /messages` endpoint (record customer message)
- `GET /conversations/{biz}/events` SSE endpoint
- `POST /conversations/{biz}/{customer}/send` endpoint (CS agent sends reply)

The SSE endpoint must be extended to also emit `reply` events when `POST /conversations/{biz}/{customer}/send` is called, not just `message` events for incoming customer messages.

## Design

### CLI modes

| Mode | Flag | Behavior |
|------|------|----------|
| **Customer** (default) | none | Send messages via `POST /messages`. Listen for replies via SSE. Display replies when they arrive. |
| **CS Agent** | `--cs-mode` | Current behavior: send messages via `POST /chat`, review/edit/approve drafts. |
| **CS Agent (auto)** | `--cs-mode --auto-approve` | Current auto-approve behavior. |

The `--as-customer` flag is removed (it's now the default). The `--auto-approve` flag only applies with `--cs-mode`.

### Customer mode flow
1. CLI connects to SSE at `GET /conversations/{biz}/events` in a background thread.
2. Customer types a message → `POST /messages` records it.
3. CLI prints "(message sent, waiting for reply...)" and continues accepting input.
4. When the CS agent approves a reply in the admin UI → `POST /conversations/{biz}/{customer}/send` pushes a `reply` SSE event.
5. CLI receives the event, displays: `Agent: <reply text>`.
6. Customer can send another message while waiting (async — messages and replies interleave naturally).

### SSE event types
The SSE endpoint needs two event types:

```
event: message
data: {"customer_id": "CUS-001", "message": "...", "timestamp": "..."}

event: reply
data: {"customer_id": "CUS-001", "reply": "...", "timestamp": "..."}
```

The CLI in customer mode only listens for `reply` events matching its customer_id.

### Banner change
```
Connected to Beauty Lab Customer Service
Customer: CUS-001
Mode: customer

Type a message to start chatting. A CS agent will reply from the admin UI.
Type /help for commands.
```

## Tasks
- [ ] Extend SSE endpoint to emit `reply` events when `POST /conversations/{biz}/{customer}/send` is called
- [ ] Refactor CLI: make customer mode the default, move current behavior behind `--cs-mode`
- [ ] Remove `--as-customer` flag (now the default)
- [ ] Implement SSE listener in CLI (background thread using `httpx-sse` or raw `httpx` streaming)
- [ ] Display incoming replies asynchronously while accepting input
- [ ] Update `/help` and banner for customer mode
- [ ] E2e test: CLI sends a customer message in customer mode, a test script calls the send endpoint to simulate the CS agent, verify the CLI receives and displays the reply
- [ ] Update `docs/cli.md` with new modes
- [ ] Update `README.md` CLI usage examples

## Notes
- Branch: agent/cli-customer-mode
- `httpx` supports SSE via streaming responses (`httpx.stream`). No extra dependency needed.
- The background SSE listener thread needs clean shutdown on exit/Ctrl+C.
- PAUSED: origin/main has async SSE (`_sse_subscribers` + `asyncio.Queue`) from cs-worker-ui plan. This branch uses thread-safe `queue.Queue`. Waiting for async-backend refactoring to land before resuming merge.
- Remaining work: fix `test_sse_endpoint_exists` test (TestClient streaming blocks), update docs, merge conflicts.
