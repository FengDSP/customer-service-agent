# Plan: Async Backend Migration

## Goal
Convert all FastAPI endpoints and internal functions (session, agent loop, config loading) to async. This eliminates sync/async mixing issues (e.g., thread-safe queue workarounds for SSE) and prepares the backend for streaming LLM responses and WebSocket support.

## Context
- [docs/backend.md](../../docs/backend.md) — backend architecture
- `src/agent/api.py` — FastAPI endpoints (currently a mix of sync `def` and async `async def`)
- `src/agent/loop.py` — agent loop (sync, calls Anthropic SDK)
- `src/agent/session.py` — session management (sync file I/O)
- `src/agent/config.py` — config loading (sync file I/O)

## Why
- FastAPI runs sync endpoints in a threadpool, async endpoints in the event loop. Mixing them makes shared state (like SSE pub/sub queues) require thread-safe primitives instead of simple asyncio ones.
- The Anthropic Python SDK supports async (`AsyncAnthropic`). Using it enables non-blocking LLM calls and future streaming.
- Async file I/O (via `aiofiles` or similar) would prevent blocking the event loop during session reads/writes.

## Tasks
- [ ] Convert all endpoint functions in `api.py` to `async def`
- [ ] Switch SSE pub/sub from `queue.Queue` to `asyncio.Queue`
- [ ] Convert `run_agent_loop` to async using `AsyncAnthropic`
- [ ] Convert session I/O (`get_or_create_session`, `append_message`) to async
- [ ] Convert config loading to async (or cache eagerly at startup)
- [ ] Update all tests to work with async endpoints (pytest-asyncio or TestClient handles this)
- [ ] E2e test: verify SSE flow works end-to-end with pure async stack

## Notes
