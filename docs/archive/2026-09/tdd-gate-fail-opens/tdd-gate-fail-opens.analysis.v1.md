# Analysis: tdd-gate-fail-opens

## Executive Summary
Six of eight FRs are fully met at `1d454948`, and the 662 feature-targeted tests pass. FR-1 (AC-1.2)
and FR-6 (AC-6.1) are not met, for one reason. The shared canonicaliser collapses `..` lexically
before it walks the target (`h-mad/scripts/h_mad_target_identity.py:77`). The spec's own M-6 fixture
therefore resolves to an absent `tests/prod.py`, which is exempt, when the kernel actually writes
`src/prod.py`. Both gates **allow** that write. On the Codex gate this is a regression: the baseline
`15681a53` denied the same spelling `no-test-resolved`. The pinning tests, the differential and the
T0 probe all missed it, because their M-6 fixture adds `tests -> src`, and with that symlink lexical
and physical `..` collapse give the same path. Classification: `code-vs-design`. Verdict: iterate
(Phase 6b), one gap.

## Match Rate: 75%

FR-level: 6 of 8 FRs have every AC met, so 6/8 = 75% (threshold 90%). AC-level: 42 of 44 ACs are
met. The two unmet ACs share one root cause.

Scope of this measurement: spec v1.5, design v1.5, impl-plan v1.3, diff `15681a53..1d454948`
(57 files, +4830/−135). Production code read: `h-mad/scripts/h_mad_target_identity.py`,
`h-mad/hooks/h-mad-tdd-gate.sh`, `h-mad/hooks/h-mad-codex-tdd-gate.py`,
`h-mad/scripts/h_mad_tdd_judge.py`, `h-mad/scripts/h_mad_resume_decision.py`, and the three
adapters.

## FR Coverage

