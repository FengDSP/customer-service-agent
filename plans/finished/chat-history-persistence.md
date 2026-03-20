# Plan: Persist Chat Histories

## Goal
Save conversation histories to disk so they survive server restarts. When a customer sends a new message, their previous conversation is loaded automatically.

## Context
- [docs/backend.md](../../docs/backend.md) — session storage is currently in-memory
- `src/agent/session.py` — current in-memory session store

## Tasks
- [x] Store chat histories as JSONL files in `data/sessions/{business_id}/{customer_id}.jsonl`
- [x] On session load, read existing history from disk
- [x] On each new message/reply, append to the file
- [x] Update session.py to accept business_id for scoped storage
- [x] Update tests
- [x] Update docs/backend.md

## Notes
- Branch: `worktree-backend`
- Format: one JSON line per message (role + content), so history can be incrementally appended
- business_id scoping keeps each business's customer data separate
