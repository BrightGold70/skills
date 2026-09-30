# Analysis: tdd-gate-fail-opens

## Executive Summary
At `f75ca887` all eight FRs are met (44/44 ACs). v1's only gap (Gap 1: `..` after a symlink was
collapsed lexically before the walk, AC-1.2/AC-6.1) is closed. I rebuilt the spec's M-6 fixture
myself and drove both gates. At `f75ca887` both deny `no-test-resolved`. At `1d454948` both allowed,
and at the baseline `15681a53` Claude allowed and Codex denied. I also ran 19 other `..` spellings
against both gates and the canonicaliser on all three trees. None of them opens a new fail-open.
One new behaviour is fail-closed: a `..` through a mode-0311 directory is now refused `judge-error`
under governance, including one governed test-file write that the kernel allows (N-1). No AC covers
it, and it goes to the operator. Verdict: advance to Phase 7.

## Match Rate: 100%

FR-level: 8 of 8 FRs have every AC met, so 8/8 = 100% (threshold 90%). AC-level: 44 of 44.

Scope of this measurement: spec v1.5, design v1.5 and impl-plan v1.3. None of the three changed
after `1d454948` (`git diff --stat 1d454948 f75ca887 -- docs/01-plan docs/02-design` is empty).
The diff is `15681a53..f75ca887`. Since v1 (`1d454948..f75ca887`), the only production file that
changed is `h-mad/scripts/h_mad_target_identity.py` (+19/−5). The other changes are tests, the
`target_identity.json` mutation spec (row TI8), the probe (`reproduce.py` M-6) and the two readings.
The hooks, the judge, the resume oracle and the adapters are byte-identical to `1d454948`, so their
line references below are unchanged from v1.

Measurement hygiene: all gate and canonicaliser probes, the self-check and the anchor check were run
against `git archive f75ca887` copies. During this analysis the working tree gained uncommitted
edits that are not part of it and were not made by it: `h-mad/hooks/h-mad-codex-tdd-gate.py` (the
`_canonical_root` arm-2 component), `codex_gate_judge_wiring.json` (+1 row) and
`test_h_mad_codex_tdd_gate_judge.py`. The targeted run collected 665 tests, which is 662 + the 3
added in `8816590e`, so it measured `f75ca887`. Those edits are out of scope for v2.

## Gap 1 re-verification (v1 Gap 1: CLOSED)

**Fix read.** `canonicalise` now joins without `normpath` (`h_mad_target_identity.py:77`). While the
walked prefix exists, a `..` is handled in one of two ways (`:87-96`):
- after a symlink, it takes the parent of the link's opened referent
  (`os.path.dirname(canonical_directory(current))`, `:89-90`);
- otherwise, it takes the opened parent (`canonical_directory(os.path.dirname(current))`, `:92`).

An `OSError` on either open is an arm-2 unresolvable (`:93-95`). Only the absent remainder is
collapsed lexically: `normpath(join(prefix, *components[deepest_directory_index+1:]))` (`:129-130`),
which is FR-1 step 5.

**Measured independently.** My scratch fixture was the spec's M-6: a real `tests/`,
`tests/l -> ../src/sub`, a real `src/sub/`, `src/prod.py`, a governing `step5` state and `git init`.
The spelling was `tests/l/../prod.py`. I drove the Claude gate with a `Write` payload and
`CLAUDE_PROJECT_DIR`. I drove the Codex gate with a stdin `apply_patch` payload
(`*** Begin Patch / *** Update File: tests/l/../prod.py`), `cwd` set to the root, and
`CODEX_PROJECT_DIR`. Each tree came from `git archive <sha> h-mad`.

| Tree | Claude gate | Codex gate | `canonicalise` |
|---|---|---|---|
| `15681a53` (baseline) | allow | deny `no-test-resolved` | (module absent) |
| `1d454948` (v1) | allow | allow | `R/tests/prod.py` (the exempt directory, wrong) |
| `f75ca887` | **deny `no-test-resolved`** | **deny `no-test-resolved`** | `R/src/prod.py`, which is where the kernel writes |

