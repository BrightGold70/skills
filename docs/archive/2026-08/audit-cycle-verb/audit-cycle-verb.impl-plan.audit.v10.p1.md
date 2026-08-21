## Summary
The implementation plan successfully captures the majority of the `audit-cycle` design, correctly translating complex bash structures and task boundaries. However, it misses several critical updates from Design v1.17–v1.19, most notably the negative guard tests and the stale-file prevention logic (`unlink`), which are load-bearing for test discrimination and correct operation. It also misses the default value for the `--passes` parameter in the shell parsing.

## Must-fix
- **Missing `unlink` and its negative test in Task 2** — The plan omits the `collected_path.unlink(missing_ok=True)` step before the report write, as well as the negative test `test_collected_write_failure_is_operational_error`. Without the `unlink`, a silent write failure on a re-run leaves the stale file, passing the `st_size > 0` guard and scoring the wrong report (Design v1.19). The missing test is required to ensure this guard is actually enforced.
- **Missing negative test for gate count mismatch in Task 4** — The plan drops `test_gate_count_mismatch_is_operational_error`, which the Design Test Plan requires to prove that `gate()`'s `len(findings) == must` assertion actually fires. Without it, the guard has no discrimination coverage (Base invariant: Test discrimination).
- **Missing `--passes` default in shell parameter parsing (Task 5)** — Step 1 specifies `--report-grace (default 5)` and `--timeout (default 900)` but omits `default 2` for `--passes`. Since bash relies on this value for the array loops (`[ "$i" -le "$passes" ]`), omitting the default when the flag is absent will cause a bash syntax error (`[: : integer expression expected`) and crash the verb.

## Should-fix
- **Missing named tests from Design Test Plan** — The plan mentions the behaviors but drops the explicit test names and specific fixture requirements for `test_verb_assemble_nonzero_exit_is_operational_error`, `test_verb_phase_validated_before_clearing` (which specifically requires stale files present on disk to prove they aren't deleted early), and `test_premise_items_formats_no_citation` / `..._formats_supplied_path_line`. These should be explicitly listed in the ACs to ensure they are implemented exactly as designed.

## Nit
None
