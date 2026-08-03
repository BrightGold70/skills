# Handoff — Agent-pane identity, and three await/dispatch correctness bugs

**Date:** 2026-08-03
**Branch:** main
**Project:** /Users/kimhawk/orca/skills (symlinked as `~/.claude/skills/h-mad` and `~/.claude/skills/handoff`)

## Session Summary

Resumed from `2026-08-03-main__orchestration-fixes-skill-reviewer.md`, cleared its entire five-item
backlog, then kept going into the bugs that clearing it exposed. Five PRs shipped and merged
(#34–#38), suite 1049 → 1072, backlog now empty. The orchestration flow is live-verified end to end
for the first time, and three genuine correctness defects were found and fixed along the way — one
of them a **false completion** (`await` accepting a report the runtime had refused). `main` @
`1052c33`, clean, in sync, 1072 + 48 green. Nothing is blocked.

## Key Learnings

- **Orca does not register hand-started agent panes.** `worktree ps` reported `liveTerminalCount: 3`
  with ONE `agents[]` entry — the coordinator — while a codex and an agy pane, both up 9h in the
  worktree, were absent. This closes the open question in
  `docs/orca-feature-request-terminal-identity.md`, which had explicitly parked it. All three
  identity passes go blind together for that pane class: paneKey join (absent from `agents[]`),
  title (tab renamed → both panes read the *tab's* title), preview (`terminal read` returns
  `returnedLineCount: 0` after an Orca restart kills the renderer buffer).
- **`ps -e` returns a PARTIAL process list in this environment.** `ps -eo pid | wc -l` gave 1374 on
  one call and 31 on the next; `ps -p 88221` finds codex, `ps -ax | grep codex` does not. My
  "visibility is fine, 1374 processes" sanity check was itself a partial enumeration — it produced
  false confidence in a wrong conclusion. `lsof -a -d cwd -c <agent>` is reliable; `ps -e` is not.
- **jq's `//` treats `false` as null-ish.** `.result.injected // "absent"` returns `"absent"` for
  exactly the value being hunted, so the first `injected=false` guard silently never fired. Use
  `has()` when the value you care about can legitimately be `false`.
- **Acking an Orca delivery destroys every message in it.** One delivery carries *all* pending
  messages for a Run, so a fanout's first `await` acks siblings' completed reports away. Reproduced:
  module A reported, an unrelated `await` acked, `await task_A` then timed out for finished work.
- **A rejected `worker_done` is still delivered to the mailbox.** Orca lifecycle-validates and can
  reject (`missing_dispatch_id`, `sender_not_assignee`) while `check` still returns the message —
  so a taskId-only match accepts a report the runtime refused. That is a false completion.
- **The worker callback requires `--dispatch-id`, and our doc omitted it.** Real Orca-dispatched
  workers were unaffected because Orca's own injected preamble states the full contract — workers
  follow *it*, not our doc, which is exactly how the omission survived unnoticed.
- **`stage: "input_accepted"` is not proof the agent will act.** A `worker-start` returning
  `state:"ready"` delivered its prompt into a codex pane still showing `Starting MCP servers (0/3)`;
  the TUI redrew over it and the module never ran. Completion must come from `worker_done` /
  report-file, never the launch response.
- **A test that passes before the fix exists pins nothing.** One new test passed against unmodified
  code because the stub replayed batches forever, so the second `await` re-matched from the queue.
  The stub now models the real drain (`--ack` → later checks empty), opt-in via
  `HMAD_STUB_ORCA_ACK_STATE`.
- **A REFUSED mutation measures nothing and looks exactly like an enforced guard.** Three runs came
  back REFUSED (anchor matched 0 times, twice because my own edits had moved the anchor) before a
  real ALL_CAUGHT. Read the token, never assume.

## Next Steps

1. **File the two upstream Orca bugs** — both have clean reproductions and neither is fixable here.
   (a) `worker-abandon --dispatch <ctx>` returns `dispatch_not_found` for an id `dispatch-show`
   still returns (repro: dispatch without `--inject`, then `task-update --status ready`, which
   clears the task row but orphans the terminal binding). (b) `terminal read` returns
   `returnedLineCount: 0` for a live pane that survived an Orca restart. Precedent + house style:
   `docs/orca-feature-request-terminal-identity.md`.
2. **Live e2e the report-file transport** — `hmad-dispatch report-wait` is the documented default
   under Orca and was exercised only incidentally this session (the workers wrote `$RP` + `.done`,
   but `report-wait` itself was never the thing under test — one invocation was swallowed by a
   `timeout` binary that does not exist on macOS). See `references/orchestration-mode.md`
   §"Report-file transport".
3. **Decide whether `_cmd_dispatch` should pre-flight pane readiness** — `dispatch --inject`
   hard-refuses with `no recognized agent detected` when the pane has no agent, which is a real
   guard we do not currently surface any earlier than the dispatch itself.

## Open / Blocked Items

- **Two upstream Orca defects** — status: not filed, not blocked. See Next Step 1. Ours-side
  behaviour is already defensive around both.
- **Nothing parked outside this repo.** No foreign-worktree items, so no HANDOVER was needed. The
  HemaSuite `feature/196` lane remains its own (`worktree ps` shows it at `Tasks 1-4 GREEN, Task 5
  unstarted`); do not adopt it from here.

## Context for Next Session

**Files touched this session (all merged to `main`):**
- `h-mad/scripts/hmad-dispatch.sh` — `_orca_find` Pass 3 (OS evidence) + `_agent_procs_in` /
  `_orca_unclaimed_panes`; `env` unresolved→FAIL + stderr replay; `_cmd_dispatch` injected guard;
  `_cmd_await` report cache, rejection filter, rejection reporting
- `h-mad/references/orchestration-mode.md` — §"Worker identity resolution" rewritten (5 passes);
  worker callback contract; fanout `worker-start` decision; delivery-batching + ack semantics
- `h-mad/references/agent-substrate.md` — `HMAD_AWAIT_CACHE_DIR`, verdict grammar
- `h-mad/invariants.base.md` — **new** §"Wrapper–runtime reconciliation"
- `h-mad/SKILL.md` — PREFLIGHT verdict grammar + scoping rule
- `h-mad/tests/stubs/lsof` (**new**), `h-mad/tests/stubs/orca` (ack-drain modelling)
- `h-mad/tests/test_hmad_dispatch.py`, `test_h_mad_invariants_layering.py`,
  `test_h_mad_assemble_audit.py` (size-band fixture recalibrated 3200/3500 → 3136/3436)
- `docs/skill-candidates.md` — backlog drained to zero open candidates
- `docs/orca-feature-request-terminal-identity.md` — open question ANSWERED (this session)

**Uncommitted changes:** the `orca-feature-request-terminal-identity.md` update above, plus this
handoff. Everything else is merged.

**Branches:** none local beyond `main`; `origin` carries `main` only (all five PR branches
auto-deleted on merge).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main                                                     # @ 1052c33
/opt/anaconda3/bin/python3 -m pytest h-mad/tests handoff/scripts -q   # 1072 expected

# the coupled consumer suite — the symlink means this repo's HEAD is what it runs
cd /Users/kimhawk/orca/HemaSuite/hematology-paper-writer
/opt/anaconda3/bin/python3 -m pytest tests/test_h_mad_*.py -q         # 48 expected
```
A bare `python3` is homebrew 3.14 with no pytest — use `/opt/anaconda3/bin/python3` for tests.
`timeout` does not exist on macOS (it is `gtimeout`); a command prefixed with it silently fails as
`command not found` while the surrounding `echo rc=$?` still prints 0.

**Agent panes (pinned this session, and NOT auto-detectable — see Key Learnings):**
```bash
bash h-mad/scripts/hmad-dispatch.sh env       # expect PREFLIGHT: PASS
# codex -> term_7d59e6d2-…  (right split, second pane)
# agy   -> term_4d3f4261-…  (right split, first pane)
```
If Orca restarts, those handles rotate and `env` will now say so explicitly (pid + candidate
handles + the exact `pin` command) instead of reporting "0 candidates".

**Live orchestration state:** Run `run_1632386a175a` is bound to this coordinator pane. The
mailbox holds read/rejected probe messages from this session's tests; they are consumed or acked
and need no cleanup.

**Related docs:**
- Prior handoff: `docs/handoffs/2026-08-03-main__orchestration-fixes-skill-reviewer.md`
- Orchestration protocol: `h-mad/references/orchestration-mode.md`
- The version-matched Orca guide (ground truth for the command surface): `orca skills get orchestration`
- PRs: #34 (identity + preflight), #35 (backlog), #36 (await cache + injected), #37 (rejection
  filter), #38 (rejection reporting)