| FR | ACs Total | ACs Met | Status | Evidence |
|---|---|---|---|---|
| FR-1: one target-normalisation rule | 11 | 10 | ⚠️ Partial | Missing AC-1.2 (Gap 1). Canonicaliser `h_mad_target_identity.py:30-168`; Claude call `h-mad-tdd-gate.sh:221` (`# M:H11`); Codex `_relative_target` `h-mad-codex-tdd-gate.py:225-250`; `# M:H20` raw conjunct `h-mad-tdd-gate.sh:266` (AC-1.11, `test_claude_outside_root_symlink_keeps_raw_conjunct`, H20B caught in `t8-census.txt`); hard-link rule `h_mad_target_identity.py:150-168` + `h-mad-tdd-gate.sh:252-290` (AC-1.9, inode precondition asserted `test_h_mad_tdd_gate_judge.py:595,608`, `test_h_mad_codex_tdd_gate_judge.py:347,357`); AC-1.7 `test_canonical_directory_returns_on_disk_spelling`, with the realpath negative control run as mutation TI1 (caught) |
| FR-2: `.py` fold before every name test | 5 | 5 | ✅ Complete | `fold_py_suffix` `h_mad_target_identity.py:171-175`; Claude `_fold_py` `h-mad-tdd-gate.sh:122` used in all three name loops `:252-290`; Codex `_is_production_python` `h-mad-codex-tdd-gate.py:253-260`; `test_py_suffixes_match_bash_fold`; both gates' `*_fold_*`, `*_test_shaped_names_stay_exempt` and `*_trailing_space_is_not_folded` tests; `test_codex_d1_repro_patch_denies` (AC-2.5) |
| FR-3: unresolvable target refused `judge-error` when governed | 6 | 6 | ✅ Complete | Arm 1 `h_mad_target_identity.py:86-106`, arm 2 at every `canonical_directory`/`scandir` site `:58-62,110-166`; Claude `h-mad-tdd-gate.sh:242-250`; Codex `h-mad-codex-tdd-gate.py:432,460`; `reading-fixed.txt` M-12/M-13/M-14 deny `judge-error`, M-18 allow, OQ-P1 a/b deny `judge-error` (step5) and allow (step3). See the design-vs-spec items D-1 to D-3 below (none of them is an AC) |
| FR-4: Codex header grammar | 7 | 7 | ✅ Complete | `_patch_header_paths` `h-mad-codex-tdd-gate.py:170-197` (`\n`-only split `:177`, both-ends trim with `isspace()` minus U+001C–U+001F `:179-182`, exact markers, control/empty path is a bad header); bad header `kind=judge-error` `:438`; self-check `:396-402`. AC-4.7 negative control **run in this analysis**: a scratch copy of the hook with the CX-TTRIM replacement applied printed `CODEX-TDD-GATE: FAIL parser`, rc 2. The unmutated hook prints `CODEX-TDD-GATE: PASS` |
| FR-5: bounded reap + `judge-timeout` | 5 | 5 | ✅ Complete | `REAP_GRACE_S = 1.0` `h_mad_tdd_judge.py:29`; six-field `BoundedRun` with `reap_failed` `:70`; bounded reap `:205-229`; name-map mapping `:283-284`; pytest-path mapping `:382-383`; priority tuple `:390-391`; `KINDS` has 12 members `:23-26`; Claude `JUDGE_DENY_RE` `h-mad-tdd-gate.sh:232`; `reading-fixed.txt` `family=d5 elapsed=3.0 timed_out=True rc=-9`; `test_claude_gate_judge_timeout_stub`, `test_codex_gate_judge_timeout_reason`; `judge-timeout` rows in `test_h_mad_tdd_gate_judge.py:125` and `test_h_mad_codex_tdd_gate_judge.py:92` (AC-5.5) |
| FR-6: pinned repros + cross-gate differential | 3 | 2 | ⚠️ Partial | Missing AC-6.1 (Gap 1: the differential's M-6 cell is not the spec's M-6, and the spec's M-6 fails the expectation row). AC-6.2 `t6-removal-claude.txt` (13 failed) and `t6-removal-codex.txt` (8 failed). AC-6.3 `t6-dd7-rerun.txt` `cells=126 softened=6 tightened=8`, identical to the published counts in `docs/archive/2026-09/codex-tdd-gate-defects/codex-tdd-gate-defects.analysis.md` |
| FR-7: every guard bites | 1 | 1 | ✅ Complete | `t8-census.txt` at `f61bb908`: all 25 floor guards plus 9 extras caught, 5 specs ALL_CAUGHT. After the census, the 6b fixes changed only the canonicaliser and the two hooks. Each 6b commit message reports ALL_CAUGHT for the specs it touched (`7e6bee62` codex 33/33; `d06d82f6` target_identity 7/7, codex 33/33, claude 41/41; `e1dfed23` claude 42/42; `2a99ef81` claude 43/43). Anchors re-checked here: `ANCHORS_OK specs=5 mutations=98 drifted=0`. I did not re-run the mutants: the harness mutates in place, which this analysis is not permitted to do |
| FR-8: Codex gate admits the resume oracle | 6 | 6 | ✅ Complete | Safe-list entry `h-mad-codex-tdd-gate.py:49`; mutually exclusive group `h_mad_resume_decision.py:178-184`; reader `:49-65`; `GIT_DIR_BOUND_S = 10.0` `:46`; `test_codex_hook_admits_adapter_oracle_lines[codex/grok/agy]`, `test_codex_hook_admits_resume_oracle_forms`, `test_codex_hook_refuses_cat_subst_oracle` (AC-8.1); `test_safe_list_resume_options_equal_parser`, `test_codex_hook_refuses_unknown_resume_options` (AC-8.2); `test_git_dir_flag_matches_session_id_token` repo/worktree × owner/other (AC-8.3); `test_git_dir_flag_failure_is_cannot_judge` (AC-8.4, mode-000 asserts `PermissionError`); `test_git_dir_flag_excludes_session_id` (AC-8.5); adapter lines `codex-runtime.md:140`, `grok-runtime.md:115`, `agy-runtime.md:128` (AC-8.6) |

AC notes that do not change a count:
- **AC-3.3 and AC-6.1, the unfixed M-18/M-14 Codex cell.** Both ACs say the unfixed Codex gate
  allows M-18's M-14 case. The committed unfixed reading has it deny `judge-error`. The operator
  approved that move on 2026-09-30; spec v1.5 records it but leaves the M-18 row, AC-3.3 and AC-6.1
  "for a separate decision". I counted AC-3.3 as met: its fixed half holds, and the stale half is a
  premise about the old tree. For the same reason, the extra `M-18/m14` in
  `t6-unfixed-differential.txt`'s gate-equality set (8 cells, where the AC says "exactly" 7) is not
  counted against AC-6.1. AC-6.1 fails on Gap 1 instead.
- **AC-4.5 is recorded as `kind=outside` in the probe.** The probe labels every kind-less Codex
  denial `outside`. The test asserts the "could not identify" reason directly
  (`test_h_mad_codex_tdd_gate_judge.py:469`).

## Gaps

### Gap 1: `..` after a symlink is collapsed lexically, not by the kernel (AC-1.2, AC-6.1) — `code-vs-design`
- **Missing**: FR-1 step 1 says no lexical `..` collapse happens before step 2, and step 2 takes
  each `..` "after the preceding symlink, as the kernel takes it". `canonicalise` runs
  `os.path.normpath(os.path.join(base, target))` before its walk (`h_mad_target_identity.py:77`).
  On the spec's M-6 fixture (a real directory `tests/`, with `tests/l -> ../src/sub` and
  `src/prod.py` present), the spelling `tests/l/../prod.py`:
  - is written by the kernel to `R/src/prod.py`;
  - is canonicalised to the absent `R/tests/prod.py` (`names=('prod.py',)`, `unresolvable=False`),
    which is an exempt directory.
