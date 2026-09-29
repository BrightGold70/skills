# Report: grok-codex-fallback

## Executive Summary
grok now works as a Phase-5 and audit fallback agent end to end. That covers `exec grok`, the grok transcript readers, audit-cycle surfaces, evidence and resolved-model, and a TDD-gate fold that refuses Claude production writes when `fallback_agent` is `grok` or invalid. The feature merges at a 98% match rate after one 6b fix cycle.

## Summary
The feature adds grok beside codex and agy on every surface that dispatches or scores an agent. After the rebase onto the merged codex-tdd-gate-defects judge gate, its TDD-gate half moved from an `ACTIVE` read to a `fallback=` fold on the judge's TDD-STATE line. That fold is owned by grok design v1.3 §D2 and adds a tag-agreement check. The live `exec grok` smoke passed against grok 1.0.41 (`grok-4.7-build`). A fresh-context verifier found four defects. The two MEDIUM ones were fixed in 6b, and the two LOW ones are carried.

## Metrics

| Metric | Value |
|---|---|
| Plan audit cycles | 2 |
| Design audit cycles | 2 (plus delta revision v1.3 after the rebase, not re-audited) |
| Impl-plan audit cycles | 2 (round cap) + advisory delta reviews v1.4 (0/5/6) and v1.5 (1/3/3) |
| Iterate cycles (Phase 6b) | 1 (the telemetry row read 0; the state write of `iterate_cycles=1` did not reach it) |
| Final match rate | 98% |
| 6a-prime architectural review | `READY_TO_MERGE` (agy, tools=4 — thin; the fresh-context verifier carried the review) |
| Tests | 4576 passing / 1 failing (the pre-existing live-binary baseline node) |
| Phases with back-propagation | Phase 4/3: after the rebase, the spec went to v1.5 and the design to v1.3 (the merged §D13 left the fold field to this design) |

## What Went Well
- Running a fresh-context adversarial verifier alongside 6a-prime found four reproduced defects. The agy review read four files and found none of them.
- Two impl-plan errata came from execution, not review:
  - The v1.5.1 RED split: a test asserted a diagnostic that the RED gate cannot print.
  - Row G9 survived v1.6.1: a later check masked the range check's outcome.
  - In both cases the test or plan was corrected, never the gate.
- The registry move ran verbatim from the plan's dry-run recipe, and its readings matched the dry run exactly.

## What To Improve Next Time
- **Rebase re-plans owe re-pinning every base sha, not just the one the plan named.** v1.4 missed `test_h_mad_assemble_tdd_agent.py`'s `507214d`.
- **A plan step pinned to "the RED commit" is lost if RED is dispatched without it.** The registry move had to be run after GREEN.
- **Tests that shell out with repo-relative paths must pin `cwd`.** The mutation harness runs pytest from `h-mad/`, so `git archive … h-mad` read BASELINE_NOT_GREEN there.
- **In zsh, an unquoted `$VAR` holding several paths produced `no tests ran`.** This hit once more this session. Write the paths out.
- **A shared per-pass log that only accumulates defeats any "complete" flag computed over the whole file.** That was D2. Clear logs where report files are cleared.

## Carry Items
- **D3 (LOW):** `CLAUDE*` environment names that are not shell identifiers reach the grok child. `compgen -e` does not list them. Fix: build the environment with `env -i` plus a filtered list.
- **D4 (LOW):** the heartbeat can split a grok event written in two `write()` calls. It fails closed as TRUNCATED. This is the same shared-log mechanism agy's path uses.
- **Registry `verify`** reads missing=4 for the multi-host-runtime records on main whose pins exist only on the mhr branch. The operator accepted this, and it clears when mhr merges.
- The D4 quality measurement of grok against codex (plan follow-up) is still deferred.
- multi-host-runtime rebases onto this merge next (merge order: tdd-gate, then grok, then mhr).

## Version History
- v1.0: Initial report draft (2026-09-29).
