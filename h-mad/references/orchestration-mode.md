# Orchestration mode (Orca)

Orchestration mode is an opt-in, Orca-only transport for H-MAD. It is active only when the coordinator pins its terminal handle:

```bash
export HMAD_ORCA_COORDINATOR_TERMINAL=<coordinator-handle>
hmad-dispatch env  # reports: orchestration: on
```

## Worker identity resolution

`dispatch` resolves an agent to a concrete terminal in two best-effort passes,
with the env pin always taking precedence:

1. `HMAD_ORCA_<AGENT>_TERMINAL` if set — authoritative.
2. Anchored, case-insensitive match on the terminal's **title** leading word.
3. Case-insensitive match on the terminal's **preview**, excluding the
   coordinator's own pane.

0 or 2+ candidates resolve to a loud `UNRESOLVED` rather than a guess.

**Pin `HMAD_ORCA_CODEX_TERMINAL` in practice.** Both auto-detect passes are
unreliable for Codex, and this is a property of Orca, not a bug to fix:

- `terminal list` reports a *derived* `.title` — the running program's name if
  it sets one, else the worktree name. `agy` self-titles, so it resolves. The
  Codex CLI does not, so its title is the worktree name (e.g. `HemaSuite`) and
  the title pass cannot match it.
- `terminal rename` does **not** help. It sets the *tab* title, and panes in a
  split share one `tabId` (only `leafId` differs), so it renames the whole tab
  and never changes the per-terminal `.title` that matching reads.
- `preview` is live scrollback. An agent's launch banner (`OpenAI Codex
  (v0.144.6)`) identifies the pane only until it scrolls away, usually within
  the first task. The preview pass is a courtesy for freshly-spawned panes, not
  a mechanism to rely on.

The coordinator is excluded from the preview pass on purpose: its own pane
renders the conversation, so a token like `codex` appears there whenever it is
merely discussed, and matching it would dispatch a task to itself.

Use these additive `hmad-dispatch` verbs:

- `task-create <label> <specfile>` — registers a task and returns its task ID. It requires the coordinator pin and prepends the worker callback handle to the task spec.
- `dispatch <agent> <task_id>` — sends a registered task to the resolved Orca agent terminal.
- `await <task_id> [--timeout <seconds>]` — waits for that task's `worker_done` callback on the coordinator terminal.
- `gate-create <task_id> <question> [<options-json>]` — creates a structured decision gate and returns its gate ID.
- `gate-resolve <gate_id> <resolution>` — resolves a gate with the selected decision.
- `worktree-create <name> [--agent <id>] [--base <ref>] [--prompt-file <path>]` — creates an Orca worktree and returns its selector.
- `worktree-ps [--limit <n>]` — returns the current Orca worktree JSON payload.
- `worktree-rm <selector> [--force]` — removes an Orca worktree.

The normal flow is:

```text
task-create → dispatch → worker_done → await → gate-create / gate-resolve
```

`task-create` records this line at the top of every registered task spec:

```text
[H-MAD] worker_done coordinator handle (use as --to): <coordinator-handle>
```

Workers dispatched through Orca must read that handle from their task spec and, after printing their normal STATUS or verdict, emit:

```bash
orca orchestration send --to <COORDINATOR_HANDLE> --type worker_done \
  --task-id <task-id> --report-path <report-file> \
  --files-modified <comma-separated-paths>
```

The sender must be the dispatched terminal handle. A worker without the `[H-MAD]` line skips `worker_done` and reports normally.

For cmux, or when `HMAD_ORCA_COORDINATOR_TERMINAL` is not set, use the universal scrape transport: `hmad-dispatch send`, `read`, and `wait`. Existing scrape transport behavior is unchanged.

## Phase 5 parallel fanout

The existing serial implementation path is the default. Partition an impl-plan so
only tasks declaring `Dependencies on other tasks: None` are independent; dependent
tasks remain serial in topological order on the shared tree.

Engage the Orca fanout only when all three conditions hold: `hmad-dispatch env`
shows `substrate=orca` (displayed as `substrate: orca`), `orchestration: on`, and
there are `≥2 independent` tasks. Any unmet condition uses the serial fallback.

For each independent task, keep at most `HMAD_ORCA_MAX_WORKTREES` live worktrees
(default 4): `worktree-create` with the staged prompt, Tier-2 `task-create` and
`dispatch --to <selector>`, `await` the worker, `git merge --no-ff` its branch, and
`worktree-rm` the selector. Queue tasks beyond the cap with
`[H-MAD] worktree_queued module=<module>`.

On a non-zero `git merge --no-ff` or any unmerged paths, run `git merge --abort`,
emit `[H-MAD] merge_conflict module=<module>`, and re-dispatch that module serially
after its siblings merge. On any fanout halt, use `worktree-ps` to enumerate the
fanout group and `worktree-rm` every member. Cleanup is idempotent: removal of an
already-gone selector logs and no-ops.