- **Measured here** (scratch fixture, `_run` from the differential module, governing `step5`):

  | Tree | Claude gate | Codex gate |
  |---|---|---|
  | `1d454948` (fixed) | allow | allow |
  | `15681a53` (baseline, via `git archive`) | allow | deny `no-test-resolved` |

  So the Codex gate has **regressed**: it used to refuse this spelling and now lets it through, a
  new fail-open.
- **Why nothing caught it**: three places use the same altered fixture, which also sets
  `tests -> src`:
  - `test_claude_dotdot_after_symlink_denies` (`h-mad/tests/test_h_mad_tdd_gate_judge.py:510-517`);
  - the differential's M-6 cell (`h-mad/tests/test_h_mad_tdd_gate_differential.py:70-75`);
  - the probe (`docs/03-analysis/probes/tdd-gate-fail-opens/reproduce.py:295-296`).

  With `tests -> src`, lexical collapse gives `tests/prod.py`, and that is `src/prod.py` anyway. The
  fixture cannot tell the two rules apart. What it actually measures is M-4, and the committed M-6
  rows in both readings are M-4 rows.
- **Classification**: `code-vs-design`. The design does not narrow the rule. It never mentions a
  pre-walk collapse, and its test plan lists "`..`-after-symlink spellings of a governed production
  file" among the cells that must deny (design `:1031`, and the M-6 rows at `:1056`, `:1132`). The
  code and the tests diverge from a design that follows the spec.
- **Where it should be**: `h-mad/scripts/h_mad_target_identity.py:77-108`, plus the three fixtures
  listed above.
- **Fix**:
  1. Join the target without `normpath`.
  2. In the walk, while the prefix exists, resolve a `..` component against the prefix's resolved
     directory (for example `current = os.path.dirname(canonical_directory(current))`, or the parent
     of `os.path.realpath(current)`). Collapse lexically only inside the absent remainder, which is
     FR-1 step 5.
  3. Change the three fixtures to the spec's M-6: a real `tests/` directory with
     `tests/l -> ../src/sub`, and no `tests -> src`.
  4. Add a Codex-gate M-6 test, and a mutation row that restores the pre-walk `normpath`.
  5. Re-take `reading-fixed.txt` and `compare-fixed.txt`. Once the probe is fixed, the unfixed M-6
     row changes too, so the unfixed reading must be re-measured as well. Record the delta.

## Design-vs-spec items (escalate; not defects, not counted in the rate beyond the ACs above)

