# Plan: CLI Draft Message Mode

## Goal
Add human-in-the-loop draft review to the CLI. When the backend returns a draft reply, the CLI shows it to the human agent for approval, editing, or rejection before it's considered "sent" to the customer. A `--auto-approve` flag bypasses review (default: off).

## Context
- `src/cli.py` — current CLI sends messages and prints replies directly (no review step)
- `plans/to-do/structured-prompt.md` — another session is upgrading the backend to return structured JSON responses (`draft_reply`, `internal_note`, `confidence`, `needs_human_review`, `suggested_actions`). This plan must work with both the current simple response (`reply` field) and the new structured response.
- `docs/cli.md` — CLI docs
- `docs/backend.md` — backend API spec

## Design

### CLI flow (draft mode, default)

```
You: When is my next appointment?

--- Draft Reply ---
Your next appointment is March 25 at 10:00 AM with Lily Chen for RF Anti-aging treatment.

[Confidence: high] [Review: not required]
Internal note: Looked up CUS-001 appointments, found confirmed APT-1009 on 2026-03-24.
Suggested actions: none

[a]pprove  [e]dit  [r]eject  [q]uit > a

Agent: Your next appointment is March 25 at 10:00 AM with Lily Chen for RF Anti-aging treatment.
```

### CLI flow (auto-approve mode)

```bash
python -m cli --business beauty_lab --customer CUS-001 --auto-approve
```

Behaves like the current CLI — prints the reply directly without review. This preserves backward compatibility and is useful for testing.

### Handling both response formats

The CLI should handle two response shapes:
1. **Current format:** `{"customer_id": "...", "reply": "..."}`
2. **New structured format:** `{"customer_id": "...", "reply": "...", "internal_note": "...", "confidence": "...", "needs_human_review": true, "suggested_actions": [...]}`

If extra fields are present, show them in draft mode. If not, just show the reply for review.

### Draft review actions

- **Approve (`a`)** — accept the draft as-is. Print it as the final agent reply. Call `POST /chat/approve` (if/when the backend adds it) or just display it.
- **Edit (`e`)** — open the draft for inline editing. The human types a replacement message. That becomes the final reply.
- **Reject (`r`)** — discard the draft. Optionally prompt for a reason. The customer sees nothing. Loop back to wait for the next human input.
- **Quit (`q`)** — exit the CLI.

### Backend integration

For now, the CLI is display-only — "approving" or "editing" just controls what gets printed as the final response. The backend doesn't yet have an approve/reject endpoint.

When the backend adds `POST /chat/approve` (future work), the CLI should call it to confirm which reply was actually sent. This plan adds a TODO comment for that integration point.

## Tasks

### Update CLI arguments
- [ ] Add `--auto-approve` flag (default: `False`)
- [ ] Update argparse help text

### Implement draft review flow
- [ ] After receiving a response, if not `--auto-approve`, show the draft in a formatted box
- [ ] Display extra fields if present (`internal_note`, `confidence`, `needs_human_review`, `suggested_actions`)
- [ ] Prompt for action: approve / edit / reject
- [ ] On approve: print as final agent reply
- [ ] On edit: prompt human for replacement text, print that as final reply
- [ ] On reject: print "Draft rejected" and loop back to next customer message input

### Handle both response formats
- [ ] Detect whether response has structured fields or just `reply`
- [ ] In auto-approve mode, always just print `reply` (same as current behavior)

### Update docs
- [ ] Update `docs/cli.md` with draft mode usage and flag documentation

### Update tests
- [ ] Add test for CLI argument parsing (auto-approve flag)

## Notes
- The `--auto-approve` flag is default OFF — draft review is the default behavior. This aligns with the project's goal of human-in-the-loop approval.
- This plan is CLI-only. The backend structured prompt changes are handled by `plans/to-do/structured-prompt.md`.
- No backend changes needed for this plan — the CLI works with whatever the backend returns today.
- Future work: when the backend adds an approve endpoint, the CLI should call it after the human approves/edits.
