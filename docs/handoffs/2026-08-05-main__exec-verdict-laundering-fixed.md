# Handoff — `exec` verdict laundering + tree-delta fixed (inbound handover accepted)

**Date:** 2026-08-05
**Branch:** main
**Project:** /Users/kimhawk/orca/skills (symlinked as `~/.claude/skills/h-mad` and `~/.claude/skills/handoff`)

## Session Summary

Cleared the three Next Steps carried by `2026-08-03-main__agent-identity-and-await-correctness.md`,
then accepted an inbound handover from a HemaSuite Phase-5 session and shipped both defects it
carried. Five commits on `main` (`a816842` → `c5f6084`), pushed, in sync; suites **1080** (was 1072)
+ 48. The recurring theme is that **four separate carried premises were wrong when re-run** — two in
the first handover's parked repros, one in a bug report I had written twenty minutes earlier, and
one residual hole the second handover's brief did not name. Nothing is blocked. One item is owed by
the operator's explicit choice (filing two bug docs upstream).

## Key Learnings

- **Replaying an incident against your own fix is a different test from unit-testing the fix, and it
  found a hole here.** The J23 boundary slice looked complete and passed its RED tests, but running
  it against the actual 20,770-byte evidence transcript still produced `STATUS: NEEDS_CONTEXT` — the
  log predates the boundary, and the "no boundary → grep everything" fallback let the defect back in.
  Same shape whenever codex dies mid-echo. The fix is now per-backend: codex **requires** the
  boundary (its absence means a missing or truncated echo, so nothing is trustworthy), agy keeps the
  whole-log read because its prompt is an arg and is never echoed.
- **A guard's message can be the load-bearing part, and a returncode-only test never notices.** Two
  of the five J22 mutations keep the exit code and stream routing correct and strip only the text;
  both were caught only because the test asserts *which terminal, the cause, the remedy*. Same shape
  in J23 — the mutation that dropped the codex fail-closed branch survived until the test was fixed.
- **Two of my own first-pass tests were weak, and the harness said so.** The truncated-echo test
  seeded a `--log` — but the codex branch redirects with `> "$log"` and truncates a caller-supplied
  log before writing, so it asserted against an empty file and passed with the guard removed. And
  nothing distinguished first- from last-boundary slicing, because when the real verdict is last,
  `tail -1` returns the same line from either region. Diagnosis matters: both were **weak tests**,
  not equivalent mutants, so the fix was a better test, never a loosened guard.
- **A stub that does not model the real transcript shape lets a test assert impossible behaviour.**
  Two pre-existing recovery tests drove codex transcripts with no prompt echo — a shape real codex
  never emits. They were made realistic (`HMAD_STUB_CODEX_ECHO_STDIN=1`) rather than having the
  guard relaxed to accommodate them.
- **`git -C <subdir> status --porcelain` reports the whole work tree.** No pathspec means no scoping;
  `-- .` is what makes `--cd` mean anything. This is a plain git fact that read as a wrapper bug.
- **`terminal read`'s empty result is recoverable-forward — the earlier absolute claim was wrong.**
  Two restart-surviving panes read seconds apart: codex (idle since restart) → 0 lines, all cursors
  `"0"`; agy (written to since) → 61 lines, `14092` → `16092`. The buffer repopulates on new output.
  Only an *idle* restart-surviving pane is undiagnosable. Corrected in
  `feedback_orca_agent_identity_by_content`, which had asserted "0 rows for ANY full-screen TUI".
- **`worker-abandon` AND `worker-stop` both fail to release a dispatch `dispatch-show` returns.** The
  parked repro blamed `task-update --status ready`; a control with nothing between `dispatch` and
  `worker-abandon` fails identically. Only `task-update --status completed` releases a pane — which
  records abandoned work as completed, the exact provenance lie `worker-abandon` exists to prevent.
- **Orca refuses `--inject` on an agentless pane atomically** (non-zero, stdout empty,
  `dispatch-show` → `dispatch: null`, pane still free), which is why J22 decided against a wrapper
  pre-flight: a check could only add a TOCTOU window and would have to re-derive "is an agent here"
  from the identity signals falsified above.
- **Give a transport e2e real work as its payload.** The `report-wait` live test carried an
  adversarial review of my own bug doc; chasing its first finding is what falsified that doc. A
  smoke-string payload would have proven the same transport and found nothing.

## Next Steps

1. **File the two Orca bug docs upstream to `stablyai/orca`** — written and pushed, deliberately not
   filed (operator chose docs-only). `gh` is authenticated as `BrightGold70`; the repo is public.
   Then stamp `> Filed: <url> (<date>)` at the top of each, matching
   `docs/orca-feature-request-terminal-identity.md:3`.
   - `docs/orca-bug-worker-release-dispatch-not-found.md`
   - `docs/orca-bug-terminal-read-empty-after-restart.md`
2. **Decide the fate of the first handover's uncommitted marker** —
   `docs/handoffs/2026-08-03-main__five-hmad-items-handover.md` is dirty with a one-line
   `**Handover-From:**` addition a HemaSuite session wrote and never committed. `git diff` it; if the
   marker is complete, that brief becomes a claimable handover — go through READ Step 3.5 (oracle,
   then `h_mad_state_write.py --claim`) rather than just working it. Deliberately left alone twice
   now: landing another session's in-flight edit is not this session's call.
