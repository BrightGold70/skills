# grok-codex-fallback — Phase 6a gap analysis (fresh-context verifier)

Match Rate: 98%

- Worktree `/Users/kimhawk/orca/skills-grok-codex-fallback`, branch `feature/216-grok-codex-fallback`, HEAD `345e35e0`.
- Phase-5 diff: `4f705707..HEAD`, 49 files, +5375 −389.
- Documents: spec v1.5, design v1.3, impl-plan v1.6.1, and the analysis doc (Phase-5 readings).
- Units: 11 FRs + 58 ACs = 69. IMPLEMENTED 66, PARTIAL 3 (FR-3, FR-5, AC-11.1), MISSING 0, CHANGED 0. (66 + 1.5) / 69 = 97.8%.
- What I ran myself: the 14 new test files, targeted and in the foreground. Result: `373 passed`, rc 0, and the tree was unchanged afterwards. The only untracked entry, `../graft/`, was already there before the run.
- What I did NOT run: the full suite (instructed not to), the mutation harness, and live grok. For AC-2.7, AC-11.1 and AC-11.2 I rely on the committed readings.
- Every repro ran under `/private/tmp/grok6a` with stubs.

## FR / AC table

| ID | Status | Implementation (file:line) | Pinning test node(s) |
|---|---|---|---|
| FR-1 | IMPLEMENTED | h-mad/scripts/h_mad_state_schema.json:153 | test_h_mad_state_fallback_agent.py (4 tests) |
| AC-1.1 | IMPLEMENTED | schema:153 | test_fallback_agent_set_writes_a_strict_record |
| AC-1.2 | IMPLEMENTED | schema enum | test_fallback_agent_set_refuses_values_outside_the_enum |
| AC-1.3 | IMPLEMENTED | schema (optional) | test_incident_replay_tiers_unchanged_by_fallback_agent |
| AC-1.4 | IMPLEMENTED | schema description | test_fallback_agent_description_states_the_four_facts |
| FR-2 | IMPLEMENTED | h_mad_tdd_judge.py:100-127 (`_fallback_tag`, `_fallback_fold`), :381-382; h-mad-tdd-gate.sh:85-107, 169, 207-227 | test_h_mad_tdd_gate_fallback_agent.py |
| AC-2.1 | IMPLEMENTED | gate.sh:195-227 | test_gate_matrix (80 cells) |
| AC-2.1b | IMPLEMENTED | judge.py:100-109 | test_invalid_class_blocks_each_value_alone, test_invalid_class_with_codex_available_is_block_codex, test_json_null_control_falls_through, test_absent_key_control_falls_through |
| AC-2.2 | IMPLEMENTED | gate.sh (unchanged paths) | test_absent_null_claude_match_the_base_hook (runs the `git archive 8ef6009f` base hook) |
| AC-2.3 | IMPLEMENTED | gate.sh:218-221 | test_block_grok_stderr_names_the_four_things |
| AC-2.4 | IMPLEMENTED | gate.sh:222-225 | test_invalid_class_blocks_each_value_alone |
| AC-2.5 | IMPLEMENTED | judge.py:112-127 | test_other_feature_grok_does_not_change_active_outcome, test_second_active_record_holding_grok_blocks, test_fold_invalid_record_governs_over_grok |
| AC-2.6 | IMPLEMENTED | gate.sh:179-191 (before the state read) | test_exempt_files_stay_exempt_under_grok |
| AC-2.7 | IMPLEMENTED (reading) | tests/mutation-specs/tdd_gate_fallback_agent.json g1/g2/g3 → test_gate_matrix (12 rows) | harness not re-run by me |
| FR-3 | **PARTIAL** (D3) | hmad-dispatch.sh:3080-3096 | test_hmad_dispatch_exec_grok.py |
| AC-3.1 | IMPLEMENTED | dispatch.sh:3086-3087 | test_exec_grok_argv_carries_prompt_file_and_headless_flags |
| AC-3.2 | IMPLEMENTED | dispatch.sh:3088-3090 | test_exec_grok_translates_model_effort_sandbox |
| AC-3.3 | IMPLEMENTED (for the four named identifiers) | dispatch.sh:3081-3082 | test_exec_grok_child_env_has_no_claude_names, test_exec_grok_hpw_backend_default, test_exec_grok_leaves_the_wrapper_shell_env_intact |
| AC-3.4 | IMPLEMENTED | dispatch.sh:3069-3073 | test_exec_codex_and_agy_keep_claude_env |
| AC-3.5 | IMPLEMENTED | dispatch.sh:3084-3085 (no OVERSIZE on the grok branch) | test_exec_grok_oversize_prompt_is_not_refused |
| AC-3.6 | IMPLEMENTED | dispatch.sh:2893-2895 | test_exec_grok_without_grok_on_path_returns_2, test_exec_unknown_agent_names_the_three_agent_set |
| AC-3.7 | IMPLEMENTED | pane verbs unchanged | test_pane_verbs_still_refuse_grok |
| FR-4 | IMPLEMENTED | dispatch.sh:2082-2145 (readers), 3097-3108, 3273-3316 | test_hmad_dispatch_exec_grok.py, test_hmad_dispatch_grok_readers.py |
| AC-4.1 | IMPLEMENTED | dispatch.sh:3099-3103 | test_exec_grok_f0_prints_the_final_message |
| AC-4.2 | IMPLEMENTED | `_grok_obj` jq filter | test_exec_grok_beat_and_spaced_match_f0 |
| AC-4.3 | IMPLEMENTED | `_grok_final_message` | test_exec_grok_decoys_are_not_recovered |
| AC-4.4 | IMPLEMENTED | dispatch.sh:3107 | test_exec_grok_no_text_takes_the_empty_path |
| AC-4.5 | IMPLEMENTED | dispatch.sh:3275, 3308-3313 | test_exec_grok_truncated_recovers_the_verdict |
| AC-4.6 | IMPLEMENTED | `_grok_last_tool` | test_exec_grok_empty_path_names_the_last_tool |
| AC-4.7 | IMPLEMENTED | `_grok_region` pre_lines | test_exec_grok_reads_only_its_own_region |
| AC-4.8 | IMPLEMENTED | `_exec_run` 124 + recovery | test_exec_grok_watchdog_kill_reports_recovery |
| AC-4.9 | IMPLEMENTED | `_grok_last_tool` `.seen` | test_exec_grok_omits_the_last_tool_line_without_tool_calls |
| AC-4.10 | IMPLEMENTED | `_grok_last_tool` `.done` | test_exec_grok_counts_completed_not_seen_ids |
| FR-5 | **PARTIAL** (D1) | dispatch.sh:2145-2180 (classifier), 2735-2748 (render) | test_hmad_dispatch_progress_grok.py, test_grok_two_instruments.py |
| AC-5.1 | IMPLEMENTED | dispatch.sh:2173-2180 | test_progress_f0_is_grok_ndjson, test_progress_f_spaced_is_grok_ndjson, test_progress_agy_init_plus_f0_is_agy_ndjson |
| AC-5.2 | IMPLEMENTED | `_GROK_RENDER_PROG` | test_progress_f0_renders_counts_without_delta_text |
| AC-5.2b | IMPLEMENTED | `_GROK_JQ_DEFS` depth 64 | test_progress_key_order_line_is_grok_ndjson, test_progress_bogus_type_line_is_codex_text, test_progress_depth_boundary, test_depth_boundary_agrees_across_surfaces |
| AC-5.3 | IMPLEMENTED | agy/codex branches untouched | existing test_hmad_dispatch_progress.py (per the reading) |
| FR-6 | IMPLEMENTED (D1 also crashes its CLI) | h_mad_review_evidence.py:122-159, 281-294 | test_h_mad_review_evidence_grok.py, test_h_mad_review_evidence_scan_grok.py |
| AC-6.1 | IMPLEMENTED | evidence.py:286-293 | test_cli_f0_prints_grok_evidence_pass |
| AC-6.2 | IMPLEMENTED | — | test_cli_f_notools_prints_none |
| AC-6.3 | IMPLEMENTED | evidence.py:283-285 | test_cli_f_trunc_is_unreadable_without_counts |
| AC-6.4 | IMPLEMENTED | parsed events only | test_scan_grok_ok_ignores_a_completed_substring_in_text |
| AC-6.5 | IMPLEMENTED | scan() semantics unchanged | test_scan_unchanged_on_f0 |
| AC-6.6 | IMPLEMENTED | — | test_cli_codex_text_output_is_byte_identical_to_base |
| FR-7 | IMPLEMENTED (spec-conformant; see D2) | h_mad_audit_cycle.py:562-570, 894-897; dispatch.sh:3453-3454 | test_h_mad_audit_cycle_grok.py, test_hmad_dispatch_audit_cycle_grok.py |
| AC-7.1 | IMPLEMENTED | dispatch.sh:3453 | test_audit_cycle_dispatches_the_grok_pass_through_exec_grok, test_audit_cycle_unknown_surface_names_agy_codex_grok |
| AC-7.2 | IMPLEMENTED | combine floor | test_combine_scores_f0_against_the_floor |
| AC-7.3 | IMPLEMENTED | — | test_combine_passes_three_completed_calls |
| AC-7.4 | IMPLEMENTED | audit_cycle.py:894 | test_combine_f_trunc_is_unmeasurable |
| AC-7.5 | IMPLEMENTED (reading) | — | existing files (per the full-suite reading) |
| FR-8 | IMPLEMENTED | h_mad_assemble_tdd.py:409, 442 | test_h_mad_assemble_tdd_agent.py |
| AC-8.1 | IMPLEMENTED | — | test_no_agent_output_is_byte_identical_to_base |
| AC-8.2 | IMPLEMENTED | — | test_agent_grok_block_names_exec_grok_with_1500, test_agent_grok_explicit_timeout_wins, test_agent_codex_default_timeout_is_900 |
| AC-8.3 | IMPLEMENTED | — | test_prompt_file_is_agent_independent |
| AC-8.4 | IMPLEMENTED | argparse choices | test_unknown_agent_exits_2_and_writes_no_prompt |
| AC-8.5 | IMPLEMENTED | — | test_state_fallback_agent_is_not_read |
| FR-9 | IMPLEMENTED | h_mad_resolved_model.py:97-120 | test_h_mad_resolved_model_grok.py |
| AC-9.1 | IMPLEMENTED | — | test_grok_reads_the_model_from_the_last_end |
| AC-9.2 | IMPLEMENTED | — | test_grok_refusals_exit_2_unknown, test_grok_empty_model_usage_refuses |
| AC-9.3 | IMPLEMENTED | — | test_grok_resolves_from_the_last_end_on_a_shared_log, test_grok_second_dispatch_model_wins |
| AC-9.4 | IMPLEMENTED (reading) | — | existing test_h_mad_resolved_model.py |
| FR-10 | IMPLEMENTED | SKILL.md:511-519, 559, 1892-1898, 2846; references/state-schema.md:47; references/agent-substrate.md | test_grok_fallback_docs.py (7) |
| AC-10.1 | IMPLEMENTED | — | test_phase5_section_documents_fallback_agent, test_exec_section_documents_exec_grok, test_teammate_section_documents_the_grok_leg, test_missing_heading_fails_not_skips |
| AC-10.2 | IMPLEMENTED | — | test_state_schema_doc_names_fallback_agent, test_agent_substrate_documents_exec_grok_and_grok_sandbox |
| FR-11 | IMPLEMENTED | — | — |
| AC-11.1 | **PARTIAL** | the carve-out diffs match (t16 floor reading, `rest_equals_base=True`) | Recorded full suite: `1 failed, 4569 passed`. The failing node is called "baseline" but is never named in the reading; not re-run by me. |
| AC-11.2 | IMPLEMENTED (reading) | — | full-suite reading |
| AC-11.3 | IMPLEMENTED | dispatch.sh:2176, evidence.py:281, audit_cycle.py:553 | test_banner_wins_on_all_three_surfaces, test_progress_banner_then_f0_is_codex_text, test_cli_banner_then_f0_keeps_codex_output, test_measure_effort_banner_then_f0_is_codex_text |

