## Summary

The design explicitly covers all 49 ACs, but contains three blocking gaps in timeout handling, argument validation, and shared-rule enforcement. Repository inspection and Python 3.11.8 probes substantiate the findings; filesystem restrictions prevented writing the requested report and marker files.

Evidence: 10 files opened, 7 greps run.

| Spec identifiers | Axis C classification |
|---|---|
| AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-1.7, AC-1.8, AC-1.9 | implemented-as-written |
| AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5, AC-2.6, AC-2.7, AC-2.8 | implemented-as-written |
| AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5, AC-3.6, AC-3.7, AC-3.8, AC-3.9, AC-3.10, AC-3.11, AC-3.12, AC-3.13, AC-3.14 | implemented-as-written |
| AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5, AC-4.6 | implemented-as-written |
| AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5, AC-5.6 | implemented-as-written |
| AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5, AC-6.6 | implemented-as-written |

## Must-fix

- **Finite positive timeouts can escape the error mapping after spawn.** With the prescribed `Popen` options, `communicate(timeout=1e300)` raises `OverflowError: timestamp too large to convert to C _PyTime_t` on Python 3.11.8; the same command with timeout `1.0` succeeds. The validator accepts this value, but the error mapping excludes `OverflowError`, leaving no verdict or specified child-reaping path. Define a representable timeout policy and test this controlled pair; coordinate any new upper-bound refusal with the spec.
  quote: docs/02-design/features/doc-block-exec.design.md › ``satisfy `math.isfinite(t) and t > 0`, else `BadTimeout(value)`, raised while there is nothing to``; ``**`err` therefore ranges over exactly three types — `OSError`, `subprocess.TimeoutExpired`, `ValueError`**

- **The default help action bypasses the promised malformed-invocation verdict.** Executing the prescribed parser configuration with `["--nope"]` raises `BadArgs`, but adding `--help`, in either order, prints help and exits 0 without `DOCBLOCK:`. Overriding `error()` does not intercept this path. Enforce the standalone-help exception explicitly and add mixed-help negative tests.
  quote: docs/02-design/features/doc-block-exec.design.md › ``UNREADABLE, CLEANUP_FAILED and LAUNCH_FAILED. `--help` alone is argparse's own``; ``output and exit 0, the one exit-0 path that emits no `DOCBLOCK:` line."""

- **The empty-key rule violates the Single-source contract.** The design prescribes independent CLI and API predicates, each tested separately, without a shared implementation or cross-surface equivalence assertion. Separate mutation tests do not establish equivalence. Share the key-validity predicate while retaining each caller’s required diagnostic payload, or specify the invariant’s equivalence-test alternative.
  quote: docs/02-design/features/doc-block-exec.design.md › ``The same predicate in both places, each pinned by its own row: `empty-key-accepted-by-api` and `cli-empty-key-delegated` ``

## Should-fix

- **The AC-2.7 test-table prescription still assigns rendered-output assertions to API tests.** The implementation plan explicitly limits these tests to exception data and assigns rendering to Task 4. Update the design’s table to match that separation; the corrected renderer-mutation killer elsewhere does not resolve this remaining contradictory instruction.
  quote: docs/02-design/features/doc-block-exec.design.md › ``asserting one `intersect: "ab" "bc" "1"` line and nothing executed``; ``asserting one `intersect: "aa" "ab" "2"` line``
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `**This test asserts the exception DATA and nothing about an emitted line**`

## Nit

None
