## Summary
Axis C reconciliation classifies every spec acceptance criterion as implemented-as-written; the table below enumerates all 49 criteria. The design nevertheless leaves an unbounded child wait on a timeout path, so its claimed wall-time bound is not actually guaranteed.

| Acceptance criteria (each) | Classification |
|---|---|
| AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-1.7, AC-1.8, AC-1.9 | implemented-as-written |
| AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5, AC-2.6, AC-2.7, AC-2.8 | implemented-as-written |
| AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5, AC-3.6, AC-3.7, AC-3.8, AC-3.9, AC-3.10, AC-3.11, AC-3.12, AC-3.13, AC-3.14 | implemented-as-written |
| AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5, AC-4.6 | implemented-as-written |
| AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5, AC-5.6 | implemented-as-written |
| AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5, AC-6.6 | implemented-as-written |

## Must-fix
- The timeout recovery calls `proc.wait()` with no timeout whenever `killpg` succeeded or the group was already gone, while claiming the run is bounded by `timeout + DRAIN_SECONDS` — a successful `killpg(SIGKILL)` is not a completion deadline for `wait()`, so this branch can block indefinitely and violates FR-5/AC-5.5 plus the base Portable time bounds invariant. Specify a bounded `wait(timeout=...)` recovery path (including its `TimeoutExpired` outcome and cleanup/precedence), then add a discriminating test and mutation; the existing OSError-only wait test does not prove this bound.

## Should-fix
None

## Nit
None
