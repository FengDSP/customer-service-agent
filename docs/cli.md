# CLI

Command-line interface for interacting with the backend service. Primary interface until the UI is built.

## Usage

```bash
# Start a conversation
python -m cli --business beauty_lab --customer CUS-001

# Auto-approve mode (skip draft review)
python -m cli --business beauty_lab --customer CUS-001 --auto-approve

# List available businesses
python -m cli --list-businesses
```

## Flags

| Flag | Description |
|------|-------------|
| `--business <id>` | Business ID (required) |
| `--customer <id>` | Customer ID (required) |
| `--url <url>` | Backend URL (default: http://localhost:8000) |
| `--list-businesses` | List available businesses and exit |
| `--auto-approve` | Skip draft review, print replies directly |
| `--as-customer` | Send messages as a customer (no agent reply) |

## Draft Review Mode

By default, the CLI shows each draft reply with metadata and prompts for approval:

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

Use `--auto-approve` to skip this and print replies directly.

## In-Session Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/info` | Show current session info |
| `quit` / `exit` | End session |

## Customer Mode

Use `--as-customer` to simulate a customer sending messages. Messages are recorded via `POST /messages` without triggering the agent loop. The CS worker web UI will show these as unreplied messages.

```bash
python -m cli --business beauty_lab --customer CUS-001 --as-customer
```

## Behavior

- `--business` and `--customer` are required. Use `--list-businesses` to discover available business IDs.
- The backend must be running before starting the CLI.
- Session history is maintained server-side per customer.
