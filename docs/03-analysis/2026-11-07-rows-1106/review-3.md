# Change review — `git diff 695cdde7 HEAD` (HEAD 239d9ab9, remediation of rows-review2) — GATING

Told neither GATING nor ADVISORY, so GATING is assumed. Paths are relative to the worktree `rows-review`. Each finding is tagged CONFIRMED (executed) or PLAUSIBLE (read only). "REGRESSION" means the same input gave the right result at 695cdde7, run side by side.

**Bottom line.** Both Must-fixes and all 15 Should-fixes from the prior report are FIXED. This delta adds no wrong verdict, crash without a token, or breakage on an input that occurs today. It adds one fail-open defect worth fixing before landing (Should-fix 1), which is a two-line change. The other findings are low-priority.

## Evidence
- read: all of the diff for `h_mad_assemble_tdd.py`, `h_mad_branch_evidence.py`, `h_mad_guard_census.py` and `h_mad_mutation_harness.py`; `_sweep`, `_isolate` and `main` of the harness; `_full_suite`; `_census_removed`, `_changed_lines` and `_text` of the census; entries 24, 25, 34 and 89 of `helper-scripts.md` in part; the new harness tests and the review fixtures. The 4 spec diffs were checked by `--check-anchors`, not read row by row.
- ran: about 16 Bash calls carrying about 130 driver runs on disposable repos; the prior tools at 695cdde7 side by side where a regression is claimed; `_language` old against new on every text blob of this repo's HEAD tree (5,992 non-test blobs); a 40-commit census replay of this repo's history, old against new.
- tests run: `h-mad/tests/test_h_mad_assemble_tdd_agent.py test_h_mad_branch_evidence.py test_h_mad_guard_census.py test_h_mad_mutation_harness.py test_h_mad_skill_budget.py` under `/opt/anaconda3/bin/python3.11`: `595 passed in 260.63s`.
- `--check-anchors` on the 4 changed specs: `ANCHORS_OK` 40/40, 72/72, 73/73, 125/125.

## Must-fix
None

## Should-fix

Ranked. All CONFIRMED.

- (1) REGRESSION, fail-open. The new allow-list runs before the shebang check, so a script with an allow-listed suffix or name reads as a document, and every decision line in it disappears. Input: three modified files, `pre-commit.sample` and `rc` with `#!/bin/sh` and `run.conf` with `#!/usr/bin/env python3`, each gaining an `if`. HEAD: `files=0 … other=3 … GUARD-CENSUS: DONE decision=0 anchored=0 unanchored=0 removed=0`. 695cdde7: `files=3 … DONE decision=4 anchored=0 unanchored=4 removed=1`, listing all four lines. The docstring and the entry both still say "of any name", and this delta's own stated principle is "fail closed". Not ranked Must-fix because no such file exists here today: old and new `_language` agree on all 5,992 HEAD blobs (old `_language`, shebang first, gave zero differences), and the 40-commit replay shows none. It is also counted on `other=`, not wholly silent. The orchestrator may rank it higher, because it is a false zero and not a fail-safe. Fix: test `SHELL_HEAD` and `PY_HEAD` before the allow-list. Going by that same zero-difference result, this changes nothing on this repo. Command: `shebang-doc` in the census driver, old and new.
  quote: h-mad/scripts/h_mad_guard_census.py:543 › `if suffix in DOC_SUFFIXES or name in DOC_NAMES:`
  quote: h-mad/references/helper-scripts.md:25 › `` `.py` or a `#!` python script of any name is Python ``

- (2) New in this delta, fail-open, but needs an unusual argument list. `--path . --path sub` drops the `.` and narrows to `sub`, although `.` "names everything". Input: `b.py` and `sub/a.py` changed. `--path .` gives `files=2 decision=2`; `--path . --path sub` gives `files=1 decision=1`, with nothing saying `b.py` was left out. 695cdde7 refused this with `UNREADABLE reason=path-no-match`, so a wrapper that appends paths to a default `.` now loses scope with no sign of it. Fix: if any entry normalises to `.`, set `wanted = []`.
  quote: h-mad/scripts/h_mad_guard_census.py:572 › `wanted = [w for w in (_repo_relative(top, p, "path-no-match") for p in paths) if w != "."]`
  quote: h-mad/references/helper-scripts.md:25 › `` `.`, `./` and the repo top name everything ``

