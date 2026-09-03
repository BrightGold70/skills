## Summary
The plan is detailed, but several task boundaries and RED claims conflict with the current consumer and paired design. In particular, its staged single-source migration and Task 6 recipe wiring are not implementable or discriminable as written.

## Must-fix
- Tasks 1 and 2 split the authoritative-bounder migration even though the paired design requires it in Task 1 — after Task 1 is declared GREEN, `extract`/`fence_aware_end` and the still-local `docsections._fence_aware_end` independently implement the same fence rule. That is a temporary breach of the single-source contract and contradicts the design’s explicit author-together order; merge the delegation, its tests, and `docsections.json` update into Task 1, or make Task 1 incapable of closing before all of them land.
- Task 2’s promised RED evidence cannot occur as described — current `docsections.py` has no `_dbe`, so `monkeypatch.setattr(docsections._dbe, ...)` raises `AttributeError`, not the required call-record assertion; both proposed isolated-import tests also pass against the unchanged module, which imports only stdlib `re`. Specify a RED-safe spy scaffold (or correct the RED classification), and add a scoped mutation of the self-contained `sys.path` setup that the isolated-cwd test demonstrably kills.
- Task 6 treats `run_recipe` as an importable module-level function, but it is currently nested inside `test_documented_gate_recipe_halts_instead_of_gating_an_empty_path`. A separate `test_recipe_runs_through_run_block` therefore has no callable to spy on. The task must explicitly hoist it to a named module-level helper, update its existing caller, and state the exact signature and return-type migration.
- Task 6 also drops the checkout-path rewrite needed by the current recipe: its proposed `dbe.run_block(_gate_block(), ...)` executes the fence’s installed `~/.claude/skills/.../h_mad_audit_gate.py` path, whereas the paired plan requires `dbe.substitute(..., {installed_path: shlex.quote(str(gate))})` before `run_block`. Without that explicit step, the delivered-path test can exercise an installed copy or fail on a bare checkout, contrary to the stated scope.
- `timeout=…` in Task 6 is an unresolved placeholder, and no acceptance test pins the value passed to `run_block`. Replace it with the exact intended argument (or deliberately rely on the documented default) and assert it in the WIRE-PIN; the current code block is not an implementable contract.

## Should-fix
- Correct the task accounting: Task 3 names nine individual tests while claiming “all eight tests,” and Task 2 says `test_docsections.py` gains one test while also requiring a distinct unbalanced-four-backtick test there. These mismatches weaken the stated RED split and the suite-floor accounting.

## Nit
None
