## Summary
The implementation plan accurately translates the six literal blocks and single-source constraints from the design into precise doc-test structures. However, it completely omits the concrete execution steps and Acceptance Criteria for the Phase-6 incident replay, which is the required behavioral proof for this feature.

## Must-fix
- Missing Incident Replay execution steps and AC (Axis A gap / Axis B Incident Replay) — The implementation plan mentions "Phase-6 dogfood" in the summary but provides no concrete steps, commands, or Acceptance Criteria for it. The design requires a replay against the real `feature/193` artifacts (using `git show 4298345c...`). The impl-plan must explicitly list the commands to reconstruct the defect and run the dispatch, and add this as a formal AC, so the implementer has clear instructions to execute the behavioral proof.

## Should-fix
- Vague regression test execution — The plan mentions verifying "the 7 coupled HemaSuite `test_h_mad_*`/`test_audit_phase_frontmatter` files" as regression guards, but unlike the primary test suite, it does not provide the exact `pytest` command or paths to run them. Provide the exact command to run these coupled tests.

## Nit
- None
