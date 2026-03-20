# Plan: End-to-End Test Script

## Goal
Create a test script that starts the backend, sends messages via the CLI, and verifies that draft replies are returned — proving the full pipeline works: API endpoint, agent loop, LLM calls, tool calls (CSV lookup), and session tracking.

## Context
- [docs/cli.md](../../docs/cli.md) — CLI usage and behavior
- [docs/backend.md](../../docs/backend.md) — POST /chat API spec
- [docs/llm-logging.md](../../docs/llm-logging.md) — LLM log format (can verify logs were written)

## Tasks

### Test script
- [x] Create `test_e2e.sh` that starts the backend server, waits for it to be ready, runs test scenarios, and shuts down
- [x] Test scenario 1: send a greeting message, verify a reply is returned
- [x] Test scenario 2: send an order lookup message (e.g., "What is the status of order ORD-1002?"), verify the reply contains order data from the CSV — proving tool calls worked
- [x] Test scenario 3: send a follow-up message in the same session, verify session continuity (multi-turn)
- [x] Verify LLM log files were created in `logs/llm/`
- [x] Print pass/fail summary with clear output

### Prerequisites
- [x] Script should check that `ANTHROPIC_API_KEY` is set before running
- [x] Script should handle cleanup (kill server) even on failure

## Notes
- Requires a valid `ANTHROPIC_API_KEY` — this is a real LLM integration test, not mocked.
- Uses curl against POST /chat directly (not the interactive CLI prompt) since the CLI's interactive loop is hard to script.
