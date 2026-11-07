# Change review — `git diff ff8234bb HEAD` (HEAD 7c357c97, ten rows of docs/skill-candidates.md:2998-3014) — GATING

Told neither GATING nor ADVISORY, so GATING is assumed. Paths are relative to the reviewed worktree. Every finding is tagged CONFIRMED (executed) or PLAUSIBLE (read only).

## Evidence
- read: 23 changed files in part or whole (all production and reference diffs, all of `h_mad_guard_census.py`, `test_h_mad_hook_live_interpreter.py`, the new test blocks in the other test files, every row of the 4 new specs and the new rows of 2 edited specs), plus `agy-spec-reviewer-prompt.md`, `codex-verifier-prompt.md`, `agy-runtime.md`, `tdd_gate_support.py`, `verify-hmad-gates/SKILL.md`
- ran: about 40 Bash calls (the gate matrix alone is 27 hook drives, plus 3 smaller gate drives), all against disposable repos under the scratchpad, or read-only against the worktree. The worktree stayed clean (`git status --short` = 0 lines).
- tests run: `h-mad/tests/test_h_mad_assemble_tdd.py test_h_mad_assemble_tdd_agent.py test_h_mad_branch_evidence.py test_h_mad_guard_census.py test_h_mad_hook_live_interpreter.py test_h_mad_mutation_harness.py test_h_mad_new_caller_carveout_copies.py` under `/opt/anaconda3/bin/python3.11`: `715 passed`, 0 skipped. Also the 23 doc-consumer test files of `codex-implementer-prompt.md` and `failure-recovery.md`: `1812 passed`.
- left behind: scratch repos under the scratchpad are deleted. `hmad-verify.sh` keeps its evidence by design, so 6 run dirs remain under `~/.local/state/h-mad/verify-hmad-gates/` (`20261107T050807-98283`, `T050840-2735`, `T050921-7077`, `T051721-68918`, `T051735-71202`, `T051758-75949`). Running these scripts may also have written the git-ignored `h-mad/scripts/__pycache__/` in the worktree; nothing tracked changed.
- mutation scored (`h_mad_mutation_harness.py --python /opt/anaconda3/bin/python3.11`, on scratch copies): hook_live_interpreter 7/7, guard_census 40/40 (5 crash kills, each a guard whose removal really crashes), assemble_tdd_review 21/21, assemble_tdd_prompt_rows 15/15, branch_evidence 9/9 new rows, mutation_harness 6/6 new rows. No survivors. Three runs read `BASELINE_NOT_GREEN` and were re-run, and these were my setup, not defects: a history-less snapshot for assemble_tdd_review (it needs commit `8ef6009f`), and `--python` on mutation_harness (see "Not covered").

## Must-fix
- CONFIRMED. `--phase review --base-ref` prints wrong paths when `--project-root` is a subdirectory of the git repo. `git diff --name-only` is repo-root-relative, `git ls-files --others` is cwd-relative, and both get joined to `project_root`. Input: repo `mono/` with `sub/src/a.py` modified, `top.txt` modified, `sub/src/fresh.py` untracked, `--project-root mono/sub --base-ref <B>`. Output under "Files Codex Changed": `mono/sub/sub/src/a.py` (does not exist), `mono/sub/top.txt` (does not exist; the real file is outside the root), `mono/sub/src/fresh.py` (correct). The template tells agy to `view_file` each path, so the implementation is never read, while the run ends `ASSEMBLE-TDD: PASS`. `--diff-path` is unaffected. The only base-ref test runs at the repo root. Fix: `git diff --relative`, or derive from `git rev-parse --show-prefix`.
  quote: h-mad/scripts/h_mad_assemble_tdd.py:812 › `["git", "-C", str(project_root), "diff", "--name-only", "-z", base_ref, "--"],`
  quote: h-mad/scripts/h_mad_assemble_tdd.py:881 › `"<INLINE_DIFF_PATHS>": "\n".join(f"- {project_root / name}" for name in ordered),`
