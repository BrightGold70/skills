AUDIT-audit-cycle-verb-impl-plan-v4-BEGIN

## Summary
The implementation plan is structurally precise and strictly faithful to the design, successfully resolving the contradictions from previous iterations. There are two oversights to correct: a sequencing error in the pseudo-code blocks that would pass an undefined variable on the halt path, and a test assertion that demands a path from an argv that does not contain it. 

## Must-fix
- Task 5 pseudo-code orders the computation of `size_status` (step 6) *after* it is consumed (step 5) — The shell script invokes `python3 "$here/h_mad_audit_cycle.py" ... --size-status "$size_status"` on an assembly halt (step 5), but `size_status` is not computed until step 6. The inline comment in step 6 acknowledges "computed before step 5 uses it", but structurally it is placed afterwards. A developer following these numbered steps linearly will evaluate an undefined `$size_status` variable on the halt path, passing an empty argument that will crash the helper or result in malformed output.
- Task 6 AC-3.2/AC-10.1 requires the test to assert distinct `report-file paths` "from the stub's recorded argv" — The `exec agy` invocation (`_cmd_exec agy "$prompt_i" --cd "$root" --out "$out_i" --log "$log_i" --timeout "$timeout"`) does not carry the report-file path in its argv (it is embedded inside the file at `$prompt_i`). The test cannot assert the report path from the argv.

## Should-fix
- Task 5 AC-2.4/AC-2.5 does not explicitly name `test_verb_assemble_no_token_is_operational_error` — Task 8 refers to this test name as the anchor for mutation 2, but the test is not explicitly named in Task 5's Acceptance Criteria. Naming it there ensures the implementer provides the exact test name the mutation spec expects.

## Nit
None

AUDIT-audit-cycle-verb-impl-plan-v4-END
