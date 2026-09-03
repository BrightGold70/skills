## Summary

All six functional requirements are implemented-as-written by the plan; no FR is restated or absent.

| Spec requirement | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |

Two cross-document execution contracts remain inconsistent enough to let verification validate the wrong suite or render verdict fields differently.

## Must-fix

- The Phase 5f full-suite gate is run from the wrong root in the paired implementation plan — `doc-block-exec.impl-plan.md` begins its verification block with `cd h-mad`, then runs the alleged full `pytest` command. The plan and AC-6.4 define the baseline/floor at repository root (2747 tests); the cited command actually collects 2485 from `h-mad/` (rechecked: root 2747, `h-mad/` 2485). A green 2485-test run cannot establish the required full-suite pass half, so make the full-suite command explicitly run at repository root while leaving scoped and mutation commands in `h-mad/`.
- The plan’s verdict-field grammar has drifted from the paired design’s authoritative exhaustive list — the plan says only `rc`, `blocks`, `shell`, `stage`, `count`, and `keys` stay bare and cites design v1.78, while the current design explicitly makes that list exhaustive and also requires bare `reason=`; it requires every other field, including `seconds=` and `pgid:`, to be JSON-quoted. This leaves a concrete output contract undecided for implementation and registry/tests, despite the plan’s claim that one escaper governs every dynamic field; copy the exhaustive list and quoting rule into the plan.

## Should-fix
None

## Nit
None