- CONFIRMED. The review prompt omits the impl-plan sections the task cites, which the GREEN prompt for the same task inlines, and says nothing about it. Input: a plan with a global `## Contract` section ("exit 3 on refusal") and Task 1 saying `Implement per §"Contract".`. `--phase green` prompt: `grep -c "exit 3 on refusal"` = 1. `--phase review` prompt: 0, with no `referenced-not-inlined:` line, because the three fields are hard-coded empty. The implementer is held to the contract and the reviewer, told to compare "line by line" with "What Was Requested", never sees it, so drift against the cited section can come back `VERDICT: COMPLIANT`. Fix: call `referenced_sections` in `assemble_review` as `assemble` does.
  quote: h-mad/scripts/h_mad_assemble_tdd.py:1144 › `meta.update(inlined_sections=[], inlined_lines=0, unresolved_refs=[])`
  quote: h-mad/scripts/h_mad_assemble_tdd.py:55 › `A global impl-plan section the task cites by `§"…"` is inlined after the task`

## Should-fix
- CONFIRMED. The `interpreter_gate_untrusted` warning states "the gate will deny" in two cases where the real gate allows. (a) `.h-mad/phase5-shell-allow` holding `/opt/anaconda3/bin/python3.11 -m pytest`: the codex gate returned allow for that command and the assembler still printed the WARN. The assembler's own helper-scripts entry names a path-spelled allow line as a supported route. (b) `/opt/anaconda3/bin` first on PATH, so the hook itself runs under that python: the gate returned allow for `/opt/anaconda3/bin/python3.11 -m pytest tests/test_w.py -q` (with the default PATH it returned deny, which matches the warning). The predicate reads neither source. Warn-and-continue is the operator's ruling and is not disputed; the wording overclaims and sends the operator to build a venv they do not need. Say "may deny", or consult the allow file.
  quote: h-mad/scripts/h_mad_assemble_tdd.py:1189 › `gate will deny the dispatch's pytest run; create a thin venv `
- CONFIRMED. `h_mad_guard_census.py` reports `DONE decision=0` for changed files it never measured, and no line counts them. Inputs that printed `files=0 … GUARD-CENSUS: DONE decision=0 anchored=0 unanchored=0`: a commit adding only a suffix-less `#!/usr/bin/env python3` script and a `.ts` file; `--path src/typo_nope.py` (no such file). `src/hook.zsh`, a `#!/bin/bash` file named `gate.v2`, and `check.js` were likewise absent from a larger run, and `SKIPPED:` had no count for them. The script's own header refuses a zero for exactly this reason on UNREADABLE. No suffix-less Python script is tracked under `h-mad`/`handoff` today, so nothing is misread on this repo's hooks yet; `hemasuite/src` does hold `.ts`/`.js`. `test_a_suffixless_file_with_another_shebang_is_not_a_target` pins the silent zero. Add an `unmeasured=` count to `SKIPPED:`, and treat a `--path` matching nothing as UNREADABLE.
  quote: h-mad/scripts/h_mad_guard_census.py:19 › `byte-identical to "nothing was measured". Read the token, never `$?`.`
  quote: h-mad/scripts/h_mad_guard_census.py:427 › `if path.endswith((".sh", ".bash")):`
- CONFIRMED. The census cannot see a deleted guard inside a modified file. Input: `def g(x):\n    if x:\n        raise ValueError\n    return x\n` changed to `def g(x):\n    return x\n`. Output: `DONE decision=0 anchored=0 unanchored=0`. A hunk `+N,0` contributes no line. The title says "adds or changes", but the "Limits, stated so they are not read as coverage" paragraph omits this, and a dropped guard is the largest verdict-moving diff a reviewer would use this tool to find.
  quote: h-mad/scripts/h_mad_guard_census.py:195 › `lines.update(range(start, start + count))`
- CONFIRMED. The census reads one spec directory, and this repo has two. Commit `5db87e97` over `--path handoff/scripts`: default `DONE decision=118 anchored=0 unanchored=118`; with `--spec-dir handoff/tests/mutation-specs`: `anchored=7 unanchored=111`. So a default run reports handoff's anchored lines as unanchored, and `--spec-dir` is not repeatable, so a diff touching both trees has no correct invocation.
  quote: h-mad/scripts/h_mad_guard_census.py:97 › `DEFAULT_SPEC_DIR = "h-mad/tests/mutation-specs"`
