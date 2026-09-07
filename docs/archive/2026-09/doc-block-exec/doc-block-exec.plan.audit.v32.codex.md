## Summary
The plan covers all six functional requirements, but its FR-6 migration contract is internally type-inconsistent with existing consumers of `_gate_bash_block`. Axis C reconciliation is complete at FR granularity:

| FR | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |

No spec narrowing or omission was found; the blocking item is a plan-to-current-source inconsistency rather than an Axis C divergence.

## Must-fix
- FR-6's declared two-point migration makes `_gate_bash_block` return `Block`, but the same current file has text-pin callers at `h-mad/tests/test_h_mad_collect_report_docs.py:283-284` (`.index` and slicing) and `:372` (`.splitlines`) — those operations are not defined on the planned frozen `Block`, so the stated implementation either immediately type-errors or must make unplanned edits despite saying “Nothing else in the file moves.” Specify the exact compatible shape (for example, those existing tests use `block.text`) and include those call-site edits in the FR-6 task and wire/mutation scope.

## Should-fix
None

## Nit
None
