# Change review — `git diff 239d9ab9 HEAD` (HEAD aed1cae4, answers Should-fix 1, 2, 3 of rows-review3) — GATING

Told neither GATING nor ADVISORY, so GATING is assumed. Paths are relative to the worktree `rows-review`. "old" is 239d9ab9, "new" is aed1cae4, both extracted with `git archive`.

**Bottom line: clean against your Must-fix bar.** All three Should-fixes are FIXED. This delta adds no wrong verdict, false pass, tokenless crash, or breakage on an input that occurs in this repo. The re-anchored rows kill for the intended reason, and the new tests fail when the fix is reverted. Two low-priority Should-fixes remain. Only the first is a false zero, and it predates this delta.

## Evidence
- read: 6 files (the 2 scripts, 2 test files, 2 specs) in the changed spans, plus `references/helper-scripts.md:25`, `SKILL.md:1767` and rows-review3 · ran: 15 Bash calls, all sequential, using absolute paths and subprocess `cwd=` under a checked scratch directory · worktree `git status --short` empty after every call that printed it, including the last.
- tests run, on a scratch clone at aed1cae4 (the worktree was never mutated):
  - The harness with `--only` on the 6 rows, which also runs each spec's own baseline command.
  - `test_a_shell_shebang_beats_the_document_allow_list`, `test_a_python_shebang_beats_the_document_allow_list`, `test_a_dot_beside_another_path_still_names_everything`, `test_a_path_naming_the_whole_repo_matches_everything`, `TestReviewPhase::test_a_base_ref_name_with_a_line_break_is_refused_on_every_route`.
  - `tests/test_h_mad_guard_census.py` with `-x`, under one hand mutant.
  - The full suite was not run, as instructed.

## Must-fix
None

## Should-fix

- (1) Low priority, not a regression. The fix stops at sh and python, so another interpreter's shebang under an allow-listed name still reads as a document. This is a false zero in the same class as rows-review3 Should-fix 1, and the documents say otherwise. Input: `fsmonitor-watchman.sample` and a suffixless `plain`, both `#!/usr/bin/perl`, each gaining an `if`. Old and new give the same result: `files=0 … other=1 unmeasured=1`, `UNMEASURED: plain`, `DONE decision=0`, and the `.sample` is listed nowhere. That file name is real: `fsmonitor-watchman.sample` is `#!/usr/bin/perl` in this machine's git hook templates, while the other 13 samples are `#!/bin/sh`. No such file exists in this repo: 0 allow-listed blobs at HEAD start with `#!`. That is why it is not a Must-fix. Fix: return `unmeasured` for any remaining `#!` just before the allow-list test. Going by that same zero count, this changes nothing here.
  quote: h-mad/scripts/h_mad_guard_census.py:548 › `if suffix in DOC_SUFFIXES or name in DOC_NAMES:`
  quote: h-mad/references/helper-scripts.md:25 › `anything else (`.ts .vue .r`, an unknown suffix, `Makefile`, another shebang)`

- (2) Low priority, fail-safe, and a direct consequence of the fix. An allow-listed name with a sh or python shebang is now read as source, so if its HEAD side is not UTF-8 or does not parse, the whole census is refused. Old gave DONE, new gives `UNREADABLE reason=unreadable-file`, rc=2. Inputs run: a `.zip` with a `#!/bin/sh` head and no NUL (git does not call it binary), a Python 2 `tool.py.backup`, and a Latin-1 `old.sh.txt`. It has a token and is not a false pass, and a suffixless file with the same bytes is already refused the same way in both old and new (control run). None of this occurs here: 0 such blobs at HEAD, and 40 of 40 first-parent commits replayed identically. It is worth knowing rather than fixing, unless `.backup` or `.original` scripts start to appear.
  quote: h-mad/scripts/h_mad_guard_census.py:544 › `if SHELL_HEAD.match(first):`

## Nit

