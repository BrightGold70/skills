# Phase 6a gap analysis — codex-tdd-gate-defects

Verifier: fresh context, read-only on the worktree. Worktree `/Users/kimhawk/orca/skills-codex-tdd-gate-defects`,
branch `feature/codex-tdd-gate-defects`, HEAD `a6477488`, base `d68635159ad5ec64b03d2852dc25536c4e3ea657`.

Match Rate: 98%

**Denominator rule.** The rate is over the 49 spec ACs (AC-0.1 … AC-8.1). AC-6.5, AC-6.6 and AC-6.7 are
mutually exclusive branches selected by FR-0. The committed reading
(`docs/03-analysis/probes/codex-tdd-gate-defects/v0.out`: `READING=E1_DOES_NOT_BLOCK FORM_A=BLOCKS FORM_B=BLOCKS CHOSEN=b`)
selects AC-6.5 with form (b), so AC-6.6 and AC-6.7 are N/A and leave the denominator: 47 ACs.
IMPLEMENTED = 1, PARTIAL = 0.5, MISSING = 0. CHANGED rows that a design decision authorises count as
IMPLEMENTED. Score: 45 IMPLEMENTED + 2 PARTIAL = 46 / 47 = 97.9%.
V-0 / V-1r / V-1 are not pytest ACs and are outside the rate (status at the end of the table).

**Test evidence re-run by me.** Targeted run (not the full suite) of the 12 relevant files:
`test_h_mad_tdd_judge.py test_h_mad_tdd_gate_judge.py test_h_mad_codex_tdd_gate_judge.py test_h_mad_tdd_gate_docs.py
test_h_mad_parse_tasks_paths.py test_h_mad_audit_suite_gate.py test_h_mad_tdd_gate_support.py test_h_mad_codex_runtime.py
test_h_mad_tdd_gate_codex.py test_h_mad_tdd_gate_state_resolution.py test_h_mad_wire_pin_gate.py test_h_mad_audit_gate.py`
→ `586 passed`. The command was `python3 -m pytest`, rewritten by the rtk proxy. The PATH `python3` (Homebrew 3.14) has no pytest, so the run used a different interpreter, most likely `/opt/anaconda3/bin/python`, the one the specs name. Mutation harness re-run on all eight feature specs in a `git archive HEAD` copy under
`/private/tmp/.../scratchpad/copy` (never in the worktree) — results under AC-8.1.

Paths below: J = `h-mad/scripts/h_mad_tdd_judge.py`, CG = `h-mad/hooks/h-mad-tdd-gate.sh`,
XG = `h-mad/hooks/h-mad-codex-tdd-gate.py`, AG = `h-mad/scripts/h_mad_audit_gate.py`,
WP = `h-mad/scripts/h_mad_wire_pin_gate.py`. Test files: TJ = `test_h_mad_tdd_judge.py`,
TCG = `test_h_mad_tdd_gate_judge.py`, TXG = `test_h_mad_codex_tdd_gate_judge.py`, TD = `test_h_mad_tdd_gate_docs.py`,
TPT = `test_h_mad_parse_tasks_paths.py`, TAS = `test_h_mad_audit_suite_gate.py`, TCR = `test_h_mad_codex_runtime.py`
(all under `h-mad/tests/`).

## FR / AC table

