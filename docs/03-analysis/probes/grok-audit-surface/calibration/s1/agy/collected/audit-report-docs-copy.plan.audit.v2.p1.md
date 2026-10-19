## Summary
The plan (`docs/01-plan/features/audit-report-docs-copy.plan.md`) is structurally sound and aligns with the repository implementation across `h_mad_audit_cycle.py`, `h_mad_collect_report.py`, `h_mad_audit_gate.py`, `hmad-dispatch.sh`, `SKILL.md`, and the test/mutation suites, but contains two blocking internal/cross-document inconsistencies: `## Requirements` narrows FR-2's `COLLECT:` contract line to `COLLECT: OK|MISSING` (omitting `|CONFLICT`), and `## Success Criteria` states `25 mutations` for `collect_report.json` against `23` everywhere else in the plan, spec, and mutation spec file. Three non-blocking issues cover an un-swept `<feature>` vs `<stem>` marker token in `## Scope`, an incomplete `h_mad_audit_cycle.py` row in `## Deliverables`, and stale line-number pins in `## Assumption verification`.

Evidence: 14 files opened, 0 greps run.

| Spec FR | Plan disposition | Status |
|---|---|---|
| FR-1 (AC-1.1–1.6) | Covered in `## Scope`, `## Goals`, `## Requirements`, `## Architecture Considerations`, `## Deliverables` | `present` |
| FR-2 (AC-2.1–2.12) | Covered across plan sections, but `## Requirements` restates the `COLLECT:` contract line as `COLLECT: OK|MISSING` without `|CONFLICT`, and `## Deliverables` omits `_write_collected_report` (`AC-2.6a`) and readback (`AC-2.12`) | `weaker` |
| FR-3 (AC-3.1–3.7) | Covered in `## Scope`, `## Requirements`, `## Architecture Considerations`, `## Deliverables` (`## Scope` still writes `<feature>` instead of `<stem>` in the refusal marker) | `present` |
| FR-4 (AC-4.1–4.3) | Covered in `## Scope`, `## Requirements`, `## Deliverables` | `present` |
| FR-5 (AC-5.1–5.4) | Covered in `## Scope`, `## Requirements`, `## Deliverables`, `## Risks and Mitigation` | `present` |
| FR-6 (AC-6.1–6.5) | Covered in `## Requirements`, `## Deliverables`, `## Success Criteria`, but `## Success Criteria` states `25 mutations` instead of `23` | `contradicted` |

## Must-fix
- `## Requirements` narrows the FR-2 `COLLECT:` contract line to `COLLECT: OK|MISSING`, omitting `|CONFLICT` — `docs/01-plan/features/audit-report-docs-copy.spec.md` (`FR-2`, `AC-2.5`, `AC-2.6a`, `AC-5.4`) and the plan's own `## Goals` and `## Architecture Considerations` require three verdict tokens (`OK|MISSING|CONFLICT`), so restating the contract line in `## Requirements` without `|CONFLICT` violates Axis C (weaker/narrower restatement of a spec requirement) and Axis A (internal contradiction).
  class: build
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `- FR-2: `h_mad_collect_report.py` with `COLLECT: OK|MISSING path=<docs path>``
  quote: docs/01-plan/features/audit-report-docs-copy.spec.md › `It prints one contract line `COLLECT: OK|MISSING|CONFLICT path=<docs path>``
- `## Success Criteria` claims `25 mutations` in `collect_report.json` while `## Requirements`, `## Deliverables`, `## Version History` v1.9, the paired spec (`AC-6.3`), and `h-mad/tests/mutation-specs/collect_report.json` all have `23` — violates Axis A (`Contradictions`) and the Base Invariant `Counts are derived, never estimated` (`v1.9` updated `## Requirements` and `## Deliverables` to 23 but left `25 mutations` in `## Success Criteria`).
  class: measurement
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `- `MUTATION: ALL_CAUGHT` on `collect_report.json` (25 mutations, every connection dropped`
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `| `tests/mutation-specs/collect_report.json` — 23 mutations, drop/force pairs per connection incl. fall-through paths and the grammar-disjointness property | mutation spec | FR-6 |`
  quote: docs/01-plan/features/audit-report-docs-copy.spec.md › `(l′) CLI error path prints a `COLLECT:` line → AC-2.10 bites. 23 mutations.`

## Should-fix
- `## Scope` states the transport refusal marker emits `[H-MAD] <feature> gate INVALID (transport file …)` whereas `## Requirements` and `## Version History` v1.10 specify `[H-MAD] <stem> gate INVALID (transport file …)` — the v1.10 wording sweep updated `## Requirements` to `<stem>` (matching `h-mad/scripts/h_mad_audit_gate.py:1012-1018`, where `args.audit_file.name.split(".")[0]` is the full dot-free transport stem) but missed `## Scope` (and `docs/01-plan/features/audit-report-docs-copy.spec.md` `FR-3`).
  class: build
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `<feature>.report.md`). Every refusal emits `[H-MAD] <feature> gate INVALID (transport`
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `with exactly `GATE: INVALID must=0 should=0` + the `[H-MAD] <stem>``
  quote: docs/01-plan/features/audit-report-docs-copy.spec.md › `It prints exactly `GATE: INVALID must=0 should=0` and `[H-MAD] <feature> gate INVALID``
- `## Deliverables` lists only `_copy_collected_report conflict-safe` for FR-2's module change in `h_mad_audit_cycle.py`, omitting `_write_collected_report` conflict safety (`AC-2.6a`) and readback verification on both mutating rungs (`AC-2.12`) — `## Scope` and `## Architecture Considerations` state both rungs and readback, so the deliverables row is narrower than the scoped module change.
  class: build
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `| `_copy_collected_report` conflict-safe | module change | FR-2 (AC-2.5) |`
  quote: docs/01-plan/features/audit-report-docs-copy.spec.md › `_write_collected_report` (the `--out` extract rung) takes the same `overwrite` keyword`
- `## Assumption verification` pins line numbers in `hmad-dispatch.sh` and `h_mad_audit_cycle.py` that have drifted in the current tree (`hmad-dispatch.sh:2493-2499` is now inside `_exec_stamp` while `_cmd_exec`'s option loop is at lines 3063–3072; `unlink` in `h_mad_audit_cycle.py` is at lines 271, 290, and 621 rather than 92 and 169) — line pins in a plan document also trip `h_mad_precheck_doc.py`'s `NO_LINE_PINS` rule.
  class: measurement
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `| `exec` has no `--report-file` | `_cmd_exec` option loop (`hmad-dispatch.sh:2493-2499`): `--cd --model --out --log --timeout --sandbox --effort` only |`
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `| The `--out` rung also clobbers | `grep -n unlink h_mad_audit_cycle.py` → lines 92 (`_copy_collected_report`) AND 169 (`_write_collected_report`) |`

## Nit
None