- `--path . --path nope` used to be `UNREADABLE reason=path-no-match` and is now DONE over the whole diff. `--path . --path ../x` used to be `reason=git` and is now DONE too. The sentence in `helper-scripts.md:25`, "one that matches no change, or lies outside the repo, is `UNREADABLE reason=path-no-match`", now has an unstated exception beside a dot. See question 3 for why this does not matter.
- The way-out message offers "gitignore it" on a tracked name as well, where it does nothing. Executed: with `Icon?` in `.gitignore`, `git diff --name-only HEAD` still prints the tracked `Icon\r`. The message offers alternatives, and `--diff-path` avoids the `--base-ref` listing altogether. Run on an untracked `Icon\r`, it gave PASS, as did rename and gitignore.
- The census of this delta lists `h_mad_guard_census.py:548` and `:549` as unanchored, because they moved. This is not a gap in the tests: deleting those two lines fails `test_documents_and_data_are_not_unmeasured_code` (`1 failed, 52 passed`, with `-x`). Only a mutation row is missing.

## 1. The three reproductions

| rows-review3 finding | Verdict | Old | New |
|---|---|---|---|
| Should-fix 1: `pre-commit.sample`, `rc`, `run.conf` with shebangs, each gaining an `if` | FIXED | `files=0 … other=3 … decision=0` | `files=3 … other=0 … decision=3 unanchored=3`, listing `pre-commit.sample:3`, `rc:3`, `run.conf:3` |
| Should-fix 2: `--path . --path sub` | FIXED | `files=1 decision=1`, `sub/a.py:2` only | `files=2 decision=2`, `b.py:2` and `sub/a.py:2`, identical to `--path .`. `--path sub --path .` and `--path <abs top> --path sub` also give `files=2`. |
| Should-fix 3: untracked `Icon\r` under `--base-ref` | FIXED | `HALT diff_path_invalid`, `… and one line` | Same halt, rc=2, no prompt written, message ends `… and one line; rename or gitignore it, or name the files with --diff-path` |

For Should-fix 3 all three ways out were executed from the `Icon\r` state on new: gitignore, rename and `--diff-path` each gave `ASSEMBLE-TDD: PASS`, rc=0. The refusal itself still stands, and a plain `--diff-path 'a\nb.py'` keeps the short message, as intended.

## 2. Moving the shebang check ahead of the allow-list

**Real files: no change.** `_language` old against new over every blob of `git ls-tree -r HEAD`: 6,522 blobs (6,525 entries less 3 gitlinks), `old!=new: 0`. The new tally is `other` 5,763, `py` 650, `sh` 33, `unmeasured` 76. The reason is direct: 0 allow-listed blobs start with `#!`. A whole-output census replay of 40 first-parent commits, old against new, gave 40 identical and none differing.

**Binary allow-listed file: unaffected when git calls it binary.** `_language` alone would return `sh` for `a.png` holding `#!/bin/sh\n\0\xff`, but `census` skips `ch.binary` before `_language` is reached. Executed: a real PNG and a shebang `.zip` with a NUL both give `binary=1`, DONE, old and new alike. The only change is a shebang file git treats as text with non-UTF-8 bytes (Should-fix 2). `%PDF` and PNG magic stay `other`.

**Empty file: no change.** The first line of `b""` is `b""`, so nothing matches. `.txt`, `.conf` and `rc` stay `other`, `noext` stays `unmeasured`, `.py` stays `py`, `.sh` stays `sh`. The 299 empty blobs at HEAD are all unchanged.

The per-side reading is correct at both ends:
- A shebang `.conf` emptied: old `other=1`; new measures the base side, `removed=1`.
- An empty `.conf` that becomes Python: old `other=1`; new lists `e.conf:2` and `e.conf:3`.

A prose `.md` that opens with `#!/bin/sh` now yields candidates (`note.md:4`, `note.md:5`). That is over-reporting, so it is fail-safe, and no such file exists here.

