## Summary
The design meticulously translates the specification into a precise implementation, successfully centralizing the docs-path derivation and codifying the codex leg's collection step. All Acceptance Criteria are addressed and implemented as written. However, a logical flaw in the same-file detection block risks bypassing the intended short-circuit when a file is initially missing, which would incorrectly fall back to the `--out` rung.

## Must-fix
- The `same` condition in `_collect_unguarded` includes `.exists()`, which defeats its intended short-circuit for missing files. — If the docs path is passed as `--report` (AC-2.8) and it does not exist initially, `same = spec.report_path.exists() and ...` evaluates to `False`. This causes execution to skip the `same` block and its explicit `return "none", None` fallback. If `--out` is also provided, the function will proceed to the `--out` rung, extract the report, and write it to the docs path. This violates AC-2.8's requirement that "no copy is attempted" and "otherwise MISSING" for the same-file case. Prescription: Remove `spec.report_path.exists() and ` from the `same` assignment in `_collect_unguarded`, making it match the CLI's correct existence-blind assignment (`same = spec.report_path.resolve() == collected_path.resolve()`).

## Should-fix
None

## Nit
None
