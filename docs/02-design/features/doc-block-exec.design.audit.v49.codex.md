## Summary
The design implements every source-spec acceptance criterion as written; the Axis C reconciliation is complete below. The paired implementation plan, however, schedules finite/positive timeout validation after stream reservation, which contradicts the design's required refusal ordering.

| Spec ACs | Design classification |
|---|---|
| AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-1.7, AC-1.8, AC-1.9 | implemented-as-written |
| AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5, AC-2.6, AC-2.7, AC-2.8 | implemented-as-written |
| AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5, AC-3.6, AC-3.7, AC-3.8, AC-3.9, AC-3.10, AC-3.11, AC-3.12, AC-3.13, AC-3.14 | implemented-as-written |
| AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5, AC-4.6 | implemented-as-written |
| AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5, AC-5.6 | implemented-as-written |
| AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5, AC-6.6 | implemented-as-written |

## Must-fix
- Task 4 defers the finite/positive `--shell-timeout` validation to `run_block`, but reserves stream artifacts first; the design requires timeout validation before reservation. With `--shell-timeout 0`/`nan`/`inf` and a missing `--stdout` path, this plan can create and hold an artifact before returning `BAD_TIMEOUT`, violating the design's “nothing reserved until every input-only refusal” invariant. Use one shared timeout validator from `main` before `_reserve` and from `run_block`, and add an artifact-absence/byte-preservation assertion to the bad-timeout CLI tests.

## Should-fix
None

## Nit
None
