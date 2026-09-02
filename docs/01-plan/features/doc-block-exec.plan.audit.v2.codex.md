## Summary
Axis C reconciliation:
| ID | Classification | Notes |
|---|---|---|
| FR-1 | implemented-as-written | Explicit document/heading/tag addressing, single opt-in tag, and non-tagged fence exclusion are covered. |
| FR-2 | implemented-as-written | Explicit substitutions and refusal on non-applying keys are covered. |
| FR-3 | implemented-as-written | Disposable cwd and fence-declared strict/plain shell mode are covered with the narrowed isolation claim. |
| FR-4 | implemented-as-written | The plan covers the verdict-token CLI, exit-code split, and stdout/stderr artifact transport. |
| FR-5 | implemented-as-written | Python-owned time bounds, no external timeout/gtimeout, process-group reaping, and timeout cleanup are covered. |
| FR-6 | implemented-as-written | The migration is treated as a wiring task with two-direction connection discrimination. |
The cited fence and extractor measurements re-check against the current tree, including `bash fences: 68 across 10 files`, `non-empty info opening fences: 83 across 10 files`, and the two `test_h_mad_collect_report_docs.py` extractor hits.

## Must-fix
- The implementation strategy says "a verdict exits 0 and a cannot-judge exits 2 carrying no counts", but the spec's AC-4.4 requires `AMBIGUOUS` to carry `blocks=<n>` while no other cannot-judge carries `blocks=` — this gives implementers conflicting instructions for the `AMBIGUOUS` verdict line and can break the parser contract even though the plan also promises all 33 ACs.

## Should-fix
- The added stdout/stderr transport says CLI streams are written to caller-named paths, but the plan does not say whether those paths are required CLI arguments, optional outputs, or what refusal token applies when they are invalid — this is not an FR-level divergence, but it should be made explicit before the impl-plan locks exact task shapes and tests.

## Nit
None