- CONFIRMED. Census Python parsing has two smaller holes. (a) `await deny(x)` is an `Expr(Await)`, so it is not a "call used as a statement" and is not listed; `with lock_or_refuse(x):` is also absent and is on neither the decision list nor the not-a-decision list. (b) A bare `\r` in source: `ast` counts it as a newline and the census does not. Input `a = 1\rb = 2\nif a:\n    print(b)\n` listed `cr.py:2 assign "if a:"` and `cr.py:3 if "print(b)"`, and `print(b)` was not listed at all. Non-UTF-8, syntax errors, bad specs, binary, deleted files, renames (delete plus add, so the whole new file is candidates) and glob-character names all behaved as documented.
  quote: h-mad/scripts/h_mad_guard_census.py:366 › `elif isinstance(st, ast.Expr) and isinstance(st.value, ast.Call):`
  quote: h-mad/scripts/h_mad_guard_census.py:279 › `"""Start offset of each line; lines split on LF only, as git counts them."""`
- CONFIRMED. A helper-scripts calibration claim is false as written. Replaying the census `--base 3489f86b --head 8a3fa99e --path h-mad/hooks --path h-mad/scripts` (no production file differs between 246531ba and 8a3fa99e) and checking the 18 lines the calibration test names: 3 remain, not 2. They are `h_mad_tdd_judge.py:344`, `h_mad_tdd_judge.py:738`, and `h-mad-tdd-gate.sh:269` (`arms-not-all-anchored`). The first half of the claim holds: `decision=170 anchored=58 unanchored=112` at 246531ba reproduced.
  quote: h-mad/references/helper-scripts.md:25 › `only v4's 2 remain`
- CONFIRMED by read of both documents. The rewritten FR-9 sentence names the verifier as the one who performs the cut, but the verifier prompt says that same revert cannot run under the gate and tells it to report the AC unmeasured. In a gated dispatch nobody the sentence names performs the cut; the performer is the orchestrator (`phase5-substeps.md:182`, and `helper-scripts.md` does name it). No surface tells GREEN to cut: see "FR-9 surfaces" below. Say "the orchestrator's wire-scoped revert".
  quote: h-mad/references/codex-implementer-prompt.md:72 › `is the verifier's wire-scoped revert, not GREEN's`
  quote: h-mad/references/codex-verifier-prompt.md:39 › `step 1b, and an env-assignment prefix such as `MPLBACKEND=Agg …`, cannot run under the gate (the`
- CONFIRMED. Two doc claims about `--phase review` inputs do not hold. `--diff-path nope/never.py` (no such file) ends `ASSEMBLE-TDD: PASS`, against "refuses a missing or unreadable input" (true only of the report). `--project-root . --diff-path src/a.py` prints `- src/a.py`, against "printed absolute" and the docstring's "the diff paths are absolute so `view_file` needs no guess". Tests use an absolute root only.
  quote: h-mad/references/phase5-substeps.md:147 › `refuses a missing or unreadable input`
  quote: h-mad/references/helper-scripts.md:34 › `relative to the root, printed absolute`
- CONFIRMED (the listing) / PLAUSIBLE (the effect). `--base-ref` lists every untracked file in the tree and every deleted file under "Files Codex Changed". In a shared tree such as this repo's main checkout (5 untracked foreign paths at session start) those land in the prompt, whose instructions are "use `view_file` on each changed path" and "Look for extra features they didn't mention", which invites a false `DRIFT`. Executed: `sub/src/fresh.py` and the deleted `top.txt` were both listed.
  quote: h-mad/scripts/h_mad_assemble_tdd.py:816 › `["git", "-C", str(project_root), "ls-files", "--others", "--exclude-standard", "-z"],`
- CONFIRMED. The default `--phase review` applies the implementer-only wiring check to a read-only reviewer. A project with no `.agents/hooks.json` (codex implementer, any non-agy lane): `ASSEMBLE-TDD: HALT agy_tdd_hook_unverified`, exit 0, no prompt. `agy-runtime.md:63` scopes the check to an implementer, the recovery row is written for 5d, and exit 0 means a driver reading `$?` proceeds with no prompt file. This is deliberate and test-pinned (`test_an_unwired_agy_review_is_refused_like_any_agy_dispatch`), and `HemaSuite` and `skills` both hold the directory, so it is a call for the operator, not a bug. Either scope the runtime doc to include the review, or skip the check for it.
  quote: h-mad/references/agy-runtime.md:63 › `Before an agy implementer dispatch, run`
- CONFIRMED. `--python` is not in the review's not-applicable list, though the review runs no pytest. `--python /nope/python` is silently dropped and ends PASS; `--python nosuchpy` halts `interpreter_not_found` on a phase that needs no interpreter. Both contradict the comment guarding that list. `--escalate` works and is marked.
  quote: h-mad/scripts/h_mad_assemble_tdd.py:1068 › `# An option that does not apply is a halt, never a silent drop: the run would`
