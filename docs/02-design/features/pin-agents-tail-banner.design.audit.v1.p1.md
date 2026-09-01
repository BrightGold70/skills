## Summary
The design successfully translates the plan into a concrete architecture, integrating the tail-evidence pass effectively without disrupting the existing Pass 0/1/2 logic. All 13 Acceptance Criteria from the spec are fully accounted for as `implemented-as-written`. However, a crucial load-bearing command flag mandated by the plan was silently dropped, which must be restored to ensure production correctness.

| AC | Classification |
|---|---|
| AC-1.1 | `implemented-as-written` |
| AC-1.2 | `implemented-as-written` |
| AC-1.3 | `implemented-as-written` |
| AC-2.1 | `implemented-as-written` |
| AC-2.2 | `implemented-as-written` |
| AC-2.3 | `implemented-as-written` |
| AC-3.1 | `implemented-as-written` |
| AC-3.2 | `implemented-as-written` |
| AC-3.3 | `implemented-as-written` |
| AC-4.1 | `implemented-as-written` |
| AC-4.2 | `implemented-as-written` |
| AC-4.3 | `implemented-as-written` |
| AC-5.1 | `implemented-as-written` |

## Must-fix
- Dropped load-bearing implementation detail from plan — The plan explicitly mandated the exact read command (`hmad-dispatch run --timeout <s> -- orca terminal read --terminal <handle> --cursor 0 --limit <n> --json`) and warned that `--cursor 0` is load-bearing; without it, the call returns the most recent rows instead of the banner at the start of scrollback. The design omits this command and the `--cursor 0` requirement entirely, which risks an implementation that passes live checks but fails in production on panes with history.

## Should-fix
None

## Nit
- `rc 1` specification for timeout — The design states `rc 1 = read failed/unreadable`, but the portable time-bounder exits `124` on timeout; ensure the script gracefully handles any non-zero exit, not strictly `1`.