| ID | Status | Implementation | Pinning test node(s) / evidence |
|---|---|---|---|
| **FR-0** | PARTIAL | probe `docs/03-analysis/probes/codex-tdd-gate-defects/v0-blocking-contract.sh`, reading `v0.out` | — |
| AC-0.1 | PARTIAL | recipe + reading + claude version (2.1.283) + the four replay rcs are committed (`v0.out`, commit `10553592`, which adds only `v0.out`) | **Gap:** the captured replay payload (`$S/payload.json`) and the per-arm `HIT <nonce>` logs (`$S/<arm>.log`) live only in the scratch dir `/var/folders/.../hmad-v0.3XE4dM`; nothing under `probes/` stores them. `v0.out` carries no skills-sha stamp (only the commit implies one). **Recoverable:** that scratch dir still exists (checked 2026-09-29: `payload.json`, `E0/E1/E2/EJ.log`, `*.replay.log`, `replay.txt`, `claude.version` present). Committing them closes the gap without re-running the probe. |
| AC-0.2 | IMPLEMENTED | `v0.out`: `READING=E1_DOES_NOT_BLOCK FORM_A=BLOCKS FORM_B=BLOCKS CHOSEN=b` | CG:4 `readonly REFUSAL_FORM=b` follows it |
| **FR-1** | IMPLEMENTED | J (whole file); XG `_load_judge` / `_main_guarded`; CG:188-207 | — |
| AC-1.1 | IMPLEMENTED | `git grep -n h_mad_derive_test_path.sh -- h-mad/hooks/` → rc 1 (no match) | TCG::test_hooks_reach_the_name_map_only_through_the_judge |
| AC-1.2 | IMPLEMENTED | 11 kinds, J:23-26 | TXG::test_codex_gate_kind[11 params]; TCG::test_claude_gate_kind[11 params] (judge-error via broken import / malformed CLI) |
| AC-1.3 | IMPLEMENTED | CG:71-74, 202-207 (rc read separately; ALLOW needs `JRC=0`) | TCG::test_judge_stub_is_judge_error[empty-line,two-lines,trailing-blank-line,maybe,unknown-kind,traceback-rc1,allow-rc1]; TCG::test_state_stub_is_judge_error[zero-lines,two-lines,trailing-blank-line,bad-value,none-rc1] |
| **FR-2** | PARTIAL (AC-2.8) | J `resolve` 198-261; WP `_PATHS_FIELD_RE` / `_NONE_VALUE_RE` | — |
| AC-2.1 | IMPLEMENTED | J:218-235 base walk | TJ::test_hemasuite_layout_resolves_from_the_task |
| AC-2.2 | IMPLEMENTED | WP `_PATHS_FIELD_RE` | TJ::test_label_spelling_resolves_the_same; TJ::test_tests_prose_line_contributes_no_candidate; TPT::test_paths_label_spelling, ::test_tests_plural_prose_label_contributes_nothing |
| AC-2.3 | IMPLEMENTED | WP `_NONE_VALUE_RE` | TJ::test_none_valued_production_does_not_match; TPT::test_none_value_contributes_nothing |
| AC-2.4 | IMPLEMENTED | J:225-231, 339-349 | TJ::test_several_candidates_first_red_allows; ::test_several_candidates_all_green_names_both |
| AC-2.5 | IMPLEMENTED | J:239-242 (`# M:R1`) | TJ::test_task_match_is_authoritative_over_the_name_map |
| AC-2.6 | IMPLEMENTED | J:246-261 | TJ::test_name_map_source_allows_via_the_cli[absolute,relative] |
| AC-2.7 | IMPLEMENTED | J:251-253 | TJ::test_unmapped_path_is_no_test_resolved (asserts plan path, `matched none`, `name map: empty for tools/x.py`) |
| AC-2.8 | PARTIAL | J:213-215 | Deny half pinned: TJ::test_unreadable_plan_is_named_in_test_missing, ::test_unreadable_plan_with_a_passing_name_map_test_is_test_passing. **Gap:** the AC's first sentence ("its failing test allows the write" with an invalid-UTF-8 plan) has no fixture — `b"\xff\xfe"` appears only at TJ:521 and TJ:878, both deny. I executed it by hand (scratch `r5`, `/opt/anaconda3/bin/python J judge …`) → `TDD-JUDGE: ALLOW kind=red-measured source=name-map`, so behaviour is right; only the pin is missing. |
| AC-2.9 | IMPLEMENTED | `git diff base HEAD -- h-mad/scripts/h_mad_wire_registry.py` empty; wire_pin/assemble_tdd/wire_registry test files have no diff | TPT::test_corpus_old_fields_unperturbed, ::test_field_re_is_unchanged, ::test_existing_fields_unchanged |
| **FR-3** | IMPLEMENTED | J `select_interpreter` 277-290, `venv_contained` 264-274; XG `_contained_venv_executable` | — |
| AC-3.1 | IMPLEMENTED | J:277-290 | TJ::test_contained_venv_shim_runs_pytest; ::test_select_interpreter_takes_the_nearest_venv |
| AC-3.2 | IMPLEMENTED | J:267 (`# M:V1`) | TJ::test_escaping_venv_denies_before_any_run; ::test_venv_contained_rows |
| AC-3.3 | CHANGED→IMPLEMENTED (OD-1 accepted) | J:264-274 (no final-hop check) | TJ::test_real_venv_interpreter_symlink_is_accepted |
| AC-3.4 | IMPLEMENTED | XG `_contained_venv_executable`, `_safe_shell_command` (`# M:G9`) | TXG::test_shell_venv_token[11 ids]; ::test_shell_policy_corpus_allows_exactly_the_expected_rows (251 rows, 17 allow) |
| AC-3.5 | IMPLEMENTED | — | TCR::test_codex_hook_rejects_untrusted_executable_paths (TCR diff touches one other line only) |
| AC-3.6 | IMPLEMENTED | XG `_safe_shell_command` python-script branch | The control-script half is pinned only by the corpus rows `contained/*/state-write` (allow), `venv-symlink-out/*/state-write` (deny), `control/usr-python-state-write` (allow) in TXG::test_shell_policy_corpus_allows_exactly_the_expected_rows. Note: TXG::test_shell_control_allowlist_under_a_venv's `contained-venv` / `usr-bin-python3-control` / `escaping-venv` cases run **pytest** argv, not a control script — the test name over-claims; only its `script-outside-scripts` case exercises the allowlist. |
| **FR-4** | IMPLEMENTED | J `score` 298-314; AG `_suite_summary`, `run_suite` | — |
| AC-4.1 | IMPLEMENTED | J:293-302 | TJ::test_pytest_missing_denies[project-venv,gate-interpreter] |
| AC-4.2 | IMPLEMENTED | J:298-314 | TJ::test_scoring_kinds (RED, GREEN, empty, skipped-only, subtests rows) |
| AC-4.3 | IMPLEMENTED | J:308 (`# M:K2`) | TJ::test_scoring_kinds (import-error row) |
| AC-4.4 | IMPLEMENTED | J:345 (rc unused) | TJ::test_rc_selects_nothing |
| AC-4.5 | IMPLEMENTED | J `_run_bounded` | TJ::test_timeout_kind (budget 1.0 s, asserts < 6.0 s); ::test_run_bounded_kills_the_process_group. See Defect D5: the bound does not hold when a detached grandchild keeps the pipe. |
| AC-4.6 | IMPLEMENTED | J:359-360 | TJ::test_scoring_kinds (asserts "import" and "inside the test body") |
| AC-4.7 | IMPLEMENTED | AG `_SGR_RE`, `_SUMMARY_LINE_RE`, `_suite_summary`, `run_suite` | TAS::test_run_suite_table_row[15 ids incl. one-error, no-tests-ran, three-skipped, five-deselected, one-xfailed, coloured, subtests-passed, subtests-failed-run]; TAS::test_suite_summary_reads_the_line |
| **FR-5** | IMPLEMENTED | XG `_payload_cwd_base`, `_main_guarded`; J `read_chain` | — |
| AC-5.1 | IMPLEMENTED | XG `_relative_target(root, raw, cwd)` | TXG::test_payload_cwd_base_resolves_a_subproject_relative_target; ::test_payload_cwd_deny_names_the_prefixed_path; ::test_payload_cwd_outside_the_root_falls_back_to_the_root |
| AC-5.2 | IMPLEMENTED | J:120-143 | TXG::test_root_step5_governs_a_subproject_with_its_own_state |
| AC-5.3 | IMPLEMENTED | — | TCR::test_codex_hook_scopes_nested_state_to_the_target_project, ::test_codex_hook_resolves_git_root_from_nested_cwd (unmodified); ::test_codex_hook_rejects_pytest_no_tests_collected_as_red (only `exit 1`→`no-tests-ran` changed) |
| AC-5.4 | IMPLEMENTED | XG `main` try/except (`# M:G2`) | TXG::test_codex_gate_kind[judge-error] (broken `scripts/h_mad_tdd_judge.py` raising ImportError) |
| **FR-6** | IMPLEMENTED | CG (whole file) | — |
| AC-6.1 | CHANGED→IMPLEMENTED (DD-13) | CG:107-150 (`# M:H1`, `# M:H2`) | TCG::test_claude_code_payload_reaches_codex_authorship; ::test_stdin_target_beats_positional; ::test_positional_alone_reaches_codex_authorship |
| AC-6.2 | IMPLEMENTED | — | diff of `test_h_mad_tdd_gate_codex.py` / `test_h_mad_tdd_gate_state_resolution.py`: the listed `returncode` / stderr assertions move to `decision(r, hook_form(HOOK))`; other changes are harness-only (`HOOK` now the worktree hook, `stdin=DEVNULL`) |
| AC-6.3 | IMPLEMENTED | CG:202-207; J | TCG::test_no_pytest_on_path_passing_test_is_refused |
| AC-6.4 | IMPLEMENTED | CG:188-207 (no existence check) | TCG::test_new_production_file_with_passing_test_is_refused |
| AC-6.5 | IMPLEMENTED (form b) | CG:15-25 `_refuse` | TCG::test_refusal_sites_use_the_chosen_form[sites]; ::test_hook_has_no_exit_1; ::test_refusal_form_is_a_readonly_literal; `grep -c '^\s*exit 1\s*$' CG` → 0 |
| AC-6.6 | N/A | branch not selected by FR-0 | — |
| AC-6.7 | N/A | branch not selected by FR-0 | — |
| AC-6.8 | IMPLEMENTED | CG:189 `_read_state --target` | TCG::test_subproject_step5_under_root_step3_is_governed |
| AC-6.9 | IMPLEMENTED | CG:174-186 before 189 | TCG::test_unreadable_chain_refuses_production; ::test_exempt_write_on_unreadable_chain_is_allowed[state-file,test-file,doc] |
| AC-6.10 | IMPLEMENTED | J:369-370 (`# M:C3`, `# M:C5`); CG:190 | TCG::test_codex_escape_needs_every_record[2]; ::test_codex_escape_all_declared_proceeds_to_judge[2] |
| AC-6.11 | IMPLEMENTED | CG:37-62 | TCG::test_fast_path_defers[dangling-state-symlink,missing-parent,unsearchable-docs] |
| AC-6.12 | IMPLEMENTED | no `jq` in CG | TCG::test_no_jq_on_path_still_judges |
| AC-6.13 | CHANGED→IMPLEMENTED (DD-13) | CG:168-172 | TCG::test_empty_target_rule[active-root,unreadable-root,no-step5-root] |
| AC-6.14 | IMPLEMENTED | J:132-133 (`# M:H14`) | TCG::test_outside_root_target_is_governed_by_root[active,no-step5] |
| AC-6.15 | CHANGED→IMPLEMENTED (DD-7 kept; v1.3 §D9) | CG:155, 177-181 | TCG::test_relative_targets; ::test_dd7_differential_matches_the_published_cells; ::test_root_under_a_test_directory_is_governed; ::test_outside_root_exemption_needs_both_spellings. See Defect D3: the §D9 root-ancestry fix holds only for the physical spelling of the root. |
| **FR-7** | IMPLEMENTED | `h-mad/references/codex-runtime.md`, `agy-runtime.md`, `codex-implementer-prompt.md`, `h-mad/SKILL.md` | — |
| AC-7.1 | IMPLEMENTED | codex-runtime.md §Trust boundary | TD::test_trust_boundary_states_the_venv_rule; TCR::test_codex_adapter_states_pytest_trust_boundary |
| AC-7.2 | IMPLEMENTED | — | TD::test_helper_scripts_registers_the_judge, ::test_tdd_gate_section_names_the_chosen_form, ::test_hook_line_names_both_gates, ::test_hook_bullets_state_the_shipped_rule, ::test_locators_fail_loudly[4] |
| **FR-8** | see AC-8.1 | `h-mad/tests/mutation-specs/{audit_suite_summary_line,claude_gate_judge_wiring,codex_gate_judge_wiring,tdd_judge_*}.json` (15+37+17+6+8+6+3+6 = 98 rows) | — |
| AC-8.1 | IMPLEMENTED | `# M:` anchors in J, CG, XG and AG; 98 mutation rows | The orchestrator's `ALL_CAUGHT … crash_kills=0` reading for all eight specs is stamped at `ab83ae92`. `git diff ab83ae92 HEAD -- h-mad/` is empty, so it covers identical code. I re-ran the harness in a copy: `audit_suite_summary_line` ALL_CAUGHT 15/15, `claude_gate_judge_wiring` ALL_CAUGHT 37/37, `codex_gate_judge_wiring` ALL_CAUGHT 17/17. The other 5 specs (29 rows) were still running when I wrote this, and their output goes to `scratchpad/harness.out`. |

