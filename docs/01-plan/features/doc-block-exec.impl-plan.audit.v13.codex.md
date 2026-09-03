## Summary
The plan is unusually specific and aligns its scanner, CLI, and mutation-count contracts across the paired design. Task 5's connection-revert mutations, however, are not specified as type-preserving implementations, so their claimed wire-only discrimination is not credible as written.

## Must-fix
- Task 5's `wire-revert-extract` / `wire-revert-run` / `wire-revert-substitute` mechanisms do not provide type-correct replacement code — `_gate_block()` is required to return `dbe.Block`, but the described regex revert returns the extracted `str`; `_run_recipe` has `subbed` but no `script`, so the described `preamble + script` inline-run revert raises `NameError`; and a `str.replace` substitution revert likewise must construct a replacement `Block` before calling `dbe.run_block`. These mutants can fail through `AttributeError`/`NameError` or break the recipe regressions rather than solely through the named spy record, violating the stated connection-only, callee-intact discrimination and leaving the mutation plan non-executable. Specify exact replacement bodies that preserve `Block`/`RunResult`-consumer behavior (for example, construct a `dbe.Block` for the regex result and use `subbed.text` for the inline run), then verify each revert fails for the recorded missing call.

## Should-fix
None

## Nit
None
