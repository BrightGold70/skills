# Design Audit v1 — orca-file-diff-review-gates

Reviewer: agy (Gemini 3.1 Pro High), adversarial_consistency + cross_doc_consistency. Cycle 1.

## Summary
The design translates the plan into concrete implementations for the two Orca-guarded file verbs and the SKILL.md review-gate additions. Two gaps: a missing early-return in the `_cmd_file_open_changed` guard, and a dropped passthrough test for that same verb.

## Must-fix
- Missing early return in `_cmd_file_open_changed` guard — the detailed design writes `_require_orca file-open-changed` without `|| return $?`. Without the early return the function does not short-circuit off-Orca and will attempt the `orca` command, violating FR-4 (no non-Orca change). (`_cmd_file_diff` correctly has `|| return $?`.)
- Dropped passthrough test for `file-open-changed` — the Test Plan has `test_file_diff_passthrough` but no equivalent for `file-open-changed`; the plan requires passthrough validation for both verbs.

## Should-fix
None

## Nit
None