## 3. `wanted = []` when `.` is present

It does change the check, and it does not matter. With a dot present, `wanted` is empty, so `for want in wanted` never runs and a sibling that matches nothing is no longer refused:

| Arguments | Old | New |
|---|---|---|
| `--path nope` | `path-no-match` | `path-no-match` |
| `--path sub --path nope` | `path-no-match` | `path-no-match` |
| `--path . --path nope`, `--path nope --path ./`, `--path . --path unchanged` | `path-no-match` | DONE, `files=2 decision=2` |
| `--path . --path ../x` | `reason=git` | DONE, `files=2 decision=2` |
| `--path . --path /etc` | `path-no-match` | `path-no-match` (refused while normalising, before the check) |

This cannot produce a false pass. The scope with a dot is the whole diff, a superset of whatever the sibling could have selected, so no candidate is lost and the typo can only add lines. Both changed files were listed in every DONE row above. The old refusal was the less correct of the two, since it treated `.` as narrower than itself. No script in the repo passes `--path` to the census (`grep` over `h-mad/scripts` and `SKILL.md`). Only the document sentence is affected (Nit 1).

## 4. Re-anchored and new rows

`--check-anchors` on both specs: `ANCHORS_OK specs=2 mutations=116 ok=116 drifted=0 unreadable=0`. The harness, run on the clone with `--only`: `ALL_CAUGHT` for both specs (3 of 3 each), `survived=0`, `hollow_kills=0`, `untargeted=0/3`, each killed by its named test.

The harness only reports a kill, so each mutant was also applied by hand and its failure text read:

| Row | Failure printed | Intended reason? |
|---|---|---|
| `rv-git-changed-names-unchecked` | `[modified-newline]` only: `ASSEMBLE-TDD: PASS … p.txt`, `assert '' == 'diff_path_invalid'` | Yes: the name reached the prompt |
| `rv-git-untracked-names-unchecked` | `[untracked-newline]` only: same text | Yes |
| `path-naming-the-repo-is-a-pathspec` | `[.]`, `[./]`, `[ABS]`: `--path '.' matches no change between the refs` | Yes, this is the row's stated mechanism |
| `rv-git-name-no-way-out` (new) | All 6 params: `a name git printed needs a way out`; the halt reason assertion passes first | Yes |
| `doc-allow-list-beats-shebang` (new) | All 3 params: `assert 0 == 8` | Yes: a script reads as a document |
| `dot-narrowed-by-sibling-path` (new) | `assert ('b.py:2' in {'sub/a.py:2': …})` | Yes: the silent narrowing itself |

Reverts, with controls green first (census tests `5 passed`, assembler test `6 passed`):

| Revert | Result |
|---|---|
| Exact pre-fix `_language` text | `4 failed, 1 passed`: both shebang tests fail, the dot test passes |
| Exact pre-fix `wanted` line | `1 failed, 4 passed`: only the dot test fails |
| Only python moved back behind the allow-list | `1 failed, 4 passed`: only the python test, `assert 'run.conf:3' in {}` |
| Only shell moved back behind the allow-list | `3 failed, 2 passed`: only the shell test |
| Way-out argument removed from the call | `6 failed`: the way-out assertion |

So each half of the fix is pinned separately. A row's narrowed `find` (`for name in changed + fresh:`) still matches once.

## Not covered

- Linux. Other repositories for the Should-fix inputs. History beyond 40 first-parent commits.
- Real `codex` and `agy`: nothing dispatched. Should-fix 3 was run with the test module's own plan and report text.
- Rows other than the 6 named were anchor-checked only, not scored.

## Reviewer note

My first census driver hit `reason=spec-dir` on every case because its fixture had no spec file. It measured nothing, so I added the spec the real tests use and re-ran it. My first assembler driver halted `review_option_not_applicable` on a wrong flag and was re-run the same way. The results above come from the re-runs. All scratch work stayed under one directory, which I removed before finishing.