3. **Optional, to sharpen the `worker-abandon` report** — run the positive control the doc marks as
   unmeasured: does `worker-abandon` resolve a dispatch created by `worker-start` (which populates
   `launch_token_hash`/`capability_hash`/`process_incarnation`, all null on the failing rows)? Needs
   a live recognized agent; `worker-start --terminal` on a plain shell returns `agent_unconfigured`.

## Open / Blocked Items

- **Two Orca bug docs not filed upstream** — status: deliberate, not blocked. See Next Step 1.
- **`five-hmad-items-handover.md` marker uncommitted** — status: deferred, not blocked. See Next
  Step 2. `repo: /Users/kimhawk/orca/skills · branch: main · worktree: none (main worktree)`.
- **`worker-start` positive control** — status: deferred, not blocked. See Next Step 3. The report
  already states this was not measured rather than asserting a cause, so it is honest without it.
- **Nothing parked outside this repo that this session owns.** The second handover's two defects
  were accepted and shipped, so its brief is now history, not a pointer. No HANDOVER was needed out.

## In-Flight Processes

Not this session's work — included because the next session will see the process and should not reap
it, and because it is live verification of the fix shipped here.

| PID | Command | Log | Started | Elapsed @ handoff | ETA | What to check on exit |
|---|---|---|---|---|---|---|
| 63566 | `codex exec --cd .../hematology-paper-writer --sandbox workspace-write --output-last-message <tmp> --skip-git-repo-check -` | none (another session owns its `--log`) | 16:38 | ~26 s | unknown — not our dispatch | Nothing for us. It is another session's Phase-5 dispatch through the shared symlinked wrapper. |

**Why it matters here:** its live prompt temp
(`/var/folders/.../T/hmad_exec_prompt.XXXXXX.9N4JYrLzrK`, 6.7 KB) ends in
`===HMAD-DISPATCH-BOUNDARY===`. That is the J23 fix running in a real dispatch, in production,
minutes after it shipped — confirmation no staged test could give. Do not interfere with it.

## Context for Next Session

**Files touched this session (all committed to `main`, pushed):**
- `docs/orca-bug-worker-release-dispatch-not-found.md` — **new** (`a816842`)
- `docs/orca-bug-terminal-read-empty-after-restart.md` — **new** (`a816842`), rewritten (`1d96cd6`)
- `h-mad/scripts/hmad-dispatch.sh` — J22 decision comment (`1134192`, comment-only); J23
  `_dispatch_boundary` + `_verdict_after_boundary` + exec boundary delivery + `-- .` pathspec (`c5f6084`)
- `h-mad/tests/test_hmad_dispatch.py` — `test_dispatch_surfaces_the_agentless_refusal_intact` (`1134192`)
- `h-mad/tests/test_hmad_dispatch_exec.py` — 6 new J23 tests; 4 delivery tests + 2 recovery tests
  updated to the new contract (`c5f6084`)
- `h-mad/tests/stubs/codex` — `HMAD_STUB_CODEX_ECHO_STDIN` (`c5f6084`)
- `h-mad/SKILL.md` — the "sidesteps prompt-echo" claim corrected in both places (`c5f6084`)
- `docs/handoffs/2026-08-03-main__exec-verdict-laundering.md` — the inbound brief, committed on
  acceptance (`c5f6084`)

**Uncommitted changes:** one, and not ours — the `five-hmad-items-handover.md` marker (Next Step 2).

**Orchestration state:** Run `run_1632386a175a` still bound to this coordinator pane.
`hmad-dispatch env` → `PREFLIGHT: PASS`; pins codex `term_7d59e6d2-…`, agy `term_4d3f4261-…`. All
probe terminals from the J22 investigation were closed and all five probe dispatches settled.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main                                                     # @ c5f6084
/opt/anaconda3/bin/python3 -m pytest h-mad/tests handoff/scripts -q   # 1080 expected

# the coupled consumer suite — the symlink means this repo's HEAD is what it runs
cd /Users/kimhawk/orca/HemaSuite/hematology-paper-writer
/opt/anaconda3/bin/python3 -m pytest tests/test_h_mad_*.py -q         # 48 expected
```
A bare `python3` is homebrew 3.14 with no pytest — use `/opt/anaconda3/bin/python3`. `timeout` does
not exist on macOS (it is `gtimeout`); a command prefixed with it fails as `command not found` while
a surrounding `echo rc=$?` still prints 0.

**Re-running the two mutation specs** (both `ALL_CAUGHT`; the harness restores the file on every path):
```bash
/opt/anaconda3/bin/python3 h-mad/scripts/h_mad_mutation_harness.py <scratchpad>/mut_j22.json  # 5/5
/opt/anaconda3/bin/python3 h-mad/scripts/h_mad_mutation_harness.py <scratchpad>/mut_j23.json  # 8/8
```
The specs live in this session's scratchpad and will not survive it; both are cheap to re-author
from the `find`/`replace` anchors described in the commit messages.

**Related docs:**
- Prior handoff: `docs/handoffs/2026-08-03-main__orca-defects-and-preflight-decision.md`
- The inbound brief this session accepted: `docs/handoffs/2026-08-03-main__exec-verdict-laundering.md`
- Report-file transport spec: `h-mad/references/orchestration-mode.md:168`
- The version-matched Orca guide (ground truth for the command surface): `orca skills get orchestration`