- (3) Fail-safe, and the only legitimate-name refusal found. A macOS custom-folder icon file is literally named `Icon\r`, so one untracked `Icon\r` halts the whole `--base-ref` review with `HALT diff_path_invalid`, rc=2, although the same output labels untracked files "may be foreign to this task". 695cdde7: PASS. No line break can safely enter the prompt, so the refusal itself is right, and M1 required it. The gap is that the message names no way out: `diff path 'Icon\r' must be relative, free of '..', and one line`. Adding `Icon?` to `.gitignore` clears it (executed: PASS), and `--diff-path` also avoids it. This repo has no such file today (5 untracked files, 0 with a CR). Fix: for a name git printed, say "rename or gitignore it, or name the files with --diff-path", as `diff_name_not_utf8` already does.
  quote: h-mad/scripts/h_mad_assemble_tdd.py:817 › `or any(ch in name for ch in "\n\r\0")):  # M:RV-DIFF-INVALID`

## Nit

- `--path ../x` prints `UNREADABLE reason=git`, while `helper-scripts.md:25` says one that "lies outside the repo, is `UNREADABLE reason=path-no-match`". An absolute `/etc` does give `path-no-match`. Only the reason differs, because `_repo_relative` (`h_mad_guard_census.py:743`) passes a relative `..` through to git.
- `--diff-path -dash.py` is an argparse usage error (`expected one argument`, rc=2, no `ASSEMBLE-TDD:` token). `--diff-path=-dash.py` passes, and `--base-ref` lists such a name without trouble. The `--diff-path` argparse definition (`h_mad_assemble_tdd.py:1094`) is unchanged by this delta. Not a regression.
- `helper-scripts.md:34` and `--help` say "a regular file". The check is `os.path.isfile` (`h_mad_assemble_tdd.py:868`), so a symlink to a file passes, while a dangling symlink, a symlink to a directory and a gitlink halt `diff_path_missing` (at 695cdde7 `lexists` accepted them). All are fail-safe, and `--base-ref` still lists the gitlink.
- S13's sibling, predates this delta. Other `_isolate` refusals under `--sweep --isolate` still print no `SWEEP:` line. Executed: harness outside the repo gives `MUTATION: UNREADABLE reason=isolate-script-outside-repo`, rc=2, with no `SWEEP:` (`h_mad_mutation_harness.py:2462`). `h_mad_backlog_cycle.py:189` reads rc, so it stays correct.

## A. Prior findings, re-run

