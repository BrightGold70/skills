# Change review — round 2, the remediation: working tree against HEAD de7d16ff (quickfix-r2.diff, 7 files) — GATING

Rubric: does the remediation close round 1's two must-fixes, its should-fix and its nits, and does it break anything new? The coordinator asked for five checks: the conditional wording, how the prefix binding compares with argparse's own abbreviation handling, whether the replaced rows are real mutants killed for the right reason, regressions, and files and lines read.

## Evidence
- read: 6 files, about 330 lines.
  - The whole round-2 diff (276 lines). `git diff` of the working tree is byte-identical to it.
  - `h_mad_assemble_tdd.py`, via grep: 852-854, 1064, 1073.
  - `test_h_mad_assemble_tdd_agent.py`, via grep: 809-811.
  - `assemble_tdd_review.json` and `guard_census.json`, read in full by script for the anchor counts.
  - `host_runtime_docs.json`: root and file list only.
- ran: about 15 commands.
  - The main tree is still locked, so I built a scratch tree from `git archive HEAD conftest.py pytest.ini h-mad` plus `git apply quickfix-r2.diff`. `cmp` showed all 7 files the same as the working tree. The scratch tree is deleted.
  - Every `find` in `assemble_tdd_review.json`, checked against its own `file`, matches exactly once.
  - I applied each changed or new row by hand, one at a time, in the scratch tree, then ran its named test. This is not the harness: each mutant was a string replacement restored in a `finally`. Rows checked: `rv-git-changed-names-unchecked`, `rv-git-untracked-names-unchecked`, `rv-tracked-name-offers-a-dead-way-out`, `rv-dash-valued-diff-path-is-a-usage-error`, `rv-dash-rewrite-swallows-an-abbreviated-option`, `rv-deleted-name-offered-git-mv`, `rv-dash-rewrite-ignores-an-abbreviated-flag`, `census-passes-a-climbing-relative-path-to-git`.
- tests run (python3.11, scratch tree, `HMAD_MUTATION_PYTHON` set): `test_h_mad_mutation_harness.py`, `test_h_mad_guard_census.py`, `test_h_mad_assemble_tdd_agent.py` and `test_h_mad_assemble_tdd.py` together gave 3 failed, 730 passed, 4 skipped. All 3 failures come from the scratch tree:
  - The anchor sweep shows `assemble_tdd_review.json ok ok=46/46` and `guard_census.json ok ok=76/76`. The drifted specs are `fr9_drive_refusals` 0/9, `grok_audit_surface` 236/465 and `host_runtime_docs` 5/7. All of them name files under `../docs/` or `../handoff/`, which the archive left out.
  - `test_no_agent_output_is_byte_identical_to_base` runs `git archive` on a sha that does not exist in the scratch repo.

Round-1 items, re-checked:
- Must-fix 1 (anchor drift) is closed. Both re-anchored rows match once. Each mutant fails its named test because a prompt was written: `AssertionError: ASSEMBLE-TDD: PASS …/p.txt` where `HALT diff_path_invalid` was expected. That is the right reason, since the name check was skipped.
- Must-fix 2 (wording) is closed for the routes the test covers. The coordinator's correction holds. In a scratch repo, with base `HEAD~1`, after `git mv` on each name:
  - `seq 1 50` → `seq 1 51` (big): dropped out of the listing (a rename was detected).
  - `v1` → `v2` (small): stayed, as a deleted name. The message then changed to `; name the files with --diff-path`, which is accurate.
  - `git diff --name-only -z HEAD~1 --` printed `added_ok.py|big_ok.py|small\nbad.py|small_ok.py|`.
- Every new or changed row is killed for its stated reason:
  - tracked-dead-way-out: the halt text contains `rename or gitignore`.
  - deleted-offered-git-mv: the deleted halt contains `git mv it if …`.
  - The three dash rows: argparse prints its usage error.
  - census row: `fatal: ../x: '../x' is outside repository` / `reason=git`.
  - Each test passed on the unmutated tree (the baseline).
- Prefix binding against argparse, run on the real parser obtained from `main()`. The parser has `allow_abbrev True`, and only `--diff-path` starts with `--d`. Results:
  - `--diff`, `--d`, `--di`, `--diff-p` with `-x` all give `diff_path=['-x']`.
  - `--diff=-x` is untouched and works.
  - `--diff=a -x` is untouched; it was `unrecognized arguments: -x` before and still is.
  - `--diff --agen codex` is untouched and refused as `expected one argument`.
  - `-diff -x` is untouched, because it is a single-dash token.
  - `--diff-pathx -x`, `--e -x` (argparse's own `ambiguous option`), `--diff --`, `--diff -h`: all untouched.
  - `--diff -` already parses.
  - `--diff -dash.py --diff b.py` gives `['-dash.py','b.py']`.
  - 3.11 agrees on the cases sampled.
  - The rule `[o for o in options if o.startswith(token)] == [flag]` refuses to bind when another option is an exact prefix of the flag. argparse would pick that exact option, so the two agree. No such option exists today.

## Must-fix
None

## Should-fix
- The modified-route message is wrong for a name added after the base (status `A` against the base, which `changed` includes because it does not filter on `--diff-filter=M`). The message says `git mv` helps only "if git will read the change as a rename", and the comment says "the base still holds it; gitignore never helps". For an added name neither is true. The base has no side to pair with, so `git mv` always removes the name. `git rm --cached` plus gitignore removes it too.

  Executed with base `HEAD~1` and HEAD adding a 2-byte `added\nbad.py`:
  - Before the fix: `HALT diff_path_invalid ; name the files with --diff-path, or git mv it if git will read the change as a rename`.
  - After `git rm --cached` and `.gitignore` = `added*`: `OK ['.gitignore']`.
  - In the second repo, `git mv` of the added name also removed it from the listing regardless of similarity.

  A user who reads the condition literally ("this is not a rename") skips a way out that always works. Fix: compute `added = set(_git_names(... "--diff-filter=A" ...))` alongside `gone`, and offer added names `; rename or gitignore it (git rm --cached), or name the files with --diff-path`. Alternatively, drop the condition and the "never" from the modified wording. A test case for an added-since-base name would pin it.
  quote: h-mad/scripts/h_mad_assemble_tdd.py:852 › `for name in changed:  # M:RV-TRACKED-WAY-OUT  the base still holds it; gitignore never helps`
  quote: h-mad/scripts/h_mad_assemble_tdd.py:854 › `else "; name the files with --diff-path, or git mv it if git will read the change as a rename")`

## Nit
- The conditional "if git will read the change as a rename" gives the user no way to check it. Adding something like "(`git diff --name-only <base>` then lists only the new name)" would make it actionable without guessing at similarity thresholds.
- The `_bind_dash_values` docstring still describes only `FLAG -x`. The abbreviated-flag binding is documented only in the inline comment at line 1073 (`# argparse also takes an unambiguous prefix (`--diff`)`). One docstring clause would cover it.
