AUDIT-regression-provenance-ledger-design-v3-BEGIN
## Summary
The design is exceptionally thorough, successfully translating the resolve-first strategy from the plan into a pure-core/I-O-shell architecture and elegantly handling the J18 and A3 defect classes. However, the shape challenge (FR-5) lacks critical implementation details regarding task attribution and the acknowledgment mechanism, leaving gaps in how the tool will actually fulfill AC-5.1 and AC-5.3.

| Spec ID | Requirement / Acceptance Criterion | Classification |
|---|---|---|
| FR-1 | Durable wire registry (AC-1.1 to AC-1.4) | `implemented-as-written` |
| FR-2 | Standing re-verification (AC-2.1 to AC-2.5) | `implemented-as-written` |
| FR-3 | Provenance vs absence (AC-3.1 to AC-3.4) | `implemented-as-written` |
| FR-4 | Declared removal (AC-4.1 to AC-4.4) | `implemented-as-written` |
| FR-5 | Challenge undeclared wiring task (AC-5.1 to AC-5.4) | `implemented-as-written` |
| FR-6 | Registration on existing path (AC-6.1 to AC-6.3) | `implemented-as-written` |

## Must-fix
- **Missing task attribution for FR-5 (Axis A gap)** — AC-5.1 requires the challenge to identify "the task" that added the crossing and did not declare `wiring`. The design states the challenge runs at 5f comparing `BASE..HEAD`, but it does not explain how the `challenge` subcommand knows the shape of the tasks or how it maps changed files in the overall diff to specific tasks. Furthermore, the CLI arguments for `challenge` are omitted from the "API / Interface Changes" section. Without this, the tool cannot know if the file change belongs to a `wiring` task or a `new-behaviour` task.
- **Missing acknowledgment mechanism for FR-5 (Axis A gap)** — AC-5.3 and the design state that "acknowledged counts" will be reported, but the design completely omits *how* an operator actually acknowledges a challenge at 5f (e.g., adding an `## Acknowledged-not-fixed` sidecar, editing a config, or changing the task shape). Without specifying where the acknowledgment is stored and how it is read, the counts cannot be accurately implemented.

## Should-fix
- **AST extraction of BASE files** — The design states "parse the BASE and HEAD versions with stdlib ast" for FR-5, but it doesn't specify how the BASE versions of the `.py` files are retrieved for parsing (e.g., using `git show <base>:<filepath>`). Explicitly stating the read mechanism ensures it is handled correctly alongside the I/O for the registry file.
- **Handling of `missing` count for tombstoned pins** — The design implies that tombstoned pins are excluded from the `missing` set, meaning any pin in `missing` is active and therefore undeclared, neatly satisfying AC-2.4 (`missing > 0` produces FAIL). Explicitly stating that the `missing` set is derived *only* from active records would clarify this mechanic.

## Nit
- None
AUDIT-regression-provenance-ledger-design-v3-END
