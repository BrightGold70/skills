## Summary
The plan is structurally sound and aligns closely with the repository implementation, tests, and mutation spec, but three internal/cross-document contradictions remain across `Requirements`, `Scope`, and `Success Criteria`. Specifically, `FR-2` in `## Requirements` omits `CONFLICT` from the `COLLECT:` verdict token set, `## Scope` and the Spec's `FR-3` still specify `<feature>` rather than `<stem>` in the transport-refusal `[H-MAD]` marker, and `## Success Criteria` states `25 mutations` where the spec, deliverables, and `collect_report.json` have `23`.

Evidence: 13 files opened, 0 greps run.

| Spec ID | Plan trace | Verdict |
|---|---|---|
| FR-1 | `## Goals` (L36), `## Requirements` (L45, L58–60), `## Deliverables` (L158) | covered |
| FR-2 | `## Goals` (L36–38, L40–41), `## Requirements` (L46–51), `## Deliverables` (L159–160) | restated |
| FR-3 | `## Scope` (L23–27), `## Goals` (L39), `## Requirements` (L52–57), `## Deliverables` (L161, L167) | restated |
| FR-4 | `## Scope` (L28), `## Goals` (L38), `## Requirements` (L61), `## Deliverables` (L162, L165) | covered |
| FR-5 | `## Scope` (L29–30), `## Goals` (L37–38), `## Requirements` (L62–63), `## Deliverables` (L163) | covered |
| FR-6 | `## Scope` (L31), `## Goals` (L42), `## Requirements` (L64–68), `## Deliverables` (L164–167), `## Success Criteria` (L192–194) | restated |

## Must-fix
- `## Requirements` restates `FR-2` narrower than the spec and its own `## Goals` by omitting `CONFLICT` from the `COLLECT:` contract line (`COLLECT: OK|MISSING` instead of `COLLECT: OK|MISSING|CONFLICT`) — an implementer or test author reading `## Requirements` for the CLI output grammar gets a two-verdict token set that drops the conflict verdict required by `FR-2` (`AC-2.5`, `AC-2.6a`, `AC-5.4`).
  class: build
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `- FR-2: `h_mad_collect_report.py` with `COLLECT: OK|MISSING path=<docs path>`
  quote: docs/01-plan/features/audit-report-docs-copy.spec.md › `It prints one contract line `COLLECT: OK|MISSING|CONFLICT path=<docs path>`
- `## Scope` in the plan and `FR-3` in the spec contradict `## Requirements` (and `v1.10` in `## Version History`) on the feature slot of the gate's transport-refusal `[H-MAD]` marker (`[H-MAD] <feature> gate INVALID` vs `[H-MAD] <stem> gate INVALID`) — `h_mad_audit_gate.py` emits the dot-free transport stem (`p.name[:-len(".report.md")]`), so `<feature>` in `## Scope` and the spec's `FR-3` states a different marker contract than `## Requirements`.
  class: build
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `Every refusal emits `[H-MAD] <feature> gate INVALID (transport`
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `+ the `[H-MAD] <stem>`
  quote: docs/01-plan/features/audit-report-docs-copy.spec.md › `It prints exactly `GATE: INVALID must=0 should=0` and `[H-MAD] <feature> gate INVALID`
- `## Success Criteria` requires `25 mutations` in `collect_report.json`, contradicting `## Requirements` (`23 named-test mutations`), `## Deliverables` (`23 mutations`), `## Version History` (`v1.9: ... → 23 mutations`), spec `AC-6.3` (`23 mutations.`), and `h-mad/tests/mutation-specs/collect_report.json` (which contains 23 mutations) — a stale count from an intermediate sweep left in the acceptance gate of the plan.
  class: measurement
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `- `MUTATION: ALL_CAUGHT` on `collect_report.json` (25 mutations, every connection dropped`
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `(AC-2.10) and readback (AC-2.12); mutation spec with 23 named-test mutations — every new`
  quote: docs/01-plan/features/audit-report-docs-copy.spec.md › `(l′) CLI error path prints a `COLLECT:` line → AC-2.10 bites. 23 mutations.`

## Should-fix
- `## Deliverables` row 2 lists only `_copy_collected_report conflict-safe` and traces only `FR-2 (AC-2.5)`, omitting `_write_collected_report` and `AC-2.6a` even though `## Scope`, `## Architecture Considerations`, and spec `FR-2` require conflict-safety (`overwrite` + `CollectConflict`) on both delivery rungs.
  class: measurement
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `| `_copy_collected_report` conflict-safe | module change | FR-2 (AC-2.5) |`
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › ``surface`; `_copy_collected_report` / `_write_collected_report` gain `overwrite` (default`
  quote: docs/01-plan/features/audit-report-docs-copy.spec.md › `_write_collected_report` (the `--out` extract rung) takes the same `overwrite` keyword`
- `## Risks and Mitigation` names `test_h_mad_audit_cycle_slices.py`, a non-existent test file, instead of `test_h_mad_audit_cycle_docs.py` (which spec `FR-5` / `AC-5.2` and `h-mad/tests/` actually use to pin `SKILL.md` slices).
  class: measurement
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `| `test_h_mad_audit_cycle_slices.py` slices SKILL.md by exact anchors | docs test red | insert outside `## Audit prompt assembly`→`## Putting …` and `6.6.`→`\n7.`; run that test after each edit |`
  quote: docs/01-plan/features/audit-report-docs-copy.spec.md › `- AC-5.2: `test_h_mad_audit_cycle_docs.py` passes unchanged (anchors intact).`

## Nit
- `## Assumption verification` cites pre-edit line numbers (`hmad-dispatch.sh:2493-2499` for `_cmd_exec` option loop, now at lines 3063–3072; `h_mad_audit_cycle.py` lines 92 and 169 for `unlink`, now in `_finalize_write` at line 271 and `_copy_collected_report` at line 290).
