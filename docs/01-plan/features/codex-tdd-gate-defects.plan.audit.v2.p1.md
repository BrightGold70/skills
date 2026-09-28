AUDIT-codex-tdd-gate-defects-plan-v2-BEGIN
## Summary
The plan covers all nine functional requirements, but FR-4 and FR-6 restate the current spec in ways that change the implementation. The offline incident probe can report completion with the original broken gate, and one planned connection test omits the required forced direction.

| FR | Classification |
|---|---|
| FR-0 | implemented-as-written |
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | restated |
| FR-5 | implemented-as-written |
| FR-6 | restated |
| FR-7 | implemented-as-written |
| FR-8 | implemented-as-written |

Evidence: 9 files opened, 4 greps run, 1 graft query; the old audit scorer returned PASS for a passing summary followed by stray `1 failed` on stderr. 🌱 graft saved ~54,565 tokens (~$0.07) this turn, 1 call.

## Must-fix
- FR-6 is restated: the plan chooses `rc1` when E1 blocks, while spec v1.1 requires form (b) if proven, otherwise form (a), and forbids retaining exit 1. The plan's probe, implementation branch, tests and success criterion must select the current spec form before Phase 5. The spec is narrower because it permits only the two proven shared forms.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `E1_BLOCKS/*)                        C=rc1 ;;`
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `AC-6.6 (branch `E1_BLOCKS`): `exit 1` is **not** kept.`
- FR-4 is restated: the plan selects the last matching text anywhere in combined stdout and stderr, including stray `N failed` after the actual summary, while the spec scores pytest's summary line. A passing run followed by diagnostic stderr could become `red-measured` and allow a production write; the current audit scorer returns PASS for `2 passed in 0.1s\n1 failed\n`. Restrict selection to an actual pytest summary and add this discriminating case. The spec is narrower because arbitrary later matches are not summaries.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `The parser reads the last `_SUITE_RE` match anywhere in `stdout + stderr` (P5), not "the final line". The design states`
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `The summary is parsed by the audit gate's scorer, `h_mad_audit_gate._suite_summary`,`
- V-1r has no executable pass assertion for its six gate verdicts: the script prints `DONE` after invoking them, and P0 checks only that marker. The plan itself records that the unfixed gate denies all six yet reaches `DONE`, so this check has not been observed failing against the unfixed code. Make the replay validate every RED/GREEN gate result and exit nonzero when any post-merge pass condition fails.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `grep -q '^V-1r: DONE ' "$D/v1-offline-replay.reading.$SHA.txt" || exit 1`
- W6 explicitly exempts the hook-to-judge path from the forced-connection mutation. The base connection invariant requires both directions; a single symlinked-hook fixture cannot detect a judge path fixed unconditionally to that one checkout. Add a second distinct hook/judge tree and force the path to the first tree, then require the second tree's test to fail.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `| W6 Claude gate → hook-relative judge path | the symlinked-hook test runs no judge, or the main tree's | none: a path has no "force" direction (stated) |`

## Should-fix
None

## Nit
None
AUDIT-codex-tdd-gate-defects-plan-v2-END
