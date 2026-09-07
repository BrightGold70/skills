## Summary
The design substantially covers the specified behavior, but it contains a contradictory normative exit-code contract and several required verification paths are not planned. Axis C reconciliation is complete below; every listed AC is implemented-as-written, so there are no silent design/spec narrowings to accept into the spec.

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
- The Architecture Overview’s normative CLI diagram says exit 2 is “only on UNREADABLE / CLEANUP_FAILED,” while the same design’s post-spawn precedence, verdict table, error table, AC-4.2, and AC-4.6 require `LAUNCH_FAILED` to exit 2 — an implementation cannot follow both contracts, and this contradicts the base audit-gate signal discipline’s requirement for a stable token/operational-error partition. Amend the diagram and every summary of the partition to include `LAUNCH_FAILED`.
- The helper mutation spec is declared as “27 named entries” and “Twenty-seven rows,” but its own entry-by-entry table contains 28 rows: `tag-check-removed` through `timeout-validation-removed` are 27, and `no-timeout-invocation-guard-removed` is a 28th self-check — this is a load-bearing count/coverage contradiction under Mutation verification; reconcile the declared count, component description, and expected harness coverage so no guard is silently omitted.
- AC-3.13 explicitly requires a failed `os.chmod(cwd, 0o700)` to clean the newly created cwd and map to `LAUNCH_FAILED stage=mkdtemp`, but the Test Plan only fault-injects `tempfile.mkdtemp`; it has no chmod-failure test or mutation — the distinct post-creation cleanup/error path can regress to an exception leak or retained cwd while every planned test passes.
- AC-3.12 requires invalid UTF-8 for both the document and preamble to be tested as `doc_unreadable` / `preamble_unreadable`; the design describes strict decoding but its Test Plan only names an unreadable preamble path and no invalid-byte document or preamble cases — the promised `UnicodeDecodeError` mappings are therefore unpinned.
- The compatibility claim that GitHub and the Claude Code viewer “take the first info-string word as the language and ignore the remainder” is load-bearing for the tag’s rendering compatibility, but the Assumptions section provides neither a throwaway verification nor observed output — this breaches Assumption verification; add reproducible renderer evidence or explicitly mark the compatibility behavior unverified and obtain operator direction.

## Should-fix
None

## Nit
None
