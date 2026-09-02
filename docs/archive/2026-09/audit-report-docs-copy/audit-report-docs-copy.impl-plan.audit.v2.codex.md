## Summary
The impl-plan is generally precise and tracks the paired design closely, especially on collector ordering, CLI signal discipline, and transport/docs grammar separation. One mutation-plan claim is still not actually implemented by the listed 19 mutants, and Task 6 has a metadata inconsistency that could send the implementer to the wrong test surface.

## Must-fix
- Task 6 does not mutation-pin the separable output parts it claims to pin — `docs/01-plan/features/audit-report-docs-copy.impl-plan.md` rows g/j and j' cover guard removal and marker removal, but there is no return-code-only or verdict-token-only mutant for the gate refusal, and no return-code/no-`COLLECT:`-only mutant for the CLI operational-error path. The plan nevertheless claims one mutation per separable output part; under the base Mutation verification invariant, those output assertions can remain decorative while `MUTATION: ALL_CAUGHT` still reports clean.

## Should-fix
- Task 6's metadata contradicts its own AC — the task header names `h-mad/tests/test_hmad_dispatch_audit_cycle.py` as the test file, while AC-6.4 says those existing spec-registry tests are not extended and the new spec is proven by the harness commands. The same section says the mutation command runs the "four new/changed test files" even though the plan/design also change `h-mad/tests/test_h_mad_audit_cycle.py` for AC-3.3; make the intended Task 6 test surface explicit so the implementer does not edit the file AC-6.4 forbids.

## Nit
- The paired design's D5 recipe sample uses a ` ```markdown` fence containing an inner ` ```bash` fence, which closes the outer fence early in normal Markdown rendering. The impl-plan summarizes the body, so this is not a hard implementation gap, but the source block should be escaped or indented before someone copies it as the canonical recipe text.
