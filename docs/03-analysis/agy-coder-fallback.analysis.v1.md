# Analysis: agy-coder-fallback

Phase 6a gap analysis, cycle 1. Fresh-context analyst; tree read at code head `ae541fb0`
(record head `a0b36ac7`), baseline (5c) `d280af07`. Inputs: spec v1.10, design v1.4,
impl-plan v1.2, `git diff d280af07..ae541fb0`, the 5d decision records
(`acf_5d_*_decisions.md`, `acf_5d_task18_19_record.md`) and the 6a-prime review. Every AC
below was checked against production lines and a test node id, read in this pass; the
AC-9.1 sweep and the AC-X mutation specs were re-run here (see §"Test Results").

## Executive Summary

Every in-scope acceptance criterion (FR-1..FR-7, FR-9, FR-10; 20 ACs) is met by production
code and a passing test that asserts it; FR-8 (AC-8.1, AC-8.2) is deferred post-merge by D-13
and excluded from the denominator. No `code-vs-design`, `design-vs-spec` or `both` gap was
found. One non-AC documentation drift is recorded as an observation (O-1).

## Match Rate: 100%

**Denominator.** The spec has 10 FRs (FR-1..FR-10). FR-8 is post-merge by spec D-13
(impl-plan Tasks 20–22) and is excluded: 10 − 1 = **9 FRs in scope**.
**Numerator.** FRs whose every AC is met: FR-1, FR-2, FR-3, FR-4, FR-5, FR-6, FR-7, FR-9,
FR-10 = **9**. Match rate = 9 / 9 × 100 = **100%**.

