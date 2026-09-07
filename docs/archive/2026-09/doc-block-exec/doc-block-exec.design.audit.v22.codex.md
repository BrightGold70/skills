## Summary
The design covers the 49 specification acceptance criteria as written; its remaining hard gaps are in the executable mutation-plan contract, not in the feature behaviour. In particular, the mutation binding described by the paired plan cannot be implemented from the design's bare test names, and the AC-5.3 "self-check" is not a real mutation of the artifact its guard reads.

| Spec AC | Classification |
|---|---|
| AC-1.1 | implemented-as-written |
| AC-1.2 | implemented-as-written |
| AC-1.3 | implemented-as-written |
| AC-1.4 | implemented-as-written |
| AC-1.5 | implemented-as-written |
| AC-1.6 | implemented-as-written |
| AC-1.7 | implemented-as-written |
| AC-1.8 | implemented-as-written |
| AC-1.9 | implemented-as-written |
| AC-2.1 | implemented-as-written |
| AC-2.2 | implemented-as-written |
| AC-2.3 | implemented-as-written |
| AC-2.4 | implemented-as-written |
| AC-2.5 | implemented-as-written |
| AC-2.6 | implemented-as-written |
| AC-2.7 | implemented-as-written |
| AC-2.8 | implemented-as-written |
| AC-3.1 | implemented-as-written |
| AC-3.2 | implemented-as-written |
| AC-3.3 | implemented-as-written |
| AC-3.4 | implemented-as-written |
| AC-3.5 | implemented-as-written |
| AC-3.6 | implemented-as-written |
| AC-3.7 | implemented-as-written |
| AC-3.8 | implemented-as-written |
| AC-3.9 | implemented-as-written |
| AC-3.10 | implemented-as-written |
| AC-3.11 | implemented-as-written |
| AC-3.12 | implemented-as-written |
| AC-3.13 | implemented-as-written |
| AC-3.14 | implemented-as-written |
| AC-4.1 | implemented-as-written |
| AC-4.2 | implemented-as-written |
| AC-4.3 | implemented-as-written |
| AC-4.4 | implemented-as-written |
| AC-4.5 | implemented-as-written |
| AC-4.6 | implemented-as-written |
| AC-5.1 | implemented-as-written |
| AC-5.2 | implemented-as-written |
| AC-5.3 | implemented-as-written |
| AC-5.4 | implemented-as-written |
| AC-5.5 | implemented-as-written |
| AC-5.6 | implemented-as-written |
| AC-6.1 | implemented-as-written |
| AC-6.2 | implemented-as-written |
| AC-6.3 | implemented-as-written |
| AC-6.4 | implemented-as-written |
| AC-6.5 | implemented-as-written |
| AC-6.6 | implemented-as-written |

## Must-fix
- The helper, wire, and re-pointed `docsections` mutation plans do not carry the runnable `test` bindings required by the paired plan — the plan says the harness executes `target_command + [test]`, that a bare function name is not runnable, and requires full node IDs such as `tests/test_h_mad_doc_block_exec.py::<name>`; the design's tables instead designate bare `test_*` names as the `test` key and omit the shared `root`/full-node-ID rule. With `target_command = ["python3.11", "-m", "pytest", "-q"]`, pytest treats a bare name as a nonexistent path, so the proposed mutation specs refuse rather than proving their named guards. This violates mutation verification and test discrimination; make the design's binding contract match the plan for all three specs.
- The AC-5.3 row is labelled as one of the 38 harness rows but says it is “not a mutation of the helper” and is tested by planting `timeout 5 bash` in a fixture copy — the mutation harness only verifies an exact replacement in the declared artifact before it runs the named test, while `test_no_timeout_invocation_in_source` is specified to inspect the real helper source. A fixture-copy change can at best test a scanner fixture; it cannot demonstrate that the source guard fails when the source acquires a forbidden invocation. Define a valid, source-preserving Python-code mutation (for example, replace the real bash argv construction with a valid argv containing `"timeout", "5"`) and bind it to the full node ID, then require the harness to observe that test red.

## Should-fix
None

## Nit
None