- **D-1: F2, the Claude gate refuses an unenterable root before governance.**
  `h-mad-tdd-gate.sh:243-246` refuses `judge-error` "project root (CLAUDE_PROJECT_DIR) cannot be
  entered" before `_chain_may_hold_state` runs, whenever the root is absent, not a directory, or
  not `x`. Spec FR-3's description says an unresolvable target with no governing state is allowed.
  Design v1.4 narrows that rule, by operator decision after archreview v1 and v3, to roots that can
  be entered, and it pins the absent-root member (`test_unenterable_project_dir_refuses`). No AC
  covers a root that cannot be entered, so no AC is unmet. Recommendation: amend spec FR-3 to state
  the design v1.4 narrowing. The operator has already chosen the behaviour; only the spec lags.
- **D-2: Codex parity on a mode-000 root is not met.** Design v1.4 records that the Codex gate's
  `rglob` swallows EACCES, so the status is inactive and the write is allowed, while the Claude gate
  refuses. This is outside FR-6's domain (OD-5 needs a readable chain) and it is owed to the
  operator.
- **D-3: the design v1.5 conjunct residual.** On an existing root spelled in a different case, the
  Claude root-refuse test `CANON_COMPONENT = CANON_ROOT` is false, because the component is now the
  on-disk spelling while the root is the spelled one. The design records this as owed to the
  operator.
