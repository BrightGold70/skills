## Summary
The plan addresses all six functional requirements and has strong coverage for the tagged-selection, process-group, and FR-6 wiring decisions. Its remaining hard gaps are the missing CLI preamble-file path required by the spec and an uncited, platform-sensitive cleanup-failure premise.

| Spec FR | Classification | Plan evidence |
|---|---|---|
| FR-1 | implemented-as-written | Explicit tag + document/heading addressing, fenced-section bounder, and `extract`/`select` API. |
| FR-2 | implemented-as-written | Explicit substitution map, missing-key refusal, literal/count/overlap handling. |
| FR-3 | implemented-as-written | `mkdtemp()` cwd, declared strict/plain shell modes, stream artifacts, and preamble API. |
| FR-4 | implemented-as-written | One `DOCBLOCK:` verdict line with the defined cannot-judge discipline. |
| FR-5 | implemented-as-written | Stdlib timeout, process-group reaping, bounded drain, and cleanup sequence. |
| FR-6 | implemented-as-written | One tagged gate fence, migrated executing path, and bidirectional wire mutations/tests. |

## Must-fix
- The CLI plan omits the required `--preamble-file <path>` contract — AC-3.12 requires a file-backed CLI preamble plus `UNREADABLE reason=preamble_unreadable` before execution, but the plan specifies only the `run_block(..., preamble=...)` API and `--stdout`/`--stderr` CLI arguments. Add the exact parser argument, read-before-spawn/error mapping, registry detail line, and its named tests; otherwise the documented CLI cannot satisfy the spec even if the migrated in-process caller works.
- Cleanup failure rests on an uncited fixture premise — the plan says `mkdir keep && chmod 000 keep` “measurably raises” from `rmtree`, but supplies neither the required throwaway command nor observed output. This is load-bearing for AC-3.14 and the mutation/cleanup test; record a real probe on the supported interpreter/platform and specify a deterministic fallback fault injection if permissions do not produce `PermissionError`, rather than shipping a test whose asserted failure mode may never occur.
- The mutation-anchor timing is internally impossible — it says exact `find` strings are pinned “at impl-plan time against the landed source,” although the source is new and cannot be landed before implementation. Replace that placeholder with a concrete ordering: author source and mutation specs together, re-read each target to establish an exact-once anchor, run the mutation harness, and record the named RED test for every mutation. Otherwise the required mutation verification can silently be deferred or a no-op anchor can pass unnoticed.

## Should-fix
- Define stream-artifact reservation/overwrite semantics — a pre-run writability check must say whether existing `--stdout`/`--stderr` files may be truncated and how distinct destinations are reserved through final write. Without it, an implementation can pass the precheck then overwrite an artifact or lose streams on a late write failure.

## Nit
None
