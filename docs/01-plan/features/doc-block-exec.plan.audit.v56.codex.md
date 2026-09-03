## Summary
The plan covers every functional requirement in the supplied spec; no FR is silently narrowed or deferred. The only finding is a concrete scope/name ambiguity in the stated module-level migration recipe.

| FR | Classification | Plan coverage |
|---|---|---|
| FR-1 | implemented-as-written | Tagged, heading-scoped extraction/selection and the shared fence-aware bounder are specified. |
| FR-2 | implemented-as-written | Explicit simultaneous substitution and refusals are specified. |
| FR-3 | implemented-as-written | Declared shell modes, disposable cwd, preamble, streams, and cleanup are specified. |
| FR-4 | implemented-as-written | The verdict-line and exit-code contract is specified. |
| FR-5 | implemented-as-written | Stdlib timeout, process-group handling, and bounded draining are specified. |
| FR-6 | implemented-as-written | The tag and executing-call-site migration land together with bidirectional wire tests. |

## Must-fix
None

## Should-fix
- The module-level `_run_recipe(...)` recipe still shows `shlex.quote(str(gate))`, although `gate` exists only as a local in today’s nested `run_recipe`; the plan also says “nothing else in the file moves.” — State the replacement explicitly (for example, derive `gate` and `collector` from `SCRIPT_DIR` inside `_run_recipe`, or introduce named module constants) so the planned hoist has no unbound name and its preamble construction is implementable without inference.

## Nit
None