- **D-4: spec-internal staleness** (spec v1.5's own note). The M-18 table row, AC-3.3 and AC-6.1
  still state the unfixed Codex M-14 cell as allow. A spec edit is owed.

## Carried findings and residuals

1. **T10a: a non-UTF-8 id file escapes `session_id_from_git_dir`.** Verified by reading and by
   running it. `h_mad_resume_decision.py:59-64` catches only `OSError` around
   `read_text(encoding="utf-8")`. In a scratch repository I wrote the id file as the bytes
   `\xff\xfe` and ran `--host codex --session-id-from-git-dir`. The result was a
   `UnicodeDecodeError` traceback, rc 1, and empty stdout. Callers treat an empty stdout as "no
   decision" and halt, so the failure is closed. But the answer is not the documented
   `cannot_judge` token. The case is outside the six failure modes of spec FR-8 change 2 (which
   names `OSError`), so no AC is unmet. Fix: catch `(OSError, UnicodeDecodeError)`, or `ValueError`,
   and add a case to `test_git_dir_flag_failure_is_cannot_judge`. The `git rev-parse` call uses
   `text=True`, so a non-UTF-8 git-dir path hits the same class.
2. **Two load-sensitive timing flakes.**
   - `test_run_bounded_plain_timeout_is_not_reap_failure` (`test_h_mad_tdd_judge.py:481-490`) gives
     a 1.0 s deadline to a plain sleeper. It asserts `reap_failed is False`, which needs the killed
     group's pipes to close within `REAP_GRACE_S = 1.0` s, and it asserts less than 4.0 s elapsed.
   - `test_timeout_kind` (`:816-828`) races the sleeper fixture against `budget_s=1.0` with a 6.0 s
     ceiling. It predates this feature: `git log -S` traces it to `f19eeb31`.

   Both passed in this analysis's targeted run of 662 tests. I did not reproduce the flake. Both
   are sensitive to load, not logically wrong.
3. **Task 5 deviation: `reap_failed` is read after `# M:K3`.** Verified at
   `h_mad_tdd_judge.py:381-383`: the `# M:K3` score line is followed by
   `if reap_failed: kind = "judge-timeout"`. Impl-plan `:781` says it is read before `# M:K3`. The
   outcome is the same, because the later assignment overrides `score()`'s kind and the `# M:K3`
   line stays byte-identical. JT-PY is caught.
4. **Absolute interpreter in three mutation specs.** Verified: `command[0]` is
   `/opt/anaconda3/bin/python` in `codex_gate_judge_wiring.json`, `claude_gate_judge_wiring.json`
   and `tdd_judge_scoring.json`, both at `1d454948` and at `15681a53` (`git show 15681a53:<spec>`).
   So it predates the feature. The plan's execution rules forbid it for this feature's rows. The
   feature's two new specs, `target_identity.json` and `resume_decision_git_dir.json`, use
   `python3.11`.
5. **T0 probe defect found at T9.** Verified from commit `196f4d70` and the readings. `fr8()` now
   builds its command from `sys.executable` (`reproduce.py:198`). The committed
   `reading-unfixed.txt` has all three FR-8 cells deny (`kind=outside`). The commit reports a
   re-measure of the unfixed tree with the fixed probe: 64 of 64 keys identical. Both readings carry
   64 `REPRO: cell=` lines (counted). This analysis adds a second probe defect of the same shape:
   the M-6 fixture (Gap 1).
6. **`reading-fixed.txt` has no `MANUAL:` lines.** Verified: 0 `MANUAL:` lines in
   `reading-fixed.txt`, 80 in `reading-unfixed.txt`. The R-4 and R-5 rows are manual
   re-measurements by the operator. `compare_readings.py` keys only `REPRO: cell=` lines, so
   `COMPARE: PASS softened=7 approved=7` says nothing about them.
7. **Low-severity impl-plan 5d items.**
   - T0 has no control for an absent `agent-cli-reachable` line. The code handles the case:
     `compare_readings.py:44-45` raises when the collected list is not `["no"]`, which includes an
     empty list. But the only committed control is the `=yes` one (control 3); no absent-line
     control was run.
   - T11's `test_codex_hook_refuses_cat_subst_oracle` is refused lexically by
     `SIMPLE_SHELL_COMMAND` before the safe list is consulted, so it cannot discriminate the new
     entry. It is AC-8.1's control ("denied fixed and unfixed"), by design.
   - T4's empty-path equality rule (`header == marker[:-1]`, `h-mad-codex-tdd-gate.py:185`) has no
     mutation row: `grep -c 'marker\[:-1\]'` over `h-mad/tests/mutation-specs/*.json` returns 0
     everywhere. `test_codex_empty_header_path_is_judge_error` pins the behaviour but is not scored.
8. **T7 re-check of the adapters' other gate sentences.** It holds, with one residual the spec
   already names.
   - codex: `codex-runtime.md:35-37` (`judge-timeout`, the `judge-error` component) and `:75-76`
     ("shell calls are fail-closed except for a small allowlist") match the fixed gate.
   - grok: `grok-runtime.md:71-79` still says the gate "reads `tool_input.file_path`, not grok's
     `toolInput`". That is still true (`h-mad-tdd-gate.sh:200`).
   - agy: `agy-runtime.md:54-64` claims neither hook speaks agy's contract, which is unchanged.
   - Residual: every adapter's claims section still lists the five `h_mad_state_write.py` lines with
     `$(cat …)` (for example `codex-runtime.md:141-145`), and the Codex gate refuses them under a
     governing `step5`. That includes `--beat`, while `codex-runtime.md:76` says "Keep claims alive
     during long dispatches". This is spec FR-8's stated residual, not a stale sentence. I found no
     committed record that the T7 re-check was performed. `f61bb908` covers the T7 edits only.
9. **Phase 6b fixes after the archreview.** Each was verified against its commit and the tree.

   | Commit | Fix | Where it is in the tree |
   |---|---|---|
   | `7e6bee62` | F1: the canonical cwd is rechecked by `_payload_cwd_base` | `h-mad-codex-tdd-gate.py:231-237`, row CX-CWD-RECHECK |
   | `d06d82f6` | F3: `_on_disk_component` moves into the canonicaliser, and the Codex scandir block is removed (operator decision; design v1.5) | `h_mad_target_identity.py:38-53`, applied at every arm-2 return |
   | `e1dfed23` | pin drift: `PRODUCTION_TARGET=${CANON_TARGET%/*}/$NAME` | `h-mad-tdd-gate.sh:289`. The commit states `15681a53` and main give `test-missing`, so this was a regression the branch introduced. Row CG-PARENT, `test_claude_absent_intermediate_dirs_judge_the_real_target[two-absent]` |
   | `2a99ef81` | the hard-link production-name loop skips test names | `h-mad-tdd-gate.sh:285-289`, row CG-PRODNAME |

   - F2 was kept by operator decision, and design v1.4 narrows it (D-1). The block is present at
     `h-mad-tdd-gate.sh:243-246`.
   - archreview v4 #1 was rejected correctly: the `tests`/`fixtures` parts check is at
     `h-mad-codex-tdd-gate.py:260`.
   - Review cycles: five archreview reports, v1 to v5, where the cap is 2. The orchestrator states
     the operator authorised the overrun; I found no separate record of that authorisation.
10. **The Task 6 differential missed the pin-drift regression.** Verified. The fixture root has no
    `hematology-paper-writer/`, `clinical-statistics-analyzer/` or `shared/` prefix, so
    `h_mad_derive_test_path.sh` exits 0 with no output for every cell. Every judged cell is
    therefore `no-test-resolved` whichever path the gate judges. No cell has absent intermediate
    directories either: AC-1.8's `src/newpkg/mod.py` is not a differential cell. Suggestion: **widen
    the fixture, not FR-6's domain.** The domain ("absolute in-root spellings over a readable
    chain") already contains these spellings. What is missing is cells where the judged path
    matters:
    - add AC-1.8's absent-leaf and absent-parent spellings under a name-map-mappable prefix (for
      example `hematology-paper-writer/tools/x.py` and `hematology-paper-writer/newpkg/x.py`), whose
      expected kind is `test-missing`, not `no-test-resolved`;
    - add the hard-link mixed-names cell (`test_a.py` + `z.py`) under the same prefix;
    - add the spec-literal M-6 cell (Gap 1).

    Gap 1 is a second instance of this finding: the differential passes because its cells cannot
    discriminate. An expectation-table row that says only `deny no-test-resolved` pins nothing about
    which path was judged.

