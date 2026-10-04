## Summary
The implementation plan is highly detailed, faithfully translates the design into shell scripts, correctly accounts for `timeout` restrictions via `_cmd_run`, and explicitly catches vacuous testing traps (such as folding Step 4 to avoid pre-green ACs). However, it contains literal TBD placeholders in the mutation spec and leaves several Python test helpers as empty stubs, violating the audit criteria for plan completeness.

## Must-fix
- Task 6 mutation spec contains literal `"…::…"` TBD placeholders in the `test` fields. The plan must define the exact pytest node IDs (e.g., `tests/test_hmad_dispatch.py::test_...`) to ensure no placeholders remain for the implementer.
- The plan leaves Python test code as empty stubs or omits it entirely: Task 1 provides docstrings but no function bodies for `_orca_read_dir` and `_orca_read_env`, and Task 5 provides no code block for the new doc-rule test it requires. The plan must include these test implementations.

## Should-fix
None

## Nit
None
