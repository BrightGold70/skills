## Summary
The implementation plan is unusually concrete, but two stated mutation/verification paths are internally inconsistent. Both defects can make a claimed mutation result misleading rather than proving the intended invariant.

## Must-fix
- `docsections-heading-lookup-reverted` restores `re.search(...)` after Task 1 explicitly removes `import re` from `h-mad/tests/docsections.py` — the mutant will fail `titled_section` with `NameError`, not because the WIRE-PIN observed the missing `_dbe.find_heading` call as claimed. Add the required `re` import within the mutation replacement (or use an import-free local selector) so the callee remains intact and the named test discriminates the connection; otherwise this violates the required connection/test-discrimination evidence.
- Phase 5f says `docsections.json` must produce `MUTATION: ALL_CAUGHT mutations=7`, while the executive summary, Task 1 acceptance criterion, and row inventory require eight rows — the completion command’s stated success token contradicts the planned artifact and can misclassify a correct eight-row run. Update the verification expectation to `mutations=8`.

## Should-fix
None

## Nit
- The version-history bullets place `v1.10` before `v1.9`; reorder them to preserve the audit trail’s chronological reading.