Out of rate: **V-0** run (`v0.out`, see AC-0.1). **V-1r** PASS 6/6 at skills `ab83ae92`
(`probes/…/v1-offline-replay.reading.ab83ae92.txt`: `DONE VERDICT=PASS fails=0/6`) — a stated merge condition,
met at a sha three commits behind HEAD; not re-run by me. **V-1** blocked on `multi-host-runtime` (not run).
Host deadline: `oqd1-host-deadline.reading.0d9dca24.txt` `VERDICT=PASS` (claude 2.1.284); judge latency worst 17.5 s
vs `JUDGE_BUDGET_S=40.0`. `~/.claude/settings.json` registers the gate for `Write|Edit` with no `timeout`.

## Defects (reproduced)

All repros ran under `/private/tmp/claude-501/-Users-kimhawk-orca-skills/ddcfd1dc-41bb-4886-ba51-8c094fc1704e/scratchpad/`
(`$SP` below). State file in every fixture: `{"orchestrator_state":{"feat":{"phase":"step5","codex_status":"exhausted"}}}`
(so the Codex-authorship check steps aside and the judge decides). `W=/Users/kimhawk/orca/skills-codex-tdd-gate-defects/h-mad/hooks`.

Severity axis: whether a governed production write gets through without a measured failing test. Adversary: an implementer that spells the target unusually. An honest agent would not trigger D1 or D2; a gamed or confused one would.