So AC-1.2 is met (fixed: Claude deny `no-test-resolved`; unfixed: allow), and the Codex regression
that v1 recorded is gone.

**v1 fix steps, each checked:**
1. Pre-walk `normpath` removed (`:77`).
2. `..` is taken after the preceding symlink while the prefix exists (`:87-96`). It is lexical only
   inside the absent remainder (`:129-130`).
3. All three M-6 fixtures now have the spec's shape:
   - `test_claude_dotdot_after_symlink_denies` (`h-mad/tests/test_h_mad_tdd_gate_judge.py:510-517`);
   - the differential M-6 cell (`h-mad/tests/test_h_mad_tdd_gate_differential.py:70-74`);
   - the probe (`docs/03-analysis/probes/tdd-gate-fail-opens/reproduce.py:295-296`).
4. New tests:
   - `test_codex_dotdot_after_symlink_denies` (`test_h_mad_codex_tdd_gate_judge.py:288-294`);
   - `test_dotdot_after_symlink_follows_the_kernel`, plus the control
     `test_dotdot_inside_absent_remainder_collapses_lexically` (`test_h_mad_target_identity.py:92-110`).

   New mutation row TI8 (`if S_ISLNK` → `if False`). In a scratch copy of `f75ca887`:
   - TI8 turns 4 of the 5 selected dotdot/M-6/deny-count tests red, and 1 of the 131 tests in
     `test_h_mad_tdd_gate_judge.py`.
   - Restoring the pre-walk `normpath` (the row v1 asked for) gives the same result: 4 failed, and
     1 failed in the Claude file. It is caught, but it is **not a committed row**. See carried item
     7.
5. Readings: both still carry 64 `REPRO: cell=` lines, and the MANUAL lines are 80 unfixed, 0
   fixed. The M-6 rows are unfixed `claude allow / codex deny` and fixed `deny / deny`, which matches
   spec row M-6. I re-ran `compare_readings.py reading-unfixed.txt reading-fixed.txt`: rc 0,
   `COMPARE: PASS softened=7 approved=7`, and the sorted output is identical to the committed
   `compare-fixed.txt`.

   `compare-fixed.txt` itself was not rewritten in `f75ca887`. Its last commit is `196f4d70`. It
   matches only because the old and the new M-6 fixtures give the same fixed and unfixed M-6 rows.
   The old fixture measured M-4, and M-4 has those same rows.

**AC-6.1 unfixed half, re-run here with the corrected fixture.** I copied the current
`test_h_mad_tdd_gate_differential.py` and `tdd_gate_support.py` into a `15681a53` archive and ran
them. Hooks and scripts are identical between `48d639f7`, the base of the committed
`t6-unfixed-differential.txt`, and `15681a53`. Result: 16 failed, 6 passed.
- Gate-equality failures: M-4, M-5, M-6, M-7, M-8, M-11, M-12, plus `M-18/m14`.
- Expectation-table failures, in addition: M-2, M-3, M-9, M-10, M-13 (leaf and intermediate), and
  M-14 (by the kind check).
- Derived deny count: Claude expected 13, got 6.

This is v1's picture, now with a spec-literal M-6. The extra `M-18/m14` is the operator-approved
cell that the spec still lags on (D-4), and it is not counted against AC-6.1, as in v1. The
committed `t6-unfixed-differential.txt` predates the fixture fix and was not re-taken. Its M-6 line
happens to read the same.

## Regression sweep over other `..` spellings (new in v2)

Each row is one scratch fixture under a governing `step5` state, driven through both gates (Claude
`Write`, Codex stdin `apply_patch`) and through `canonicalise`, on all three trees. "Kernel" is
where a write actually lands. For absent remainders it assumes `mkdir -p` semantics.

