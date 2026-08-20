## Summary
The design for the `audit-cycle` verb successfully composes the shell and Python boundaries, maintaining a strong signal discipline and strict isolation of per-pass channels. It fully implements the core fallback and gating logic outlined in the plan. However, there is a minor gap regarding the premise checklist's visibility on an `UNVERIFIED` verdict, and two specification reconciliations are required: one absent requirement for rejecting invalid pass counts, and one necessary restatement that corrects a contradiction in the spec's error routing.

## Must-fix
- Axis C (Absent): Spec AC-3.1 requires that `--passes N` for `N<1` is rejected as an operational error. The design is completely silent on validating or rejecting `< 1` values. — This drops a required validation guard; the design must explicitly include logic to reject `N<1` as an operational error.
- Axis C (Restated): Spec AC-5.6 dictates "The pass becomes delivered=none per AC-4.6." The design restates this by keeping the actual `delivered` channel (e.g., `report-file` or `out`) and instead routing on `r.verdict == "INVALID"` to yield `reason=no_gate_sections:p<index>`. — The design's approach is narrower and correct, as blindly mapping to `delivered=none` would trigger `reason=no_report:p<index>`, making `no_gate_sections` unreachable and breaking AC-6.3. The spec must be updated to match the design's corrected routing.
- Axis A (Gap): The design is silent on whether the premise checklist is emitted when the verdict is `UNVERIFIED`. (It explicitly states `reports:` and `note:` are omitted, and covers `PASS`/`FAIL`, but omits `UNVERIFIED`). — If one pass succeeds but the other is invalid, a partial checklist might be printed on a "cannot judge" cycle. The design must explicitly omit the checklist on `UNVERIFIED` to match the absence of count fields.

## Should-fix
None

## Nit
- The Python helper's signature includes `--project-root R` (from the full helper invocation example), but the plan stated this flag was only forwarded to `h_mad_assemble_audit.py` and is unused by the extraction or gating steps. It can likely be dropped from `h_mad_audit_cycle.py`'s signature to reduce noise.
