## Summary
The implementation plan is detailed and largely cross-document consistent, but Task 4 contains a direct, load-bearing contradiction about argparse failures. It would make the parser test and mutation gate enforce the opposite of the declared verdict and exit-code contract.

## Must-fix
- Resolve Task 4’s parser contract and make `test_parser_rejects_all_dir_and_abbreviations` exact — the Task 4 description, `VERDICT_TABLE`, paired plan, design, and the `argparse-error-unrouted` mutation require every unknown option/missing value (including `--all`, `--dir x`, and a rejected `--shell-t`) to produce `DOCBLOCK: BAD_ARGS` and exit 0, but the AC at `docs/01-plan/features/doc-block-exec.impl-plan.md:1143` instead requires argparse usage, exit 2, and no token. This breaches the base audit-gate signal discipline if implemented as written and makes the two tests mutually incompatible. State one outcome (the declared BAD_ARGS/0 contract), and give the abbreviation case a complete otherwise-valid argv (`doc`, `--heading`, `--shell-t 5`) so `allow_abbrev=True` reaches a different outcome rather than merely failing later on missing required arguments.

## Should-fix
- Correct the Task 4 coverage-count wording: `test_verdict_table_exit_codes` says it parametrizes all 23 `VERDICT_TABLE` heads and lists 17 subprocess plus 6 in-process producers, but immediately says it “produces each of the 22 heads for real.” The stale count obscures whether the new `BAD_ARGS` head is actually covered.

## Nit
- The `_field` code-structure docstring says it renders 18 dynamic values, while the surrounding rendering-slot accounting correctly says 19 quoted values (7 bare + 19 quoted = 26).
