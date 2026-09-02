## Summary
The implementation plan is structurally sound and strictly adheres to the base invariants, including maintaining the `GATE: INVALID` exit 2 signal discipline and fully specifying mutation tests. However, the plan fails the orchestrator's strict writing-plan formatting constraints by extensively using TBD placeholders and omitting exact file paths. Furthermore, there is a discrepancy between the declared code structures and the detailed design regarding function usage and type annotations.

## Must-fix
- The plan violates the explicit "no TBD placeholders" and "exact file paths" constraints by extensively using `...` and `…`. This occurs in Code Structures for missing function bodies (e.g., `_copy_collected_report`, `collect`, `_section`, `build_parser`), Acceptance Criteria paths (e.g., `docs/02-design/features/…`, `.../audit_f_plan_cycle3_codex.report.md`, `<absent>`), Detailed Design logic blocks (e.g., `... semantic checks`, `collect(..., surface=S)`), and the Task 6 JSON mutation spec (`"name": "..."`, `"file": "scripts/…"`).
- The `render_verdict` function is declared in Task 3's Code structure but is neither implemented nor referenced in Detailed Design D2, which instead handles verdict rendering inline with `print`. This violates the "code blocks that match referenced functions" constraint.

## Should-fix
- Type consistency gap: Detailed Design D1 omits type annotations for several function parameters (e.g., `_copy_collected_report(report_path, collected_path, *, overwrite=True)` and `_collect_unguarded`), whereas Task 1 provides them. Ensure type hints are applied consistently across the design doc.

## Nit
None
