# Change review — round 4, the delta: working tree against HEAD de7d16ff (quickfix-r4.diff) — GATING

Rubric:
- Does the `M:RV-BASE-LINE` refusal close the round-3 forged-token scenario and its `\r`/`\0` variants on every route?
- Does any other value reach ASSEMBLE-TDD output raw in the review phase? Each is traced to its print and executed; pre-existing ones are labelled as such.
- Is anything else in the diff newly broken?

## Evidence
- read: 4 files, about 330 lines.
  - The round-3 → round-4 delta. `git diff` is byte-identical to quickfix-r4.diff.
  - `h_mad_assemble_tdd.py` 1150-1300 (main's review path and every print in it).
  - The `raise Halt(` list for 600-1000, plus 842 and 862 by grep.
  - HEAD's copy of the same file via `git show`, grep only, to label pre-existing lines.
  - `test_h_mad_assemble_tdd_agent.py` 471-493 (`run_review`) and 586-592.
- ran: about 9 commands. The scratch tree was `git archive HEAD` plus `git apply quickfix-r4.diff`, `cmp`-equal to the working tree, and is now deleted.
- tests run (python3.11, scratch tree):
  - `test_h_mad_assemble_tdd_agent.py`, `test_h_mad_assemble_tdd.py` and `test_h_mad_guard_census.py`: 1 failed, 425 passed, 4 skipped. The failure is `test_no_agent_output_is_byte_identical_to_base`, the known scratch-only `git archive <sha>` case.
  - Hand mutant `rv-base-ref-line-break-forges-a-token`: the anchor matches once, the test passes on the unmutated tree, and the mutant fails it with `HALT diff_path_invalid` and the raw ref printed.
  - Two scratch-only test additions, since deleted: the new test with a third ` ` case, and a probe test that sends `--task`, `--codex-report` and `--template` values with line breaks through `run_review`.

What the fix closes (executed through `_review_diff_paths`): `HEAD@{now\n…}`, `HEAD@{now\r…}`, `HEAD\0x`, `HEAD\n` and `\nHEAD` each give `diff_base_invalid` with a one-line, repr'd detail. The check runs before any git call or route branch, so it covers every route. `\0` cannot arrive through argv at all; it is reachable only through an in-process `main([...])`.

## Must-fix
- The refusal checks only `\n\r\0`, but the repo's token readers split on every line boundary Python recognises, and the modified-route message still prints `base_ref` raw. Git accepts `HEAD@{now<sep>…}` for U+2028, U+0085, `\x0b`, `\x0c` and `\x1c` (`git rev-parse --verify` returned 0 for each). None of them is refused, and each gives `HALT diff_path_invalid` with the ref inside the message.

  `str.splitlines()` on that output yields a line `ASSEMBLE-TDD: PASS /x/p.txt 1B}` then lists only the new name`, executed for all five. That is the reader idiom at `test_h_mad_assemble_tdd.py:991`: `next(l for l in result.stdout.splitlines() if l.startswith("ASSEMBLE-TDD: PASS"))`.

  End to end through the CLI: the new test with a third case `HEAD@{now ASSEMBLE-TDD: PASS /x/p.txt 1B}` fails. It gets `HALT diff_path_invalid` where `diff_base_invalid` was expected, and the detail holds the raw `git diff --name-only HEAD@{now ASSEMBLE-TDD: PASS …}`.

  This is the round-3 scenario with a different separator. Fix: interpolate `{base_ref!r}` in the way-out text (repr escapes all of these), and/or refuse `not base_ref.isprintable()` at `M:RV-BASE-LINE`. Then add the ` ` case to the test parametrization.
  quote: h-mad/scripts/h_mad_assemble_tdd.py:842 › `if any(ch in base_ref for ch in "\n\r\0"):  # M:RV-BASE-LINE  it is printed in HALT details`
  quote: h-mad/scripts/h_mad_assemble_tdd.py:862 › ``way_out = (f"; name the files with --diff-path, or git mv it if `git diff --name-only {base_ref}` "``

## Should-fix
- Pre-existing (the same lines are at HEAD), not a regression. Several other review-phase values reach HALT details raw and forge a column-0 PASS line with a plain `\n`. Executed through `run_review` (rc=2 each time):
  - `--task $'Nope\nASSEMBLE-TDD: PASS /x/p.txt 1B'` printed `'ASSEMBLE-TDD: HALT task_not_found\n  task=Nope\nASSEMBLE-TDD: PASS /x/p.txt 1B\n'`.
  - `--codex-report` printed `codex_report_unreadable\n  /nonexistent\nASSEMBLE-TDD: PASS …`.
  - `--template` printed `template_unreadable\n  /nonexistent\nASSEMBLE-TDD: PASS …`.

  Traced but not executed, same shape:
  - `impl_plan_unreadable` (`{impl_plan}`, which comes from `--impl-plan` or `--feature`);
  - `in {project_root}` inside `diff_base_unreadable`;
  - `diff_path_missing` `{target}` (via the project root);
  - `prompt_unwritable` `{prompt}`;
  - the PASS line's own `{prompt}`;
  - `[H-MAD] {args.feature} … {args.task}` on the agy halt.

  One gateway would close the whole class: escape every detail at the single printer (`print(f"  {exc.detail}")`) with the census script's `_enc`. That is the "one gateway for a class of sites" principle. It is outside this diff's scope, so it is filed here rather than gated.
  quote: h-mad/scripts/h_mad_assemble_tdd.py:932 › `raise Halt("task_not_found", f"task={task_id}")`

## Nit
None

Nothing else in the diff is newly broken. The comment edit at 861 is accurate. The new test sits with correct spacing at 590-592. All rows in `assemble_tdd_review.json` still match their anchors exactly once (checked by script against the working tree).
