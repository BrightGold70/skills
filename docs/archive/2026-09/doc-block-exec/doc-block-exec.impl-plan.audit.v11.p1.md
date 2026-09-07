## Summary
The implementation plan is exceptionally thorough and robust, correctly sequencing the refactoring of fence boundaries and standardizing execution across tasks. It accurately guards the `subprocess` lifecycle and operational fault paths without leaking descriptors or masking exceptions. Minor adjustments are required to correct an inline syntax error and clarify a remnant count in the documentation.

## Must-fix
- Invalid Python syntax in `RunResult` instantiation (Task 3 prose) — The phrase `return RunResult(rc=proc.returncode, stdout, stderr, shell=block.shell)` uses positional arguments after keyword arguments, which raises a `SyntaxError`. It must be written with all keyword arguments (`rc=proc.returncode, stdout=stdout, stderr=stderr, shell=block.shell`) or entirely positional.

## Should-fix
None

## Nit
- In Task 4, the prose states "The emittable detail keys are a module-level tuple `DETAIL_KEYS`, so tests can enumerate all three" which contradicts the 10 elements defined in the code block. It should read "all 10" or "all of them".