- CONFIRMED. The red-baseline misreading the isolate row exists to remove survives on three spellings. `--isolate --python nosuchpy`, `HMAD_MUTATION_PYTHON=./py311 … --isolate`, and `--python py311` (a bare name for a file in cwd) each print `MUTATION: BASELINE_NOT_GREEN`. Argparse's `--pyth ./py311` passes the caller check, is not rewritten, and the child reports `python-not-found` for a path inside the temp worktree. The row's literal case is fixed; see "Row verdicts".
  quote: h-mad/scripts/h_mad_mutation_harness.py:2440 › `return os.path.normpath(os.path.join(caller_cwd, value)) if "/" in value else value`
- CONFIRMED. `--full-suite --python <an executable whose shebang names a missing interpreter>` passes the `isfile`/`X_OK` check, then `_child` raises `FileNotFoundError`: a traceback, rc=1, no `FULL-SUITE:` line and no `EVIDENCE-VERDICT:`. It is not COMPLETE, so it fails safe, but a driver reading the token gets nothing, against the row's "fails closed" contract of a named reason.
  quote: h-mad/scripts/h_mad_branch_evidence.py:477 › `if not (os.path.isfile(python) and os.access(python, os.X_OK)):`
- CONFIRMED. The hostile-limits paragraph omits the limit that bites hardest: `[]` in the project root, not only in a test path. Root `repo Ω [*] 'q'` with a correctly failing test: all three gates deny every production write `no-tests-ran` (rc=4), because the judge hands pytest an absolute path. The same matrix under root `repo` gives the expected decisions. The behaviour predates this diff; the paragraph presents itself as the complete list ("Hostile has three limits"), and `hmad-verify.sh mkroot` builds exactly this root, so anyone following the verify recipe for a pytest-reaching path hits it, as this review did.
  quote: h-mad/references/codex-implementer-prompt.md:80 › `do not put `[]` in a test-file path you hand pytest`
- CONFIRMED by read. Text naming the old behaviour remains outside `docs/archive`. `agy-spec-reviewer-prompt.md:4-5` still says the orchestrator stages the template by hand and dispatches via `send`. `helper-scripts.md:34` documents `phase=<red|green|gate>` while the tool prints `phase=review`. `--help` still reads "Stage a Phase-5d/5e Codex dispatch" (`h_mad_assemble_tdd.py:1002`). `python-not-found` and `crash reading unavailable` appear in no reference document; the failure-recovery row covers `UNREADABLE` only generically.
  quote: h-mad/references/agy-spec-reviewer-prompt.md:5 › `> `INLINE_*` placeholders substituted, then dispatches via `hmad-dispatch send``
- CONFIRMED by read. `test_a_flag_that_does_not_apply_to_a_review_halts_instead_of_being_dropped` parametrizes 4 of the 10 refused flags. Removing `--sandbox`, `--report-file`, `--authors-test`, `--expect-pass` or either env-known-failure flag from the list would pass; `rv-not-applicable-dropped` only proves the whole list is live. The two Must-fix defects above also have no test. This is a coverage gap, not a vacuous test.
  quote: h-mad/tests/test_h_mad_assemble_tdd_agent.py:634 › `@pytest.mark.parametrize("flag", [("--expect-fail", "1"), ("--test-path", "tests/x.py"),`

## Nit
None

## Rubric 2: prose claims, executed

**RED stub order** (`codex-implementer-prompt.md:126`, assembler RED directive). Real gates, `HMAD_VERIFY_H_MAD_ROOT` at this worktree, driven through `hmad-verify.sh`, disposable root `repo`, `python3` with pytest on PATH, plan listing `tools/w.py` and `tests/test_w.py`. The same result on all three hosts:

| State when the stub is written | claude | codex | agy |
|---|---|---|---|
| No test file, stub first (stub absent, or already present) | deny `test-missing` | deny `test-missing` | deny `test-missing` |
| Test `from tools import w` (module absent; also with `tools/` absent) | deny `pytest-error` | deny `pytest-error` | deny `pytest-error` |
| Test `from tools.w import f`, module absent | allow | allow | allow |
| Test `import tools.w as w`, module absent | allow | allow | allow |
| Test `from tools.w import f`, `tools/` absent too | allow | allow | allow |
| Stub present, assertion fails | allow | allow | allow |
| Suite green | deny `test-passing` | deny `test-passing` | deny `test-passing` |

