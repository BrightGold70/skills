## Summary
The plan addresses all six functional requirements, and the transport grammar, readback rule, and both-direction mutation list match the spec. Two contract slots are narrower than the spec, and the success criterion's mutation total disagrees with the spec's enumerated list and with `h-mad/tests/mutation-specs/collect_report.json` (23 `name` entries).

| FR | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | restated |
| FR-3 | restated |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |

Evidence: 9 files opened, 21 greps run.

## Must-fix
- FR-2's Requirements token grammar lists `OK|MISSING` only, which is narrower than the spec's three-verdict line. A collector that emits no `CONFLICT` line still matches that Requirements sentence, while spec AC-2.5 requires `COLLECT: CONFLICT` and unchanged docs bytes when the collected file differs. Architecture and Goals still name a CONFLICT verdict, so the copied grammar and the rest of the plan disagree.
  class: build
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `COLLECT: OK|MISSING path=<docs path>`
  quote: docs/01-plan/features/audit-report-docs-copy.spec.md › `COLLECT: OK|MISSING|CONFLICT path=<docs path>`
- FR-3's Requirements put the dot-free transport stem in the refusal marker's identity slot. The spec, and the plan's Scope, put `<feature>` in that same slot. Those are different strings: the stem of `audit_nlmpin_plan_cycle8_codex.report.md` is `audit_nlmpin_plan_cycle8_codex`, and `<feature>` elsewhere in the gate is the feature slug. The stem reading has to land in the spec before the marker text is stable.
  class: build
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `[H-MAD] <stem>`
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `[H-MAD] <feature> gate INVALID (transport`
  quote: docs/01-plan/features/audit-report-docs-copy.spec.md › `[H-MAD] <feature> gate INVALID`
- Success criteria require 25 mutations on `collect_report.json`. Spec AC-6.3 enumerates 23 (a through l′), and the plan's own FR-6 and Deliverables say 23. The mutation file has 23 `name` entries. A run that catches the spec's list misses this success bar.
  class: measurement
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `25 mutations, every connection dropped`
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `mutation spec with 23 named-test mutations`
  quote: docs/01-plan/features/audit-report-docs-copy.spec.md › `AC-2.10 bites. 23 mutations.`
- The overview's skip census and the assumption row's agy-leg file count are behavioural premises with no runnable command. This tree has 0 `nlm-cli-version-pin.plan.audit.v*.p1.md`, so neither figure can be re-derived from the plan. A behavioural premise carries its command beside the output.
  class: measurement
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `Seven of eight consecutive plan cycles on HemaSuite`
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `persisted by the verb | 23`

## Should-fix
- The docs-anchor risk names `test_h_mad_audit_cycle_slices.py`. The only occurrence of that name is this plan row. The anchors it names are the slices in `h-mad/tests/test_h_mad_audit_cycle_docs.py` (`## Audit prompt assembly` through `## Putting `hmad-dispatch` on PATH`, and `6.6.` through a newline `7.`). Spec AC-5.2 names that docs test, so an edit pass that runs the plan's filename does not exercise the pin.
  class: build
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `test_h_mad_audit_cycle_slices.py`
- Implementation Strategy says this gate follows `h_mad_new_gate.py`'s rule that a cannot-judge carries no counts. FR-3 and the existing missing-sections path in `h_mad_audit_gate.py` both print `GATE: INVALID must=0 should=0`, and `h_mad_audit_cycle.GATE_RE` matches only lines that include `must=` and `should=`. Correct the strategy sentence. Keep the counts on the token.
  class: build
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `cannot-judge carries no counts, exit 0 on any verdict`
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `GATE: INVALID must=0 should=0`
- The assumption table's `GATE_RE` citation rejects a trailing field. `h_mad_audit_cycle.py` line 55 is `^GATE:\s+(\S+)\s+must=(\d+)\s+should=(\d+)(?:\s+\S+)*\s*$`, and `test_a_gated_GATE_line_still_parses` holds a `gated=1` line. `GATE: PASS must=0 should=0 gated=1` matches the code and fails the cited expression. Compared with HEAD; git blame was unavailable (`git` could not read `.gitconfig`).
  class: build
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `GATE_RE = ^GATE:\s+(\S+)\s+must=(\d+)\s+should=(\d+)\s*$`
- The Phase-7 census command in the assumption table, `ls docs/04-report/features/*.report.md`, lists 4 files on this tree. `gate-blindness-hardening.report.md` is at `docs/archive/2026-08/gate-blindness-hardening/gate-blindness-hardening.report.md`. The same row's archive example `docs/archive/2026-08/audit-cycle-verb/audit-cycle-verb.report.md` is present, and `find docs -name 'audit_*'` is still 0. The suffix-rule warning still has live `<feature>.report.md` files; the published 7 and the features-directory example are stale.
  class: measurement
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `→ 7 Phase-7 reports`

## Nit
- Next Steps still starts from operator approval of v1.0. Version History ends at v1.11.
- Assumption-table line anchors do not match HEAD. Unlink is cited at lines 92 and 169; both writers now unlink inside `_finalize_write` at line 271. The exec option loop is cited at 2493–2499; the loop is at 3063–3071 and its flag set still matches the row (`--cd --model --out --log --timeout --sandbox --effort`, and no `--report-file`).
