# Plan: exec-missing-report-recovery

## Executive Summary
Add an empty-final-message recovery path to `hmad-dispatch exec` that always retains the log, recovers the verdict from it, reports the tree delta, and signals with a reserved exit code — leaving the clean-success contract untouched.

## Overview
On the `exec` path a completed run whose primary verdict channel came back empty currently exits 0 with empty stdout, indistinguishable from both a pass and a no-verdict halt. This plan makes that failure recoverable and unambiguous, so an orchestrator on the default one-shot 5d/5e path never scores channel loss as either outcome. It matters now because `exec` is the documented default for one-shot 5d/5e, so this failure sits on the primary path.

## Scope
`h-mad/scripts/hmad-dispatch.sh` `_cmd_exec` (both `codex` and `agy` branches), its test module, and the SKILL.md exec-dispatch documentation. No change to the pane path, to `_cmd_exec`'s public flags, or to the clean-success stdout/rc contract. Purely additive on the empty-output branch.

## Goals
- Guarantee a survivor transcript channel on every exec dispatch — FR-1.
- Detect an empty final message instead of swallowing it — FR-2.
- Recover the verdict line from the log so extraction still works — FR-3.
- Distinguish "work landed, channel failed" from "nothing happened" — FR-4.
- Signal the empty-output case with a reserved, branchable exit code — FR-5.
- Align docs with the exec verdict channel and the new rc — FR-6.
- Verify across both coupled suites with mutation-tested guards — FR-7.

## Requirements
- FR-1: transcript always retained (default `--log`, deleted on clean success, kept on empty).
- FR-2: empty final message detected on both branches.
- FR-3: last `STATUS:`/`VERDICT:` recovered from log to stdout, tagged.
- FR-4: `git status --porcelain` delta reported in the dispatch cwd.
- FR-5: reserved rc 3 for exit-0-but-empty; crash/timeout rc preserved.
- FR-6: SKILL.md documents rc 3 + terminal-mode exec; playbook retained.
- FR-7: both suites green; each guard mutation-tested.

## Implementation Strategy
Single-layer change in the wrapper's `_cmd_exec`. The existing structure already branches codex-vs-agy and already has the `if [ -s "$last" ]` / `if [ -n "$resp" ]` emptiness test — the recovery path hangs off the *else* of that test rather than a new control structure, keeping the diff small and the clean path literally unchanged. A default log is materialised only when `--log` is absent, and torn down on the success path so behavior on a clean run (stdout, rc, no litter) is byte-for-byte what it is today. Recovery reads the log that already exists, so no new capture machinery. Follow the existing wrapper idioms: stderr for diagnostics, stdout reserved for the payload, `local` vars, `rc` captured via `|| rc=$?`.

## Architecture Considerations
- **stdout/stderr discipline is load-bearing.** The recovered verdict must go to stdout (so `h_mad_extract_verdict.py` reads it) while every diagnostic (log path, tree delta, recovery marker) goes to stderr — the same split the wrapper already enforces, so a caller piping stdout to the extractor is unaffected.
- **rc 3 must be reserved, not overloaded.** It fires only for exit-0-but-empty; a real crash keeps the agent rc and a watchdog keeps 124, so callers can branch cleanly. This is the integration contract other H-MAD steps read.
- **Take the last verdict line.** A single exec subprocess has no prior-cycle scrollback, but a transcript can still restate a `STATUS:` mid-run; last-line matches the extractor's own discipline.
- **Symlink coupling.** `hmad-dispatch.sh` is reached by HemaSuite tests through `~/.claude/skills/h-mad`; both suites are the acceptance boundary, and skill edits during any in-flight run happen in a worktree.

## Deliverables
| Deliverable | Type | Satisfies |
|---|---|---|
| `_cmd_exec` default-log + teardown | shell logic | FR-1 |
| `_cmd_exec` empty-detection branch (codex + agy) | shell logic | FR-2 |
| `_cmd_exec` log verdict-recovery to stdout | shell logic | FR-3 |
| `_cmd_exec` tree-delta reporter | shell logic | FR-4 |
| `_cmd_exec` reserved rc 3 | exit-code contract | FR-5 |
| SKILL.md exec-dispatch doc update | docs | FR-6 |
| `test_hmad_dispatch_exec.py` cases + mutation checks | tests | FR-1..FR-5, FR-7 |

The test deliverable covers **FR-1 too** (AC-1.1 auto-log deleted on clean success, AC-1.2 retained+path-printed on empty, AC-1.3 caller `--log` honored, AC-1.4 clean-path regression), not only FR-2..FR-5.

## Risks and Mitigation
| Risk | Impact | Mitigation |
|---|---|---|
| rc 3 collides with an existing caller expectation | orchestrator misbranches | Verified 2026-07-30: `grep -nE 'return 3\|exit 3' h-mad/scripts/hmad-dispatch.sh` → no matches, and every `exec` call site in SKILL.md reads `rc=$?` as an operational signal then extracts the verdict separately (none branches on `rc == 3`). rc 3 is therefore free to reserve; documented in SKILL.md per FR-6. |
| Clean-success path regresses (litter, changed rc/stdout) | breaks every existing exec dispatch | FR-1.4 + FR-2.3 + FR-5.4 regression guards assert the clean path is unchanged |
| A guard tests vacuously (mutation survives) | false confidence | FR-7.3 mutation-tests each guard both directions |
| Stubbing a fake codex/agy in tests drifts from real CLI behavior | tests green, real path broken | Phase-6 live dogfood on a real exec dispatch, not stubs only |
| Symlink edit breaks HemaSuite mid-run | unrelated suite red | run both suites before merge; edit in a worktree if a run is live |

## Convention Prerequisites
- Feature branch `feature/<NNN>-exec-missing-report-recovery` off `main` (Phase 5c).
- Codex authors Phase 5 (TDD RED+GREEN dispatched via `hmad-dispatch exec codex`); Claude orchestrates/verifies.
- No new external dependency (POSIX `git`/`grep`, bash 3.2).

## Success Criteria
- All spec ACs pass automated tests.
- Both coupled suites 100%.
- Each new guard proven discriminating by mutation.
- One real exec dispatch dogfooded to confirm the recovery path fires live.

## Out-of-Scope (confirmed from spec)
- Dirty-tree re-dispatch guard on `exec`/`send`.
- Report-file polling on the exec path.
- Any pane-path (`send`/`ask`/`report-wait`) change.
- Pushing the already-merged doc commits (`68c9f22`/`53807f1`) — Phase-7 rollout decision.

## Next Steps
User approves v1.0 → auto-cycle plan audit via agy → gate until must-fix=0 AND should-fix=0 → Phase 4 design.

## Version History
- v1.0: Initial plan draft.
- v1.1: Plan-audit cycle 1 fixes — (must-fix) mapped FR-1 into the test deliverable; (must-fix) cited the `grep 'return 3|exit 3'` evidence proving rc 3 is unused (Assumption-verification invariant).
