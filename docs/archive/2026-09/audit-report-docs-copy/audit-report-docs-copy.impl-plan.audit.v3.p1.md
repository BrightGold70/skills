## Summary
The implementation plan is precise, providing clear code structures, meticulously mapped ACs, and comprehensive mutation targets that test each separable part of the guards. However, there are contradictions between the high-level code structures and the detailed design blocks (notably around `_finalize_write`), a discrepancy in the mutation spec's test array, and a redundant CLI check that renders one of the mutations untestable by a subprocess.

## Must-fix
- Untestable Mutation (`e'`) — The mutation `e'` (`cli-collects-on-fallthrough`) assumes removing the CLI's early `--surface` check will cause a test failure. However, because `collect()` calls `_collected_path` which natively calls `validate_surface`, the exact same `ValueError` is raised, caught by the CLI's outer `try` block, and produces identical subprocess output. The mutant will survive (violating the Mutation Verification invariant). Fix: Drop the redundant early `validate_surface` check in the CLI and remove mutation `e'`.
- Contradiction in Code Snippets — Task 1's `Code structure` correctly extracts `_finalize_write` to share readback logic between both writers, and mutations `a` and `h` explicitly target it. However, the Detailed Design D1 code snippet for `_copy_collected_report` still inlines `unlink`, `write_bytes`, and `_readback_equal`, never actually calling `_finalize_write`.
- Contradiction in Test Spec — Task 6's description states the mutation spec `command` runs FIVE test files (explicitly naming `test_h_mad_audit_cycle.py`), but the JSON code block only lists FOUR files in the array, omitting it.

## Should-fix
- Redundant CLI `mkdir` logic — CLI step 1 specifies checking if "docs dir cannot be created (`mkdir` raises)". Since `_copy_collected_report` already calls `collected_path.parent.mkdir` inside an `_fs_errors` block that identically routes to the CLI's `OperationalError` handler, this early CLI check is dead code and should be removed.

## Nit
None