### D1 (HIGH, inherited, both gates) — a case-variant `.PY` suffix bypasses both gates on macOS's case-insensitive FS

CG:186 `[[ "$TARGET_PATH" != *.py ]] && _allow` and XG `_is_production_python` (`path.suffix != ".py"`) compare the
suffix case-sensitively. On APFS (default, case-insensitive) `src/prod.PY` **is** `src/prod.py`.

```
cd $SP/r2   # git root, step5 state, src/prod.py exists
ls src/prod.PY                       -> src/prod.PY   (FS is case-insensitive)
printf '{"tool_name":"Write","tool_input":{"file_path":"%s/src/prod.PY"}}' $PWD | CLAUDE_PROJECT_DIR=$PWD bash $W/h-mad-tdd-gate.sh
                                     -> (no output) rc=0            # control src/prod.py -> deny JSON
apply_patch payload "*** Update File: src/prod.PY" | CODEX_PROJECT_DIR=$PWD python3 $W/h-mad-codex-tdd-gate.py
                                     -> (no output) rc=0            # allowed
codex 0.157.1 apply_patch (arg0) of that patch in $SP/r4/w:
  "Success. Updated the following files: M src/prod.PY"; ls src -> prod.py; cat -> X=2
```
End to end on the Codex side: a governed production file was modified with no test measured. Inherited, measured: the base Claude gate (`git show base:h-mad/hooks/h-mad-tdd-gate.sh`, run as `$SP/oldtree/hooks/h-mad-tdd-gate.sh $SP/r2/src/prod.PY`) also exits rc 0, and for `prod.py` it BLOCKs. The base Codex gate has the same `suffix != ".py"` test, but it meets this task's fail-open definition.

