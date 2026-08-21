## Summary
The design for `audit-cycle-verb` robustly orchestrates the two-pass audit cycle, successfully eliminating the fragile hand-run steps while maintaining strict signal discipline. The division of responsibilities—shell for job control and assembly, Python helper for text extraction and gating—is well reasoned and strictly enforces a single-source verdict formatter. I've reconciled the design against the spec and found all Acceptance Criteria to be implemented as written. However, there are critical gaps in how the design handles assumptions regarding missing files and exit codes from the composed scripts, and a test isolation violation that must be addressed before implementation.

| Spec Identifier | Classification |
|---|---|
| AC-1.1 to AC-1.4 | `implemented-as-written` |
| AC-2.1 to AC-2.5 | `implemented-as-written` |
| AC-3.1 to AC-3.5 | `implemented-as-written` |
| AC-4.1 to AC-4.6 | `implemented-as-written` |
| AC-5.1 to AC-5.7 | `implemented-as-written` |
| AC-6.1 to AC-6.4b | `implemented-as-written` |
| AC-7.1 to AC-7.5 | `implemented-as-written` |
| AC-8.1 to AC-8.4 | `implemented-as-written` |
| AC-9.1 to AC-9.5 | `implemented-as-written` |
| AC-10.1 to AC-10.5b | `implemented-as-written` |

## Must-fix
- **Unverified assumption on `h_mad_extract_report.py` missing-file behavior** — The design triages `h_mad_extract_report.py` such that "exit 2, sentinel pair missing/empty" yields `delivered=none`, while any other non-zero exit crashes the cycle (exit 4). Because the shell clears `<out_path>` before dispatch, an `exec agy` run that dies instantly will leave no `<out_path>` file. The design fails to state whether the extractor safely exits 2 on a non-existent file or whether the helper explicitly checks for file existence before calling it. If the extractor raises `FileNotFoundError` (exit 1), a normal dispatch crash will incorrectly crash the entire cycle. This violates the **Assumption verification** and **Missing Error Path** invariants.
- **Unstated assumption on `h_mad_report_wait.py` exit code** — The triage table states that `h_mad_report_wait.py` returns a non-zero code meaning "timeout with no file" (routing to the `--out` fallback), but fails to state *which* exact exit code represents this timeout. If the helper treats all non-zero codes as timeouts, it masks real operational errors; if it checks for a specific code, that code must be stated explicitly to ensure the helper's implementation aligns with the script's actual contract. This violates **Assumption verification**.
- **Test isolation violation for collected reports** — The design states that the collected report path is derived from `--project-root` and written under `<audit-dir>/<feature>.<phase>.audit.v<N>.p<i>.md`, verified by re-reading. However, the test plan for collection (e.g., `test_collect_report_file_present`) does not explicitly require sandboxing `--project-root`. Without an explicit mock or temporary directory for `--project-root` during these tests, the test suite will write artifact files directly into the repository's live `docs/` tree, violating the **Test discrimination** (isolation) base invariant.

## Should-fix
None

## Nit
- In the Test Plan, `test_gate_invalid_discards_counts` states it verifies the helper's `INVALID` verdict and dropped counts. It would be clearer to explicitly mention that this test (or `test_combine_unverified_outranks_fail`) also asserts the *cycle* verdict becomes `UNVERIFIED reason=no_gate_sections:p<i>`, directly confirming AC-10.4.
