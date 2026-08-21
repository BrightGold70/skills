## Summary
The design cleanly delineates the shell and Python boundaries, properly isolates the passes, and faithfully implements the complex reaping and gating rules from the spec. However, it introduces a contradiction in handling missing gate tokens, omits the shell aggregation logic for `size_status`, and drops several required print outputs on the final verdict line.

## Must-fix
- Contradiction in `gate` absent-token routing — The `gate` outcome table correctly identifies an absent `GATE:` line as `(None, 0, 0) -> operational error`. However, the `combine` pseudo-code checks `r.verdict in (None, "INVALID")` and routes it to an `UNVERIFIED` verdict. This violates both the doc's own error handling strategy and spec AC-5.5/AC-2.5: an operational error must exit non-zero with no verdict line, whereas `UNVERIFIED` is a verdict that exits 0.
- AC-2.3 (`size_status` aggregation) `absent` — Spec requires the shell to report the worst `size_status` across passes. The shell architecture block parses the `ASSEMBLE:` token but lacks the logic to extract and aggregate the worst `size_status` to pass to the helper.
- AC-4.1b (pre-reap collection path) `absent` — Spec states `--report-timeout` applies only to a pre-reap collection path. The design includes the flag in the CLI API but its architecture only defines a reap-first flow (`wait each PID ... reap FIRST`), leaving the flag completely disconnected from any logic.
- AC-4.4 (naming collected report paths) `absent` — Spec requires the paths of the collected reports to be named on the verb's output. The `render` logic and example outputs omit printing these paths entirely.
- AC-5.4 (double-count warning in output) `restated` (narrowed) — Spec requires the verb's output to explicitly *state* that the sum may double-count a finding. The design discusses the math but relies on the per-pass `p<i>=` fields to make it visible, dropping the requirement to print the warning string itself.
- AC-6.3 (reason string mapping) `absent` — Spec requires the `reason=` value to distinguish `no_report:p<i>` and `no_gate_sections:p<i>`. The `combine` block groups `delivered == "none"` and `verdict == "INVALID"` into a single branch returning `UNVERIFIED, reason` without mapping the distinct conditions to the spec-required strings.

## Should-fix
None

## Nit
None
