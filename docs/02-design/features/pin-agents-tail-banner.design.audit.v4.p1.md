## Summary
The design successfully maps the new tail-evidence pass into `_orca_find` between Passes 2 and 4, accurately tracking all 13 acceptance criteria from the spec. It correctly handles time-bound limits, pool scoping, and fallback semantics. However, it contradicts its own stdout safety rules by proposing an idiom that leaks the tail text to stdout, and it drops crucial verification steps required by the plan and invariants.

| Spec AC | Design Coverage | Status |
|---|---|---|
| AC-1.1 | Scenario 1 | `implemented-as-written` |
| AC-1.2 | Scenario 2 | `implemented-as-written` |
| AC-1.3 | Scenario 3 | `implemented-as-written` |
| AC-2.1 | Scenario 4 | `implemented-as-written` |
| AC-2.2 | Scenario 5 | `implemented-as-written` |
| AC-2.3 | Scenario 6 | `implemented-as-written` |
| AC-3.1 | Scenario 7 | `implemented-as-written` |
| AC-3.2 | Scenario 8 | `implemented-as-written` |
| AC-3.3 | Scenario 9 | `implemented-as-written` |
| AC-4.1 | Scenario 10 | `implemented-as-written` |
| AC-4.2 | Scenario 11 | `implemented-as-written` |
| AC-4.3 | Scenario 12 | `implemented-as-written` |
| AC-5.1 | Scenario 13 | `implemented-as-written` |

## Must-fix
- Contradiction in output routing (Axis A) — The design strictly enforces that `_orca_find` returns the bare handle on stdout. However, it defines `_orca_tail_sig` to return the tail text on stdout, then explicitly licenses calling it via `if _orca_tail_sig "$h"; then …`. Doing so will stream the raw tail text directly to `_orca_find`'s stdout, corrupting the returned handle. The caller MUST capture the output (e.g., `out="$(_orca_tail_sig "$h")" || rc=$?`).
- Dropped plan requirements (Axis A Cross-doc, Axis B Test discrimination) — The plan's Success Criteria explicitly mandated a live check (`hmad-dispatch env` resolving codex), confirming that tests fail against unfixed code (RED-before-GREEN), and stating expected failing/passing counts in the 5d dispatch. The design drops all three from its verification section, violating both cross-doc consistency and the process requirement of the Test Discrimination invariant.

## Should-fix
None

## Nit
None
