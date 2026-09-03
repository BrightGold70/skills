## Summary

FR reconciliation:
| FR | Classification |
|---|---|
| FR-1 | restated |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |

The plan covers FR-2 through FR-6, but its stated authoritative scanner contract narrows FR-1 by omitting two required fence forms. Its mutation-plan references also do not provide executable named-test bindings for the two new mutation specs.

## Must-fix
- FR-1 is restated rather than implemented as written: the spec requires “including when the enclosing fence is a tilde fence … Tilde fences are tracked for bounding only” and says an opener/closer may be indented only 0–3 spaces, while the plan’s sole authoritative-bounder contract is “ignoring fenced blocks with CommonMark backtick-run tracking.” That is narrower: a backtick-only state machine can terminate a section at a heading inside a tilde fence, and the plan gives no 0–3-space rule to distinguish CommonMark fences from four-space indented code. State tilde-run and indentation handling explicitly in `fence_aware_end`’s contract and bind both to named tests/mutations.
- `h-mad/tests/mutation-specs/doc_block_exec.json` and `h-mad/tests/mutation-specs/doc_block_exec_wire.json` are promised to have per-mutation named tests, but the plan supplies neither each spec’s required `command`/`target_command` nor full pytest node IDs. The named-test harness invokes `target_command + [test]`; the table’s bare function-name labels are not runnable node IDs, and no `target_command` makes a `test` key invalid. This leaves the base mutation/test-discrimination evidence unexecutable; prescribe the exact argv and `tests/...py::test_...` binding for every new mutation, as the plan already does for `docsections.json`.

## Should-fix
- Clarify `extract(doc: str | Path, heading: str)`: explicitly say that `str` is Markdown text and `Path` is a strictly UTF-8-read document path (or narrow the type). Without this, a path supplied as `str` is indistinguishable from document content, so `DocUnreadable` behavior is not deterministic across callers.

## Nit
None
