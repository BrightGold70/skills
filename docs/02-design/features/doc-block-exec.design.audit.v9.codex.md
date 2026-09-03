## Summary

The design covers all 47 source-spec acceptance criteria as written; the Axis C reconciliation is below. It nevertheless leaves three hard operational/verification gaps that can produce an uncontracted traceback, corrupt two promised stream destinations, or accept a failing full-suite run.

| Spec AC(s) | Classification |
|---|---|
| AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-1.7, AC-1.8, AC-1.9 | implemented-as-written |
| AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5, AC-2.6, AC-2.7 | implemented-as-written |
| AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5, AC-3.6, AC-3.7, AC-3.8, AC-3.9, AC-3.10, AC-3.11, AC-3.12, AC-3.13, AC-3.14 | implemented-as-written |
| AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5 | implemented-as-written |
| AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5, AC-5.6 | implemented-as-written |
| AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5, AC-6.6 | implemented-as-written |

## Must-fix

- Unmapped runtime/setup errors can bypass the one-verdict contract — `mkdtemp()` and `Popen()` failures are absent from `DocBlockError` and the verdict table, while the design explicitly lets any `killpg` `OSError` other than `ProcessLookupError` propagate. Since `main` only maps `DocBlockError`, these normal operational failures can produce a traceback and no `DOCBLOCK:` line; define and map them to an operational verdict, with tests.
- Resolved-path comparison does not ensure distinct stream artifacts — it misses hard-link aliases and has a check-to-open race, so the two held append handles can name the same inode even though the pre-open resolved strings differed. The final writes can then merge/overwrite the promised separate streams, contradicting AC-3.9 and the design's claim that destinations cannot collapse; compare the opened descriptors' `(st_dev, st_ino)` before any truncation and add a hard-link/alias test.
- The stated Phase-5f full-suite gate discards pytest's result — `python3.11 -m pytest -q -p no:cacheprovider | tail -1` exits with `tail`'s status, so pytest can fail while the command succeeds. It cannot establish AC-6.4's pass half and violates test-discrimination evidence requirements; preserve/check pytest's status and emit a deliberate success/failure result.

## Should-fix

- `CleanupFailed`'s causal data is ambiguous — the design says it both carries the recorded cleanup `OSError` and is raised `from pending`, while the combined timeout test requires `__cause__` to be `BlockTimeout`. Define a separate named cleanup-error attribute and state the exact `__cause__` rule for normal, cleanup-only, and timeout-plus-cleanup failures.

## Nit

None