| Spelling (fixture) | Kernel | `15681a53` C / X | `1d454948` C / X | `f75ca887` C / X | Note |
|---|---|---|---|---|---|
| `tests/l/../prod.py` (spec M-6) | `src/prod.py` | allow / deny | allow / allow | deny / deny | Gap 1 closed |
| `/..<R>/src/prod.py` (`..` at `/`) | `src/prod.py` | deny / deny | deny / deny | deny / deny | unchanged |
| `../R/src/prod.py` (`..` at the root, re-enter) | `src/prod.py` | deny / deny | deny / deny | deny / deny | unchanged |
| `src/sub/../prod.py` (plain directory) | `src/prod.py` | deny / deny | deny / deny | deny / deny | unchanged |
| `tests/../src/prod.py` (through an exempt directory) | `src/prod.py` | deny / deny | deny / deny | deny / deny | unchanged |
| `a/b/../mod.py`, `a -> src/sub` (real directory under a link) | `src/sub/mod.py` | deny / deny | deny / deny | deny / deny | unchanged |
| `src/newdir/../prod.py` (absent remainder) | `src/prod.py` | deny / deny | deny / deny | deny / deny | lexical collapse, spec FR-1 step 5 |
| `tests/l/new/../../prod.py` (absent remainder after a link) | `src/prod.py` | allow / deny | **allow / allow** | deny / deny | **a second Gap-1 instance, also closed** |
| `src/newdir/../../tests/x.py` (remainder into `tests/`) | `tests/x.py` (exempt) | allow / allow | allow / allow | allow / allow | correct allow, unchanged |
| `d/../../../src/prod.py`, `d -> a/b/c` (lexically escapes, physically inside) | `src/prod.py` | deny / deny | deny / deny `outside` | deny / deny `no-test-resolved` | now physical; fail-closed on every tree |
| `o/../prod.py`, `o ->` outside `zz/deep` (lexically inside, physically outside) | `zz/prod.py` (outside) | deny / deny `outside` | deny / deny | deny / deny `outside` | kind as at baseline; Claude denies via the raw conjunct |
| `o/../R/src/prod.py`, `o ->` outside `zz` (out and back) | `src/prod.py` | deny / deny | deny / deny | deny / deny | canonical now `R/src/prod.py` (v1: `R/R/src/prod.py`) |
| `../outside.py` (escapes the root) | outside | deny / deny `outside` | same | same | unchanged |
| `tests/l/../../../escape.py` (escapes via a link) | outside | deny / deny `outside` | same | same | unchanged |
| `src/lnk.py/../prod.py`, `lnk.py -> prod.py` | ENOTDIR | deny / deny | deny / deny | deny / deny | write cannot land; verdict inert |
| `src/prod.py/../prod.py` | ENOTDIR | deny / deny | deny / deny | deny / deny | same |
| `a/b/../../tests/test_x.py`, `a` at mode 0311 | `tests/test_x.py` (exempt) | allow / allow | allow / allow | **deny `judge-error` / deny `judge-error`** | **N-1: new tightening** |
| `a/b/../../src/prod.py`, `a` at mode 0311 | `src/prod.py` | deny / deny | deny / deny | deny `judge-error` / deny `judge-error` | kind moves `no-test-resolved` → `judge-error` |
| `tests/l/../prod.py`, `src/sub` at mode 0311 | `src/prod.py` | allow / deny | allow / allow | deny `judge-error` / deny `judge-error` | fail-open closed, as arm 2 |
| `src/tl/in/../test_y.py`, `src/tl -> ../tests`, `tests/in` at mode 0311 | `tests/test_y.py` | allow / allow | allow / allow | allow / allow | unchanged: the opened parent is readable |

C = Claude gate, X = Codex gate. Where no kind is given, a deny is `no-test-resolved`. `outside` is
the Codex "write target is outside or unreadable" reason, which carries no `kind=`.

**Findings from the sweep.**
- **No new fail-open.** Every spelling whose kernel landing is governed production is denied by both
  gates at `f75ca887`.
- The sweep found a **second instance of Gap 1** that v1 did not name: a `..` in an absent remainder
  that follows a link (`tests/l/new/../../prod.py`). `1d454948` allowed it on both gates. It is
  closed by the same fix, because the remainder now collapses against the link's resolved prefix.
