## Summary
The design accurately translates the spec and plan into a robust architecture, capturing all Acceptance Criteria exactly as written (`implemented-as-written`). However, there are two contradictions in the API and error handling strategies: `extract` has a return type of `list[Block]` despite raising exceptions when exactly one block isn't found, and the exception handling in `main` omits the `UNREADABLE` cases. These gaps must be closed to maintain the required invariants.

| Spec AC | Design Classification | Notes |
|---|---|---|
| AC-1.1 - 1.6 | `implemented-as-written` | Tagged selection and edge cases fully mapped |
| AC-2.1 - 2.5 | `implemented-as-written` | Substitution logic and occurrence counts covered |
| AC-3.1 - 3.9 | `implemented-as-written` | Execution environment, streams, and pre-checks covered |
| AC-4.1 - 4.5 | `implemented-as-written` | Verdict token logic and no-count rules mapped |
| AC-5.1 - 5.4 | `implemented-as-written` | Process group timeout correctly defined |
| AC-6.1 - 6.6 | `implemented-as-written` | Wire migration tests fully addressed |

## Must-fix
- Contradiction in `extract` return type — The API section types `extract` as returning `list[Block]`, but the Error Handling Strategy states that `extract` raises `BlockNotFound` (for 0 blocks) and `AmbiguousBlock` (for >1 block without an index). If `extract` enforces finding exactly one block and raises otherwise, its return type must be `Block`.
- Missing exception mapping for UNREADABLE — The Error Handling Strategy claims `main` catches exactly `BlockNotFound`, `AmbiguousBlock`, `BadInfoString`, `MissingSubstitution`, and `BlockTimeout`. However, the verdict table specifies an `UNREADABLE` verdict for `doc_unreadable` and `stream_path_unwritable`. If standard IO exceptions aren't explicitly caught and mapped to `UNREADABLE`, an unwritable stream path or missing document will raise an untranslated traceback, breaking the "Audit-gate signal discipline" invariant.

## Should-fix
None

## Nit
None
