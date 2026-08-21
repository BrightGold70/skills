## Summary
The implementation plan successfully translates the complex error routing, bash/python boundary constraints, and verification strategy from the design into detailed execution steps. However, there are two test-mapping contradictions on Axis A (Adversarial Consistency) where assertions and mutation specs are attached to the wrong tests, violating the required scope boundaries, plus a minor undefined variable in the shell snippet.

## Must-fix
- **Test Scope Contradiction (Task 4 / AC-1.2)** — The plan grafts the dispatch assertion ("the dispatch stub records no further invocation") onto the helper test `test_fail_in_either_pass_fails_cycle` in Task 4, while omitting the verb test `test_verb_fail_dispatch_count` entirely. A helper test cannot assert on the shell's dispatch stub because the helper never invokes dispatch (it has no `exec` path). Move this assertion back to the verb suite under `test_verb_fail_dispatch_count` as specified by Design AC-1.2.
- **Mutation Spec Contradiction (Task 8)** — Mutation 10 (`helper-gate-force-none`) lists `test_combine_invalid_yields_unverified` as its failing test for the `no_report:p<i>` case. This is a contradiction: `test_combine_invalid_yields_unverified` covers the `GATE: INVALID` verdict (missing gate sections, yielding `no_gate_sections:p<i>`), not `delivered=none`. The correct failing test for removing the `delivered != "none"` guard is `test_combine_unverified_outranks_fail` (which exercises `p2 none` to assert `UNVERIFIED reason=no_report:p<i>`).

## Should-fix
- **Undefined variable in shell block (Task 5)** — Step 4 redirects assembly output to `>"$asm_i"` and parses it from `"$asm_i"`, but `asm_i` is never defined in the path templating block (Step 2) or anywhere else in the snippet. Add `asm_i="${stem}_p${i}.asm.txt"` to Step 2 to ensure the script does not fail with an ambiguous redirect.

## Nit
None
