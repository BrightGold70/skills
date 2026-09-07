## Summary

The plan covers every functional requirement in the paired spec as written; no FR-level restatement or omission was found. The implementation plan is not reconciled with the current plan/design for two required FR-6 connection mutations, so its execution and verification instructions would leave those wires untested.

| FR | Classification | Plan coverage |
|---|---|---|
| FR-1 | implemented-as-written | Explicit `hmad:exec` addressing, heading selection, and authoritative fence bounding are planned. |
| FR-2 | implemented-as-written | Literal simultaneous substitution and refusal paths are specified. |
| FR-3 | implemented-as-written | Declared shell mode, disposable stdlib cwd, preamble, streams, cleanup, and error handling are specified. |
| FR-4 | implemented-as-written | The verdict-token CLI and exit partition are specified. |
| FR-5 | implemented-as-written | `Popen.communicate(timeout=…)`, process-group cleanup, and timeout validation are specified. |
| FR-6 | implemented-as-written | The tag/migration is planned together, with directional wire enforcement required. |

## Must-fix
- `docs/01-plan/features/doc-block-exec.impl-plan.md` Task 5 remains on the superseded six-row wire spec — the current plan and design require eight rows, including `wire-revert-select` and `wire-revert-substitute`, but Task 5 says “six rows below,” its WIRE-PINs spy only `dbe.extract` and `dbe.run_block`, and Phase 5f expects `mutations=6`. A consumer can therefore replace `dbe.select` with list-first/local policy or `dbe.substitute` with `str.replace` while the helper remains intact and all described Task-5 tests/mutations pass. This violates the connection-enforcement invariant and leaves the implementation plan unable to realize the plan’s FR-6 verification. Update the two existing pins to observe the required `dbe.select`/`dbe.substitute` calls and arguments, add both mutation rows, and make every Task-5 list and verification count eight.

## Should-fix
- The implementation-plan provenance header still cites design v1.50 / plan v1.52 although the current documents are design v1.53 / plan v1.55 — update it with the reconciliation above so the executable plan has an auditable source contract.

## Nit
None
