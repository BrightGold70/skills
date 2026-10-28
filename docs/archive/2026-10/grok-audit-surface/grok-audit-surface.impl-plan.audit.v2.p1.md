## Summary
The v1.2 implementation plan for `grok-audit-surface` resolves all five Cycle 1 findings: all 28 named mutation `find`/`replace` spans match the target tree at `30917a1a`, the S0 row total (169 = 28 named + 141 P-rows) and probe marker count (115) are internally consistent, and all 15 Phase-5 carry items are mapped. No Must-fix issues remain; two `class: build` Should-fix items in Task 2 and Task 7 around `smoke`'s `refusal_token` assertion for `--help` and open-input tracking across `refusal_token(mode, exc, argv)` are noted below.

## Must-fix
None

## Should-fix
- Task 2 Test 4 (`test_help_flag_prints_the_mode_token`) asserts `reason=internal:UsageError` across all nine modes without the `smoke` exception (`reason=input_unparseable:<--data value>`) — Task 2 Tests 1 and 2 include the parenthetical `smoke` exception (`reason=input_unparseable:` followed by the `--data` value) matching Design D1/D2 and AC-1.7, and Test 4 even instructs passing `--data` before `--help` for `smoke`, but its assertion line specifies `reason=internal:UsageError` unconditionally, which would fail on the `smoke` parametrization at GREEN.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › `4. `test_help_flag_prints_the_mode_token` — parametrized over the nine modes, argv `[mode, "--help"]` (`smoke`: with `--data` before it). Exit 2, stdout has no line other than the token, and the token is the mode's refusal token with `reason=internal:UsageError`.`
  quote: docs/02-design/features/grok-audit-surface.design.md › `Every parser error in the table's other eight modes prints `<TOKEN>: UNREADABLE reason=internal:UsageError` on stdout and exits 2; in `smoke` it prints `SMOKE: UNREADABLE reason=input_unparseable:<--data or "">` and exits 2, because AC-1.7 closes `SMOKE: UNREADABLE` to `input_missing:<path>` and `input_unparseable:<path>`.`
- Task 2 defines `refusal_token(mode, exc, argv)` for `smoke` as reading only `argv`'s `--data` value, whereas Task 7 and Design D1 specify that `smoke` tracks the currently open input path so the last-resort handler reports that open path — neither Task 2 nor Task 7 specifies how the open input path tracked inside `smoke(args)` is passed to `refusal_token(mode, exc, argv)` in `main()` when an unexpected exception escapes `smoke`.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › `So `refusal_token(mode, exc, argv)` takes the word after the first exact `--data` (or the `--data=` value) and gives `SMOKE: UNREADABLE reason=input_unparseable:` followed by that value, or by the empty string when argv has no `--data`.`
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › `The smoke tracks the input it has open, so the last resort's `input_unparseable:` path is that input (D1).`
  quote: docs/02-design/features/grok-audit-surface.design.md › `For `smoke` it is `SMOKE: UNREADABLE reason=input_unparseable:<path>`, where `<path>` is the input the derivation had open when the exception escaped, or the `--data` directory when none was open yet (AC-1.7 allows only `input_missing:<path>` and `input_unparseable:<path>`).`

## Nit
None