## Defects (reproduced)

### D1 — MEDIUM — `scan_grok` crashes on an RFC-8259 number that overflows a float (h-mad/scripts/h_mad_review_evidence.py:151)

- **Cause.** `thinking += int(value)` runs for any `float`. `json.loads` turns the valid JSON number `1e999` into `inf`, and `int(inf)` raises `OverflowError`. Nothing catches it.
- **What it breaks:**
  - the `h_mad_review_evidence.py` CLI dies with a traceback (rc 1);
  - `h_mad_audit_cycle.measure_effort` raises, and it runs unguarded at audit_cycle.py:1183, so the whole combine step dies;
  - FR-5's rule that the two detectors agree across the agreement domain is broken. The line has depth 2, no BOM, no surrogate and no CR, yet the shell classifies it `grok-ndjson` and the Python detector raises.
- **Repro:**
  ```
  printf '%s\n' '{"type":"usage","usage":{"reasoning_tokens":1e999}}' > one.ndjson
  hmad-dispatch.sh progress one.ndjson   # -> format: grok-ndjson
  python3 -c "from h_mad_review_evidence import scan_grok; scan_grok(open('one.ndjson').read())"
  # -> OverflowError: cannot convert float infinity to integer
  ```
  - F0 with its three `reasoning_tokens` set to `1e999` gives the same traceback from the CLI and from `measure_effort`.
  - Python also parses `NaN` and `-Infinity` tokens, which fail the same way (`int(nan)` raises ValueError). Those two are outside RFC 8259.
