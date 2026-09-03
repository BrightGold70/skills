## Summary
The implementation plan is highly detailed, carefully translating the design constraints into strict test cases and mutation guards. While the logic and structural alignment are excellent, there are textual mismatches between the provided code deltas and the literal `find`/`replace` payloads required for the mutation harness. Fixing these mismatches will ensure the mutation specs apply cleanly without missing their anchors or introducing syntax errors.

## Must-fix
- `docsections-local-bounder-restored` find block vs Task 1 delta mismatch — The Task 1 code structure delta for `docsections.py` contains instructional inline comments (`# replaces the local re.search at :53` and `# the loud failure stays local`) which are omitted from the `docsections-local-bounder-restored` find block. Because the plan strictly requires the delta and the find anchor to be "one literal source shape", this mismatch guarantees that the literal string replacement will miss the landed source if the comments are implemented, or the delta is misleading if they are not.

## Should-fix
- `consumer-from-import` description contradiction — The text claims "the consumer's `import h_mad_doc_block_exec as dbe` spelling is replaced by a bare `from h_mad_doc_block_exec import`," but the find/replace block and subsequent text explicitly leave the alias import at line 23 untouched and instead insert the new import locally above the functions. The summary sentence is misleading and should accurately reflect that the alias is bypassed rather than replaced.
- Task 5 mutation payload indentation mismatch — The `find` and `replace` blocks for the Task 5 mutations (e.g., `wire-revert-extract`, `wire-revert-substitute`) are formatted with 8 spaces of indentation because they are nested in a markdown list. Since the plan insists that "indentation included" applies strictly to these payloads, copying them literally into the JSON spec will cause the find anchors to miss the actual 4-space indented source and introduce `IndentationError`s.

## Nit
None
