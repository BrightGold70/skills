# Orchestration mode (Orca)

Orchestration mode is an opt-in, Orca-only transport for H-MAD. It is active when a coordinator terminal resolves. The coordinator is **auto-detected**: Orca exports `ORCA_PANE_KEY="<tabId>:<leafId>"` into each pane, and the coordinator is this pane, whose `leafId` matches a terminal's `.leafId` in `orca terminal list`. So under Orca `hmad-dispatch env` reports `orchestration: on` with no manual setup. Pin it explicitly only to override the auto-detect (e.g. a coordinator in a different pane):

```bash
hmad-dispatch env                                   # auto-detected → orchestration: on
export HMAD_ORCA_COORDINATOR_TERMINAL=<handle>      # optional override; pin wins
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
- `gate-wait <gate_id> [--timeout <s>] [--interval <s>]` — blocks until the gate is resolved (by a human in the Orca UI or by `gate-resolve`) and echoes its resolution. Polls `orchestration gate-list`. This is the half `gate-create` lacked: without it a "blocking" gate could be opened but never waited on.
- `report-wait <report-path> [--timeout <s>] [--interval <s>]` — blocks until a dispatched agent drops `<report-path>` + a `<report-path>.done` marker, then emits the file. The reliable replacement for `wait`+`read`+`extract_report` (see "Report-file transport" above). Substrate-agnostic — no coordinator pin needed.
- `worktree-create <name> [--agent <id>] [--base <ref>] [--prompt-file <path>]` — creates an Orca worktree and returns its selector.
- `worktree-comment [<selector>] <text>` — sets a worktree's free-text comment (a durable, mobile-visible checkpoint), defaulting to the `active` worktree. Captures the response and fails non-zero on an `ok:false` envelope, so a swallowed error cannot read as success.
- `worktree-current` — returns the active worktree's JSON payload (read-only; used by the `handoff` READ reconcile).
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

## Report-file transport (preferred report/verdict channel under Orca)

Screen-scraping a live TUI is the least reliable way to collect an agent's report,
and it is the root of most of the audit-path fragility (a redrawing TUI fragments
the `BEGIN/END` sentinels, `tui-idle` is fooled by a spinner, the retained
scrollback can be shorter than the report, and indentation/bullets from the render
reach the gate). When the coordinator and agent share a filesystem — always true
under Orca, and true for cmux on one host — a **file drop** removes every one of
those failure modes: the agent writes its complete report to a file and the
coordinator reads the file, so there is no render race, no idle guess, and no
sentinel.

**Contract.** The dispatched prompt gives the agent an absolute report path `$RP`
and instructs it to, as its final action:

1. Write its full report (the same content it would otherwise print) to `$RP`.
2. Create the completion marker `$RP.done` (e.g. `: > "$RP.done"`).

The marker — not mere file existence — is the done signal, so a half-written
report is never read.

**Flow (coordinator).** Instead of `send` → `wait` → `read` → `extract_report`:

```bash
RP="/tmp/audit_<feature>_<phase>_cycle<N>.report.md"
rm -f "$RP" "$RP.done"
# stage the prompt with the report-file contract + $RP substituted, then:
hmad-dispatch send agy /tmp/audit_<feature>_<phase>_cycle<N>.txt
hmad-dispatch report-wait "$RP" --timeout 600 > docs/01-plan/features/<feature>.<phase>.audit.v<N>.md
# the file is clean markdown — gate it directly, no dedent/sentinel needed:
python3 ~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py docs/.../<feature>.<phase>.audit.v<N>.md
```

`report-wait` is substrate-agnostic (no coordinator pin required) and polls
`$RP.done`, so it also replaces the unreliable `wait --for tui-idle` step. If the
agent cannot write the file (older prompt, non-cooperating agent), `report-wait`
times out — fall back to the scrape path (`read` + `extract_report`), which stays
fully supported. **Scrape remains the fallback; report-file is the default under
Orca.**

## Phase 5 parallel fanout

The existing serial implementation path is the default. Partition an impl-plan so
only tasks declaring `Dependencies on other tasks: None` are independent; dependent
tasks remain serial in topological order on the shared tree.

Engage the Orca fanout only when all three conditions hold: `hmad-dispatch env`
shows `substrate=orca` (displayed as `substrate: orca`), `orchestration: on`, and
there are `≥2 independent` tasks. Any unmet condition uses the serial fallback.

For each independent task, keep at most `HMAD_ORCA_MAX_WORKTREES` live worktrees
(default 4): `worktree-create` with the staged prompt, Tier-2 `task-create` and
`dispatch --to <selector>`, `await` the worker, then run the **winner-merge gate**
(below), and `worktree-rm` the selector. Queue tasks beyond the cap with
`[H-MAD] worktree_queued module=<module>`.

### Progress checkpoints (best-effort)

At each of RED-verified, GREEN-verified, and audit-complete for a fanned module,
stamp the module's worktree so its live progress is visible in the Orca UI and
mobile app without reading its terminal:

```bash
hmad-dispatch worktree-comment <module-selector> "h-mad <feature> · <module> · <RED|GREEN|audit> · <n>/<total>"
```

This is non-blocking: a non-zero result emits `[H-MAD] worktree_comment_skipped
module=<module>` and never halts the fanout.

### Winner-merge decision gate

The merge that lands a module carries a decision record. The gate engages only
when `orchestration: on`; **when orchestration is off the merge is the plain
`git merge --no-ff` below with no gate** (the serial/unpinned fallback, unchanged).

With orchestration on, for each module:

1. **Non-clean verdict** (the module's 5e review returned `DRIFT`, or its tests
   are not green): do **not** attempt the merge. Open a **blocking** gate
   `gid=$(gate-create <task> "Merge <module>? verdict=<v>" '["yes","no"]')`, then
   block on the human's decision with `gate-wait "$gid"` (echoes the resolution),
   and act on it. Emit `[H-MAD] merge_gate blocked module=<module> reason=verdict`.
   Note: `gate-wait` is the half that makes a blocking gate actually block —
   `gate-create` only opens it; `await` waits for `worker_done`, not a gate.
2. **Clean verdict**: attempt `git merge --no-ff <module-branch>`.
   - **Clean merge** (zero exit AND `git ls-files --unmerged` empty): record the
     decision without pausing — `gate-create <task> "Auto-record clean merge of <module>" '["yes","no"]'`
     then `gate-resolve <gate> yes` — and emit `[H-MAD] merge_gate auto-resolved module=<module>`.
     The gate is an audit trail here, not a human stop.
   - **Conflict** (non-zero exit OR unmerged paths): `git merge --abort`, emit
     `[H-MAD] merge_conflict module=<module>`, open a **blocking**
     `gid=$(gate-create <task> "Merge conflict in <module> — resolve?" '["yes","no"]')`,
     and block on `gate-wait "$gid"`. On `yes` → re-dispatch the module serially
     after its siblings merge; on `no` → skip and log.

On any fanout halt, use `worktree-ps` to enumerate the fanout group and
`worktree-rm` every member. Cleanup is idempotent: removal of an already-gone
selector logs and no-ops.

### Reviewing diffs at the merge gate

When surfacing a module's diff for review (`hmad-dispatch file-open-changed
--mode diff` / `file-diff <path>`), the diff anchors to the worktree's recorded
start-from (base) ref rather than a `HEAD~n` guess, so the review shows exactly
the module's changes against its baseline. This stays best-effort and
non-blocking, exactly like the existing review-gate surfacing — a non-orca or
no-editor result is logged and the gate proceeds.

### Ship path (Orca)

After the winner merges to the feature branch, the recommended ship path under
Orca uses the Source Control panel's safe actions: **commit** (optionally
AI-drafted from the staged diff, pre-commit hooks run inline), **push** (sets
upstream on first push; a history rewrite surfaces *Force push with lease* as a
separate, explicit action that uses `--force-with-lease` and aborts on a stale
remote view), then **create the hosted-review PR/MR**. This preserves the base
invariant **never `git push --force`** — the wrapper adds no push/force-push
automation; force-push remains a deliberate, `--force-with-lease` UI action.
