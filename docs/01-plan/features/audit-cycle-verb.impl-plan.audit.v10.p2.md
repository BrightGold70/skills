## Summary
The implementation plan is well-structured and aligns closely with the paired design, correctly translating the majority of architectural decisions into actionable tasks with pinned connections. However, it completely misses the critical Phase-4 re-audit updates from Design v1.17, v1.18, and v1.19, leading to the omission of three load-bearing negative tests and a missing `unlink` step that prevents stale-report gating.

## Must-fix
- Task 2 omits the `unlink` step before writing the collected report — Design v1.19 proved that `collected_path` is not covered by pre-dispatch clearing (which only targets `/tmp`), meaning a silent write failure on a re-run leaves `exists()` and `st_size > 0` True on the OLD file. Task 2 must explicitly require unlinking the destination before writing.
- Task 2 omits `test_collected_write_failure_is_operational_error` — This is the negative test for the `exists() and st_size > 0` guard (added in Design v1.17 and refined in v1.18 to monkeypatch `write_bytes` to a no-op). Without it, the guard has no discrimination coverage.
- Task 4 omits `test_gate_count_mismatch_is_operational_error` — This is the negative test proving that the `len(findings) == must` assertion actually fires (added in Design v1.17). It must be added to Task 4's ACs.
- Task 4 omits the "real collected reports" corpus requirement for `test_premise_items_match_gate_count` — Design v1.19 added the requirement to run against "a sample of REAL collected reports from `docs/0{1,2}-*/features/*.audit.v*.p*.md`" to satisfy the Reimplementation parity invariant. Task 4 currently only lists synthetic shapes (bulleted, prose, `• `-rendered, acknowledged-filtered) and must include the real-artifact requirement.

## Should-fix
- Missing explicit AC test names from the Design Test Plan — Several tests are described in the Impl-Plan's ACs but omit the specific test names designated in the Design's Test Plan, which creates friction for implementers checking off requirements. Consider explicitly naming:
  - `test_verb_assemble_nonzero_exit_is_operational_error` (implied in Task 5 AC-2.4).
  - `test_verb_phase_validated_before_clearing` (implied in Task 5 AC-1.4, but missing the explicit "stale files are STILL THERE" assertion that proves the ordering).
  - `test_premise_items_formats_no_citation` / `..._formats_supplied_path_line` (implied in Task 1 AC-7.3).

## Nit
None
