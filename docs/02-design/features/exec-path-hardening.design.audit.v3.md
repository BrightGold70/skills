## Summary
The design cleanly implements the unified execution shape and the bounded, stateless composition logic requested in the plan, addressing all Spec Acceptance Criteria (`implemented-as-written`). However, it introduces two critical unverified assumptions regarding `jq` base64 encoding and nested `set -m` job control, which violate the Base Invariant for Assumption Verification and hide a defect where missing comments would cause stamp abandonment.

## Must-fix
- **Axis B (Assumption Verification) — `jq` base64 encoding of missing keys**: The design relies on base64 encoding to transport the comment across lines and explicitly claims that a missing `.comment` key is "usable (treated as empty)". However, standard `jq`'s `@base64` formatter crashes when applied to `null` (`jq: error: null (null) cannot be base64-encoded`). This would cause `_exec_wt_target` to exit non-zero and inadvertently abandon the stamp. This load-bearing assumption was not executed as a throwaway command with cited output, violating the invariant.
- **Axis B (Assumption Verification) — Nested job control (`set -m`)**: The design states that nesting `_exec_run` inside its own poll loop is fully supported because `set -m` is cleanly toggled and `wait` uses explicit PIDs. This relies on complex nested bash job-control behavior (especially when the inner `_exec_run` is invoked via command substitution to capture output), but lacks a cited throwaway command proving this exact shape operates without stalling the parent or mishandling signals.

## Should-fix
None

## Nit
None