**AC-level count (calibration).** The spec lists 22 ACs: AC-1.1..1.3 (3), AC-2.1..2.2 (2),
AC-3.1..3.2 (2), AC-4.1..4.2 (2), AC-5.1..5.2 (2), AC-6.1 (1), AC-7.1..7.3 (3),
AC-8.1..8.2 (2), AC-9.1..9.4 (4), AC-X (1) = 22. Excluding AC-8.1 and AC-8.2 leaves
**20**; met **20/20**. FR-10 has no `AC-10.n` of its own; it is scored against its own
bullets (spec §FR-10), each pinned by a doc test, and against AC-1.1 / AC-9.1 where those
name FR-10 surfaces. AC-X is cross-cutting (it applies to every FR's guards); it is scored
once and, being met, does not withhold any FR.

### Deferred by D-13 (post-merge) — not in the denominator
- **AC-8.1** — probe directory payload capture, real refusal, RED/GREEN readings, and the
  FR-8-formula timeout in `h_mad_assemble_tdd.py`. Expected absent: `TIMEOUT_DEFAULTS["agy"]`
  is still D-4's provisional 1500 s (`h-mad/scripts/h_mad_assemble_tdd.py:74`).
- **AC-8.2** — forced-handler-timeout reading (FR-8 step 2a).
Spec AC-8.1 binds: the feature is **not recorded COMPLETE** before both pass (Tasks 20–22 on
main after the merge).

## FR Coverage

| FR | ACs Total | ACs Met | Status | Evidence (production · test) |
|---|---|---|---|---|
| FR-1: state fields | 3 (AC-1.1–1.3) | 3 | ✅ Complete | `h-mad/scripts/h_mad_state_schema.json:157-193` (5 properties after `fallback_agent`); `h-mad/scripts/h_mad_state_validate.py:169` `rfc3339_datetime`, `:189` `_semantic_ok`, `:197` `property_valid`, `:210` `classify`; `h-mad/references/state-schema.md:46-52`; `h-mad/scripts/h_mad_state_write.py:57` `APPEND_ONLY` · `test_h_mad_state_validate_fallback.py::test_fr1_value_accepted`, `::test_fr1_value_refused`, `::test_fr1_record_without_new_fields_unchanged`, `::test_switch_ts_refused[library/bundled-*]` (not-a-date, date-only, feb-30, leap-60, …), `::test_switch_ts_accepted[*-writer-form]`, `::test_implementation_authors_accepted`, `::test_implementation_authors_refused` (all on the `path` fixture = library + bundled via `_FORCE_FALLBACK`); `test_h_mad_state_schema_fr1_docs.py` (6 tests: both descriptions, both rows, order); `test_h_mad_state_write.py::TestAppend::test_refused_entry_leaves_store_byte_identical[implementation-authors-gemini]`; `test_h_mad_state_fallback_agent.py` green |
| FR-2: resolver + `implementer` verb | 2 (AC-2.1–2.2) | 2 | ✅ Complete | `h-mad/scripts/h_mad_tdd_judge.py:145` `resolve_implementer`, `:133` `_implementer_tag`, `:495-541` verb with `--record` / `record=failed` · `test_h_mad_tdd_judge_implementer.py::test_resolve_implementer_matrix` (4 tags × 2 × 2), `::test_each_cause_alone[env/status-unavailable/status-exhausted/cli-absent]`, `::test_peers_out_fallback_tag_decides`, `::test_implementer_verb_line[file-absent…peers-out]`, `::test_implementer_verb_record_writes_switch_once`, `::test_implementer_verb_record_failed`, `::test_implementer_verb_switch_none_writes_nothing` |
| FR-3: Claude-side authorship gate | 2 (AC-3.1–3.2) | 2 | ✅ Complete | `h-mad/hooks/h-mad-tdd-gate.sh:254` `STATE_ACTIVE_RE` (5th field), `:335/345/351/371/377` the five `_refuse` kinds; `h-mad/scripts/h_mad_tdd_judge.py:458-473` `format_state_line` author field · `test_h_mad_tdd_gate_peers.py::test_agy_authorship_refused_when_agy_resolves`, `::test_codex_authorship_refused_when_codex_resolves`, `::test_implementer_invalid_refused`, `::test_fallback_grok_refused_when_peers_out`, `::test_fallback_invalid_refused_when_peers_out`, `::test_implementer_invalid_outranks_codex_authorship`, `::test_peer_refusal_outranks_fallback_invalid`, `::test_chain_fold_blocks_on_the_first_eligible_record`, `::test_today_shape_state_line_is_judge_error`, `::test_three_message_bodies_match_a8d9ba99`. AC-3.2 diff vs `a8d9ba99` re-run here: exactly one changed literal in each of `test_h_mad_tdd_gate_fallback_agent.py` (`RECORD`), `test_h_mad_tdd_gate_judge.py` (`state_line` default) and `test_h_mad_tdd_judge.py` (`ACTIVE_RE`); no other existing `test_h_mad_tdd_gate_*.py` modified |
| FR-4: agy write gate | 2 (AC-4.1–4.2) | 2 | ✅ Complete | `h-mad/hooks/h-mad-agy-tdd-gate.py:15-23` `CLASS_A`/`CLASS_B`/`GATE_KINDS`, `:28` `classify_tool`, `:58` `main`, `:114` workspacePaths, `:150-158` T4, `:162` T5, `:166-184` T6–T7 (chain authoritative under `inactive`), `:186-232` class (c), `:234-237` class (d) · `test_h_mad_agy_tdd_gate.py::test_deny_row_kind[*]` (17 ids = design FR-4 deny table's 17 rows, each `endswith kind=<k>`), `::test_every_exit_prints_one_json_object`, `::test_unsearchable_chain_denies_although_the_scan_is_inactive`, `::test_class_b_no_target`, `::test_class_b_directory_target[.-/src/ × active/unknown/inactive]` (D-16), `::test_out_of_root_py_denies_under_unknown`, `::test_workspace_paths_cross_check`, `::test_unknown_tool_is_class_d`, `::test_production_py_with_failing_test_allows`, `::test_tmp_non_py_write_allowed_under_active`, `::test_artifact_directory_path`; kind-count scan at `test_h_mad_agy_tdd_gate.py:100`; target + shell differential `test_h_mad_agy_tdd_gate_differential.py` (incl. `tmp-py`, `chmod000-chain` cells) |
| FR-5: wiring + assembler check | 2 (AC-5.1–5.2) | 2 | ✅ Complete | `h-mad/scripts/h_mad_hook_wiring.py:201` `check_agy`; `h-mad/scripts/h_mad_assemble_tdd.py:684-702` (UNWIRED → exit 0, UNREADABLE / no-token → exit 2, before any prompt write); agy gate `--self-check` FAIL on stdout exit 0 · `test_h_mad_hook_wiring_agy.py::test_unwired_reason[*]` (all 7 reasons, exit 0), `::test_unreadable_hooks_file`, `::test_wired`, `::test_timeout_floor_is_derived_from_the_judge_budget`; `test_h_mad_assemble_tdd_agent.py::test_agent_agy_unwired_halts_with_exit_0[7 reasons]`, `::test_agent_agy_unreadable_halts_with_exit_2`, `::test_agent_agy_no_token_halts_with_exit_2`, `::test_agent_agy_wired_writes_the_prompt`; `test_h_mad_agy_tdd_gate.py::test_self_check_policy_fail_is_a_verdict_with_exit_0`; mutants `fr5-unwired-exits-2` (assemble_tdd_agy.json) and `selfcheck-verdict-fail-exits-2` (agy_tdd_gate.json) caught |
| FR-6: shared shell policy | 1 (AC-6.1) | 1 | ✅ Complete | `h-mad/scripts/h_mad_target_identity.py:302` `_any_phase5_status`, `:436` `_safe_shell_command`, `:451` `_shell_allowance`, `:472` `_operator_allowed`; Codex gate guarded import `h-mad/hooks/h-mad-codex-tdd-gate.py:26-59`, self-check verdicts `:258`, `:267` · `test_h_mad_shared_gate_policy.py::test_each_moved_function_has_one_definition_in_the_identity_module[*]`, `::test_each_moved_constant_is_assigned_in_the_identity_module[*]`, `::test_codex_gate_binds_every_moved_name_to_the_identity_module`; `test_h_mad_agy_tdd_gate.py::test_unsafe_tuple_parity`; Codex gate tests unmodified (`git diff --stat d280af07..ae541fb0 -- 'h-mad/tests/test_h_mad_codex*'` empty); re-pointed specs ALL_CAUGHT (§Test Results) |
| FR-7: review-independence flag | 3 (AC-7.1–7.3) | 3 | ✅ Complete | `h-mad/scripts/h_mad_phase7_preconditions.py:109-149` `_review_independence_warnings`; `h-mad/scripts/h_mad_state_write.py:57`, `:217` append-only; SKILL.md `:341` closure procedure (attribution, OD-1 (A)) · `test_h_mad_phase7_preconditions.py::TestReviewIndependence::test_non_independent_entry_warns`, `::test_malformed_entry_warns`, `::test_warnings_never_move_ready`, `::test_unrecorded_fires_for_each_implementer[codex-field-absent/codex/agy/grok/claude]`, `::test_unrecorded_fires_for_each_archreview_value[READY_TO_MERGE/WITH_FIXES/NO]`, `::test_unrecorded_is_quiet`; `test_h_mad_state_write.py::…::test_append_keeps_both_earlier_entries`, `::test_refused_entry_leaves_store_byte_identical[review-independence-bad-leg]`; `test_h_mad_review_attribution_docs.py::test_attribution_transcription[5 cases]` (each asserts the rule's answer AND that the named mutant differs), `::test_transcription_is_tied_to_the_skill_text` |
| FR-8: live tracer + timeout | 2 (AC-8.1–8.2) | — | ⏸ Deferred (D-13) | Post-merge, excluded from the denominator |
| FR-9: implementer-neutral prompt + new-caller | 4 (AC-9.1–9.4) | 4 | ✅ Complete | six copies: `h-mad/references/codex-implementer-prompt.md` (L1, L2, L6), `h-mad/SKILL.md:500` (L3), `h-mad/references/failure-recovery.md:36` (L4), `h-mad/scripts/h_mad_assemble_tdd.py` `assemble()` header (L5) · `test_h_mad_assemble_tdd_agent.py::test_prompt_file_is_agent_independent` (codex, grok, agy); `test_h_mad_implementer_neutral_prompt.py`; `test_h_mad_new_caller_carveout_copies.py::test_copy_carries_the_canonical_block[L1..L6]`, `::test_locator_refuses_zero_or_many_spans`; `test_h_mad_wire_pin_new_caller_corpus.py::test_corpus_case_red_is_real[4 cases]`, `::test_changed_verdicts_are_exactly_new_caller`; AC-9.1 sweep re-run at head (`union=10 unparsed=0`, `PROBE: PASS`, control FAIL); AC-9.3 replay `docs/03-analysis/probes/agy-coder-fallback/fr9_incident_replay.py` record `cases=3 reproduced=3`, stamped Skills `3236ade6` + HemaSuite `ad9b7abc` |
| FR-10: documentation surfaces | (bullets; no AC-10.n) | all | ✅ Complete | SKILL.md `:530` §"Codex authors Phase 5", `:582` §"Exit-code dispatch", `:596-601` staging halts, `:501` 5e author append, `:341` closure WARNING carry, `:3133-3141` teammate bullet; `h-mad/references/agy-runtime.md:53-66` §"The TDD gate"; `h-mad/references/state-schema.md:46-52`; `failure-recovery.md:36` · `test_h_mad_agy_authorship_docs.py` (9 tests incl. `::test_teammate_bullet_separates_audit_selection_from_authorship`, `::test_agy_runtime_tdd_gate_names_the_agy_gate_and_keeps_the_halt`, `::test_agy_runtime_sessionstart_claim_is_rechecked_and_stamped`, `::test_staging_step_halts_on_record_failed_before_any_dispatch`); `test_h_mad_review_attribution_docs.py::test_closure_step_carries_every_warning_line`, `::test_5e_bullet_appends_the_author_at_green_acceptance`, `::test_5d_bullet_appends_no_author`; `test_h_mad_tdd_gate_docs.py` (teammate anchor + tokens) green |

## Gaps

**None.** No in-scope AC is unmet, so step 4.5's three-way classification has no entry to
classify: 0 `code-vs-design`, 0 `design-vs-spec`, 0 `both`.

### Notes on ACs that were met under a recorded decision (not gaps)
- **AC-7.3 — met on OD-1 (A)'s surface.** The spec allowed that attribution might have no code
  to drive, and routed it to the impl-plan as an OPEN-DECISION; the operator closed OD-1 with
  option (A), a transcription test over the written SKILL.md procedure (impl-plan
  §"Decisions (closed)"). `test_attribution_transcription` defines `attribute()` in the test,
  ties it to the SKILL.md sentences (`test_transcription_is_tied_to_the_skill_text`), and per
  case asserts both the rule's answer and that the named mutant gives a different answer.
  Residual (impl-plan §Residuals): this pins the procedure's words, not an orchestrator's
  execution of them, and no production reader of `implementation_authors` exists
  (`grep -rn implementation_authors h-mad/scripts h-mad/hooks` hits only the schema and the
  writer). The 6a-prime review's statement that `h_mad_phase7_preconditions.py` validates
  `implementation_authors` entries is **not** borne out by the tree; it validates
  `review_independence` only. That does not move any AC.
- **AC-3.2 — the a8d9ba99 message check normalises `PEER_` → `BLOCKER_`** variable names
  before comparing literals (`test_three_message_bodies_match_a8d9ba99`). The message text is
  byte-identical; only the shell variable a message interpolates was renamed. Read as met.
- **AC-4.1, `unknown` + "a `run_command` FR-6 refuses"** — the fixture `class-c-unknown` uses
  `ls`, which FR-6 admits; under `unknown` the gate denies every shell command
  (`h-mad-agy-tdd-gate.py:201-203`), so an FR-6-refused command is denied a fortiori. Read as
  met; a literal fixture with an FR-6-refused command under `unknown` would be stricter.
- **AC-1.2's `rfc3339_validator` clause is conditional** ("if the mechanism uses the library's
  format checker"); the mechanism is a stdlib predicate (`h_mad_state_validate.py:169`), so the
  clause does not apply.

### Observation (not an AC; outside every FR's text)
- **O-1 · SKILL.md assembler entry is stale on exit codes.** `h-mad/SKILL.md:3200` still says
  `h_mad_assemble_tdd.py` exits "2 on `ASSEMBLE-TDD: HALT <reason>`", and its halt-reason list
  omits `agy_tdd_hook_unverified`, which exits 0 on `UNWIRED` (FR-5;
  `h_mad_assemble_tdd.py:702`). The script docstring was updated and pinned
  (`test_docstring_states_the_agy_halt_exit_rule`), the SKILL.md line was not. FR-10 does not
  name this line, so no AC is unmet; recommend a one-line fix before Phase 7 or carrying it.

## Test Results

Scoped run (never the whole suite, per the dispatch): every test file changed in
`d280af07..ae541fb0` plus the guard files the ACs name (`test_h_mad_state_fallback_agent.py`,
`test_h_mad_codex_tdd_gate_judge.py`, `test_h_mad_wiring_task_shape_docs.py`,
`test_h_mad_agent_definitions.py`, `test_h_mad_assemble_tdd.py`, `test_h_mad_tdd_gate_docs.py`,
every `test_h_mad_tdd_gate_*.py`):
```
/opt/anaconda3/bin/python3 -m pytest <those files> -q -p no:cacheprovider
1445 passed, 2 warnings in 421.45s (0:07:01)
```
Full suite: not re-run here (21 min); the orchestrator measured `6514 passed` at `ae541fb0`.

AC-9.1 sweep, re-run at head:
```
python3 docs/03-analysis/probes/agy-coder-fallback/fr9_union_sweep.py
READING: line=10 strings=5 comments=0 text=5 joined=10 union=10 unparsed=0
PROBE: PASS            (--control → PROBE: FAIL)
```

AC-X / AC-6.1 mutation specs (every spec changed in the diff, run alone from `h-mad/`):
```
python3 scripts/h_mad_mutation_harness.py tests/mutation-specs/<spec>.json
agy_authorship_docs          ALL_CAUGHT  8/8
agy_tdd_gate                 ALL_CAUGHT 20/20
assemble_tdd_agent           ALL_CAUGHT  2/2
assemble_tdd_agy             ALL_CAUGHT  4/4
assemble_tdd_mutation_rows   ALL_CAUGHT  5/5
claude_gate_judge_wiring     ALL_CAUGHT 45/45
codex_gate_judge_wiring      ALL_CAUGHT 45/45  (first pass TREE_MOVED, inner=ALL_CAUGHT: this
                                                analysis file was created mid-run; re-run alone
                                                on a stable tree → ALL_CAUGHT)
codex_gate_shell_allowance   ALL_CAUGHT  9/9
hook_wiring_agy              ALL_CAUGHT  8/8
implementer_neutral_prompt   ALL_CAUGHT  4/4
new_caller_carveout_copies   ALL_CAUGHT 10/10
phase7_review_independence   ALL_CAUGHT  4/4
review_attribution_docs      ALL_CAUGHT  6/6
shared_gate_policy           ALL_CAUGHT  4/4
state_fr1_fields             ALL_CAUGHT  4/4
state_write_append           ALL_CAUGHT  5/5
tdd_gate_differential        ALL_CAUGHT  8/8
tdd_gate_fallback_agent      ALL_CAUGHT 12/12
tdd_gate_peers               ALL_CAUGHT  7/7
tdd_judge_implementer        ALL_CAUGHT  4/4
20 specs, 214 rows, 0 survived, 0 hollow_kills, 0 untargeted
```

## Verdict
Match rate: 100% (9/9 in-scope FRs; threshold 90%). AC-level 20/20 (AC-8.1, AC-8.2 deferred
by D-13). Tests: 1445/1445 scoped passing; full suite 6514 passed (orchestrator, `ae541fb0`).
→ **Advance to Phase 7.** Carry: FR-8 Tasks 20–22 post-merge (feature not COMPLETE before
AC-8.1/8.2 pass); O-1 SKILL.md:3200 exit-code line.

## Version History
- v1.0: Initial gap analysis (cycle 1), 2026-10-17, fresh-context analyst at `ae541fb0`. 9/9 in-scope FRs, 20/20 ACs; FR-8 deferred (D-13); 0 gaps; O-1 doc drift.
