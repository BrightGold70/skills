## Summary
The plan is structurally sound and aligns with the implementation and test suite across most functional requirements, but it contains a contract omission in `## Requirements` for `FR-2` (`COLLECT: OK|MISSING` omitting `CONFLICT`) and an internal mutation-count contradiction (`25 mutations` in `## Success Criteria` vs `23` everywhere else and in `collect_report.json`). Additionally, `## Risks and Mitigation` cites a non-existent test file (`test_h_mad_audit_cycle_slices.py` instead of `test_h_mad_audit_cycle_docs.py`), and `## Scope` retains `<feature>` instead of `<stem>` for the transport refusal marker.

Evidence: 12 files opened, 0 greps run.

| Requirement | Classification | Notes |
|---|---|---|
| FR-1 | `implemented-as-written` | Covered in Scope, Requirements, Architecture Considerations, Deliverables |
| FR-2 | `restated` | `## Requirements` narrows the `COLLECT:` verdict set to `OK\|MISSING`, omitting `CONFLICT` |
| FR-3 | `implemented-as-written` | Covered in Scope, Requirements, Architecture Considerations, Deliverables |
| FR-4 | `implemented-as-written` | Covered in Scope, Requirements, Deliverables |
| FR-5 | `implemented-as-written` | Covered in Scope, Requirements, Deliverables |
| FR-6 | `implemented-as-written` | Covered in Requirements, Deliverables, Success Criteria (modulo stale 25 vs 23 count in Success Criteria) |

## Must-fix
- [Axis C / Axis A — FR-2 restated] `## Requirements` restates the `FR-2` `COLLECT:` contract line as `COLLECT: OK|MISSING path=<docs path> delivered=report-file|out|none [forced=1]`, omitting the `CONFLICT` verdict token required by the spec (`COLLECT: OK|MISSING|CONFLICT`, `AC-2.5`, `AC-2.6a`, `AC-5.4`) and contradicting the plan's own `## Goals` (`COLLECT: MISSING|CONFLICT`) and `## Architecture Considerations` (`MISSING and CONFLICT exit 0 (verdicts)`). Update `## Requirements` FR-2 to `COLLECT: OK|MISSING|CONFLICT`.
  class: build
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `- FR-2: `h_mad_collect_report.py` with `COLLECT: OK|MISSING path=<docs path>`
  quote: docs/01-plan/features/audit-report-docs-copy.spec.md › `It prints one contract line `COLLECT: OK|MISSING|CONFLICT path=<docs path>`
- [Axis A — Contradictory mutation count] `## Success Criteria` requires `25 mutations` in `collect_report.json`, contradicting `23` in `## Requirements`, `## Deliverables`, `## Version History` (v1.7, v1.9), the spec's `AC-6.3` (`23 mutations`), and `h-mad/tests/mutation-specs/collect_report.json` (which has 23 entries in `"mutations"`). Update `## Success Criteria` from `25 mutations` to `23 mutations`.
  class: measurement
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `- `MUTATION: ALL_CAUGHT` on `collect_report.json` (25 mutations, every connection dropped`
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `(AC-2.10) and readback (AC-2.12); mutation spec with 23 named-test mutations — every new`
  quote: docs/01-plan/features/audit-report-docs-copy.spec.md › `(l′) CLI error path prints a `COLLECT:` line → AC-2.10 bites. 23 mutations.`

## Should-fix
- [Axis A — Wrong test filename in Risks and Mitigation] `## Risks and Mitigation` names `test_h_mad_audit_cycle_slices.py` as the test that slices `SKILL.md` by exact anchors (`## Audit prompt assembly`→`## Putting …` and `6.6.`→`\n7.`) and instructs running that test after each edit, but no `test_h_mad_audit_cycle_slices.py` exists in `h-mad/tests/`; the actual test file containing those slice helpers is `h-mad/tests/test_h_mad_audit_cycle_docs.py` (as cited in `AC-5.2`).
  class: measurement
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `| `test_h_mad_audit_cycle_slices.py` slices SKILL.md by exact anchors | docs test red | insert outside `## Audit prompt assembly`→`## Putting …` and `6.6.`→`\n7.`; run that test after each edit |`
  quote: docs/01-plan/features/audit-report-docs-copy.spec.md › `- AC-5.2: `test_h_mad_audit_cycle_docs.py` passes unchanged (anchors intact).`
- [Axis A — Inconsistent transport refusal marker slot between Scope and Requirements] `## Scope` states that every transport refusal emits `[H-MAD] <feature> gate INVALID (transport file …)`, whereas `## Requirements` FR-3 (updated in `v1.10`) specifies `[H-MAD] <stem> gate INVALID (transport file …)` because a transport filename has no reliable feature grammar and `h_mad_audit_gate.py` emits the dot-free stem verbatim. Align `## Scope` (and `docs/01-plan/features/audit-report-docs-copy.spec.md` FR-3 description) with `<stem>`.
  class: measurement
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › ``<feature>.report.md`). Every refusal emits `[H-MAD] <feature> gate INVALID (transport`
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › ``_collected_path`) with exactly `GATE: INVALID must=0 should=0` + the `[H-MAD] <stem>`

## Nit
- In `## Deliverables`, row 2 (`| `_copy_collected_report` conflict-safe | module change | FR-2 (AC-2.5) |`) names only `_copy_collected_report` and `AC-2.5`, whereas `## Scope` and `## Architecture Considerations` state that both `_copy_collected_report` and `_write_collected_report` gain `overwrite` and post-write readback (`AC-2.5`, `AC-2.6a`, `AC-2.6b`, `AC-2.12`).
- In `## Assumption verification`, the line-number citations `hmad-dispatch.sh:2493-2499` for `_cmd_exec` and `h_mad_audit_cycle.py` lines `92` and `169` for `unlink` reflect an older revision of those files (`_cmd_exec`'s option loop is now at `hmad-dispatch.sh:3063-3072`, and `unlink` in `h_mad_audit_cycle.py` is at lines `271` and `290`).
