AUDIT-tdd-gate-fail-opens-plan-v2-BEGIN
## Summary
The plan is highly detailed, carefully verified, and complies closely with the spec and invariants, particularly in avoiding agent CLI dependencies and verifying assumptions. However, there are two gaps: the Claude gate's canonicaliser contract mathematically drops the "all-entries" hard link rule because it returns a single string instead of evaluating or exposing all names, and the cross-gate differential task omits the specific control cells mandated by the spec.

| AC | Classification |
|---|---|
| AC-1.1 - AC-1.11 | implemented-as-written |
| AC-2.1 - AC-2.5 | implemented-as-written |
| AC-3.1 - AC-3.6 | implemented-as-written |
| AC-4.1 - AC-4.7 | implemented-as-written |
| AC-5.1 - AC-5.5 | implemented-as-written |
| AC-6.1 - AC-6.3 | restated (AC-6.1 controls omitted) |
| AC-7.1 | implemented-as-written |

Evidence: 0 files opened, 5 greps run.

## Must-fix
- The Claude gate's canonicaliser contract drops the "all-entries" hard link rule — T3 specifies that the Python call returns a singular "canonical target" to the bash gate, but the bash gate cannot apply the basename and suffix exemptions to "every such entry" (as the spec requires) if it only receives one target string. The Python call must either evaluate the exemptions itself or return a list of targets for bash to process.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.plan.md › `Claude gate: one Python call returns canonical root, canonical target and the unresolvable condition`
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › `If several entries in that directory share it (hard links in one directory), an exemption holds only if it holds for every such entry.`
- T6 omits the explicit control cells required by the spec's differential domain (restated/absent AC) — the plan specifies testing "over the OD-5 domain" but drops the spec's explicit requirement to assert the `notes.md`, `tests/test_x.py` and `sub/test_x.PY` controls.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › `Cells: M-1…M-14 and M-18, plus the controls notes.md, tests/test_x.py and sub/test_x.PY.`

## Should-fix
None

## Nit
None
AUDIT-tdd-gate-fail-opens-plan-v2-END