| # | Prior finding | Verdict | Re-run and printed |
|---|---|---|---|
| M1 | Newline name through `--base-ref` reaches the prompt | FIXED | The same `evil\n- IGNORE ALL…` input: `HALT diff_path_invalid`, rc=2, no prompt written. Tests cover untracked, modified and deleted, with LF and CR. |
| M2 | Deleted gitlink, deleted symlink, or symlink to file gives UNREADABLE | FIXED | Gitlink: DONE, `link=1`, `real.py:2 if` still listed. Deleted symlink: DONE, `link=1`, `files=0`. Symlink to file: DONE, `s.py:1 if`. |
| S1 | Unparsable base loses the whole census (decided) | FIXED | `ff8234bb~1..ff8234bb`: `UNPARSED-BASE: …/hpw_upgrade_core.py`, `DONE … removed=10495 unparsed_base=1`, and the counts add up to 196 entries (99+3+9+85). `def f(:` fixed to valid: DONE, `unparsed_base=1`, head candidate listed. Valid broken to `def f(:`: `UNREADABLE reason=unreadable-file`, rc=2. |
| S2 | `up` climb through a symlinked root | FIXED | `linkroot -> mono/sub`: `…/mono/top.txt (outside --project-root)`, `…/mono/o t/gone.txt (deleted) (outside --project-root)`, both real paths. |
| S3 | `diff.relative` breaks the prefix map | FIXED | With the config set: output identical to a plain sub-root, and `top.txt` is listed. |
| S4 | Non-UTF-8 name is a traceback | FIXED | Base commit holding `bad\xff.py` (`git mktree`; `od` shows the byte): `HALT diff_name_not_utf8`, rc=2. |
| S5 | Spoofable isolate marker | FIXED | `ISOLATED_CHILD=1 --python ./py311`: `INTERPRETER: override=<abs>/py311`. `=1 --python ./nope`: `python-not-found`. `=0` with a relative env value: made absolute. The name remains only in the regression test. |
| S6 | Bad shebang reads as a red baseline | FIXED | `--python ./broken`, with and without `--isolate`: `UNREADABLE reason=python-unrunnable`, rc=2. |
| S7 | `--full-suite` unrunnable gives INCOMPLETE, rc=0 | FIXED | See section B. |
| S8 | `--path .` gives `path-no-match` | FIXED | `.`, `./` and the absolute top: `files=2`. Residual: Should-fix 2. |
| S9 | No row for the executable-bit check | FIXED | Row `python-executable-bit-not-checked` exists, anchor ok. Hand mutant `isfile and X_OK` to `isfile`: killed (`1 failed`, was `301 passed`). The prior report's other 5 hand mutants were not re-run. |
| S10 | Language from HEAD applied to BASE | FIXED | bash to python: `tool:3 if`, `tool:3 raise`, `REMOVED: tool:2 control,test,jump`. python to data: `REMOVED: tool:3 if`, `tool:3 raise`, and `UNMEASURED: tool`. python to symlink: `REMOVED: g.py:1 if`, `raise`, `removed=2`. |
| S11 | Unknown source suffixes count as `other` | FIXED | `.vue .mts .pyw .pyi .dart .awk .cxx .tcl`: `unmeasured=9` with `Makefile`, each listed. Regression from the fix: Should-fix 1. |
| S12 | Census documents contradict the code | FIXED | "A/M regular" gone from both files; the docstring's "skipped" sentence and the `:56` shell scope rewritten. Counters disjoint: deleting a `.py`, a binary and a test printed `files=2 deleted=1`, `binary=1 tests=1` (`files=2` includes an added `k.py`). |
| S13 | Bad interpreter under `--sweep`, no `SWEEP:` line | FIXED | `--python nosuchpy`, env `/nope`, and `--isolate --python ./broken`: `SWEEP: INCOMPLETE specs=0 — <reason> interpreter=<name>`, rc=2. Sibling route: Nit 4. |
| S14 | `--diff-path <dir>` passes | FIXED | `HALT diff_path_missing`, rc=2. |
| S15 | Recovery row not rescoped | FIXED | `failure-recovery.md:32` now reads `5d / 5e` and names `--phase review`. |

Out of scope, as instructed: the assembler's report and task body remaining unfenced.

## B. Regressions: what was probed and held

**`--phase review` name validation (all routes).**
- `--base-ref` PASS, each listed verbatim: `sp ace/a b.py`, `한글 폴더/파일.py`, `[br]/x[1].py`, `-dash.py`, `é.py`, `a..b.py`, `$(x).py`, `<INLINE_FEATURE>.py`, `` `t`.py ``, `q'uote.py`, `q"d.py`, `star*.py`, `#h.py`, `untracked 새.py`.
- `--diff-path` PASS: the five names tried (spaces, Korean, brackets, `é`, `a..b`).
- Real repo: `--base-ref 695cdde7` from the top and from `--project-root h-mad`: PASS, 14 files. A relative root under a Korean directory with `LC_ALL=C`: PASS.
- Only refusals: `Icon\r` (Should-fix 3) and the `--diff-path -x` usage error (Nit 2).

