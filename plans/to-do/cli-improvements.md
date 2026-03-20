# Plan: CLI Usability Improvements

## Goal
Make the CLI easier to use with discovery features, draft review mode, and better help. Currently the CLI requires you to know exact business and customer IDs, has no draft review, and no way to explore what's available.

## Context
- `src/cli.py` — current CLI (bare-bones: `--business`, `--customer`, `--url`)
- `src/agent/api.py` — backend already returns structured responses (`reply`, `internal_note`, `confidence`, `needs_human_review`, `suggested_actions`) but CLI ignores all fields except `reply`
- `src/agent/config.py` — loads configs from `configs/` dir
- `configs/` — YAML files (one per business)
- `plans/to-do/cli-draft-mode.md` — existing plan for draft review (to be merged into this plan)
- `docs/cli.md` — CLI docs

## Tasks

### 1. Add `--list-businesses` flag
- [ ] Add `--list-businesses` flag that lists all available business IDs from the backend
- [ ] Add `GET /businesses` endpoint to the backend that scans `configs/` and returns `[{"business_id": "...", "name": "..."}]`
- [ ] When `--list-businesses` is passed, print the list and exit
- [ ] Example:
  ```
  $ python -m cli --list-businesses
  Available businesses:
    acme_retail    — Acme Retail Support
    beauty_lab     — Beauty Lab Customer Service
  ```

### 2. Add `--list-customers` flag
- [ ] Add `--list-customers --business <id>` that lists customers from the business's customer CSV
- [ ] Add `GET /businesses/{business_id}/customers` endpoint that returns customer IDs and names
- [ ] Example:
  ```
  $ python -m cli --list-customers --business beauty_lab
  Customers (beauty_lab):
    CUS-001  Aurora White
    CUS-002  Wendy Lewis
    ...
  ```

### 3. Interactive business/customer selection when args are missing
- [ ] If `--business` is omitted, fetch the business list and prompt the user to pick one
- [ ] If `--customer` is omitted, prompt the user to enter a customer ID (or list available ones)
- [ ] This makes `python -m cli` work with zero args — it walks you through setup

### 4. Draft review mode (from cli-draft-mode plan)
- [ ] Add `--auto-approve` flag (default: `False`)
- [ ] When not auto-approve, show draft in a formatted block with metadata:
  ```
  --- Draft Reply ---
  Your next appointment is March 25 at 10:00 AM.

  [Confidence: high] [Review: not required]
  Internal note: Looked up appointments for CUS-001.

  [a]pprove  [e]dit  [r]eject >
  ```
- [ ] `a` — approve and print as final reply
- [ ] `e` — prompt for replacement text, print that as final reply
- [ ] `r` — reject draft, loop back to next message input
- [ ] In auto-approve mode, just print `reply` directly (current behavior)

### 5. In-session commands
- [ ] `/help` — show available commands
- [ ] `/businesses` — list businesses (same as --list-businesses)
- [ ] `/customers` — list customers for current business
- [ ] `/switch <business_id>` — switch to a different business mid-session
- [ ] `/info` — show current business, customer, and backend URL
- [ ] `/history` — show conversation history for current session

### 6. Better startup banner
- [ ] Show business name (not just ID) on connect
- [ ] Show customer name if available
- [ ] Show hint about `/help` for commands
- [ ] Example:
  ```
  Connected to Beauty Lab Customer Service
  Customer: CUS-001 (Aurora White)
  Type a message, or /help for commands.
  ```

### 7. Update docs
- [ ] Update `docs/cli.md` with all new flags and commands
- [ ] Update README quick start section

## Notes
- This plan supersedes `plans/to-do/cli-draft-mode.md` — all draft mode tasks are included here.
- Backend needs two new read-only endpoints (`GET /businesses`, `GET /businesses/{id}/customers`). These are small additions scoped to this plan.
- The `--auto-approve` flag default is OFF — human review is the default, matching the project's copilot philosophy.
- In-session commands use `/` prefix to distinguish from customer messages.
