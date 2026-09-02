## Summary
The design is robust, accurately addressing the execution constraints, isolating process groups for clean timeouts, and ensuring that no unintended side-effects leak into the working tree. However, it fails to include recent spec additions (such as the fixture preamble and duplicate heading rules) in its Test Plan, and contains internal contradictions in its API and error mapping tables.

| Identifier | Classification | Notes |
|---|---|---|
| AC-1.1 to AC-1.6 | implemented-as-written | |
| AC-1.7 | absent | Covered in design text, but missing from the Test Plan. |
| AC-1.8 | implemented-as-written | |
| AC-2.1 to AC-2.7 | implemented-as-written | |
| AC-3.1 to AC-3.10 | implemented-as-written | AC-3.10 is described in the AC-3.1-3.9 Test Plan row despite numbering. |
| AC-3.11 to AC-3.13 | absent | Covered in design text, but entirely missing from the Test Plan. |
| AC-4.1 to AC-4.5 | implemented-as-written | |
| AC-5.1 to AC-5.4 | implemented-as-written | |
| AC-6.1 to AC-6.6 | implemented-as-written | |

## Must-fix
- Missing Tests for Preamble and mkdtemp (AC-3.11–3.13) — The Test Plan table for `FR-3` stops at `AC-3.1-3.9`, leaving `AC-3.11` (fixture preamble), `AC-3.12` (preamble errors), and `AC-3.13` (mkdtemp constraints) completely untested. This creates a hard gap where these critical boundaries could fail silently. (Axis C `absent`).
- Missing Test for Duplicate Headings (AC-1.7) — `AC-1.7` (Duplicate headings refuse) is described in the design text but is completely absent from the Test Plan table, leaving a load-bearing refusal unverified. (Axis C `absent`).
- Contradictory `extract` API docstring — The `extract` docstring states "Raises DocUnreadable or BadInfoString only", which directly contradicts the "Scanning (`extract`)" section and Error Handling table that both require `extract` to raise `AmbiguousHeading(n)`. This creates an ambiguous contract for implementers.
- Incomplete Exception Mapping for Preamble Errors — The Verdict Lines table requires `DOCBLOCK: UNREADABLE reason=preamble_unreadable`, but the "Error Handling Strategy" table defines no corresponding exception class. This gap will cause a `KeyError` traceback in `main`'s mapping dispatcher instead of the required clean exit 2.

## Should-fix
None

## Nit
- The Test Plan table row labeled `AC-3.1–3.9` describes the unwritable stream path check (`AC-3.10`), so the row label should be updated to `AC-3.1–3.10` for accuracy.
