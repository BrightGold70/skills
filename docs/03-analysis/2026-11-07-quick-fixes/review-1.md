# Change review — working tree against HEAD de7d16ff (quickfix.diff, 7 files, +118/-4) — GATING

Rubric: correctness of the four stated claims, plus the probes the dispatch named (claim-3 premise, claim-4 edge cases, claim-2 `--spec-dir`/`./..`, consumers that pin the old behaviour).

## Evidence
- read: 11 files, about 560 lines: the whole diff (227 lines); `h_mad_guard_census.py` 100-118, 555-600, 715-800; `h_mad_assemble_tdd.py` 143-148, 790-875, 1064-1072, 1080-1137 (the add_argument lines); `test_h_mad_assemble_tdd_agent.py` 770-807; `test_h_mad_mutation_harness.py` 20-53 plus grep hits; `mutation-specs/assemble_tdd_review.json` 275-289 and the new rows; `guard_census.json` (keys and new row); `grok_audit_surface.json` (file counts only); `references/helper-scripts.md` 20-30 and the `diff_path_invalid` span of 34; `docs/skill-candidates.md` 3030; `docs/03-analysis/2026-11-07-rows-1106/review-4.md` (grep hits 30, 39, 41, 80).
- ran: about 25 commands. The main tree's `.h-mad/mutation.lock` was held by the background job (`SUITE: BUSY holder=8115`), so every pytest run used a scratch tree: `git archive HEAD conftest.py pytest.ini h-mad` plus `git apply quickfix.diff`. `cmp` showed all 7 changed files byte-identical to the working tree.
- tests run (python3.11, in the scratch tree):
  - `tests/test_h_mad_mutation_harness.py` with `HMAD_MUTATION_PYTHON` set: 2 failed, 309 passed. Both failures are anchor-drift tests (see Must-fix 1).
  - Control: the HEAD version of the same file under the same override: 7 failed. These are the same 2, plus the 5 CLI cases the row names (`test_isolate_preserves_child_error_output_and_exit_code`, `test_isolate_reruns_its_dirty_script_…`, `test_reachability_disabled_preserves_exact_output_existing_guard[single|sweep]`, `test_python_flag_substitutes_the_spec_interpreter`). So claim 1 holds: the fixture is what turns those 5 green.
  - `tests/test_h_mad_guard_census.py tests/test_h_mad_assemble_tdd_agent.py`: 204 passed, 4 skipped, 1 failed. The failure (`test_no_agent_output_is_byte_identical_to_base`) comes from the scratch tree: `git archive 8ef6009f` exit 128, because that sha is absent there.
  - Collect-only shows that the new mutation rows' node ids `[modified-newline]` and `[abbreviated]` exist.

## Must-fix
- Two existing mutation rows now anchor on a line the change deleted, and the committed-spec drift tests go red. `rv-git-changed-names-unchecked` and `rv-git-untracked-names-unchecked` both use `find: "for name in changed + fresh:"`. The diff splits that loop into `for name in changed:` and `for name in fresh:`, so the anchor matches 0 times. Executed in the scratch tree, both tests fail:
  - `test_committed_mutation_specs_are_not_drifted` prints `rv-git-changed-names-unchecked: anchor matched 0 times in scripts/h_mad_assemble_tdd.py, expected exactly 1` (and the same for the untracked row).
  - `test_committed_mutation_harness_anchor_sweep_is_ok` prints `ANCHORS: assemble_tdd_review.json DRIFTED ok=42/44`.

  Failure scenario: any full-suite run, or `h_mad_mutation_harness.py --check-anchors` over the committed specs, on this tree. Fix: re-anchor the two rows on the new loops, for example `for name in changed:  # M:RV-TRACKED-WAY-OUT` replaced by `for name in []:`, and `for name in fresh:` (first occurrence; it must be unique). Keep their kill tests. The rest of the drift in the scratch output (`fr9_drive_refusals.json` 0/9, `grok_audit_surface.json` 236/465) comes from the scratch tree: the 229 missing rows are exactly the `../docs/03-analysis/probes/...` files that `git archive h-mad` left out. That part is not caused by the change.
  quote: h-mad/tests/mutation-specs/assemble_tdd_review.json:278 › `"find": "for name in changed + fresh:",`
  quote: h-mad/scripts/h_mad_assemble_tdd.py:852 › `for name in changed:  # M:RV-TRACKED-WAY-OUT  the base still holds it: only --diff-path gets out`

