AUDIT-audit-report-docs-copy-impl-plan-v1-BEGIN

## Summary
Three acceptance criteria in the impl-plan tell a 5e implementer to build the wrong exit code, pin the project-root mutation to a test that stays green when that guard is removed, and paste a `/tmp` report path that step 6.6 no longer uses. The rest of the task order, the 23-row mutation table, and the collector/gate signatures line up with the design and the tree.
Evidence: 15 files opened, 27 greps run.

## Must-fix
- AC-3.1 requires the transport refusal to exit 1. The same task's code block returns 2, AC-2.9 and the hand replay require exit 2, and `h_mad_audit_cycle.gate()` treats any return code other than 0 or 2 as `OperationalError`, so an exit-1 refusal never produces AC-3.3's `("INVALID", 0, 0, [])`. Mutation k also anchors on `return 2`.
  class: build
  quote: docs/01-plan/features/audit-report-docs-copy.impl-plan.md › `exit 1; likewise for`
  quote: h-mad/scripts/h_mad_audit_cycle.py › `if result.returncode not in (0, 2):`
- Row e′ names `test_cli_usage_and_operational_errors_have_markers_no_collect_or_traceback` as the force-direction kill for `if not project_root.is_dir()`. That test's project-root case is a file (`file_root.write_text`). Removing the guard still dies in `collected_path.parent.mkdir` with `NotADirectoryError` (an `OSError`), which `main` already maps to exit 2, `operational_error`, and no `COLLECT:` line — the same observation the test asserts. An absent root is the case that mkdir's successfully and then prints `COLLECT: MISSING` / exit 0; that is `test_cli_absent_project_root_refuses_and_creates_nothing`. The harness scores only the named test, so e′ survives and the connection-enforcement pair does not bite. The spec on disk already points e′ at the absent-root test; the plan table does not. Repair: point row e′ at that absent-root test, or change the named test's fixture to an absent root with no report and no `--out`.
  class: build
  quote: docs/01-plan/features/audit-report-docs-copy.impl-plan.md › `test_cli_usage_and_operational_errors_have_markers_no_collect_or_traceback`
  quote: h-mad/tests/test_h_mad_collect_report.py › `The project-root guard's discriminating case is a root that does not`
- AC-3.5a (docs half) and design D5 tell the implementer to read and paste `RP=/tmp/audit_<feature>_<phase>_cycle<N>.report.md` and `..._cycle<N>_codex.report.md` (D5 also `rm -f`s that stable path). SKILL.md step 6.6 and the second-surface section both use a fresh stem, `_run$RUN` and `_codex_run$RUN`. A test that searches for the cited literal does not find it, and pasting D5 drops the reuse guard step 6.6 states.
  class: build
  quote: docs/01-plan/features/audit-report-docs-copy.impl-plan.md › `RP=/tmp/audit_<feature>_<phase>_cycle<N>.report.md`
  quote: h-mad/SKILL.md › `RP=/tmp/audit_<feature>_<phase>_cycle<N>_run$RUN.report.md`
  quote: docs/02-design/features/audit-report-docs-copy.design.md › `RP=/tmp/audit_<feature>_<phase>_cycle<N>_codex.report.md`

## Should-fix
- AC-3.5a (wrapper half) names `install_audit_stub_harness`. No such function exists. The harness that records assembler `--report-file` argv is `install_audit_cycle_stubs` in `h-mad/tests/test_hmad_dispatch_audit_cycle.py`.
  class: build
  quote: docs/01-plan/features/audit-report-docs-copy.impl-plan.md › `install_audit_stub_harness`
  quote: h-mad/tests/test_hmad_dispatch_audit_cycle.py › `def install_audit_cycle_stubs(tmp_path):`
- AC-6.3 says the spec has exactly the 24 mutations above, while the table has 23 rows (a through l′), the task prose says 23, AC-6.3a asserts 23 names, and the same bullet's harness line says `mutations=23`.
  class: measurement
  quote: docs/01-plan/features/audit-report-docs-copy.impl-plan.md › `exactly the 24 mutations above`
- AC-6.3's expected harness line ends at `unreadable=0`. The measured verdict keeps going: `crash_kills`, `crash_visible`, `timeout_kills`, `untargeted`, `hollow_kills`, and `host_skipped`. A left-to-right substring still matches; an exact-line compare of the AC string does not.
  class: measurement
  quote: docs/01-plan/features/audit-report-docs-copy.impl-plan.md › `mutations=23 caught=23 survived=0 refused=0 unreadable=0`
  quote: h-mad/scripts/h_mad_mutation_harness.py › `unreadable=0 crash_kills=0 crash_visible=19/19`
- The design's doc-template compliance line says the SKILL.md edit is additive inside an existing section. D5 and impl-plan Task 5 both add a new top-level `## Second surface — the codex leg` after `## Putting hmad-dispatch on PATH` and outside the slice `test_h_mad_audit_cycle_docs.py` pins.
  class: measurement
  quote: docs/02-design/features/audit-report-docs-copy.design.md › `is additive inside an existing section.`

## Nit
- Design overview still introduces "The plan (v1.5, gated at audit cycles 7+8)" while the impl-plan version history ends at v1.13 and the design history ends at v1.18.
  quote: docs/02-design/features/audit-report-docs-copy.design.md › `The plan (v1.5, gated at audit cycles 7+8)`

AUDIT-audit-report-docs-copy-impl-plan-v1-END
