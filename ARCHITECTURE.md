# Architecture

A customer service copilot that drafts reply messages by autonomously retrieving company data. Human agents approve or modify drafts before sending.

## Setup

The Python backend requires a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Components

### Backend Service (FastAPI, Python)
Handles incoming customer messages, runs an agent loop (LLM + tool calls) to pull relevant data, and returns draft replies.

- Agent loop calls LLM APIs with business-specific config (system prompt, instructions, available data sources).
- Data access is encapsulated as LLM tool calls. Starting with read-only local CSV files.
- Business configs live in `configs/` as YAML files (one per business).
- LLM call logs are saved to a local folder for debugging. See `docs/llm-logging.md`.
- Admin API endpoints for log browsing and LLM replay. See `docs/admin-ui.md`.
- Local runnable for development. Cloud hosting required for production use.

Details: `docs/backend.md`

### CLI
The primary interface until the UI is built. Sends customer messages to the backend and displays draft replies. Supports multi-turn conversations with session tracking and human-in-the-loop draft review.

Details: `docs/cli.md`

### Admin UI (Next.js)
Web-based portal for browsing LLM call logs and replaying individual LLM calls with edited prompts. Pure presentation layer that fetches all data from the FastAPI backend.

Details: `docs/admin-ui.md`

### CS Worker UI (Next.js)
Human-in-the-loop interface where CS agents see incoming customer messages, review AI-generated draft replies, and approve/edit/send them. Shares the Next.js app with Admin UI. Receives real-time updates via SSE when new customer messages arrive.

Details: `docs/admin-ui.md`

## Planned (not yet built)

- **Chat app integration** — Hook into real chat platforms (e.g., WhatsApp, Slack) as a CS account, generating drafts for each incoming message.
- **Database / MCP data sources** — Extend beyond CSV to support databases and MCPs as tool-call backends.
