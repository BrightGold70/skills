## Summary
`docs/01-plan/features/grok-audit-surface.impl-plan.md` (v1.1) thoroughly translates Design v1.4, Spec v1.7, Plan v1.5, D4, and the 15 Phase-5 carry items into 18 tasks with exact file paths, a 166-row mutation spec (`28` named + `138` P-rows), and concrete RED/GREEN test definitions. One Must-fix (`class: build`) remains in Task 2 where the `argparse` subparser and `refusal_token` wiring cannot preserve parsed subparser arguments (`--data`) or intercept top-level unrecognized-argument errors required by `test_usage_error_prints_the_mode_token`. Two Should-fix (`class: build`) items cover an internal signature mismatch on `extract_all` in Task 8 and stale RED/GREEN pass counts in Task 17 after carry item 8 added a seventh test to `test_grok_fallback_docs.py` in Task 16.

## Must-fix
- Task 2's `_TokenArgumentParser` and `refusal_token(mode, exc, args)` specification cannot satisfy Test 3 (`["smoke", "--data", str(tmp_path / "s1"), "--no-such-flag"]` → `SMOKE: UNREADABLE reason=input_unparseable:<tmp_path>/s1`) for two reasons: (1) in Python's `argparse`, `_SubParsersAction.__call__` runs `subparser.parse_known_args()` and returns unrecognized flags (`--no-such-flag`) to the top-level parser's `parse_args()`, so if only `add_subparsers(parser_class=_TokenArgumentParser)` uses `_TokenArgumentParser` while `build_parser()` returns a standard `argparse.ArgumentParser`, `--no-such-flag` triggers `ArgumentParser.error()` (`sys.exit(2)` with empty stdout) instead of raising `UsageError` at `# M:GAS-USAGE`; and (2) even when the top-level parser is also a `_TokenArgumentParser`, raising `UsageError` inside `parse_args(argv)` aborts before `parse_args` returns a `Namespace`, so unless `main()` pre-allocates `args = argparse.Namespace()` and passes `namespace=args` to `parse_args(argv, namespace=args)`, `args` is `None` in the `except` handler and `refusal_token` emits an empty `--data` suffix (`SMOKE: UNREADABLE reason=input_unparseable:`) instead of `<tmp_path>/s1`.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › `Every subparser is built from `_TokenArgumentParser` (`add_subparsers(parser_class=_TokenArgumentParser)`), whose `error()` prints the message on stderr and raises `UsageError` (`# M:GAS-USAGE`); the last resort then prints that mode's refusal token with `reason=internal:UsageError`. For `smoke` the D1 rule gives `SMOKE: UNREADABLE reason=input_unparseable:` followed by the `--data` value, which is the empty string when `--data` was not given.`
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › `def refusal_token(mode: str, exc: BaseException, args: argparse.Namespace | None) -> str:`
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › `["smoke", "--data", str(tmp_path / "s1"), "--no-such-flag"]` → exit 2, stdout `SMOKE: UNREADABLE reason=input_unparseable:<tmp_path>/s1`

## Should-fix
- Task 17's expected RED/GREEN pytest counts for `h-mad/tests/test_grok_fallback_docs.py` (`RED: 2 failed, 6 passed` and `GREEN: 8 passed`) are off by one because Task 16 (which always runs before Task 17 on `SEEDSCORE: PASS`) brings `test_grok_fallback_docs.py` to 7 passing tests after carry item 8 added `test_grok_runtime_documents_audit_surface_s1`; Task 17 adds 2 more tests, so its expected counts in 5d/5e are `RED: 2 failed, 7 passed` and `GREEN: 9 passed`.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › `Expected pytest result — GREEN: 7 passed.`
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › `Expected pytest result — RED: 2 failed, 6 passed.`
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › `Expected pytest result — GREEN: 8 passed.`
- Task 8's Description specifies the two-argument signature `extract_all(tree, s2_dir)` (matching Design D12, where `score` calls `extract_all(tree, s2_dir)` for re-extraction), whereas Task 8's Code structure declares `def extract_all(tree: Path, s2_dir: Path, sources: dict[str, str]) -> list[dict]: ...` with a required third parameter `sources` and no default or call-site note in Task 9 (`# M:GAS-KEY-REEXTRACT`).
  class: build
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › ``extract` per D12: `extract_all(tree, s2_dir)` (the one function `score` calls for re-extraction)`
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › `def extract_all(tree: Path, s2_dir: Path, sources: dict[str, str]) -> list[dict]: ...`
  quote: docs/02-design/features/grok-audit-surface.design.md › `The same function, `extract_all(tree, s2_dir)`, is what `score` calls for re-extraction, with `s2_dir` the score-sha tree's own `s2/`.`

## Nit
None