- **Inherited.** agy's `scan()` has the same `int(value)` at evidence.py:227, so this class predates the feature.
- **Fix direction.** Skip non-finite floats, as FR-6 already skips non-numeric values.

### D2 — MEDIUM — a truncated grok re-run that did nothing scores as a PASS when its per-pass log is reused (h-mad/scripts/h_mad_audit_cycle.py:563; h_mad_review_evidence.py:281; per-pass log path at hmad-dispatch.sh:3485/3491, never cleared at 3496-3503)

- **Cause, three parts:**
  - `audit-cycle` names each pass log `/tmp/audit_<feature>_<phase>_cycle<N>_p<i>.log`. The clearing loop removes the report, `.done`, out, prompt and asm files, but never the log.
  - `exec grok` appends to the log with `>>`.
  - `scan_grok` and `measure_effort` read the whole file, not the dispatch's region. `complete` therefore comes from a previous attempt's `end` event, and `ok` is the union of both attempts' tool calls.
- **Repro, through the public `exec grok` path and one shared `--log`:**
  1. The first dispatch is F0 plus 3 more completed read_file calls. It gives `EVIDENCE: PASS tools=5 ok=5`.
  2. The retry, into the same log, carries only `thought` events and no `end`. Exec correctly reports `TRUNCATED` with rc 3.
  3. The CLI on the shared log still prints `EVIDENCE: PASS tools=5 ok=5 unresolved=0 thinking=121 format=grok stop_reason=end_turn` (rc 0).
  4. `measure_effort` returns `shape: grok, ok: 5`, and `combine` returns `('PASS', None)`.
  5. The retry's log alone gives `UNREADABLE reason=truncated_no_end` / `grok-truncated`, which is the right answer.
