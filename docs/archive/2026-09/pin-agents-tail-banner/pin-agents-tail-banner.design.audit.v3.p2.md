## Summary
The design is solid, defensively bounds the terminal reads, and incorporates the required fixes from earlier audits. Spec reconciliation confirms all 13 Acceptance Criteria are addressed. However, there is an internal contradiction and undocumented plan drift regarding the candidate pool (`$ids` vs `$scoped`) that must be resolved.

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
- Contradiction and silent plan drift in candidate pool logic — The plan dictates the pass runs "over `$scoped`" for both 0 or >1 survivors. The design silently drifts from this by narrowing the `n > 1` pool to `$ids` (Pass 1's ambiguous matches). It then contradicts itself when justifying the `n == 0` pool, claiming "Passes 1–2 are MATCHERS, not filters; they removed nothing from consideration" — if they removed nothing, the `n > 1` pool must *also* be `$scoped`. The design must pick one consistent pool (likely `$scoped` unconditionally) that aligns with the plan, or explicitly document and justify the narrowing.

## Should-fix
- Missing component definition for AC-5.1 — The Test Plan correctly verifies that the 2000-line retention cap is documented at the pass (AC-5.1), but the "Components Changed / Added" table omits this comment (it only lists the Pass 4 comment adjustment). Add it to the components table to ensure the implementer writes it.

## Nit
- Env var scope creep — The plan specified `--timeout <s>`; the design upgrades this to an environment-configurable `${HMAD_TAIL_READ_TIMEOUT:-2}`. It's a sensible defensive pattern, but technically undocumented in the plan/spec.
