## Summary
The design closely aligns with the plan and successfully addresses all 13 Acceptance Criteria from the spec without narrowing or restating any of them (all are `implemented-as-written`). However, the design contains a critical violation of the Assumption Verification base invariant by failing to cite the actual JSON output it relies upon, and it leaves a functional gap regarding how the JSON extraction translates missing keys into the required error status.

| AC | Status |
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
- Axis B (Assumption verification) — The design claims the `orca terminal read` output contains `.result.terminal.tail` and lacks `.content`/`.preview`, stating "both confirmed live". It fails to cite the actual observed JSON output to prove this. The invariant explicitly forbids this: "The evidence belongs in the document, not only in the author's terminal. A cited output is checkable by a reviewer; 'I verified this' is not."
- Axis A (Gap in error handling) — The design mandates that a read lacking the `.terminal.tail` key must return `rc 1` (unreadable), but leaves the extraction command unspecified. Standard `jq -r` outputs the literal string `"null"` and exits with `0` when a key is absent, which would silently bypass the error condition. The design must specify the exact pipeline (e.g., `jq -re '.result.terminal.tail'`) required to translate a missing key into a non-zero exit code.

## Should-fix
None

## Nit
- The design states that the Pass 4 comment ("Reached only when every pass above found nothing") "becomes false on insertion." This statement was actually already false prior to this design: an ambiguous title (`n > 1`) in Pass 1 bypassed Pass 2 and reached Pass 4 without having "found nothing".
