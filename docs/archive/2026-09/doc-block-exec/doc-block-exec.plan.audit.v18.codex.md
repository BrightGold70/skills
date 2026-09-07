## Summary
The plan implements FR-1 through FR-6 as written, but its prescribed conversion of `docsections.json` to named-test scoring is not executable. The bare test names it supplies are not valid pytest node IDs for the mutation harness.

| FR | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |

## Must-fix
- The `docsections.json` migration tells the implementer to put bare names such as `test_a_fenced_comment_does_not_end_the_section` (and the delegation test) in each `test` field, while its `target_command` is `['python3.11', '-m', 'pytest', '-q']` — the harness runs `target_command + [test]`, so this invokes pytest with a nonexistent path rather than the named test. Require the full node IDs (for example, `tests/test_docsections.py::test_a_fenced_comment_does_not_end_the_section`) for all five rows; otherwise the planned mutation evidence cannot prove that its stated test ran and failed, violating the mutation-verification and test-discrimination invariants.

## Should-fix
None

## Nit
None