### D2 (HIGH, inherited, Codex gate) — patch headers with a trailing space or CRLF escape the Codex gate

XG `PATCH_TARGET = r"^\*\*\* (?:(?:Add|Update|Delete) File|Move to): (.+)$"` keeps trailing whitespace / `\r` in the
captured path, so the suffix is `.py ` / `.py\r` and `_is_production_python` returns False. Codex's own parser trims
the header, so it writes the real file.

```
payload {"tool_name":"apply_patch","cwd":$SP/r2,"tool_input":{"command":P}} | CODEX_PROJECT_DIR=$SP/r2 python3 $W/h-mad-codex-tdd-gate.py
  P = LF header "*** Update File: src/prod.py"        -> deny JSON (control)
  P = CRLF line endings                               -> (no output) rc 0
  P = "*** Update File: src/prod.py " (trailing space) -> (no output) rc 0
codex 0.157.1 apply_patch in $SP/r4/w:
  trailing-space header -> "Success. Updated ... M src/prod.py", file now X=2
  CRLF patch            -> "Success. Updated ... M src/prod.py", file now X=2
```
Regex unchanged from the base (`git show base:h-mad/hooks/h-mad-codex-tdd-gate.py` line 24).

### D3 (MEDIUM, Claude gate; §D9 fix incomplete) — a symlinked spelling of the project root under `tests/` or `fixtures/` exempts every write

