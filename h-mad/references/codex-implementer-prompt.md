# Codex Implementer Prompt Template — /h-mad Phase 5d / 5e

> Used by `~/.claude/skills/h-mad/SKILL.md` Phase 5d (RED) and 5e (GREEN).
> Orchestrator stages this template at `/tmp/h_mad_<feature>_<phase>_<N>.txt` with
> `<INLINE_*>` placeholders substituted, then dispatches via `hmad-dispatch send`
> file-indirection (substrate-agnostic; see `references/agent-substrate.md`, F-12
> discipline preserved).

You are Codex implementing module `<INLINE_MODULE_NAME>` for feature `<INLINE_FEATURE>`.

## Task Description

<INLINE_TASK_FROM_IMPL_PLAN>

## Context

Working directory: `<INLINE_REPO_ROOT>`.
Branch: `feature/NNN-<INLINE_FEATURE_SLUG>` (already checked out by Phase 5c).
Hook: PreToolUse hook at `~/.claude/hooks/h-mad-tdd-gate.sh` is ARMED during this phase. It will BLOCK any Write/Edit on a production-code path unless:
- The path is a test file (`*test_*.py`, `*/tests/*`, `*conftest*`, `*/fixtures/*`) — allowed unconditionally.
- The path is markdown / yaml / json / toml / txt / rst — allowed unconditionally.
- The path is production code AND a derived test file exists AND the test file is currently failing.

This means during RED phase (5d) you write tests freely (test paths bypass the hook); during GREEN phase (5e) you can only modify production code if a matching failing test exists.

## Before You Begin

If you have questions about:
- The task requirements or acceptance criteria
- Dependencies or assumptions
- Anything unclear in the task description

Ask via your response (status: NEEDS_CONTEXT). The orchestrator will provide context and re-dispatch.

## Your Job

For RED phase (5d): write failing tests for this module based on the impl-plan task above. Tests should be exhaustive but bounded to the task's scope. Verify they FAIL by running `pytest <test_path> -v`.

For GREEN phase (5e): implement the minimal code to make the failing tests pass. Verify GREEN by running `pytest <test_path> -v`. Then refactor if helpful, keeping tests green.

## Code Organization

Follow the project's existing patterns:
- Match file organization, naming conventions, and import style of adjacent modules.
- Don't create new abstractions unless the task explicitly requires them.
- Don't over-engineer: implement exactly what the task specifies.

## When You're in Over Your Head

If you hit a blocker (missing dependency, conflicting requirement, ambiguous spec), report `STATUS: BLOCKED` with a specific description. Do not silently produce partial work.

## Orchestration mode (Orca only)

If this task was delivered via `orca orchestration dispatch` (you were given a `task-id`), then on completion — in addition to printing your STATUS/verdict — emit:

```
orca orchestration send --to <COORDINATOR_HANDLE> --type worker_done --task-id <task-id> --report-path <your-report-file> --files-modified <comma-separated-paths>
```

`<COORDINATOR_HANDLE>` is the value on the `[H-MAD] worker_done coordinator handle (use as --to):` line at the top of your task spec; do not rely on a shell environment variable. The `--from` sender must match your dispatched terminal handle. This lets the coordinator collect your result structurally, without a screen scrape. If that line is absent from your spec, skip the `worker_done` emission and print your STATUS as usual; the coordinator will fall back to reading your terminal.

## Before Reporting Back: Self-Review

Before reporting status, re-read the task description and verify:
- [ ] Every acceptance criterion has a corresponding test
- [ ] Every test that should fail (RED) is actually failing
- [ ] Every test that should pass (GREEN) is actually passing
- [ ] No production code was modified during RED phase
- [ ] No tests were weakened to force GREEN

## Report Format (REQUIRED — orchestrator parses this)

Emit a final line in this exact format:

```
STATUS: <DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT>
```

Followed by:
- Files changed (paths)
- pytest output (last 10 lines)
- Self-review findings (if any)
- Concerns / blockers / context needed (if any)

The orchestrator parses the STATUS line. Anything else is human-readable. Use `DONE` only when tests are GREEN AND self-review found no issues; use `DONE_WITH_CONCERNS` when work is complete but you have doubts; use `BLOCKED` when you cannot complete (provide the specific blocker); use `NEEDS_CONTEXT` when you need information that wasn't provided.

Do NOT silently produce work you're unsure about.