The prompt's claims hold. Caveats from the same drive: with no pytest in the hook's python every cell with a test file is `pytest-missing`, and the helper's default `[*]` root makes those cells `no-tests-ran`; neither reflects stub order.

**Hostile-path limits** (pytest 9.1.1, Python 3.11.8). All true as written:
- `d[x]/test_a.py` and `d[x]/test_a.py::test_a`: `ERROR: path cannot contain [] parametrization`, `no tests ran`. Started inside `d[x]/` with `test_a.py`: `1 passed`.
- `c:d/test_a.py`: `1 passed`.
- `venv` with `:` anywhere in the absolute path, including a relative `.venv` argument from inside `c:d/`: `Refusing to create a venv … because it contains the PATH separator :`.
- Whitespace: `_NON_PY_PATH_RE` is `` `([^`\s]*[/.][^`\s]*)` ``; `_parse_tasks` on `` `bin/run me.sh` `bin/ok.sh` `my dir/a.py` `` returns `['my dir/a.py', 'bin/ok.sh']`. Gate writes: `bin/run me.sh` allow on all three hosts ("no longer gated" holds), `bin/ok.sh` deny `test-missing` on all three.

**Bare `hmad-dispatch` claim** (`codex-implementer-prompt.md`, bounded run). Codex gate: the dispatch on PATH is this skill's own file: allow. No dispatch on PATH, or `~/.agents/skills/h-mad/bin` (a different file from the hook's skill): deny. The claim holds. `.venv/bin/python -m pytest`, relative or absolute: allow.

**FR-9 surfaces.** `git grep -i "wire-cut"` over `h-mad` outside tests: `codex-implementer-prompt.md:72,82,86`, `failure-recovery.md:40`, `helper-scripts.md:34`, `phase5-substeps.md:146`, and the assembler's wiring block (`h_mad_assemble_tdd.py:689`). I read each one. None tells GREEN to perform a cut; `helper-scripts.md:34` says "NOT". `GREEN must prove` survives only in mutation `replace` text and in `not in` assertions. The premise holds too: a green suite is `test-passing` on every gate.

**`--phase review` block.** With a wired `.agents/hooks.json`, `h-mad/tests/stubs` and `h-mad/bin` on PATH, the printed block ran under bash and ended `[H-MAD] f phase5e verdict_COMPLIANT`, `block_rc=0`. It matches the substeps block plus a `$rc` check, and `--model`/`--effort` went through. Real agy was not run. Hostile values (report and task quoting `<INLINE_FEATURE>`, `<INLINE_DIFF_PATHS>`, `\1`, `\g<0>`; module `mo$(x)d`) were inserted verbatim once. An unfilled template slot halts `residual_slots`.

## Rubric 3 and 4: tests and edited pins

- Rows sampled by reading `find`/`replace`: all 7 of hook_live_interpreter, all 15 of assemble_tdd_prompt_rows, all 21 of assemble_tdd_review, all 40 of guard_census, 9 new in branch_evidence, 6 new in mutation_harness. No mutant failed to disable its guard. Rows scored are listed under Evidence.
- No test re-implements its subject. `TestRedStubOrderMatchesTheGate` drives the real Claude hook. `test_the_measured_limits_are_true_under_this_interpreter` runs pytest and venv for real. The text pins are paired with those measurements and have mutants that revert the text.
- `test_h_mad_hook_live_interpreter.py`: not vacuous here. `python3` is 3.15 and the suite runs 3.11, so 0 skipped; the shim-log control proves the launch went through PATH, and 7/7 mutants die. The skip is correct and is itself pinned. On a host where `python3` is the suite interpreter, its 8 live cases skip by design.
- `test_h_mad_new_caller_carveout_copies.py`: justified. The FR-9 constant now carries the new sentence, and the pin still requires the block on all surfaces.
- `test_h_mad_assemble_tdd.py:2066`: justified. One literal changed, and the whole directive is still compared.
- `test_h_mad_assemble_tdd_agent.py` `test_no_agent_output_is_byte_identical_to_base`: justified, not weakened. It applies one replacement, guarded by `assert base_prompt.count(old_directive) == 1`, and every other byte is still compared.
- `assemble_tdd_agent.json`: the row re-anchored to `default=None,` and its mutant (`default="grok",`) still bites.
- `new_caller_carveout_copies.json`: re-anchored to the new sentence; same edit delta.
- `test_h_mad_branch_evidence.py`: only the pytest stub changed (logs `argv`, adds `STUB_FULL_MODE`, handles zero files). All old-path output is unchanged. Justified.

