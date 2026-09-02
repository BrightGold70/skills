Based on the architectural review of the Phase 5 implementation for `audit-report-docs-copy`, I have identified two critical issues that violate the design specifications and invariant compliance. 

1. **Bug in `h_mad_audit_cycle.py` `_collect_unguarded` skipping the `grace` period wait**
2. **`SKILL.md` Second surface section deviating heavily from the explicit design text and dropping required fallback flags**

These deviations introduce a race condition during report collection and incorrectly document the codex leg execution and fallback mechanism.

***

**1. `_collect_unguarded` skips `grace` wait when both files exist and are empty**
- **File:line reference:** `/Users/kimhawk/orca/workspaces/skills/audit-report-docs-copy/h-mad/scripts/h_mad_audit_cycle.py:307-313`
- **What's wrong:** The implementation short-circuits with `return "none", None` if `report_bytes == collected_bytes` and `report_bytes` is falsy (e.g., `b""`). This completely skips `_run_report_wait` and its `grace` period if the report file was created (e.g., via `touch`) but not yet populated.
- **Why it matters:** It breaks the `grace` wait delay which is designed specifically to poll for the report file completion. If an operator or tool creates an empty report file while `collect` is called with `grace > 0`, it instantly fails instead of waiting. The design explicitly mandates falling through to `_has_complete_report` and `_run_report_wait` if `already` is false (empty files are never "already collected").
- **How to fix:** Rewrite the block to exactly match the AC-2.11 design logic:
  ```python
  if spec.report_path.exists() and collected_path.exists():
      report_bytes = spec.report_path.read_bytes()
      collected_bytes = collected_path.read_bytes()
      if report_bytes == collected_bytes and report_bytes:
          return "report-file", collected_path
  ```
- **Operator override reasonable:** No.

**2. `SKILL.md` Second surface section deviates from the exact specified text and drops required flags**
- **File:line reference:** `/Users/kimhawk/orca/workspaces/skills/audit-report-docs-copy/h-mad/SKILL.md:1804-1847` (and corresponding docs tests in `/Users/kimhawk/orca/workspaces/skills/audit-report-docs-copy/h-mad/tests/test_h_mad_collect_report_docs.py:118-148, 260-264, 277-292, 294-362`)
- **What's wrong:** The implementor ignored the exact markdown block provided in the D5 design. Critically, this caused the omission of `--out`, `--log`, and `--timeout` flags from the `exec codex` command, dropped the `_codex` suffix from the input text file, and dropped the `--out` fallback argument from `collect-report`. Furthermore, the explicit gating instructions were replaced with a complex `if ! printf` bash block which the design never specified.
- **Why it matters:** The design provides exact text to ensure doc-template superset compliance. By omitting the `--out` argument in `collect-report`, the fallback rung is completely undocumented, making it impossible for an operator to recover if the report file delivery fails. The missing `exec codex` flags violate the `exec` leg contract.
- **How to fix:** Replace the entire `## Second surface — the codex leg` section in `SKILL.md` with the exact text block provided in the D5 design document. Update or remove the tests in `test_h_mad_collect_report_docs.py` (specifically `test_second_surface_section_is_between_path_setup_and_helper_registry_with_ordered_flow`, `test_second_surface_gates_the_path_printed_by_collect_report`, `test_gate_block_guards_on_the_collect_token_before_gating`, and `test_documented_gate_recipe_halts_instead_of_gating_an_empty_path`) so they assert the correct text from the design instead of the fabricated bash script.
- **Operator override reasonable:** No.

ASSESSMENT: WITH_FIXES
