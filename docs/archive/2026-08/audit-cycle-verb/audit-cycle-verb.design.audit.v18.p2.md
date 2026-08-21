## Summary
The design fully implements the requirements established in the spec and plan. All 56 Acceptance Criteria (AC-1.1 through AC-10.5b) are present and `implemented-as-written`. The boundaries between the shell and the helper are clearly delineated, error paths are explicitly routed by tokens, and the load-bearing per-pass gating requirement is preserved. However, two critical data-verification assertions inside the Python helper lack negative tests, rendering them decorative and their mutations uncatchable (Axis B violations).

**Axis C: Spec Reconciliation**
| Spec AC | Design Status | Spec AC | Design Status |
|---|---|---|---|
| AC-1.1 | implemented-as-written | AC-5.4 | implemented-as-written |
| AC-1.2 | implemented-as-written | AC-5.5 | implemented-as-written |
| AC-1.3 | implemented-as-written | AC-5.6 | implemented-as-written |
| AC-1.4 | implemented-as-written | AC-6.1 | implemented-as-written |
| AC-2.1 | implemented-as-written | AC-6.2 | implemented-as-written |
| AC-2.2 | implemented-as-written | AC-6.3 | implemented-as-written |
| AC-2.3 | implemented-as-written | AC-6.4 | implemented-as-written |
| AC-2.4 | implemented-as-written | AC-6.4b | implemented-as-written |
| AC-2.5 | implemented-as-written | AC-7.1 | implemented-as-written |
| AC-3.1 | implemented-as-written | AC-7.2 | implemented-as-written |
| AC-3.2 | implemented-as-written | AC-7.3 | implemented-as-written |
| AC-3.3 | implemented-as-written | AC-7.4 | implemented-as-written |
| AC-3.3b | implemented-as-written | AC-7.5 | implemented-as-written |
| AC-3.4 | implemented-as-written | AC-8.1 | implemented-as-written |
| AC-3.5 | implemented-as-written | AC-8.2 | implemented-as-written |
| AC-4.1 | implemented-as-written | AC-8.3 | implemented-as-written |
| AC-4.1b | implemented-as-written | AC-8.4 | implemented-as-written |
| AC-4.2 | implemented-as-written | AC-9.1 | implemented-as-written |
| AC-4.3 | implemented-as-written | AC-9.2 | implemented-as-written |
| AC-4.4 | implemented-as-written | AC-9.3 | implemented-as-written |
| AC-4.4b | implemented-as-written | AC-9.4 | implemented-as-written |
| AC-4.5 | implemented-as-written | AC-9.5 | implemented-as-written |
| AC-4.6 | implemented-as-written | AC-10.1 | implemented-as-written |
| AC-5.1 | implemented-as-written | AC-10.2 | implemented-as-written |
| AC-5.2 | implemented-as-written | AC-10.2b| implemented-as-written |
| AC-5.3 | implemented-as-written | AC-10.2c| implemented-as-written |
| | | AC-10.3 | implemented-as-written |
| | | AC-10.4 | implemented-as-written |
| | | AC-10.5 | implemented-as-written |
| | | AC-10.5b| implemented-as-written |

## Must-fix
- Missing negative test for the `len(findings) == must` guard — The design states that `gate()` asserts `len(findings) == must` to ensure the subprocess count and in-process enumeration agree. However, the Test Plan lacks a test that deliberately feeds a mismatched count (e.g., stub returns `must=2` for a file with 1 finding) to prove this assertion fires and crashes the cycle. Without this negative test, a permissive mutation (deleting the assertion) survives silently behind a green suite. This violates Axis B (Test discrimination / Mutation verification).
- Missing negative test for the `collected_path` write-verification guard — The design states that `collect()` asserts `collected_path.exists() and collected_path.stat().st_size > 0` to verify that the report file write successfully landed before scoring it. While the shell's `rm` guard is verified via `test_verb_unremovable_path`, there is no equivalent test in the Python suite that forces this write to fail (e.g., using a read-only destination directory) to ensure the guard bites. Without it, the guard lacks discrimination coverage and its mutation cannot be verified. This violates Axis B (Test discrimination / Mutation verification).

## Should-fix
- Test Plan lacks explicit coverage for `h_mad_assemble_audit.py` non-zero exit — While AC-2.4 defines a non-zero exit from assembly as an operational error, and the design lists a test for an absent token (`test_verb_assemble_no_token_is_operational_error`), there is no explicit test verifying the cycle crashes appropriately on a standard non-zero exit. Adding a test for this error path ensures AC-2.4 is mechanically enforced.

## Nit
- The Test Plan text states "The three rows marked *anchors* are the positive tests...", but there are actually five test rows that explicitly use the word "anchors" in their descriptions (`test_verb_two_distinct_dispatches`, `test_fail_in_either_pass_fails_cycle`, `test_completed_cycle_emits_token`, `test_verb_assemble_no_token_is_operational_error`, `test_main_delivered_none_is_unverified`). Update the prose count to match the table.