- **What it defeats.** FR-6/FR-7's rule that "could not measure" never takes the "measured" branch.
- **Spec status.** The code follows the spec's letter: `complete` is defined as "at least one `end`" over the text. The spec itself handles F-SHARED only for resolved-model.
- **Inherited.** agy's whole-log `scan()` shares this class. The grok `complete` flag is new, and this path defeats it.

### D3 — LOW — `CLAUDE*` environment names that are not shell identifiers reach the grok child (h-mad/scripts/hmad-dispatch.sh:3081)

- **Cause.** The scrub iterates over `compgen -e`, which lists only valid bash identifiers. Bash still passes other environment entries through to its children.
- **Repro.** `env 'CLAUDE-HYPHEN=leak1' 'CLAUDE.DOT=leak2' CLAUDECODE=1 hmad-dispatch.sh exec grok …`. A stub that runs `env | grep ^CLAUDE` records `CLAUDE.DOT=leak2` and `CLAUDE-HYPHEN=leak1`, while `CLAUDECODE` is correctly removed.
- **What it contradicts.** FR-3: "Every variable whose name begins with `CLAUDE` is removed. The class is `^CLAUDE`."
- **Real-world risk.** Low. HPW's markers are identifiers.
- **Fix direction.** Build the child environment with `env -i` plus a filtered `env -0` list, or have Python do the scrub.