## Rubric 1: results where nothing was wrong

- `h_mad_branch_evidence.py` without the flag: old script (ff8234bb) and new script on one scratch branch gave `cmp` identical output.
- With `--full-suite`, real pytest: PASS `COMPLETE`; failing test outside the changed set `INCOMPLETE reason=…,full-suite-failed`; `/usr/bin/false` and a pytest-less 3.15 `UNREADABLE reason=full-suite-pytest-missing`; `./nosuch` and `nosuchbare` `full-suite-python-missing`; `--full-suite-timeout 3` `full-suite-pytest-timeout`; a test that litters `tree-moved`; dirty `SKIPPED reason=dirty`, `INCOMPLETE`. `collect` has two returns, and neither can reach COMPLETE without the step having passed.
- `_isolate`: `--python ./py311`, `--python=./py311`, the same with `--`, and `--python ../py311` / `--python=../py311` from a subdirectory: `ALL_CAUGHT`, `ISOLATE: removed=yes`. A path after `--` is left alone by construction (read).
- New nonexistent-path refusal: `MUTATION: UNREADABLE reason=python-not-found`. `--check-anchors --python ./nosuch` is exempt and still runs. I found no legitimate case it breaks, because `main` already made a relative path absolute against the caller's cwd, so such a path could only ever have failed.

## Row verdicts

- `assemble-tdd-red-forbids-plan-stubs`: fine. Prompt and checklist match the gates on all three hosts.
- `green-prompt-demands-a-wire-cut-the-gate-refuses`: does what it needs; the attribution to the verifier is wrong under the gate (Should-fix).
- `assembled-test-command-the-gate-denies`: warn-and-continue as ruled; the wording overclaims (Should-fix). 5c venv guidance and the bounded-run example are true.
- `hostile-path-limits-in-the-red-template`: fine. All three limits are true as measured; the bracketed-root limit is missing (Should-fix).
- `assemble-the-agy-spec-review`: not fine. Two Must-fix.
- `guard-census-from-the-diff`: core and first calibration are true; blind spots and one false doc claim (Should-fix).
- `hook-tests-run-under-the-wrong-interpreter`: fine.
- `isolate-relative-python-false-baseline`: fine for the row's literal case; three adjacent spellings still misread (Should-fix).
- `close-out-measurement-wrapper`: fine; one tokenless crash path (Should-fix).
- `crash-visible-empty-denominator`: fine. Executed on a scratch spec; the detail reads `crash reading unavailable`. A consumer grep found nothing parsing `no traceback from`.

## Not covered

- The full suite (as instructed), and so the 95 doc-consumer files of `helper-scripts.md` and `phase5-substeps.md`, which overlap it heavily. Both documents changed, so run those before landing.
- `mutation_harness.json` under `--python`: with `HMAD_MUTATION_PYTHON` set, 5 cases of `test_h_mad_mutation_harness.py` fail (`test_isolate_preserves_child_error_output_and_exit_code`, `test_isolate_reruns_its_dirty_script_with_rebased_cwd_and_original_arguments`, `test_reachability_disabled_preserves_exact_output_existing_guard[single]` and `[sweep]`, `test_python_flag_substitutes_the_spec_interpreter`), so that spec's baseline reads red under its own flag. All four test functions exist at ff8234bb, so this predates the diff and is reported only as a note. Without the flag, the 6 new rows scored 6/6.
- `assemble_tdd_review` was scored on a sparse shared clone, not the worktree, and the other specs on a plain snapshot; both hold the same HEAD contents.
- Real `agy` and real `codex` binaries: the block was run against `h-mad/tests/stubs`.
- A non-UTF-8 file name reaching `--base-ref`: APFS refused to create one. `subprocess.run(text=True)` has no `UnicodeDecodeError` handler there (`h_mad_assemble_tdd.py:811-819`), so a traceback on Linux is PLAUSIBLE and unverified. A non-UTF-8 impl-plan does traceback, in `--phase review` and in `--phase red` alike, so that predates this diff.
- `--full-suite` against this repository's own suite, and pytest exit 5 as a live case (the scratch attempt did not reach it; `pytest-rc<N>` is by read and by the stub tests).
- A live wiring-task GREEN or verifier dispatch through a real gate.
