# Architecture

A customer service copilot that drafts reply messages by autonomously retrieving company data. Human agents approve or modify drafts before sending.

## Components

### Backend Service (FastAPI, Python)
Handles incoming customer messages, runs an agent loop (LLM + tool calls) to pull relevant data, and returns draft replies.

- Agent loop calls LLM APIs with business-specific config (system prompt, instructions, available data sources).
- Data access is encapsulated as LLM tool calls. Starting with read-only local CSV files.
- Business configs live in `configs/` as YAML files (one per business).
- LLM call logs are saved to a local folder for debugging. See `docs/llm-logging.md`.
- Local runnable for development. Cloud hosting required for production use.

Details: `docs/backend.md`

### CLI
The primary interface until the UI is built. Sends customer messages to the backend and displays draft replies. Supports multi-turn conversations with session tracking. Does not include human-in-the-loop approval — replies are returned directly.

Details: `docs/cli.md`

## Planned (not yet built)

- **Frontend UI** — Human-in-the-loop interface where CS agents approve/modify drafts before sending. Will be built after CLI is functional.
- **Chat app integration** — Hook into real chat platforms (e.g., WhatsApp, Slack) as a CS account, generating drafts for each incoming message.
- **Database / MCP data sources** — Extend beyond CSV to support databases and MCPs as tool-call backends.
- **Eval portal** — Browse and replay LLM call logs for debugging and evaluation.