### D4 — LOW (conditional, inherited mechanism) — the heartbeat can split a grok event and turn a completed run into TRUNCATED (hmad-dispatch.sh:3093 `_HMAD_EXEC_BEAT_LOG="$log"`, with the beat writer at :2622-2625)

- **Cause.** The heartbeat appends `#hmad-beat` lines to the same file grok's stdout appends to. A child that writes one JSON event in two `write()` calls gets a beat line inserted mid-event.
- **Repro.** With `HMAD_EXEC_HEARTBEAT_SEC=1`, a stub prints a text event `STATUS: DONE`, then half of the `end` event, sleeps 3 s, and prints the other half. The result:
  - rc 3;
  - `TRUNCATED — no end event`;
  - `verdict recovered from log`;
  - the log shows `{"type":"end","stopReason":"end_turn",#hmad-beat …`.
- **Why the severity is low:**
  - It fails closed: rc is non-zero, evidence becomes UNREADABLE, and resolved-model refuses.
  - It needs grok to write one event in more than one `write()`, which has not been observed.
  - The agy path has used the same shared-log heartbeat since before this feature.

## Unverified

- **(a) Gate bypass: none found.** 9 adversarial state files were run through the real hook with `HMAD_CODEX_UNAVAILABLE=1` (codex off PATH for one). Every one DENIED with the right kind:
  - two records, claude then grok, with a key holding a space, a comma and a `%`;
  - grok then an invalid `"gr ok,%x"`, where the invalid value governs;
  - fullwidth `ｇｒｏｋ`;
  - `1e999` and `NaN`;
  - a 200 KB string;
  - a 5000-deep array;
  - `codex_status: exhausted` with codex off PATH.
- **Duplicate JSON key.** `{"fallback_agent":"grok","fallback_agent":null}` falls through to the judge, because the last key wins. Every reader (Python and jq) resolves it the same way, and `h_mad_state_write.py` cannot produce such a file. Not reported as a defect.
- **The hook trusts `fallback=none` without checking it against the record tags.** A judge that says `none` while a record tag reads `grok` would allow the write. The spec states this as a residual, and I found no judge path that produces it.
- **Truncated partial verdict.** If grok is killed mid-token (for example after `STATUS: DONE` of a `STATUS: DONE_WITH_CONCERNS`), recovery writes `STATUS: DONE` to `--out`. rc stays 3 or 124, and this is the spec's intended recovery table. Not probed live.
- **Stale partial line.** A previous dispatch whose last line has no trailing newline makes the new region's first line concatenate onto it. That event is lost; it is never mis-recovered, since jq `fromjson` rejects concatenated values (checked on jq 1.8.2).
- **`_cmd_notify … 2>/dev/null`** (dispatch.sh:3363) now hides notify stderr for codex and agy as well. FR-11 names only stdout and rc, and no stderr pin exists for it.
- **Prompt echo.** Whether live grok ever echoes prompt content (which could forge `tool_call_update` lines) into the log is not probed; the stubs only.
- **Readings I did not re-run:** AC-2.7 mutation ALL_CAUGHT, the full-suite readings behind AC-11.1 and AC-11.2, and the name of the one "baseline" failing node.
