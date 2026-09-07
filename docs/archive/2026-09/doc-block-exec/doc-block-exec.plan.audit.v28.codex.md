## Summary

Axis C reconciliation finds every functional requirement implemented as written; no FR is restated or absent.

| Requirement | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |

The plan has one contradictory implementation instruction for the timeout reap path, despite otherwise specifying the required behavior and tests.

## Must-fix

- The timeout risk row calls `communicate(timeout=…) → killpg(proc.pid, SIGKILL) →` bounded drain the “full sequence,” but omits `proc.poll()`; later in the same plan, the measured AC-5.5 sequence explicitly requires `poll() → killpg()` and says omission turns the zombie-only-group race into `LAUNCH_FAILED stage=reap` rather than `TIMEOUT`. — These are incompatible implementation instructions for FR-5/AC-5.5. Correct the risk row (and any condensed sequence) to require `poll()` before `killpg`, with only `ProcessLookupError` treated as already reaped.

## Should-fix

- The `_final_write(handle, text)` description enumerates `seek; truncate; write; flush; close` but does not prescribe a `finally`-protected close if an earlier operation raises. — AC-3.8 requires every held descriptor to close on every failure path; state the exception-safe close/ownership sequence so an I/O fault cannot leave a held stream descriptor open or escape outside `stream_write_failed` mapping.
- The success criterion labels the 49-AC count “as of spec v1.34,” while the supplied/current spec is v1.35 (the count does still re-derive to 49). — Update the version anchor and record the re-derivation, as the plan itself requires when the spec version moves.

## Nit

None
