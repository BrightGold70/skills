## Summary
The design successfully outlines a strict, side-effect-free test boundary for executing documented bash blocks, correctly employing `mkdtemp` and isolating the process group to ensure robust timeouts. However, the design contradicts its own API definitions, misses an error mapping for the new preamble feature, and truncates the Test Plan, leaving several late-addition Acceptance Criteria untested or narrowed.

| Spec AC | Classification |
|---|---|
| AC-1.1–1.6, AC-1.8, AC-2.1–2.7, AC-3.1–3.10, AC-4.1–4.5, AC-5.1–5.4, AC-6.1–6.6 | `implemented-as-written` |
| AC-1.7, AC-3.11 | `absent` |
| AC-3.12, AC-3.13 | `restated` |

## Must-fix
- Axis A / Internal Contradiction (extract signature) — The `Scanning` section correctly states that `extract` "raises AmbiguousHeading(n) rather than taking the first". However, the `API / Interface Changes` section provides a docstring for `extract` that explicitly claims it "Raises DocUnreadable or BadInfoString only — never on candidate count", contradicting the earlier section and precluding the `AmbiguousHeading` exception.
- Axis A / Missing Error Mapping — The `API` and `Verdict lines` sections specify that an unreadable preamble file refuses with `DOCBLOCK: UNREADABLE reason=preamble_unreadable`. However, the `Error Handling Strategy` mapping table omits any exception to map to this verdict. Since `main` dispatches based on exception type, this missing mapping will cause a preamble read failure to surface as an unhandled traceback rather than the contracted verdict token.
- Axis C / Spec Restatements and Absent Tests (AC-1.7, AC-3.11, AC-3.12, AC-3.13) — The Test Plan table stops AC enumerations at AC-3.9, entirely omitting test coverage for duplicate heading rejection (AC-1.7), preamble bounds and execution (AC-3.11/3.12), and the `mkdtemp` isolation guarantees (AC-3.13). An AC is not satisfied if its test coverage is dropped. Additionally, the design explicitly narrows the spec by:
  - Spec AC-3.12 requires "A run with a preamble reports rc/stdout/stderr for the combined invocation"; the design states the preamble is run in the same invocation but omits the explicit contract that the combined streams are captured and reported.
  - Spec AC-3.13 requires asserting that the temp dir mode is "observed from inside the running block" and that "The source contains no mktemp invocation"; the design drops these explicit test assertions entirely.

## Should-fix
None

## Nit
- Mislabeled Test Plan row — The Test Plan row labeled `AC-3.1–3.9` includes the test description for AC-3.10 ("unwritable stream path refuses and the block leaves no side effect"), meaning the label missed the AC number it actually covers.