CG:153 sets `ROOT_ABS` with `pwd -P` (physical) but CG:155 only `normpath`s the target, so when `CLAUDE_PROJECT_DIR`
and the target use a symlinked spelling, CG:159 sets `IN_ROOT=no` and CG:179 runs `_dir_match` on the whole lexical
path — i.e. on the root's ancestry, the exact case design v1.3 §D9 says is closed.

```
$SP/r1/real = git root with step5 state;  ln -s $SP/r1/real $SP/r1/tests/link
CLAUDE_PROJECT_DIR=$SP/r1/tests/link, stdin Write file_path=$SP/r1/tests/link/x.py  -> (no output) rc=0   # allowed
CLAUDE_PROJECT_DIR=$SP/r1/real,       stdin Write file_path=$SP/r1/real/x.py        -> BLOCK kind=no-test-resolved (deny JSON)
base gate (d686351) on the same fixture, positional arg: symlinked spelling rc=0, physical spelling rc=1
```
Inherited from the base, but the feature claims to fix root-ancestry exemption (AC-6.15 / §D9) and its pins
(`test_root_under_a_test_directory_is_governed`) use a resolved `tmp_path`, so they cannot see this. Needs a
symlinked root path containing a `tests`/`fixtures` component (whether Claude Code ever passes such a lexical
`CLAUDE_PROJECT_DIR` is not verified).

### D4 (MEDIUM, Claude gate, inherited exemption semantics) — a `tests/` symlink to a production dir is exempted by the Claude gate but governed by the Codex gate

CG:177-178 match `*/tests/*` on the lexical path; XG resolves (`Path.resolve()`) before `_is_production_python`.

```
cd $SP/r2; ln -s src tests      # tests -> src ; src/prod.py is production
Claude gate, Write $SP/r2/tests/prod.py  -> (no output) rc=0   # allowed; the write lands in src/prod.py
Claude gate, Write $SP/r2/src/prod.py    -> deny JSON          # control
Codex  gate, Write $SP/r2/tests/prod.py  -> deny "requires a failing test before src/prod.py"
```
The spec says the exemption patterns "keep their bytes", so this is inherited, but the two gates now disagree on
the same write. (That Claude Code's Write follows the symlink is ordinary filesystem behaviour; not run through
Claude Code itself.)

### D5 (LOW, judge) — `_run_bounded` can wait past its deadline

J:188-194: after `TimeoutExpired`, `os.killpg` kills only pytest's process group, and the second
`proc.communicate()` has **no timeout**. A grandchild that left the session (`start_new_session=True` / `setsid`) and
still holds stdout/stderr keeps the pipe open, so the judge waits until that grandchild exits.

```
$SP/r3.py: j._run_bounded([python, "-c", "Popen(['sleep','12'], start_new_session=True); sleep(30)"], ., now+2.0)
-> bound=2.0s elapsed=12.0s timed_out=True rc=-9
```
With `sleep 200` in place of `sleep 12` the judge (budget 40 s) outruns the host hook timeout. Needs test code
(or a plugin/conftest) that detaches a daemon still holding the inherited pipe.

## Examined, no reproduced defect

