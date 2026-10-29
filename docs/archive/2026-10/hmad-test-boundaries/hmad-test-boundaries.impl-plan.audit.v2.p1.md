AUDIT-hmad-test-boundaries-impl-plan-v2-BEGIN
## Summary

The revised plan's mutation census and reference AC counts reproduce, but its structural-error precedence contradicts a required integration test. Task 2 also needs a literal-match clarification to avoid a false test failure.
Evidence: 196 files opened, 5 greps run (including two filename filters).
🌱 graft saved ~366,739 tokens this turn, 5 calls (last call valued at <$0.01).

## Must-fix

- Resolve Task 1's structural early returns versus Task 3's unreadable-spec requirement — the prescribed checker returns `FAIL` with `missing_section` before reading the paired spec, but `test_unreadable_paired_spec_fails_gate_closed` deliberately omits the section and requires `UNREADABLE`. Both contracts cannot reach GREEN together. For non-exempt designs, establish operational-input error precedence before structural early returns while retaining the specified structural diagnostics for readable inputs; cover the combined-invalid case explicitly.
  class: build
  quote: docs/01-plan/features/hmad-test-boundaries.impl-plan.md › ``Missing `## Test Boundaries` on non-exempt design: `Issue(row="-", col="-", code="missing_section", detail="missing ## Test Boundaries section")` (returns `FAIL` immediately).``; ``Runs `h_mad_audit_gate.py` on an external `.design.md` (no `## Test Boundaries` heading) paired with a sibling `.spec.md` containing invalid UTF-8 bytes (`b"\xff\xfe"`); asserts `should_activate_design_check` returns `True`, `h_mad_audit_gate.py` emits `GATE: FAIL` and `TEST-BOUNDARIES: UNREADABLE`, and does not crash``

## Should-fix

- Align Task 2's required explanatory substring with its prescribed Markdown, or explicitly normalize inline backticks before matching — the required substring contains plain `h-mad`, while the rule encloses that word in backticks. An in-memory comparison returned false for the prescribed rule and true after removing backticks, so a literal assertion would reject the intended GREEN edit.
  class: build
  quote: docs/01-plan/features/hmad-test-boundaries.impl-plan.md › ``(where <skill_dir> is the active H-MAD skill directory for the current host, e.g. `h-mad` in this checkout``; ``and `(where <skill_dir> is the active H-MAD skill directory for the current host, e.g. h-mad in this checkout`, requiring `TEST-BOUNDARIES: PASS` before `DESIGN-AUTHOR: DONE` ``

## Nit

None
AUDIT-hmad-test-boundaries-impl-plan-v2-END
