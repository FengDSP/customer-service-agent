# Plan: CLI

## Goal
Build the command-line interface for interacting with the backend service, enabling interactive multi-turn conversations.

## Context
- [docs/cli.md](../../docs/cli.md) — CLI spec
- [docs/backend.md](../../docs/backend.md) — Backend API spec (POST /chat)

## Tasks
- [x] Implement `cli.py` with interactive prompt loop
- [x] Accept `--business` argument for business ID
- [x] Send messages to POST /chat, display draft replies
- [x] Maintain session ID across the conversation
- [x] Handle `quit`/`exit` to end session
- [x] Handle connection errors gracefully (backend not running)
- [x] Test manually against the backend

## Notes
- Branch: `worktree-backend`
