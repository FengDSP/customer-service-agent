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

## Notes
Decisions made, blockers hit, approach changes during execution.
```

### Plan Lifecycle

1. Pick a plan from `plans/to-do/`.
2. Move it to `plans/in-progress/` and note the branch name in the file.
3. Work through the tasks. Update checkboxes and the Notes section as you go.
4. When done, move the plan to `plans/finished/`.

If a plan is in `plans/in-progress/`, it is taken — pick a different one.

## Branching and Worktrees

Each agent works in its own git worktree on a feature branch.

- Branch naming: `agent/<plan-name>` (e.g., `agent/csv-tool-calls`)
- Branch from `main` at the latest commit.
- Do not work on `main` directly.
- Each worktree is isolated — agents do not coordinate in real time.

## Commits and PRs

Agents commit directly and push without waiting for human review.

- Make small, focused commits with clear messages.
- Commit format: `<type>: <description>` (e.g., `feat: add order lookup tool`, `fix: handle missing CSV column`, `test: add agent loop unit tests`).
- Push the branch and open a PR when the plan is complete (or at meaningful checkpoints for large plans).
- PR description should summarize what was done and link to the plan file.
- Merge your own PR into `main` once CI passes (or immediately if no CI is set up yet). Do not wait for human review.
- The human reviews code asynchronously after merge. If issues are found, they will be addressed in a follow-up plan.

## Code Practices

- Read existing code before modifying it. Understand context first.
- Run tests before committing. If tests don't exist yet for the area you're touching, write them.
- Do not modify files outside the scope of your plan without good reason. If you need to, note it in the plan.
- Keep changes minimal. Solve the task, not adjacent problems.
- Do not add dead code, speculative features, or TODOs for future agents. If something needs doing, write a plan for it.

## Documentation

- `ARCHITECTURE.md` contains only must-know information and links to `docs/` files. Keep it concise.
- Each component gets its own file in `docs/` (e.g., `docs/agent-loop.md`, `docs/csv-tools.md`).
- When you build a new component, create its doc. When you modify a component, update its doc.
- Do not duplicate information between ARCHITECTURE.md and docs/ files. ARCHITECTURE.md links; docs/ explains.

## LLM Logging

All LLM API calls made by the backend service (not by the agent harness) are logged for debugging. See `docs/llm-logging.md` once it exists for the format and location.

## Conflict Resolution

Since agents work in parallel on separate branches, merge conflicts can happen.

- Keep your changes scoped to your plan to minimize conflicts.
- Merge latest `main` into your branch every 10 minutes during an active session. Resolve conflicts immediately — if a conflict is non-trivial, note it in your plan and ask the human.
- If two plans touch the same files, the earlier merge wins. The later agent resolves conflicts on their branch.

## Cross-Agent Plan Changes

If your work requires changes to another agent's plan (e.g., you discovered a dependency, a conflicting approach, or missing prerequisite work):

- Do not edit their in-progress plan directly.
- Create a note file at `plans/in-progress/<their-plan-name>.note.md` describing what you need changed and why.
- If the change is blocking your work, document the blocker in your own plan's Notes section and move on to other tasks or stop.
- The human will coordinate between agents during async review.

If the other plan is in `to-do/` (unclaimed), you may edit it directly since no agent is working on it.

## What Not to Do

- Do not modify another agent's in-progress plan or branch.
- Do not commit directly to `main` — always go through a branch and PR.
- Do not refactor code unrelated to your plan.
- Do not add dependencies without justification in the plan notes.
- Do not leave the plan in `in-progress/` if you're done — move it to `finished/`.
