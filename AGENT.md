# Agent Operating Guide

This file defines how autonomous agents work in this repo. For what the repo does, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Repo Structure

```
ARCHITECTURE.md          # Must-know knowledge, links to component docs
AGENT.md                 # This file — how agents operate
docs/                    # Component documentation (one md per component)
plans/
  to-do/                 # Unclaimed plans (available work)
  in-progress/           # Plans currently being worked on
  finished/              # Completed plans
```

## Plans

Each agent session works on exactly one plan. A plan is a markdown file that describes a self-contained unit of work.

### Plan Format

```markdown
# Plan: <title>

## Goal
What this plan accomplishes.

## Context
Links to relevant docs/ files and ARCHITECTURE.md sections.

## Tasks
- [ ] Task 1
- [ ] Task 2
- ...
- [ ] Verifiable e2e test

## Notes
Decisions made, blockers hit, approach changes during execution.
```

### Plan Requirements

Every plan **must** include at least one verifiable end-to-end test in its task list. This test should exercise the full flow of the feature — from API call (or CLI command) through to observable output — so that the plan's completion can be verified automatically. Unit tests alone are not sufficient. If a CI test workflow exists (e.g., `.github/workflows/test.yml`), the e2e test must be added to it so it runs automatically.

### Plan Lifecycle

1. Pick a plan from `plans/to-do/`.
2. Move it to `plans/in-progress/` and note the branch name in the file. **Commit this move, push, create a PR, and merge it to `main` immediately — before doing any actual work on the plan.** This signals to other agents that the plan is taken.
3. Work through the tasks. Update checkboxes and the Notes section as you go.
4. When done, move the plan to `plans/finished/`. **Commit this move, push, create a PR, and merge it to `main` immediately** so other agents see the plan is complete.

If a plan is in `plans/in-progress/`, it is taken — pick a different one.

## Branching and Worktrees

Each agent works in its own git worktree on a feature branch. Never push directly to `main`.

- Branch naming: `agent/<plan-name>` (e.g., `agent/csv-tool-calls`)
- Branch from `main` at the latest commit.
- Do not work on `main` directly.
- Each worktree is isolated — agents do not coordinate in real time.
- Push your feature branch to the remote as its own branch (e.g., `git push origin HEAD -u`). Never push to `origin/main` directly.

## Commits and PRs

Agents commit to their feature branch and merge to `main` via PRs.

- Make small, focused commits with clear messages.
- Commit format: `<type>: <description>` (e.g., `feat: add order lookup tool`, `fix: handle missing CSV column`, `test: add agent loop unit tests`).
- Merge early and often. If a change is atomic and self-contained (e.g., a `.gitignore` update, a new config file, a standalone utility), open a PR and merge it immediately. Do not batch unrelated changes.

### PR workflow

Every git commit must be immediately followed by a push, then a PR creation, then a PR merge. Do not batch these steps or delay any of them.

1. Push your feature branch to the remote: `git push origin HEAD -u`
2. Create a PR with `gh pr create` targeting `main`. PR description should summarize what was done and link to the plan file (e.g., `plans/in-progress/my-plan.md`).
3. Merge immediately with `gh pr merge <number> --merge`. Do not wait for human review. If CI is set up, wait for it to pass first.
4. Do not wait until the entire plan is complete — open and merge PRs at meaningful checkpoints.

The human reviews code asynchronously after merge. If issues are found, they will be addressed in a follow-up plan.

## Prerequisites

- **Python 3.11+** with pip — `pip install -e ".[dev]"` from repo root
- **Node.js 20+** — `brew install node` (Homebrew). Required for frontend work (`src/frontend/web/`).
- After cloning or switching worktrees, run `cd src/frontend/web && npm install` before any frontend work.

## Code Practices

- Read existing code before modifying it. Understand context first.
- Run tests before committing. If tests don't exist yet for the area you're touching, write them.
- Do not modify files outside the scope of your plan without good reason. If you need to, note it in the plan.
- Keep changes minimal. Solve the task, not adjacent problems.
- Do not add dead code, speculative features, or TODOs for future agents. If something needs doing, write a plan for it.

### Bug Fix Workflow (Test First)

When fixing a bug, always follow this order:

1. **Write or fix the test first.** Add a test that reproduces the bug, or fix an existing test so it actually fails for the right reason. Run CI to confirm the test fails.
2. **Then fix the code.** Only after you have a reliably failing test, fix the actual bug in the source code.
3. **Run CI again** to confirm the test now passes.

Never fix the code before you have a test that covers the bug. If an existing test passes despite the bug, the test is wrong — fix the test first.

## Documentation

- `ARCHITECTURE.md` contains only must-know information and links to `docs/` files. Keep it concise.
- Each component gets its own file in `docs/` (e.g., `docs/agent-loop.md`, `docs/csv-tools.md`).
- When you build a new component, create its doc. When you modify a component, update its doc.
- Do not duplicate information between ARCHITECTURE.md and docs/ files. ARCHITECTURE.md links; docs/ explains.

## LLM Logging

All LLM API calls made by the backend service (not by the agent harness) are logged for debugging. See `docs/llm-logging.md` once it exists for the format and location.

## Session Start

Complete all of the following **before** responding to the first human message:

1. The `SessionStart` hook automatically fetches and merges the latest `main` into your branch.
2. Create a feature branch from `main` if not already on one: `git checkout -b agent/<plan-name>` (see [Branching and Worktrees](#branching-and-worktrees) for naming conventions). Never work directly on `main`.
3. Run: `/loop 10m git fetch origin main && git merge origin/main --no-edit` — this keeps your branch up to date throughout the session and reduces merge conflicts.

If a merge fails due to conflicts, resolve them immediately — if a conflict is non-trivial, note it in your plan and ask the human.

## Conflict Resolution

Since agents work in parallel on separate branches, merge conflicts can happen.

- Keep your changes scoped to your plan to minimize conflicts.
- If two plans touch the same files, the earlier merge wins. The later agent resolves conflicts on their branch.

## Cross-Agent Plan Changes

If your work requires changes to another agent's plan (e.g., you discovered a dependency, a conflicting approach, or missing prerequisite work):

- Do not edit their in-progress plan directly.
- Ask the human to copy-paste your message to the other agent's session.
- If the change is blocking your work, document the blocker in your own plan's Notes section and move on to other tasks or stop.

If the other plan is in `to-do/` (unclaimed), you may edit it directly since no agent is working on it.

## Available Agents

Specialized agents live in `.claude/agents/`. Each coding agent session should ask the human developer to kick off the relevant agent if there is a need.

| Agent | File | Purpose |
|-------|------|---------|
| **Janitor** | `.claude/agents/janitor.md` | Fixes failing CI (test failures, lint errors). Run after merging code to clean up any issues. |

### When to request an agent

- After merging a PR, if CI fails → ask the human to kick off the **janitor** agent.
- If you notice lint warnings while working but they're outside your plan scope → note it and ask for the janitor.
- Do not do janitor work yourself unless the human explicitly asks you to.

## What Not to Do

- Do not modify another agent's in-progress plan or branch.
- Do not commit directly to `main` — always go through a branch and PR.
- Do not refactor code unrelated to your plan.
- Do not add dependencies without justification in the plan notes.
- Do not leave the plan in `in-progress/` if you're done — move it to `finished/`.
