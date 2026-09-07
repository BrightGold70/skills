## Summary

The design is broadly aligned with all 48 specified acceptance criteria, but it contains two mutually inconsistent execution/error-path contracts that can produce a non-compliant implementation. Axis C reconciliation is below; every AC is implemented-as-written except that AC-3.9 has an internal conflict called out under Must-fix.

| FR | AC reconciliation |
|---|---|
| FR-1 | AC-1.1 implemented-as-written; AC-1.2 implemented-as-written; AC-1.3 implemented-as-written; AC-1.4 implemented-as-written; AC-1.5 implemented-as-written; AC-1.6 implemented-as-written; AC-1.7 implemented-as-written; AC-1.8 implemented-as-written; AC-1.9 implemented-as-written |
| FR-2 | AC-2.1 implemented-as-written; AC-2.2 implemented-as-written; AC-2.3 implemented-as-written; AC-2.4 implemented-as-written; AC-2.5 implemented-as-written; AC-2.6 implemented-as-written; AC-2.7 implemented-as-written |
| FR-3 | AC-3.1 implemented-as-written; AC-3.2 implemented-as-written; AC-3.3 implemented-as-written; AC-3.4 implemented-as-written; AC-3.5 implemented-as-written; AC-3.6 implemented-as-written; AC-3.7 implemented-as-written; AC-3.8 implemented-as-written; AC-3.9 implemented-as-written (subject to the contradictory implementation direction below); AC-3.10 implemented-as-written; AC-3.11 implemented-as-written; AC-3.12 implemented-as-written; AC-3.13 implemented-as-written; AC-3.14 implemented-as-written |
| FR-4 | AC-4.1 implemented-as-written; AC-4.2 implemented-as-written; AC-4.3 implemented-as-written; AC-4.4 implemented-as-written; AC-4.5 implemented-as-written; AC-4.6 implemented-as-written |
| FR-5 | AC-5.1 implemented-as-written; AC-5.2 implemented-as-written; AC-5.3 implemented-as-written; AC-5.4 implemented-as-written; AC-5.5 implemented-as-written; AC-5.6 implemented-as-written |
| FR-6 | AC-6.1 implemented-as-written; AC-6.2 implemented-as-written; AC-6.3 implemented-as-written; AC-6.4 implemented-as-written; AC-6.5 implemented-as-written; AC-6.6 implemented-as-written |

## Must-fix

- The architecture says “Exactly three non-`RAN` outcomes can follow a spawn” (`CLEANUP_FAILED`, `TIMEOUT`, and stream-write `UNREADABLE`), but the same design and AC-4.6 require `LAUNCH_FAILED stage=reap` after a spawned process when non-`ESRCH` `killpg` fails — this is a fourth post-spawn outcome, and it is neither included in that count nor placed in its stated precedence. Correct the count and define the ordering (or restrict the statement to successfully completed runs), otherwise an implementer can omit or mis-prioritize the required reap failure path.
- AC-3.9/spec require alias detection from `(st_dev, st_ino)` on the two reserved descriptors, and the Detailed Design correctly says no string-level pre-check occurs; however, the Error Handling Strategy table instead says `StreamPathsAlias` is raised by “main's pre-check (resolved-path compare).” Those approaches differ for hard links and have different race properties. Remove the resolved-path direction and make the exception table consistently name descriptor-level detection after reservation.

## Should-fix

- Define the preamble-file text decoding/error policy (or catch decode errors as `PreambleUnreadable`) — the design promises a verdict rather than a traceback for an unreadable preamble, but only says that exception wraps `OSError`; a malformed UTF-8 preamble can instead raise `UnicodeDecodeError` if it is read as UTF-8 text.

## Nit

None
