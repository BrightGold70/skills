AUDIT-exec-path-hardening-plan-v5-BEGIN
## Summary
The plan is highly rigorous, backing its claims with live probe evidence (A1-A6) and strictly enforcing connection testability (W1-W5) to prevent blind writes and unenforced wiring. However, it misses the explicit test mandate for the no-timeout heartbeat case required by the spec, contradicts itself on the behavior of `truncated` API reads, and introduces duplicated log-appending logic without the equivalence tests demanded by the base invariants. 

| Spec FR | Plan Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | restated |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | restated |

## Must-fix
- **Spec FR-2 AC-2.4 (Axis C restated)** — The Spec explicitly mandates: "An `exec` invoked without `--timeout` ... One of the two must be pinned by a test; silence on this case is a failure." The plan states: "Unifying on one shape ... makes the heartbeat unconditional", but is completely silent on providing the mandated test. The plan is narrower because it implements the behavior but omits the explicitly required test guard for the no-timeout path.
- **Spec FR-6 AC-6.3 (Axis C restated / Axis A Contradiction)** — The Spec states: "An unreadable or truncated `worktree ps` falls back to `active` and never fails the dispatch." The plan states in the Deliverables that the resolver provides an "`active` fallback on no-match/`truncated`", but the Implementation Strategy explicitly states: "If `worktree ps` fails, times out, returns `truncated`... the checkpoint attempt is abandoned silently — no `worktree set` is issued." The plan is narrower (and internally contradictory) because it proposes unconditionally abandoning the stamp on a truncated read instead of executing a target fallback to the `active` worktree.
- **Base Invariant (Single-source contract)** — The plan implements the `--log` append contract by changing codex's `> "$log"` to `>> "$log"`, duplicating the logic already present in the agy backend. A rule applied by more than one surface must either use exactly one authoritative implementation or include a test asserting byte-equivalence across surfaces. The plan proposes neither for the log writing logic, leaving independent re-implementations that can silently diverge.

## Should-fix
- **Base Invariant (Test discrimination / Isolation)** — The new stateful orca stub persists comment values to a "temp file". Per the path-resolution invariant warning, to prevent test pollution or cross-test clobbering, this state file should be strictly isolated per-test (e.g., scoped via an environment variable that the test harness sets uniquely per run), not a global or hardcoded temp file.

## Nit
None
AUDIT-exec-path-hardening-plan-v5-END
