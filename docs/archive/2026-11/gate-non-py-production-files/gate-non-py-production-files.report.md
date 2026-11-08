# Report: gate-non-py-production-files

## Executive Summary
All three TDD gates now judge a listed code-like non-`.py` file while doc and data files stay exempt, and the feature closes at 100% of 55 ACs against the fourth analysis's census, with one intermittent suite failure whose cause is unestablished.

## Summary
The Claude, codex and agy gates share one listing matcher and one doc/data definition, so a file an impl-plan lists under its Production files gets the same test-first judgement as Python. Late verification changed production code after the first clean reading: a file named exactly `.py` now counts as Python on codex and agy, in and out of the root, and `_tmp_report_target` reads every canonical name through `canonicalise` instead of one resolved name. Phase 6 took six architectural reviews and five gap analyses, and the match rate went 100, 91, 91, 91, 100 as the method for finding unmarked guards improved, not because the code regressed.

## Metrics

| Metric | Value |
|---|---|
| Plan audit cycles | 2 |
| Design audit cycles | 2 |
| Impl-plan audit cycles | 2 |
| Iterate cycles (Phase 6b) | 4 |
| Final match rate | 100% (11 of 11 FRs, 55 of 55 ACs at `bbcd731b`), with AC-9.3 resting on analysis v4's census, not a fresh one |
| 6a-prime architectural review | `READY_TO_MERGE` at `e524b58a`, under a prompt that narrowed what counts as Critical; v4 and v5 returned `WITH_FIXES` |
| Tests | Two full runs at `bbcd731b`: 8645 passing / 0 failing, and 8644 passing / 1 failing |
| Mutation | 161 of 161 caught across 13 specs, 124 of them in the 10 feature specs; `ANCHORS_OK` 3043 |
| FR-9 | 33 of 33 rows PASS at `e524b58a`; no hook or script changed after it |
| Phases with back-propagation | Phase 6: spec to v1.15, design to v1.12, impl-plan to v1.11, none re-audited |

## What Went Well
- Re-measuring instead of carrying a number exposed that v1's 100% was over-stated: a census of `# M:` markers could not see an unmarked decision arm. A diff-derived census found 16 lines, 3 with no test.
- Fresh-context verifiers and authors corrected the orchestrator's briefs repeatedly, by measurement: the guard's condition is the process cwd rather than the repo root, and W5AR and W5AF do not both pin target binding.
- Running the harness in the orchestrator caught what codex's sandbox could not: `CX-TMP-PY-UNRESOLVABLE` read `SURVIVED` after a fix codex reported as done.

## What To Improve Next Time
- A marker census is blind to unmarked code. Derive a guard census from the diff at Phase 6a, since a hand list was incomplete twice here.
- A test asserting text from `Path.resolve()` passed only because the suite ran the hook under Python 3.11 while the live hook runs under 3.15. Hook tests that touch interpreter-sensitive behaviour need a reading under the live interpreter.
- Fixtures can hide a whole class: every second-plan fixture was unreadable, so nothing exercised a readable second active plan.
- The orchestrator's machine-wide `pkill -f` while stopping a run was broader than this worktree. Stop by task id and verify by working directory.
- An author's failed `cd` wrote probe files into the main checkout; they were moved out and the tree verified. Subagent commands that depend on a scratch directory must check the `cd`.

## Carry Items
- `test_hmad_dispatch_exec_stamp.py::test_heartbeat_stamps_across_three_intervals` failed one of two full runs, cause unestablished. `FAILDIFF: SAME` with 0 failures over 5 repeats, and `FLAKE-VERDICT: NOT_REPRODUCED runs=30`. The feature does not touch the test or the wrapper.
- AC-9.3 clause 1 holds against analysis v4's census. Censuses found 3, 16 and 2 lines; the operator chose on 2026-11-06 not to run a fourth, so further unanchored lines may exist.
- Named residuals, not fixed: a listed file with a same-directory `test_*.py` hard link reads DENY on Claude and ALLOW on codex and agy; a hard link in a different directory reads ALLOW on all three hosts.
- The primary record of the 2026-11-04 operator ruling behind the ninth FR-9 refusal was not found at closure. Located 2026-11-08: a typed operator prompt, recorded in `gate-non-py-production-files.ruling-2026-11-04.md`. AC-9.5 does not depend on it.
- `crash_visible=0/0` on the host specs means their crash count has no denominator. Only reading an assertion line tells a crash from a guard.
- Analysis v5's 11 nits, at `docs/archive/2026-11/gate-non-py-production-files/gate-non-py-production-files.analysis.v5.md`.
- Merging changes live gates at once, because `~/.claude/skills/h-mad` links to the main checkout. Effect on other active Phase 5 lanes is to be measured before the push.

## Version History
- v1.0: Initial report draft.
