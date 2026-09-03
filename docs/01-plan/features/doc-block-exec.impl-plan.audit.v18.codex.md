## Summary
The implementation plan is otherwise concrete and aligned with the current design on its task structure, paths, seams, and mutation coverage. One stale paired-plan statement still contradicts the bounded timeout contract and can direct an implementation toward an unbounded reap.

## Must-fix
- The paired plan still defines the reap sequence as `poll()` → `killpg` → bounded drain → close pipes → `wait()` and its cited probe calls bare `p.wait()` (`docs/01-plan/features/doc-block-exec.plan.md:580-616`), while the design, spec, and Task 3 require `proc.wait(timeout=DRAIN_SECONDS)` with a `TimeoutExpired` mapped to `LAUNCH_FAILED stage=reap` (`docs/02-design/features/doc-block-exec.design.md:452-461`; `docs/01-plan/features/doc-block-exec.spec.md:391-393`; `docs/01-plan/features/doc-block-exec.impl-plan.md:575-581`). This is a cross-document contradiction on the portable-time-bound invariant: following the plan leaves a post-kill path unbounded and makes the new `wait-unbounded`/`wait-expiry-unmapped` tests incoherent. Update the plan’s normative sequence and measurement/prose to the bounded wait and its expiry verdict.

## Should-fix
None

## Nit
None
