AUDIT-pin-agents-tail-banner-impl-plan-v42-BEGIN
## Summary
The audit of `pin-agents-tail-banner.impl-plan` reveals several critical adversarial consistency gaps, primarily around undeclared variables causing `NameError`s in the Python tests and a cross-document consistency failure in the verification table. The logic of the Bash scripts and the regex modifications themselves appear sound and correctly matched to the production structure. Fixing these test suite gaps is required before implementation can proceed.

## Must-fix
- `STUB_ORCA_READ_DIR` in `test_tail_pass_prose_mentioning_agent_does_not_resolve` — Throws a `NameError` as it is undeclared (should be `d`), breaking the test.
- `tmp_path` missing from `test_tail_sig_times_out` parameters — Throws a `NameError` when used to construct the bindir, breaking the test.
- `tmp_path` missing from `test_tail_stub_read_helpers_shape` parameters — Throws a `NameError` when creating the temp directory `d`, breaking the test.
- `STUB_ORCA` in `test_tail_stub_read_helpers_shape` — Throws a `NameError` as it is undeclared (should be `STUBS / "orca"`), breaking the test.
- Incomplete Test-name contract table — Omits multiple mutations defined in the JSON spec (e.g., `tail-re-widened-to-launch-line-agy` from AC-3.2, `skill-md-description-reworded` from AC-5.3, `wire-rival-matcher-forced-empty` from AC-4.6, `timeout-override-ignored` from AC-2.6, and the `wire-wanted-matcher-*` mutations from AC-3.17). This breaks the exact cross-document consistency mapping required for green-at-RED proofs.

## Should-fix
None

## Nit
None
AUDIT-pin-agents-tail-banner-impl-plan-v42-END
