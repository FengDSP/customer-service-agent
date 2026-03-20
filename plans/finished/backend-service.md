# Plan: Backend Service

## Goal
Build the FastAPI backend service that receives customer messages, runs an agent loop (LLM + tool calls), and returns draft replies.

## Context
- [ARCHITECTURE.md](../../ARCHITECTURE.md) — overall system design
- [docs/backend.md](../../docs/backend.md) — API spec, agent loop, session storage
- [docs/business-config.md](../../docs/business-config.md) — YAML config format
- [docs/llm-logging.md](../../docs/llm-logging.md) — LLM call logging format

## Tasks

### Project setup
- [x] Create `pyproject.toml` with dependencies (fastapi, uvicorn, pydantic, anthropic SDK, pyyaml, pandas)
- [x] Add `.env.example` for API keys and config (e.g., `ANTHROPIC_API_KEY`, `LLM_MODEL`)

### Business config loader
- [x] Implement config loader that reads YAML from `configs/<business_id>.yaml`
- [x] Define Pydantic models for business config (business_id, name, system_prompt, data_sources)
- [x] Create a sample config (`configs/acme_retail.yaml`) with sample data files in `data/acme/`
- [x] Create sample CSV data files (orders.csv, products.csv) with realistic test data

### CSV lookup tool
- [x] Implement CSV tool that reads a CSV file and returns matching rows
- [x] Tool accepts a data source name and a natural-language query description; uses simple filtering (column value matching or keyword search)
- [x] Generate LLM tool definitions from business config data_sources entries

### Agent loop
- [x] Implement the agent loop: build prompt from config + history + message, call LLM, handle tool calls in a loop until final text reply
- [x] Use the Anthropic Python SDK (claude-sonnet-4-6 as default model)
- [x] Wire tool execution into the loop — dispatch tool calls to CSV lookup (or future tools) and feed results back

### Session storage
- [x] Implement in-memory session store (dict of session_id -> conversation history)
- [x] Auto-generate session_id if not provided

### LLM logging
- [x] Log each agent loop invocation to `logs/llm/{session_id}_{timestamp}.json`
- [x] Capture full conversation (all turns, tool calls, tool results), model name, and token usage

### API endpoint
- [x] Implement `POST /chat` endpoint matching the spec in docs/backend.md
- [x] Load business config, retrieve/create session, run agent loop, return draft reply
- [x] Add basic error handling (invalid business_id, missing fields)

### Testing
- [x] Write unit tests for config loader
- [x] Write unit tests for CSV lookup tool
- [x] Write integration test for the `/chat` endpoint (mock LLM calls)
- [x] Manual smoke test: start server, send messages via curl, verify multi-turn conversation works

## Notes
- Branch: `worktree-backend`
- Smoke test: server starts, accepts requests, routes to correct config. Full LLM round-trip requires ANTHROPIC_API_KEY in .env.
