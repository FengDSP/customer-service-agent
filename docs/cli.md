# CLI

Command-line interface for interacting with the backend service. Primary interface until the UI is built.

## Usage

```bash
# Interactive mode (walks you through business/customer selection)
python -m cli

# Specify business and customer directly
python -m cli --business beauty_lab --customer CUS-001

# Auto-approve mode (skip draft review)
python -m cli --business beauty_lab --customer CUS-001 --auto-approve

# List available businesses
python -m cli --list-businesses

# List customers for a business
python -m cli --list-customers --business beauty_lab
```

## Flags

| Flag | Description |
|------|-------------|
| `--business <id>` | Business ID (interactive selection if omitted) |
| `--customer <id>` | Customer ID (prompted if omitted) |
| `--url <url>` | Backend URL (default: http://localhost:8000) |
| `--list-businesses` | List available businesses and exit |
| `--list-customers` | List customers for `--business` and exit |
| `--auto-approve` | Skip draft review, print replies directly |

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
| `/businesses` | List available businesses |
| `/customers` | List customers for current business |
| `/switch <id>` | Switch to a different business |
| `/info` | Show current session info |
| `/history` | Show conversation history note |
| `quit` / `exit` | End session |

## Behavior

- If `--business` or `--customer` are omitted, the CLI interactively walks you through selection.
- The backend must be running before starting the CLI.
- Session history is maintained server-side per customer.