- **N-1, a new fail-closed tightening that `f75ca887` introduced.**
  - Where the fix breaks: the non-symlink `..` branch *opens* the parent directory
    (`canonical_directory(os.path.dirname(current))`, `:92`). On a mode-0311 parent (`x` without
    `r`) that open raises `EACCES`, and the target becomes arm-2 unresolvable.
  - What the kernel needs: only `x` to take `..`, so the write would succeed.
  - The effect under governance: `a/b/../../tests/test_x.py` is a governed write of a test file, in
    an exempt location. It moves from allow, on the baseline and on `1d454948`, to deny
    `judge-error` on both gates. Ungoverned, the write is still allowed (arm 2 is refused only when
    governed).
  - Classification: **not an unmet AC.** No AC or design row covers `..` through an unreadable
    directory, and FR-6's domain requires a readable chain. It is arguably within the letter of
    spec FR-3 arm 2 ("an existing component of the … target on which the on-disk-spelling
    primitive's operation raises `OSError`").
  - Why it is still owed: it is a verdict change toward DENY that no document states.
  - Recommendation (operator's choice):
    - either accept it, and add a sentence to the design's FR-3 section;
    - or, in 6b, replace `:92` with `current = os.path.dirname(current)`. For a non-symlink existing
      directory, the spelled parent is already the physical parent, so the open is unnecessary.
      Then add a control cell for this row.
    - The symlink branch (`:90`) opens the link's referent. Its 0311 case (the `src/sub` row above)
      is a deny either way.
- **Unchanged but worth stating.** On spellings that escape the root, the two gates deny with
  different reasons: Claude says `no-test-resolved` through the `# M:H20` raw-spelling conjunct,
  and Codex says "outside". That was already so at `15681a53`. These cells are outside FR-6's
  in-root domain. Both gates fail closed.

## FR Coverage

| FR | ACs Total | ACs Met | Status | Evidence |
|---|---|---|---|---|
| FR-1: one target-normalisation rule | 11 | 11 | ✅ Complete | Canonicaliser `h_mad_target_identity.py:30-183` (`canonicalise` `:56`; `..` rule `:87-96`; absent remainder `:123-132`). AC-1.2 is now met: this analysis's M-6 measurement above, `test_claude_dotdot_after_symlink_denies` `test_h_mad_tdd_gate_judge.py:510-517`, `test_dotdot_after_symlink_follows_the_kernel` `test_h_mad_target_identity.py:92-102`, and TI8 caught in scratch. The other ACs are unchanged from v1. Claude call `h-mad-tdd-gate.sh:221` (`# M:H11`); Codex `_relative_target` `h-mad-codex-tdd-gate.py:225-250`; raw conjunct `h-mad-tdd-gate.sh:266` (AC-1.11); hard-link rule in the canonicaliser `:160-181` and in the hook `h-mad-tdd-gate.sh:252-290` (AC-1.9); AC-1.7 `test_canonical_directory_returns_on_disk_spelling`, all passing in the targeted run of 665 |
| FR-2: `.py` fold before every name test | 5 | 5 | ✅ Complete | `fold_py_suffix` `h_mad_target_identity.py:185-189`; Claude `_fold_py` `h-mad-tdd-gate.sh:122`, applied in the name loops `:252-290`; Codex `_is_production_python` `h-mad-codex-tdd-gate.py:253-260`. Tests as v1, passing |
| FR-3: unresolvable target refused `judge-error` when governed | 6 | 6 | ✅ Complete | Arm 1 `h_mad_target_identity.py:103-118`. Arm 2 at `:61,94,109,116,127,141,155,162,176,179`; the new `:94` is the `..` open, see N-1. Claude `h-mad-tdd-gate.sh:242-250`; Codex `h-mad-codex-tdd-gate.py:432,460`. Readings: M-12/M-13/M-14 deny `judge-error`, M-18 allow, OQ-P1 a/b deny `judge-error` (step5) and allow (step3). The comparator was re-run: PASS |
| FR-4: Codex header grammar | 7 | 7 | ✅ Complete | Hook unchanged since `1d454948`. `_patch_header_paths` `h-mad-codex-tdd-gate.py:170-197`; self-check re-run here: `CODEX-TDD-GATE: PASS`. v1's AC-4.7 negative control (CX-TTRIM → `FAIL parser`, rc 2) stands, because the code is identical |
| FR-5: bounded reap + `judge-timeout` | 5 | 5 | ✅ Complete | `h_mad_tdd_judge.py` unchanged; references as v1 (`:29`, `:70`, `:205-229`, `:283-284`, `:381-383`, `:390-391`, `:23-26`). `test_h_mad_tdd_judge.py`, including both timing tests, passed in this run |
| FR-6: pinned repros + cross-gate differential | 3 | 3 | ✅ Complete | AC-6.1: the differential passes on `f75ca887` (in the 665-test run). On the unfixed tree, re-run here with the corrected M-6, it fails exactly as AC-6.1 states, plus the approved `M-18/m14` (D-4). AC-6.2 `t6-removal-claude.txt` / `t6-removal-codex.txt` (not re-run; the hooks are unchanged). AC-6.3 `t6-dd7-rerun.txt` `cells=126 softened=6 tightened=8`: DD7 exercises the hooks with no `..` cells, so the canonicaliser change cannot move it. It was not re-run |
| FR-7: every guard bites | 1 | 1 | ✅ Complete | Orchestrator (`f75ca887` commit): target_identity 8/8, codex_gate_judge_wiring 33/33, claude_gate_judge_wiring 43/43 ALL_CAUGHT. Anchors re-checked here: `ANCHORS_OK specs=5 mutations=99 ok=99 drifted=0` (98 plus TI8). TI8, and a pre-walk-`normpath` mutant, both caught in a scratch copy |
| FR-8: Codex gate admits the resume oracle | 6 | 6 | ✅ Complete | `h_mad_resume_decision.py`, the Codex hook's safe list and the three adapters are unchanged; references as v1 (`h-mad-codex-tdd-gate.py:49`, `h_mad_resume_decision.py:46,49-65,178-184`, `codex-runtime.md:140`, `grok-runtime.md:115`, `agy-runtime.md:128`). `test_h_mad_resume_decision.py` and `test_h_mad_codex_tdd_gate_judge.py` passed |

AC notes that do not change a count (carried from v1; re-checked):
- **AC-3.3 and AC-6.1, the unfixed M-18/M-14 Codex cell.** It is still deny `judge-error`
  unfixed, and I re-observed that in the unfixed differential re-run. The operator approved it, and
  the spec lags (D-4). It is not counted against either AC.
- **AC-4.5 is recorded as `kind=outside` in the probe.** Unchanged
  (`test_h_mad_codex_tdd_gate_judge.py:469` asserts the reason).

## Gaps

None. v1 Gap 1 is closed (see above). N-1 is not an unmet AC; it is listed for the operator.

## Design-vs-spec items (escalate; not defects, not counted in the rate)

D-1 to D-4 are carried unchanged. No spec or design edit landed after `1d454948`, and the code
sites are unchanged.
- **D-1**: the F2 root-refuse before governance (`h-mad-tdd-gate.sh:243-246`), which design v1.4
  narrows. The spec's FR-3 text still lags.
- **D-2**: Codex parity on a mode-000 root is not met (`rglob` swallows `EACCES`). Owed to the
  operator.
- **D-3**: the design v1.5 conjunct residual (a mis-cased existing root makes
  `CANON_COMPONENT = CANON_ROOT` false).
- **D-4**: the spec's M-18 row, AC-3.3 and AC-6.1 still state the unfixed Codex M-14 cell as allow.
- **New, D-5 (candidate): N-1.** A `..` through a mode-0311 directory is now refused `judge-error`
  when governed, including an exempt test-file write. The spec's FR-3 arm 2 arguably covers it by
  its letter. The design does not state it. Operator's call: accept it and document it, or narrow
  `:92` to a lexical parent for non-symlink directories.

## Carried findings and residuals

Each item was re-verified at `f75ca887`. Where the file is unchanged since `1d454948`, v1's
measurement stands and I re-read the site.

1. **T10a: a non-UTF-8 id file escapes `session_id_from_git_dir`.** UNCHANGED. The code is
   unchanged (`h_mad_resume_decision.py:59-64` still catches only `OSError`). It fails closed (empty
   stdout, rc 1) but does not print the `cannot_judge` token. Not re-run; the file is identical to
   the one v1 measured.
2. **Two load-sensitive timing flakes** (`test_run_bounded_plain_timeout_is_not_reap_failure`,
   `test_timeout_kind`). UNCHANGED. Both passed again in this analysis's targeted run of 665 tests.
3. **Task 5 deviation: `reap_failed` is read after `# M:K3`.** UNCHANGED (`h_mad_tdd_judge.py:381-383`).
   The outcome is the same; JT-PY is caught.
4. **Absolute interpreter in three mutation specs.** UNCHANGED.
   - `codex_gate_judge_wiring`, `claude_gate_judge_wiring` and `tdd_judge_scoring` still use
     `/opt/anaconda3/bin/python`.
   - `target_identity`, which now has 8 rows including TI8, and `resume_decision_git_dir` use
     `python3.11`.
5. **T0 probe defects.** CHANGED: the second defect is fixed.
   - `fr8()` builds its command from `sys.executable`, as before.
   - The M-6 fixture defect that v1 added is **fixed** in `8816590e`
     (`reproduce.py:295-296`, the spec shape).
   - Both readings were re-taken in `f75ca887`: still 64 `REPRO: cell=` lines each. The unfixed
     reading was taken from a `git archive a737962a`, which is the Task 0 commit, one commit after
     `15681a53`, with no hook or script changes.
6. **`reading-fixed.txt` has no `MANUAL:` lines.** UNCHANGED (0 fixed, 80 unfixed). The comparator
   keys only `REPRO` lines.
7. **Low-severity impl-plan 5d items.** UNCHANGED, with one addition.
   - T0 absent-line control: still not run.
   - T11 `cat`-subst control: lexical refuse, by design.
   - T4 `marker[:-1]`: still 0 rows in every mutation spec (re-grepped).
   - Added: v1's Gap-1 fix step 4 asked for "a mutation row that restores the pre-walk `normpath`".
     TI8 mutates the symlink branch instead. A scratch pre-walk-`normpath` mutant is caught by the
     same tests (4 failed + 1 failed), but it is not a committed row.
8. **T7 re-check of the adapters' other gate sentences.** UNCHANGED. The adapters are unchanged,
   the `$(cat …)` claims residual still stands, and there is still no committed record of the T7
   re-check.
9. **Phase 6b fixes after the archreview.** CHANGED: one row added.

   | Commit | Fix | Where it is in the tree |
   |---|---|---|
   | `7e6bee62` | F1 cwd recheck | `h-mad-codex-tdd-gate.py:231-237`, CX-CWD-RECHECK |
   | `d06d82f6` | F3 `_on_disk_component` in the canonicaliser | `h_mad_target_identity.py:38-53` |
   | `e1dfed23` | pin drift `PRODUCTION_TARGET=${CANON_TARGET%/*}/$NAME` | `h-mad-tdd-gate.sh:289`, CG-PARENT |
   | `2a99ef81` | hard-link production-name loop skips test names | `h-mad-tdd-gate.sh:285-289`, CG-PRODNAME |
   | `8816590e` + `f75ca887` | **v1 Gap 1**: `..` after a symlink follows the kernel | `h_mad_target_identity.py:77,87-96,129-130`, TI8 |

   F2 is kept (D-1). archreview v4 #1 was rejected correctly (`h-mad-codex-tdd-gate.py:260`). There
   were five archreview cycles; the authorisation for exceeding the cap is still not separately
   recorded.
10. **The Task 6 differential cannot discriminate which path was judged.** PARTLY CHANGED.
    - Its M-6 cell is now spec-literal (one of v1's three suggestions), and on the unfixed tree it
      now fails for the right reason.
    - The fixture root still has no name-map-mappable prefix, so every judged cell is still
      `no-test-resolved` whichever path is judged.
    - AC-1.8's absent-leaf/absent-parent cells and the hard-link mixed-names cell are still absent.
    - The same limit hides N-1's class and the second Gap-1 instance
      (`tests/l/new/../../prod.py`): neither is a differential cell.

Other residuals observed (carried from v1):
- A hard link named `test_a.py` + `notes.md` leaves `PRODUCTION_TARGET` empty
  (`h-mad-tdd-gate.sh:282-291`). It fails closed by reading; it was not measured. UNCHANGED.
- Census row counts exist only at `f61bb908`. The rows added afterwards, now five with TI8, are
  scored only in commit messages. CHANGED: the count is five, not four.

New residuals at `f75ca887`:
- **N-1** (above): a mode-0311 `..` is now refused `judge-error` when governed. It is fail-closed.
- `..` after a symlink to a *file*, or after a regular file, takes the file's parent. The kernel
  fails with `ENOTDIR`, so the verdict is inert (both gates deny `no-test-resolved`, the same as on
  both earlier trees).

## Test Results
```
cd h-mad && /opt/anaconda3/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_h_mad_target_identity.py tests/test_h_mad_tdd_gate_judge.py \
  tests/test_h_mad_codex_tdd_gate_judge.py tests/test_h_mad_tdd_gate_differential.py \
  tests/test_h_mad_tdd_judge.py tests/test_h_mad_resume_decision.py \
  tests/test_host_runtime_docs.py tests/test_h_mad_codex_runtime.py
665 passed in 278.72s (0:04:38)
```
- Full `h-mad/tests` suite, the orchestrator's run at `f75ca887` (not re-run here): 4870 passed,
  1 failed. The failure is
  `test_h_mad_check_plugin_hooks.py::TestAgainstTheLiveBinary::test_top_level_key_set_still_matches`,
  pre-existing live-binary drift.
- Mutation, orchestrator: target_identity 8/8, codex_gate_judge_wiring 33/33,
  claude_gate_judge_wiring 43/43.
- Anchors, re-checked here: `ANCHORS_OK specs=5 mutations=99 ok=99 drifted=0`.
- Comparator, re-run here: `COMPARE: PASS softened=7 approved=7`, identical to `compare-fixed.txt`.
- Unfixed differential with the current test file, re-run here: 16 failed, 6 passed, matching
  AC-6.1 plus the approved `M-18/m14`.

## Verdict
Match rate: 100% (threshold: 90%). AC-level: 44/44. Tests: 665/665 targeted passing, full suite
4870/4871 with one known pre-existing failure.
→ **Advance to Phase 7.** Gap 1 is closed and independently re-measured on both gates. The `..`
sweep found no new fail-open. For the operator:
- N-1 (candidate D-5): a fail-closed tightening on `..` through a mode-0311 directory. Accept and
  document it, or narrow `:92` in a follow-up.
- D-1 to D-4: reconciliation items, unchanged.

Neither N-1 nor D-1 to D-4 blocks the rate.

## Version History
- v1.0: Initial gap analysis (2026-09-30) at `1d454948` against spec v1.5, design v1.5 and
  impl-plan v1.3. 6/8 FRs, 42/44 ACs. One `code-vs-design` gap: `..` is collapsed lexically before
  the walk, so spec M-6 is allowed on both gates, a Codex regression from `15681a53`. Four
  design-vs-spec items and ten carried findings, each verified.
- v2.0: Phase 6b cycle 1 re-measurement (2026-09-30) at `f75ca887`, after `8816590e` (RED) and
  `f75ca887` (GREEN). Gap 1 closed, independently re-measured on both gates with the spec M-6
  fixture. 8/8 FRs, 44/44 ACs, 100%. A 20-spelling `..` sweep over three trees found no new
  fail-open. It found a second, already-closed Gap-1 instance, and one new fail-closed tightening
  (N-1, mode-0311 `..`) for the operator. The ten carried findings were re-verified: items 5, 7, 9
  and 10 changed.
