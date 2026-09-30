AUDIT-tdd-gate-fail-opens-impl-plan-v1-BEGIN
## Summary
The plan covers the design's main interfaces, but three specified discrimination runs cannot establish the claimed result as written. The gaps are in the unfixed differential overlay and two forced-connection controls. Evidence: 8 files opened, 5 greps run.

## Must-fix
- T6's unfixed-tree run copies only the new differential test, while its case-dependent M-8/M-9 rows must call T1's new `assert_case_insensitive` helper. The archived base has no such helper, so collection or execution fails before the promised gate-equality and expectation-table failure sets can be measured. Overlay the support helper without overlaying the fixed gates, then verify the intended failures. — The required unfixed discrimination is otherwise unmeasured.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.impl-plan.md › `cp h-mad/tests/test_h_mad_tdd_gate_differential.py "$T/h-mad/tests/"`
- The T2 forced-script connection test specifies an expected path spelling, but `_safe_shell_command` returns only a boolean and does not expose the resolved script path. A test of `Path.resolve` outside that call would pass even if the forced `canonical_directory` mutant were installed. Specify an observable boolean-changing fixture or a spy on the value passed within `_safe_shell_command`, and require CX-FORCE-SCRIPT to be caught alone. — The forced direction of WIRE 1 lacks a discriminating observation.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.impl-plan.md › `The expected result is the `Path.resolve` spelling.`
- T10b's forced-read guard asserts only `owned_elsewhere` for the no-flag `--session-id` path. An unconditional git-dir read whose result is discarded still produces that token, so RD-FORCE can survive while the forbidden read occurs. Assert the read did not execute, for example with the recording git stub already used for AC-8.5, and make the forced mutant trigger it. — The forced direction of the resume wire is not enforced by the stated test.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.impl-plan.md › `test_session_id_alone_does_not_read_git_dir`. `--session-id` of another live session, without the flag, prints `owned_elsewhere`.

## Should-fix
- T3 requires the reader to reject `directory-with-names` and `file-with-zero-names`, but the `CANON 1` record has no file/directory field and the plan never specifies how `_read_canon` distinguishes those states. State whether the reader checks the target's file type, and how absent leaves avoid a false protocol error, or extend the record grammar and its tests. — This leaves two protocol tests and the parser implementation open to incompatible interpretations.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.impl-plan.md › `[directory-with-names]`, `[file-with-zero-names]`. Each case uses`

## Nit
- Rename the T1 `OPEN-DECISION` heading once its proposed two-handler solution is adopted; the surrounding text already prescribes the handlers.
AUDIT-tdd-gate-fail-opens-impl-plan-v1-END
