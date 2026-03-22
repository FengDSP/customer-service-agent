# CLI

Command-line interface for interacting with the backend service. Supports two modes: customer mode (default) for simulating customers, and CS agent mode for reviewing AI-generated draft replies.

## Usage

```bash
# Customer mode (default) — send messages as a customer, receive replies via SSE
python -m cli --business beauty_lab --customer CUS-001

# CS agent mode — review/edit/approve AI-generated drafts
python -m cli --business beauty_lab --customer CUS-001 --cs-mode

# CS agent mode with auto-approve (skip draft review)
python -m cli --business beauty_lab --customer CUS-001 --cs-mode --auto-approve

# List available businesses
python -m cli --list-businesses
```

## Modes

### Customer Mode (default)

Simulates a customer sending messages. Messages are recorded via `POST /messages` without triggering the agent loop. A background SSE listener connects to `GET /conversations/{biz}/events` and displays replies from the CS agent in real time.

```
Connected to Beauty Lab Customer Service
Customer: CUS-001
Mode: customer

Type a message to start chatting. A CS agent will reply from the admin UI.
Type /help for commands.

You: When is my next appointment?
  (message sent, waiting for reply...)

Agent: Your next appointment is March 25 at 10:00 AM.
```

### CS Agent Mode (`--cs-mode`)

The original draft-review mode. Sends messages via `POST /chat`, which runs the agent loop and returns a draft reply for review.

```
--- Draft Reply ---
Your next appointment is March 25 at 10:00 AM.

[Confidence: high] [Review: not required]
Internal note: Looked up appointments for CUS-001.

[a]pprove  [e]dit  [r]eject >
```

- `a` — approve and print as final reply
- `e` — enter replacement text
- `r` — reject and return to message input

Use `--auto-approve` with `--cs-mode` to skip review and print replies directly.

## Flags

| Flag | Description |
|------|-------------|
| `--business <id>` | Business ID (required) |
| `--customer <id>` | Customer ID (required) |
| `--url <url>` | Backend URL (default: http://localhost:8000) |
| `--list-businesses` | List available businesses and exit |
| `--cs-mode` | CS agent mode: review/edit/approve AI-generated draft replies |
| `--auto-approve` | (CS mode only) Skip draft review, print replies directly |

## In-Session Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/info` | Show current session info (business, customer, mode) |
| `/history` | Show conversation history (paginated, recent first) |
| `quit` / `exit` | End session |

## Behavior

- `--business` and `--customer` are required. Use `--list-businesses` to discover available business IDs.
- The backend must be running before starting the CLI.
- Session history is maintained server-side per customer.
- In customer mode, the SSE listener reconnects automatically if the connection drops.
