## Summary
The plan cleanly and comprehensively maps all Functional Requirements from the specification to an implementation strategy, architecture considerations, and a detailed test and mutation matrix. The execution bounds, artifact stream handling, and wiring migrations are rigorously defined without contradiction or invariant violation.

| Functional Requirement | Classification | Details |
|---|---|---|
| FR-1 | `implemented-as-written` | The plan covers explicit opt-in addressing by document, heading, and tag, including duplicate heading refusal and the single authoritative bounder. |
| FR-2 | `implemented-as-written` | The substitution map implementation, its literal overlapping-key refusal, and parser contract are accurately laid out. |
| FR-3 | `implemented-as-written` | Temporary directory execution, output stream truncation/append semantics, preamble file parsing, and exact `tempfile.mkdtemp` mechanisms are specified in full. |
| FR-4 | `implemented-as-written` | The single `DOCBLOCK:` output format, detail lines, and rigid exit code partition (0 for verdicts, 2 for operational errors) align completely with the spec. |
| FR-5 | `implemented-as-written` | The internal time bounding is detailed, explicitly respecting invariants against external CLI dependencies, alongside safe process group reaping paths. |
| FR-6 | `implemented-as-written` | The targeted extraction migration covers the executing harness, retaining the text-scan for the non-executing target, backed by bidirectional wire discrimination tests. |

## Must-fix
None

## Should-fix
None

## Nit
None
