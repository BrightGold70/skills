## Summary
Axis C reconciliation is complete: each functional requirement is implemented-as-written by the plan.

| Spec requirement | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |

The plan nevertheless has three blocking cross-document/contract gaps that must be closed before implementation.

## Must-fix
- Dynamic-field escaping still permits an input to forge an `rc=` token on a refusal — the plan says `_field` escapes only control characters, while the paired design explicitly says spaces and other printable characters pass verbatim. Thus `--heading 'x rc=0'` can produce `DOCBLOCK: NOT_FOUND heading=x rc=0`, contradicting the plan's and AC-4.3's guarantee that no cannot-judge line carries `rc=` and misleading a key/value consumer. Define a machine-safe encoding or delimiter rule that prevents field-token injection, and add a discriminating hostile-input test and mutation; the existing newline-only mutation does not cover this case.
- AC-6.4's floor test has no specified working directory — the plan records that the `2747` baseline was run from the repository root, but specifies only a `--collect-only` subprocess for `test_suite_floor_holds`. The current design and impl-plan correctly require `cwd=REPO_ROOT` because the same command from `h-mad/` collects `2485`; without that exact requirement the floor is non-reproducible and can fail or measure a different suite. Carry `cwd=REPO_ROOT` and the root-relative collector invocation into this plan.
- The empty-`--subst` execution path contradicts the current design and impl-plan — the plan's API table says the empty-key rule lives in `substitute` and “`main` reaches the same rule through `substitute`,” whereas the design/impl-plan require `main` to reject the empty key while parsing and “never reaches it,” preserving the raw `arg==V`; `substitute` remains the separate API guard. These are mutually exclusive implementation instructions for a load-bearing CLI diagnostic. Update the plan to state the two-layer contract and its separate CLI/API tests and mutations.

## Should-fix
None

## Nit
- “five functions plus `main`, `find_heading` (all seven in `__all__`)” is grammatically and numerically unclear; list the six functions and `main` directly.
