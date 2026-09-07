## Summary
The plan is highly specific and its main task boundaries, wire pins, and verification commands are coherent. One connection-only mutation is not executable as described, so its claimed `ALL_CAUGHT` result would not establish the wire invariant.

## Must-fix
- `docsections-delegation-reverted` loads `h_mad_doc_block_exec.py` with `module_from_spec(...); exec_module(...)` while explicitly never registering that private module in `sys.modules`; Task 1's module has `from __future__ import annotations` and frozen `@dataclass` declarations, and Python 3.11's dataclass processing dereferences `sys.modules[cls.__module__]`, so this load raises `AttributeError` during import instead of preserving behaviour and making only the WIRE-PIN fail. Register the private instance under a distinct private spec name in `sys.modules` before `exec_module` (or use another behaviour-preserving connection-only revert), then re-run the mutant: otherwise the harness records a collection/refusal, not the required connection-enforcement discrimination.

## Should-fix
None

## Nit
None
