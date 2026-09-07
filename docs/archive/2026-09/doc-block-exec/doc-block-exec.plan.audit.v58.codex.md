## Summary
The plan is concrete and reconciles FR-1, FR-2, FR-3, FR-4, and FR-6 with the supplied spec. FR-5 is restated incompletely: its timeout sequence leaves the final `wait()` unbounded, so the stated strategy cannot establish that every run is bounded.

| FR | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | restated |
| FR-6 | implemented-as-written |

## Must-fix
- FR-5 / AC-5.5's bounded post-kill wait is missing from the plan's executable strategy — the spec requires that total wall time include a bounded `wait(timeout=DRAIN_SECONDS)` and that its expiry map to `LAUNCH_FAILED stage=reap`; the plan instead specifies “bounded drain → close pipes → `wait()`” and says only that the leader is reaped. A bare `Popen.wait()` can block indefinitely after the pipes are closed, so this silently weakens the spec's “every run is bounded” guarantee and leaves the expiry verdict/test/mutation undefined. State the timeout, `LAUNCH_FAILED stage=reap` mapping with pending `BlockTimeout` context, and its named test/mutations.

## Should-fix
None

## Nit
None
