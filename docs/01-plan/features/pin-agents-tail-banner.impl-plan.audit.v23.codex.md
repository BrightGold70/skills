AUDIT-pin-agents-tail-banner-impl-plan-v23-BEGIN
## Summary
The production algorithm, task dependencies, and 27-mutation map are otherwise coherent, and the saved plan still re-derives 290 existing module tests and 40 proposed nodes. One RED classification is impossible under the prescribed test-first workflow, which also invalidates the stated per-task/aggregate splits and leaves that newly green node without reject-direction proof.

## Must-fix
- AC-1.5 cannot be `RED: FAIL` when T1's prescribed RED patch includes the shown `_orca_read_env` and `_orca_read_dir` bodies — `test_tail_stub_read_helpers_shape` tests only those test-file helpers, so with the required helpers present it passes before the stub changes; withholding them produces a `NameError`/missing-helper failure rather than a behavioural assertion and forces test implementation during GREEN. This breaches Test discrimination and makes T1's 3/3 split plus the aggregate 29/11 counts unsatisfiable; classify the node as green at RED, add discriminating mutation coverage for the helper properties (splitting the node if needed), and sweep the resulting T1/aggregate counts through the impl-plan, source plan, and design.

## Should-fix
- The paired design's candidate-pool justification is logically backwards: it says widening to `$scoped` “can only turn a resolution into a decline,” but adding one uniquely banner-matching pane turns a decline into a resolution — that is this feature's intended path. Keep `$scoped`, but ground its safety in the scope boundary, wanted/rival banner predicates, and exactly-one matching candidate rather than the false monotonicity claim.

## Nit
- The live check removes a created pane but never removes the `mktemp -d` directory used for the isolated pin file, leaving one empty temporary directory per run.
AUDIT-pin-agents-tail-banner-impl-plan-v23-END
