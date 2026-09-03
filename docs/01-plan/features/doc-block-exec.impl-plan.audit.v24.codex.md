## Summary
The plan is unusually detailed, but its claimed executable mutation specifications are not consistently concrete. Two required mutation rows defer their exact payloads even though their anchors are in existing files and the plan says those payloads are already supplied.

## Must-fix
- Complete the exact `find` and `replace` strings for `docsections-local-bounder-restored` and `consumer-from-import` in their mutation specs (or include literal JSON rows) — both are described only as “same text”/a source range plus prose edits, while the harness requires one exact-once `str.replace` pair and the plan expressly says the existing-file `docsections.json` and `doc_block_exec_wire.json` payloads are present now. Without concrete payloads, the promised `ALL_CAUGHT` runs cannot verify that the intended connection/source guard was actually mutated, breaching the mutation-verification invariant and leaving implementation-time interpretation as a hard gap.

## Should-fix
None

## Nit
- The Task 1 delta omits `titled_section`/`section_from` docstrings, while the local-bounder-restored row says its exact find range includes those docstrings verbatim; make the delta and mutation description use the same literal source shape.
