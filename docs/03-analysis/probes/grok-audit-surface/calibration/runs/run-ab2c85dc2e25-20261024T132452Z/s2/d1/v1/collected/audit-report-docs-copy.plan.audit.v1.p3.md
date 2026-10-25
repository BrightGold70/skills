AUDIT-audit-report-docs-copy-plan-v1-BEGIN

## Summary
FR-1, FR-4, FR-5, and FR-6 match the spec (40 unique `AC-*` identifiers in the spec). FR-2 and FR-3 are restated: the plan's `COLLECT:` alternation omits `CONFLICT`, and the transport-refusal marker uses a stem slot plus an ellipsized parenthetical where the spec names `<feature>` and a full sentence. Success Criteria still requires 25 mutations after FR-6, the deliverables table, and `collect_report.json` all fix the set at 23.

| FR | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | restated |
| FR-3 | restated |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |

Evidence: 8 files opened, 20 greps run.

## Must-fix
- FR-2's published token grammar is `COLLECT: OK|MISSING`, which drops the `CONFLICT` verdict the spec requires on a differing docs file (exit 0, bytes unchanged). Goals and the signal-discipline bullet in this same plan still treat `CONFLICT` as a verdict, so a registry line or CLI printer copied from the contract alternation fails AC-2.5 and AC-5.4. Repair: put `CONFLICT` back into that alternation so it matches the spec. Treating `CollectConflict` as an operational error (exit 2, no `COLLECT:` line) would be a different contract and needs a spec change.
  class: build
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `COLLECT: OK|MISSING path=<docs path>`
  quote: docs/01-plan/features/audit-report-docs-copy.spec.md › `COLLECT: OK|MISSING|CONFLICT path=<docs path>`
- FR-3 restates the refusal marker. Requirements pin the slot as `<stem>` and call `(transport file …)` the exact text; Scope in the same plan still emits `<feature>`. The spec's exact line is `[H-MAD] <feature> gate INVALID` plus the full parenthetical below. The same FR-3 bullet defines the grammar as an `audit_` prefix, a dot-free stem, and a `.report.md` suffix, so "stem" can mean the `[^.]+` group (`hnag_c28_agy`) or the basename before the first dot (`audit_hnag_c28_agy`). AC-3.1 only requires the substring `transport file`, so either string passes. Repair: make Scope, Requirements, and the spec name one slot string and the full parenthetical. Leaving the ellipsis inside an "exactly" backtick keeps the bytes unspecified.
  class: build
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `[H-MAD] <stem>`
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `[H-MAD] <feature> gate INVALID (transport`
  quote: docs/01-plan/features/audit-report-docs-copy.spec.md › `(transport file — collect it into docs first: h_mad_collect_report.py)`
- The docs-anchor mitigation names `test_h_mad_audit_cycle_slices.py`, and no file of that name exists under `h-mad/tests`. The anchors it describes (`## Audit prompt assembly`, `6.6.`, `\n7.`) are the slices in `h-mad/tests/test_h_mad_audit_cycle_docs.py` (`_audit_prompt_assembly`, `_report_transport_step`), which is the test spec AC-5.2 names. An edit run against the plan's filename never executes that pin. Repair: name `test_h_mad_audit_cycle_docs.py` in the risk row.
  class: build
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `test_h_mad_audit_cycle_slices.py` slices SKILL.md by exact anchors
- Success Criteria requires `MUTATION: ALL_CAUGHT` on 25 mutations. FR-6, the deliverables row, version-history v1.9, and spec AC-6.3 all say 23, and `h-mad/tests/mutation-specs/collect_report.json` has 23 `"name"` entries (a through l′, with no a′). A build that catches the enumerated 23 fails this completion line. Repair: set the success criterion to 23. Adding two mutations to reach 25 would be a spec change, not a correction of this count.
  class: measurement
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `(25 mutations, every connection dropped`
  quote: docs/01-plan/features/audit-report-docs-copy.spec.md › `AC-2.10 bites. 23 mutations.`

## Should-fix
- The assumption table's `GATE_RE` ends at `should=(\d+)\s*$`. The regex in `h_mad_audit_cycle.py` is that pattern plus `(?:\s+\S+)*` before the end, and the comment above it records `GATE: PASS must=0 should=0 gated=1` as a line the strict form rejected. Executed here: the plan's pattern matches `GATE: INVALID must=0 should=0` and does not match the `gated=1` line; the live pattern matches both. Copying the cited regex back into the parser would drop legal gate lines. The token this feature prints still matches the live regex, so the feature's own INVALID line does not depend on the tightening.
  class: build
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `GATE_RE = ^GATE:\s+(\S+)\s+must=(\d+)\s+should=(\d+)\s*$`
- The strategy says to follow `h_mad_new_gate.py`'s rule that a cannot-judge carries no counts and that any verdict exits 0. FR-3 requires `GATE: INVALID must=0 should=0` and exit 2, which is the shape `_gate_token` already parses (`h_mad_audit_cycle.py` maps that rc 2 onto `INVALID`). A scaffold that omits `must=` and `should=` becomes `OperationalError: missing GATE token` instead of AC-3.3's `("INVALID", 0, 0, [])`. The FR-3 "exactly" line is the binding shape; the cited scaffold rule is the one to correct.
  class: build
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `cannot-judge carries no counts, exit 0 on any verdict`
- The risk row says to use the worktree CLI after task 2. The order of work makes task 2 the gate refusal and task 3 the CLI, and the architecture note already says to hand-collect until the CLI exists. Invoking the verb at the end of task 2 runs a script the plan has not created yet.
  class: build
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `after task 2, use the worktree CLI`

## Nit
- Overview's "Seven of eight consecutive plan cycles" has no command in the assumption table, so the fraction cannot be re-derived.
- Re-running the cited `ls docs/04-report/features/*.report.md` returns 4 files, and `gate-blindness-hardening.report.md` is at `docs/archive/2026-08/gate-blindness-hardening/gate-blindness-hardening.report.md`. The suffix-rule conclusion still holds for the four names that are there. The table is dated 2026-09-02.

AUDIT-audit-report-docs-copy-plan-v1-END