- CG `_refuse` / `_allow` called inside `_read_state`: both run in the main shell (no `$(…)`), so their `exit` ends the hook.
- CG `set -u`: `${1:-}`, `${HMAD_CODEX_UNAVAILABLE:-}` and `${CLAUDE_PROJECT_DIR:-.}`. `ESCAPE`/`BLOCKER_RECORD` are set on every path that returns from `_read_state`. `set -f` guards the `for word in $SOUT` split, and the state-line fields are %-encoded (`_enc`, safe=`/._-`), so no space or comma survives inside a field.
- CG `_on_exit`: an undecided exit (set -e, or python3 missing at `_find_judge`) falls to `_refuse judge-error` under `set +euo pipefail`. `_json_str` escapes `\` and `"` and turns control bytes into spaces.
- CG output capture: `$(cmd; printf 'rc=%s' $?)` keeps the rc apart from stdout. An ALLOW needs `JRC=0` plus a full-line regex. Zero lines, several lines or a trailing blank line refuse (TCG stubs).
- J `main`: `parser.error` gives rc 2 and no stdout, so the gate refuses. An exception in the `state` verb gives rc 2 and no stdout, so the gate refuses. `print(format_verdict_line…)` sits outside the try: a UnicodeEncodeError there (a path that is not UTF-8) gives rc 1 and zero lines, so the gate refuses. `_enc` on a surrogate raises inside the try, so the state verb refuses.
- J `_state_at`: `O_NONBLOCK` plus an `fstat` regular-file check, so no FIFO hang (TXG fifo tests). The chain returns at the first unreadable file.
- J `resolve`: candidates are realpath'd and dropped outside the root; the name-map output is realpath'd and contained; stdin is `DEVNULL` in `_run_bounded`.
- XG `_main_guarded`: every exception becomes `_deny(… kind=judge-error)`. A payload that is not UTF-8 raises UnicodeDecodeError, which the guard catches and denies. A target outside the root is denied when active or unknown.
- Traversal: CG `normpath` before the exemptions (TCG::test_traversal_target_is_gated); XG `.resolve()`. The lexical-vs-physical divergences are D3 and D4.

## Unverified

- **D5's consequence.** If the host kills a hook that overruns its timeout, whether Claude Code / Codex treat that
  as allow (fail-open) or block is not measured here. The Claude registration has no explicit `timeout`.
- **Codex `workdir`.** XG resolves relative venv tokens against payload `cwd` (`_payload_cwd_base`), ignoring any
  `tool_input.workdir`. If Codex's shell tool runs in a `workdir` different from payload `cwd`, a relative
  `.venv/bin/python -m pytest` would be checked against one venv and executed from another (possibly escaping). No
  test or doc mentions `workdir`; Codex's payload shape was not probed.
- **`python*`-named executables inside a contained venv.** The corpus pins `.venv/bin/python-evil -m pytest` (a
  shell script `exit 0`) as ALLOW (`tdd_gate_support.py` `shell_corpus`). An agent that could make such a file
  executable would run arbitrary code under the shell policy. I checked Codex 0.157.1's `apply_patch`: Add File and
  Update+Move both produced mode `0644`, so I found no way for Codex to create one in step5. This is the FR-3
  residual as stated, not a defect.
- **Empty/unparseable stdin with a governed sub-project.** Under design DD-13, stdin that holds bytes but no target
  (valid JSON without a target field included) leaves the target empty, and the empty-target rule reads **only the
  root**. With the root `none` and a sub-project in step5, the write is allowed. This follows the design (a spec
  CHANGE that DD-13 authorised: spec FR-6 names only a failed read or a control character). Claude Code always sends
  `tool_input.file_path` for Write/Edit, so I did not find a reachable trigger.
- **Operability, not a defect.** CG runs the judge with the `python3` on PATH. Here that is Homebrew 3.14 with no
  pytest, so in a project without a `.venv` every governed write is refused with `pytest-missing` (fail-closed). I
  observed this on scratch `r5`.
- **Audit gate, outside the TDD gates.** `run_suite` scores `2 passed, 1 error` as `SUITE: PASS`. TAS pins this row,
  it is inherited, and spec FR-4 lists it as a non-change.
