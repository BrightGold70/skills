# Report: exec-missing-report-recovery

## Executive Summary
`hmad-dispatch exec` now recovers from an empty primary verdict channel — retaining the log, recovering the verdict, reporting the tree delta, and reserving rc 3 — instead of exiting 0 silently; shipped via H-MAD with 100% AC match, both coupled suites green, and mutation-verified guards.

**Status:** COMPLETE · **Branch:** feature/211-exec-missing-report-recovery · **Base→Head:** b302c9e → 2914900
**Suite:** h-mad 754/0 · HemaSuite coupled 54/0 · **Match rate:** 100% (24/24 ACs) · **Archreview:** READY_TO_MERGE

## What shipped
`_cmd_exec` (`h-mad/scripts/hmad-dispatch.sh`) no longer turns an empty primary verdict channel into a silent exit-0. On an empty final message it: defaults `--log` to a temp transcript (echoed to stderr + deleted on clean success, retained on empty), reserves rc **3** only over a clean agent exit, recovers the last `^(STATUS|VERDICT):` line from the transcript to stdout, and prints a `git status --porcelain` tree-delta. Both codex and agy branches. `SKILL.md` documents rc 3 and exec terminal-mode; the pre-existing exec recovery playbook is retained.

This turns the manual recovery the merged `feat/exec-missing-report` docs described into wrapper behavior.

## Phase ledger
- P1–P4: brainstorm → spec → plan → design, all audit gates PASS (plan 2 cyc, design 2 cyc; 1 back-prop AC-3.1).
- P5: impl-plan (2 audit cyc) → RED (Codex, 8 new-behavior FAIL genuine) → GREEN (Codex, 754/0) → 5e spec-review found DRIFT.
- **5e drift resolution (key event):** the reviewer's 2 findings matched design words but contradicted FR-1.4 + the RED tests. Verified against the tests → the *design* was wrong, not the impl. Reverted the drift-fix, back-propagated design to v1.2. Lesson reinforced: verify a review finding against the tests/source before applying it ([[feedback verify-review-finding-before-acting]]).
- P6: 6a-prime READY_TO_MERGE · 6a gap 100% · no iterate.
- **Live dogfood:** the feature verified itself — an `exec agy` timeout (rc=1, empty) triggered the new recovery arm correctly (rc preserved, tree-delta printed).

## Verification evidence
- RED genuine: production script unchanged, 8 failures were real AssertionErrors (feature absent).
- Anti-gaming: every guard mutation-tested — disable auto-log→24 RED, rc-3→7 RED, `tail→head`→1 RED; restored 38 green.
- Both coupled suites green (symlink boundary).

## Follow-ups / carry
- Rollout: local `main` also carries the earlier already-merged docs commits (`68c9f22` + `53807f1`, the original `feat/exec-missing-report` docs) not yet on origin — they push together with this merge.
- Deferred (out of scope, documented): dirty-tree re-dispatch guard on `exec`/`send`; report-file polling on exec.

## Version History
- v1.0: Phase 7 closure report.
