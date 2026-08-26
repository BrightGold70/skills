## Summary
The design implements the vast majority of the spec as written, cleanly integrating the new precheck functionality and enforcing directory-scoped resolution. However, Axis C (cross-doc consistency) reveals that two Acceptance Criteria (AC-2.6 and AC-6.1) were restated to drop specific required tests. Furthermore, Axis B (invariant compliance) shows a gap in connection enforcement.

| AC | Status |
|---|---|
| AC-1.1 - AC-1.5 | `implemented-as-written` |
| AC-2.1 - AC-2.5 | `implemented-as-written` |
| AC-2.6 | `restated` |
| AC-3.1 - AC-3.5 | `implemented-as-written` |
| AC-4.1 - AC-4.5 | `implemented-as-written` |
| AC-5.1 - AC-5.5 | `implemented-as-written` |
| AC-6.1 | `restated` |
| AC-6.2 - AC-6.6 | `implemented-as-written` |
| AC-7.1 - AC-7.5 | `implemented-as-written` |

## Must-fix
- Axis B (Connection enforcement) — The design explicitly plans to mutate the connection in only one direction ("remove the call alone"). The invariant requires mutating in BOTH directions: "force it to fire unconditionally -> the fall-through/negative test must fail", which is absent and leaves the fall-through untested.
- Spec AC-2.6 `restated` — Spec requires: "A test asserts the property across every committed spec, so a future spec cannot reintroduce a root above its own skill." Design specifies: "Re-root and re-prefix the handoff spec; same assertions plus its suite still green (AC-2.6)". This is narrower, dropping the repository-wide test preventing future specs from rooting above their skill.
- Spec AC-6.1 `restated` — Spec requires: "...and a test asserts the two agree so they cannot drift apart." Design states: "The mutations test is the loader's own necessary condition... not a second guess at spec shape", but drops the test that asserts the classifier and `_load_spec` mechanically agree.

## Should-fix
None

## Nit
None
