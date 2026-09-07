## Summary
Axis C reconciliation: all ACs are implemented-as-written except AC-3.8, which is restated incompletely in the design. The design otherwise aligns with the plan/spec, but its FIFO nonblocking guarantee rests on an uncited platform assumption, which breaches the assumption-verification invariant.

| AC identifiers | Classification |
|---|---|
| AC-1.1–AC-1.9 (each) | implemented-as-written |
| AC-2.1–AC-2.8 (each) | implemented-as-written |
| AC-3.1–AC-3.7, AC-3.9–AC-3.14 (each) | implemented-as-written |
| AC-3.8 | restated |
| AC-4.1–AC-4.6 (each) | implemented-as-written |
| AC-5.1–AC-5.6 (each) | implemented-as-written |
| AC-6.1–AC-6.6 (each) | implemented-as-written |

## Must-fix
- AC-3.8 is restated incompletely in the design's write/close failure path. The spec requires `_final_write` to “flushes and closes the handle inside the region mapped to `stream_write_failed`”; the paired plan is stricter, requiring “the `close()` in a `finally`.” The design only prescribes `seek(0); truncate(); write(); flush(); close()` and relies on `main`'s outer `finally` to close a handle that `_final_write` did not close. If `seek`, `truncate`, `write`, or `flush` raises, that later close (and an error from it) is outside the stated mapped region and can escape as a traceback. Specify an exception-safe `_final_write` ownership/mapping sequence, including close-in-finally and mapped close errors, and add a discriminating fault test/mutation for an operation before `close`.
- The FIFO reservation rule makes a load-bearing, platform-specific assertion without cited evidence: the design says opening a reader-less FIFO with `O_NONBLOCK` “fails at once with `ENXIO`,” but neither the design nor paired plan records a throwaway command and observed output for that behavior. It determines whether the CLI can always return a bounded refusal before spawn, so the unsupported assertion violates the base Assumption verification invariant. Probe `os.mkfifo` plus the exact `os.open` flags on the supported interpreter/platform and cite the observed errno and timing (or revise the protocol to what the probe establishes).

## Should-fix
None

## Nit
None