- Claim 3's premise is false for a rename, and the new test pins the false premise. `git diff --name-only <base>` runs with rename detection on (`diff.renames` unset, so git's default applies). After `git mv`, a tracked bad name stops appearing.

  Failure scenario, executed in a scratch repo with base commit holding `bad\nname.py`:
  - Modify the file, then `git mv "bad\nname.py" good.py`. `git diff --no-relative --name-only -z HEAD --` prints only `good.py|`.
  - A name added after the base (`--base-ref HEAD~2`, then `git mv "new\nbad.py" fine.py`) also drops out.
  - `_review_diff_paths(project_root=r, diff_paths=[], base_ref='HEAD~2')` halted `diff_path_invalid` before the two `git mv`s. After them it returned `[(…/fine.py,''), (…/good.py,''), …]`, with no halt.

  So "rename it" is a working way out on the tracked `modified` route, and the change removed it. Only a plain `mv` (the old name lists as deleted), the `deleted` route, and gitignore (review-4 line 30, which only ever reported gitignore) leave the name in place. The code comment and the test comment state the false fact. The test asserts `"rename" not in out`, which pins the wrong message: a correct fix (offer `git mv`) would turn the test red, and the new mutation row `rv-tracked-name-offers-a-dead-way-out` would score that correct message as a mutant to kill. Suggested message for `changed`: `; git mv it, or name the files with --diff-path`. For `deleted` names, only `--diff-path`. Adjust the test and the row to match.
  quote: h-mad/tests/test_h_mad_assemble_tdd_agent.py:805 › `# printing it after a rename or a gitignore; only --diff-path gets out.`
  quote: h-mad/tests/test_h_mad_assemble_tdd_agent.py:806 › `assert "gitignore" not in out and "rename" not in out, out`

## Should-fix
- Claim 4 only covers the exact flag spelling. argparse accepts `--diff` as an abbreviation of `--diff-path`, and no other option starts with `--diff`. But the rewrite tests `token == flag`, so `--diff -dash.py` still fails as an argparse usage error with no ASSEMBLE-TDD token. Executed: `['--diff', '-dash.py'] -> ['--diff', '-dash.py'] :: EXIT 2: error: argument --diff-path: expected one argument` (same on 3.11 and 3.15). This is the failure the claim set out to remove, under a spelling argparse itself accepts. Either match `flag.startswith(token)` for tokens of at least 3 characters that pick out a single option, or set `allow_abbrev=False`. The second changes CLI behaviour, so it is the operator's call.
  quote: h-mad/scripts/h_mad_assemble_tdd.py:1070 › `if (token == flag and nxt is not None and nxt.startswith("-")`

## Nit
- `_bind_dash_values` reads the private `ap._option_string_actions`. It works on 3.11 and 3.15, but `[s for a in ap._actions for s in a.option_strings]` uses a less private attribute and gives the same set.
- A value whose text before `=` is just `-` or `--` (for example a file named `-=x`) is still refused, because every option starts with `-`. Executed: `['--diff-path', '-=x'] -> unchanged :: EXIT 2`. This is harmless: a bare `-` already parses as a value (`diff_path=['-']`, executed). It could be one line in the docstring.
- `test_h_mad_mutation_harness.py` has three blank lines before the new fixture (40-42) and one after it (51). PEP 8 wants two before a top-level def.

Probed and found correct (no finding):
- Claim 4 on both interpreters:
  - `--diff-path` with `-dash.py`, `-1`, `-1.5`, `-a b`, `-hx.py` (argparse would otherwise read it as `-h` with an explicit argument), `-f`, `--x=y`: all bind as values.
  - `--`, `-h`, `--d`, `--diff`, `--diff-path=`, `--diff-path`, `--agent=codex`, `--feature=x`: left alone and refused as before.
  - `--diff-path a --diff-path -b` gives `['a','-b']`. A `--` before the flag passes through unchanged.
  - `--expect-fail -1` is untouched. `--sandbox --diff-path -x` and `--report-file --diff-path -x.md` were usage errors before and still are.
  - No input found that parsed before and parses differently now. Every case argparse already accepted (negative numbers, values with a space) gets the same value through `=`.
  - `argv=None` reads `sys.argv[1:]`, and a list is copied.
- Claim 2:
  - Old against new, executed: `--spec-dir ../x` and `--spec-dir ./..` changed `reason=git` to `reason=spec-dir`, which matches the docstring's "`spec-dir` (… or outside the repository)" (census line 110-111).
  - `--path ./..`, `../`, `sub/../..` changed `git` to `path-no-match`. `.../x` and `..foo` are `path-no-match` on both.
  - A path through a symlink that leaves the repo (`lnk/x`) was already `path-no-match`.
  - No test or doc pins `reason=git` for a climbing path. `_repo_relative` is called only at census lines 571-572. The spec `root: "../.."` values go through a separate code path.
- Consumers: no doc pins the old refusal wording. helper-scripts.md:34 lists `diff_path_invalid` by its conditions only. The only other uses of the `rename or gitignore` text are the untracked line and the mutation rows.
