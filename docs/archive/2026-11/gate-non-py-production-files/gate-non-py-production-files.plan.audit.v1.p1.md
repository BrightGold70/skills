AUDIT-gate-non-py-production-files-plan-v1-BEGIN
## Summary
The plan addresses every functional requirement as written and preserves the operator rulings. One blocking verification gap remains: replay of the motivating case using existing repository artifacts.

| Requirement | Classification | Coverage |
|---|---|---|
| FR-1 | implemented-as-written | D1, D3, D10 |
| FR-2 | implemented-as-written | D1–D3 |
| FR-3 | implemented-as-written | D4, D10, D11 |
| FR-4 | implemented-as-written | D5, D10 |
| FR-5 | implemented-as-written | D6, D10 |
| FR-6 | implemented-as-written | D7, D10 |
| FR-7 | implemented-as-written | D8, D10 |
| FR-8 | implemented-as-written | D4, D6–D8, D10 |
| FR-9 | implemented-as-written | D11, D12 |
| FR-10 | implemented-as-written | D9 |
| FR-11 | implemented-as-written | D6–D8, D10, D11, D13 |

Evidence: 25 files opened, 19 greps run.

## Must-fix
- Require an incident replay using an existing impl-plan Task and its actual shell target — D10/D12 prescribe scratch-fixture proof, while M5 only counts historical tokens. A reachable historical Task already lists the motivating dispatcher; the existing corpus test checks legacy fields rather than the changed production mapping or hook verdict. Add an isolated replay preserving that Task's text and target spelling, with before/after hook observations and an unlisted control. Synthetic proof alone leaves the base Incident replay invariant unmet.
  class: build
  quote: docs/01-plan/features/gate-non-py-production-files.plan.md › `Per-host fixture tests for every AC of FR-1..FR-8 and FR-11 (AC-11.3 and AC-11.4 one case per member), each host driven through its real hook entry point at the worktree path`
  quote: docs/archive/2026-07/dispatch-resolve-verb/dispatch-resolve-verb.impl-plan.md › ``**Production file**: `h-mad/scripts/hmad-dispatch.sh` ``
  quote: h-mad/tests/test_h_mad_parse_tasks_paths.py › `fields = ("shape", "wire", "pin", "wires", "pins")`
  quote: h-mad/invariants.base.md › `**Synthetic cases alone are a violation** whenever such artifacts exist and are reachable.`

## Should-fix
None

## Nit
None
AUDIT-gate-non-py-production-files-plan-v1-END
