## Summary
Axis C reconciliation: all acceptance criteria are implemented-as-written except AC-2.8, which the design explicitly restates. The restatement fixes an apparent diagnostic-information problem, but it changes the spec's stated control flow and must be made explicit in the source-of-truth spec.

| Spec ACs | Classification |
|---|---|
| AC-1.1–AC-1.9 | implemented-as-written |
| AC-2.1–AC-2.7 | implemented-as-written |
| AC-2.8 | restated |
| AC-3.1–AC-3.14 | implemented-as-written |
| AC-4.1–AC-4.6 | implemented-as-written |
| AC-5.1–AC-5.6 | implemented-as-written |
| AC-6.1–AC-6.6 | implemented-as-written |

## Must-fix
- AC-2.8 is silently restated at the CLI/API boundary — the spec says the empty-key rule lives in `substitute` and “`main` reaches the same rule through `substitute`,” whereas the design says “`main` refuses an empty `--subst` key itself while building the map” and that `substitute` is only the API wall. This is a source-of-truth divergence (and changes where the raw `=V` diagnostic is preserved); update AC-2.8 to authorize the design's split explicitly, or revise the design to implement the specified delegation.

## Should-fix
None

## Nit
None
