## Summary
The plan is unusually concrete about paths, failure modes, and mutation execution, and its current repository references and 2,747-test collection baseline check out. However, Task 5 declares helper-mediated selection and substitution connections that its proposed tests and mutations do not actually discriminate.

## Must-fix
- Task 5 leaves `dbe.select` and `dbe.substitute` as unpinned declared wires — `test_gate_block_resolves_through_doc_block_exec` spies only on `extract`, so `_gate_block` can manually implement the empty/list-first policy; `test_recipe_runs_through_run_block` only observes the resulting block and `run_block`, so a direct `str.replace` can replace `dbe.substitute`. Both variants preserve the specified assertions and all six wire mutations, while removing the helper connection with the callee intact. This violates connection enforcement. Spy on `dbe.select` and `dbe.substitute` in the existing wire pins (including their required arguments/results) and add selective `wire-revert-select` / `wire-revert-substitute` mutations bound to those pins; retain the existing negative test for tag-gating.

## Should-fix
- Task 1 publishes future exception names in `__all__` but explicitly does not define them until Tasks 2–4 — `from h_mad_doc_block_exec import *` will fail during the Task-1 green state. Either define the complete exception hierarchy in Task 1 or add symbols to `__all__` only in the task that defines them.

## Nit
- The provenance header identifies the source design as v1.50 even though this plan relies on the v1.51 prose-only heading rule; update the cited design revision/commit so the audit trail identifies the actual source contract.