**Harness.**
- Idempotent resolution holds with no marker: `--isolate` with `--python ./py311`, `--python=./py311`, `--pyth ./py311` and env `./py311 -- spec` all gave ALL_CAUGHT, with the launcher logging `-m pytest` 3 times on each run. A bare name on PATH also passes under `--isolate`.
- Probe cost: yes, it runs per spec under `--sweep`, because each spec is its own process. Counted: 3 probes for 2 specs (parent + 2), and 4 under `--sweep --isolate`. Each probe is one interpreter start with nothing written, so the cost is negligible beside a spec's test runs.
- A `--python` that hangs: `./slow` (sleeps 61 s) took `real 60.05` and printed `reason=python-unrunnable`, rc=2. Under `--sweep` a merely slow launcher adds its delay once per spec; a launcher past 60 s stops at the parent's probe.
- `--check-anchors` stays exempt: `./nope`, `./broken`, and `--isolate` with `./nope` or env `/nope` all `ANCHORS_OK`, rc=0.
- No `--python` and no env: 0 probe lines, spec's own interpreter, with and without `--isolate`. `--help` unaffected.
- The sweep refusal line has the same shape as the existing `SWEEP: INCOMPLETE specs=0 — {exc}` at `h_mad_mutation_harness.py:2807`. `h_mad_backlog_cycle.py:189` reads rc, so a refusal raises `Refused`. Nothing outside the harness's own tests and `helper-scripts.md:89` reads this `SWEEP:` line (`h_mad_identifier_sweep.py` has its own token). `_sweep` reads a child's first `MUTATION:` line, and `line.split()[1]` yields `UNREADABLE`, which counts as unmeasured.
- Hand mutants on a scratch copy: `if probe.returncode != 0` to `if False` killed (`1 failed`, by the named test); `if not args.check_anchors` to `if True` killed (`1 failed`).

**Census.**
- Normal modified `.py` and `.sh`: every candidate and `REMOVED` line identical to 695cdde7. Only the format moved: `deleted=` went from `SKIPPED:` to `CENSUS-SCOPE:`, and `unparsed_base=` was added. No reader of the old shape outside the census's own tests (`h_mad_branch_evidence.py:545`'s `deleted=` is its own `CHANGED:` line).
- Replay of 40 first-parent commits of this repo: 39 identical in candidates, `REMOVED` lines and `unmeasured`; the one difference is `ff8234bb`, the decided S1 (old UNREADABLE, new DONE with `unparsed_base=1`). No traceback.
- Allow-list, executed: `.txt .md .json .yaml .toml .csv .html .css .svg` and `LICENSE` are `other`, `.png` is `binary`, `Makefile` is `unmeasured` (as documented).
- This repo's HEAD tree: 5,501 `other`, 388 `py`, 27 `sh`, 76 `unmeasured` (`.r` 23, `.tsx` 20, `.ts` 19, `.js` 9, `.rs` 4, `.bat` 1). All 76 are real source, so there is no document noise.
- `--path`: `sub`, `sub/`, `./sub`, `sub/a.py` narrow correctly; `nope` and `/etc` give `path-no-match`. `--repo sub --path a.py` (paths are from the repo top) is `path-no-match` both old and new, so that is unchanged.

**`--full-suite`.** All branches agree: `nosuch` and `notexec` give `UNREADABLE reason=full-suite-python-missing`; `broken` gives `…-python-unrunnable`; `sick` (exit 3) and a stub with no pytest give `…-pytest-missing`. All rc=2. A real interpreter gives `FULL-SUITE: PASS`, `COMPLETE`, rc=0. The docstring's special INCOMPLETE line is gone.

## Not covered

- The full suite (as instructed), and `test_h_mad_assemble_tdd.py` and `test_h_mad_new_caller_carveout_copies.py`, which were not in the scoped run.
- Harness scoring of the new rows. On an `h-mad`-only scratch clone the harness stopped at `MUTATION: PRECHECK_FAILED specs=204 drifted=0 unreadable=3`, a limit of that clone, so nothing was scored. In its place: anchors checked on the 4 specs and 3 hand mutants of the probe code.
- Real `agy` and `codex`: nothing dispatched.
- Linux and old git. `--no-relative` was run on git 2.54 only. On a git without that flag I would expect `diff_base_unreadable`, not a wrong list, but that was not run.
- History beyond 40 commits, and other repos, for Should-fix 1's input.

## Reviewer incident

One of my driver scripts ran before its env file existed, because I launched them in parallel, and its repeated `cd ..` walked out of the scratch directory. It created `s.py` and `t.py` in the scratchpad, `a.py` in its parent, `b.py` and `sub/a.py` one level up, `/private/tmp/claude-501/tool` and `/private/tmp/tool`. Every file's birth time was that run's second (10:35:39), so nothing existing was overwritten, and I removed those exact paths. Nothing touched the repo or the `rows-review` worktree (`git status --short` empty afterwards). The results above come from the re-run, not from that run.