Other residuals observed:
- A hard link whose names are `test_a.py` and `notes.md` in one directory leaves `PRODUCTION_TARGET`
  empty (`h-mad-tdd-gate.sh:282-291`), so the Claude gate calls the judge with `--target ""`. By
  reading the code this is fail-closed; it was not measured.
- A census row count exists only at `f61bb908`. The four rows added afterwards (TI7,
  CX-CWD-RECHECK, CG-PARENT, CG-PRODNAME) are scored only in their fix commits' messages, not in a
  committed census file.

## Test Results
```
cd h-mad && /opt/anaconda3/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_h_mad_target_identity.py tests/test_h_mad_tdd_gate_judge.py \
  tests/test_h_mad_codex_tdd_gate_judge.py tests/test_h_mad_tdd_gate_differential.py \
  tests/test_h_mad_tdd_judge.py tests/test_h_mad_resume_decision.py \
  tests/test_host_runtime_docs.py tests/test_h_mad_codex_runtime.py
........................................................................ [ 87%]
........................................................................ [ 97%]
..............                                                           [100%]
662 passed in 287.38s (0:04:47)
```
Full `h-mad/tests` suite (the orchestrator's run, not re-run here): 4867 passed, 1 failed. The failure
is `test_h_mad_check_plugin_hooks.py::TestAgainstTheLiveBinary::test_top_level_key_set_still_matches`,
live-binary drift that predates this feature.

Mutation anchors: `ANCHORS_OK specs=5 mutations=98 ok=98 drifted=0` over the five feature specs.

## Verdict
Match rate: 75% (threshold: 90%). AC-level: 42/44. Tests: 662/662 targeted passing, full suite
4867/4868 with one known pre-existing failure.
→ **Iterate: 1 gap to close** (Gap 1, `code-vs-design`, a Phase 6b fix to the canonicaliser plus the
three M-6 fixtures). Closing it closes AC-1.2 and AC-6.1 together, which takes FR-1 and FR-6 to
complete (8/8). D-1 to D-4 are operator reconciliation items: 6b cannot close them, and they do not
block the rate.

Note for the orchestrator: protocol step 6 also requires the same content at the unversioned
`docs/03-analysis/tdd-gate-fail-opens.analysis.md`. That file was not written here, because this
dispatch permitted creating one file only.

## Version History
- v1.0: Initial gap analysis (2026-09-30) at `1d454948` against spec v1.5, design v1.5 and impl-plan
  v1.3. 6/8 FRs, 42/44 ACs. One `code-vs-design` gap: `..` is collapsed lexically before the walk,
  so spec M-6 is allowed on both gates, a Codex regression from `15681a53`. Four design-vs-spec
  items and ten carried findings, each verified.
