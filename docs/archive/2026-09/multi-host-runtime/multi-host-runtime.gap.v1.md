# multi-host-runtime — Phase 6a gap analysis (fresh-context verifier)

Match Rate: 97%  (49.5 / 51 ACs; PARTIAL = 0.5)

- Worktree `/Users/kimhawk/orca/skills-multi-host-runtime`, branch `feature/multi-host-runtime`, HEAD `18d725c4`, merge-base with main `52a78ca8`.
- Phase-5 diff `b9354139..HEAD` read. Scoped run (read-only, `env -u HMAD_HOST`, `-p no:cacheprovider`): 8 modules
  (`test_h_mad_host_declaration`, `test_h_mad_install_check_roots`, `test_host_construct_parity`, `test_host_runtime_docs`,
  `test_h_mad_context_budget`, `test_h_mad_resume_decision`, `test_h_mad_install_check`, `test_h_mad_feature_lock`)
  → **461 passed**. `smoke_assert.py rehearse` → `REHEARSAL: PASS n=92`. Worktree `git status --short` unchanged (1 line, `?? graft/`) before and after.
- The full suite was not run, as instructed.
- **Counting rule.** The denominator is the 51 spec ACs of FR-1..FR-10 and FR-12. FR-11's V-11.1..V-11.5 are
  "verification criteria, not tests" (spec FR-11), so they are left out of the denominator and listed separately
  below as operator steps still pending. `docs/03-analysis/multi-host-runtime.live-smoke.md` does not exist.
- **Base-sha caveat, which drives 2 PARTIALs and 1 defect.** Every `<base>`-keyed reading in the analysis doc uses
  `BASE_SHA=3b5c4388`. That is 86 commits before the rebase target `52a78ca8`, the grok-codex-fallback merge. Spec
  §Scope requires the rebase before the 5c baseline, and it requires the reasons to be re-derived at that base.
  - AC-4.6 survives: I re-ran `calibrate.sh 52a78ca8` and got the same totals (h-mad 122/13, handoff 71/12).
  - AC-5.2 does not survive (defect D1).

## Table

| AC | Status | Implementing file:line | Pinning test |
|---|---|---|---|
| AC-1.1 registry shape / failure kinds | IMPLEMENTED | h-mad/references/host-constructs.json; h-mad/tests/host_parity.py:253 `check` | test_host_construct_parity.py::test_kind_fixture_reports_exactly_its_pair (REGISTRY_UNREADABLE/DUPLICATE_ID/BAD_PATTERN cases) |
| AC-1.2 22 seed ids | IMPLEMENTED | host-constructs.json | ::test_registry_holds_every_seed_id |
| AC-2.1 one row per declared construct | IMPLEMENTED | 6 adapters `## Construct mapping` (h-mad codex:148, agy:141, grok:130; handoff codex:49, agy:56, grok:53) | ::test_live_adapter_is_clean[6] |
| AC-2.2 non-empty cells | IMPLEMENTED | host_parity.py `_cells`:181 | kind fixtures CELL_EMPTY ×6 |
| AC-2.3 advisor not-applicable + substitute | IMPLEMENTED | h-mad/references/{codex,agy,grok}-runtime.md advisor rows | test_host_runtime_docs.py::test_advisor_row |
| AC-2.4 task-tools rung | IMPLEMENTED | handoff/references/*-runtime.md | ::test_task_tools_row |
| AC-2.5 session-id-env row | IMPLEMENTED | h-mad adapters | ::test_session_id_env_row |
| AC-3.1 gate clean on tree | IMPLEMENTED | host_parity.py:253 | ::test_live_registry_and_skill_files_are_clean, ::test_live_adapter_is_clean |
| AC-3.2 mention ≠ mapping | IMPLEMENTED | host_parity.py:196 `adapter_table` | kind fixture ROW_MISSING (advisor) |
| AC-3.3 one fixture per disjunct (42) | IMPLEMENTED | — | ::test_kind_fixture_reports_exactly_its_pair (42 params), ::test_clean_baseline_yields_nothing |
| AC-3.4 STALE_ENTRY / UNDECLARED_SKILL | IMPLEMENTED | host_parity.py | kind fixtures |
| AC-3.5 no host CLI | IMPLEMENTED | host_parity.py (no launcher import) | ::test_gate_runs_no_host_cli, ::test_host_cli_stub_control_fires[3], ::test_host_parity_has_no_direct_launcher_import |
| AC-4.1 0 UNREGISTERED | IMPLEMENTED | host_parity.py catch-all | ::test_live_registry_and_skill_files_are_clean |
| AC-4.2 per-branch controls | IMPLEMENTED | host_parity.py:65 `a4_pattern` | ::test_catch_all_axis_alone_reports_its_fixture[6], ::test_removing_an_axis_or_branch_clears_its_fixture[7] |
| AC-4.3 exclusion controls | IMPLEMENTED | host_parity.py | ::test_exclusion_suffix_hides_its_fixture[6], ::test_removed_exclusion_suffix_reports_its_fixture[6] |
| AC-4.4 TeamCreate | IMPLEMENTED | — | ::test_unregistered_teamcreate_then_registered_passes |
| AC-4.5 calibration in analysis doc | IMPLEMENTED | analysis.md §Calibration at BASE_SHA | (doc artifact) |
| AC-4.6 re-derive after rebase | PARTIAL | analysis.md §AC-4.6 record uses 3b5c4388, which predates grok-codex-fallback. My re-run at 52a78ca8 gives identical totals, so no registry change is owed, but the record is missing | (doc artifact) |
| AC-5.1 1.0.41 / compat toggles | IMPLEMENTED | h-mad/references/grok-runtime.md, handoff/references/grok-runtime.md | ::test_version_and_compatibility |
| AC-5.2 TDD halt token + reasons at base | PARTIAL (CHANGED) | grok-runtime.md:71-76. The halt token is present; reason (i) is stale (D1) | ::test_tdd_gate_section pins `exit 1` via test_host_runtime_docs.py:29-30 `REFUSAL_FORM_AT_BASE="exit1"` |
| AC-5.3 advisor substitutes | IMPLEMENTED | grok-runtime.md advisor row | ::test_advisor_row |
| AC-5.4 todo_write rung 1 | IMPLEMENTED | handoff/references/grok-runtime.md | ::test_task_tools_row |
| AC-5.5 GROK_SESSION_ID conditional | IMPLEMENTED | h-mad grok-runtime.md | ::test_grok_session_id_condition |
| AC-5.6 claude-projects-store n/a | IMPLEMENTED | grok-runtime.md | ::test_claude_projects_store_row |
| AC-5.7 source cell format | IMPLEMENTED | grok tables | ::test_grok_source_cells_format |
| AC-6.1 pre-change gap table | IMPLEMENTED | analysis.md §AC-6.1 (at 3b5c4388) | (doc artifact) |
| AC-6.2 four adapters pass FR-3 | IMPLEMENTED | — | ::test_live_adapter_is_clean |
| AC-6.3 codex/agy advisor substitutes | IMPLEMENTED | codex/agy-runtime.md | ::test_advisor_row |
| AC-6.4 agy/codex task-tools | IMPLEMENTED | handoff/references/{agy,codex}-runtime.md | ::test_task_tools_row |
| AC-6.5 no session var → minted | IMPLEMENTED | h-mad codex/agy adapters | ::test_session_id_env_row |
| AC-6.6 negative assertions unchanged | IMPLEMENTED | — | test_h_mad_codex_runtime.py / test_handoff_codex_runtime.py (unchanged files) |
| AC-7.1 Host runtime names 3 adapters | IMPLEMENTED | h-mad/SKILL.md:8, handoff/SKILL.md:8 | ::test_host_runtime_names_every_adapter |
| AC-7.2 no UNREGISTERED | IMPLEMENTED | — | ::test_live_registry_and_skill_files_are_clean |
| AC-7.3 locator fails loudly | IMPLEMENTED | — | ::test_host_runtime_locator_fails_loudly |
| AC-8.1 declared host → host_unsupported | IMPLEMENTED | h-mad/scripts/h_mad_host.py:11-19; h_mad_context_budget.py:155-164 | test_h_mad_host_declaration.py::test_budget_host_unsupported_valid_transcript (+ precedes_transcript/usage) |
| AC-8.2 unknown host encoding | IMPLEMENTED | h_mad_context_budget.py:160-164 (`re.fullmatch` / `json.dumps`) | ::test_budget_unknown_host_encoding |
| AC-8.3 module twice | IMPLEMENTED | — | analysis.md Task 18 item 3 (31/31) |
| AC-8.4 ceiling on non-Claude host | IMPLEMENTED | adapters §Context budget | test_host_runtime_docs.py::test_context_budget_section, ::test_budget_line_runs_and_reports_host |
| AC-8.5 order vs bad_window | IMPLEMENTED | h_mad_context_budget.py:155 (before ceiling/window) | ::test_budget_host_check_precedes_window_check, ::test_budget_unknown_host_precedes_window_check |
| AC-9.1 cannot_judge without id | IMPLEMENTED | h_mad_resume_decision.py:95-110 | ::test_decide_cannot_judge_without_session_id, ::test_decide_unknown_host_without_session_id, ::test_decide_empty_session_id_is_no_id, ::test_resume_decision_cli_under_grok |
| AC-9.2 legacy tests unchanged | IMPLEMENTED | — | test_h_mad_resume_decision.py, test_h_mad_feature_lock.py (passed in my run) |
| AC-9.3 minted-id procedure | IMPLEMENTED | adapters §claims fenced lines | test_host_runtime_docs.py::test_claims_section_fenced_lines, ::test_claims_lines_execute_across_invocations |
| AC-9.4 cannot_judge row second cause | IMPLEMENTED | h-mad/SKILL.md:297 | ::test_cannot_judge_row_names_host_cause |
| AC-10.1 agents-dir fixtures | IMPLEMENTED | h_mad_install_check.py:202-203 | test_h_mad_install_check_roots.py::test_agents_root |
| AC-10.2 existing install tests unchanged | IMPLEMENTED | — | test_h_mad_install_check.py (passed); ::test_absent_roots_add_no_line |
| AC-10.3 empty → UNREADABLE; option beats env | IMPLEMENTED | h_mad_install_check.py:63-68, 248-254 | ::test_empty_root_option_is_unreadable, ::test_empty_env_override_is_unreadable, ::test_explicit_option_beats_env_override |
| AC-10.4 ln -s commands in adapters | IMPLEMENTED | codex/grok/agy-runtime.md install sections | test_host_runtime_docs.py::test_install_section |
| AC-10.5 agy root cells | IMPLEMENTED | h_mad_install_check.py:152-170 `split_agy_root`, 204-211 | ::test_agy_root_cell, ::test_detail_lines_sorted_and_after_verdict |
| AC-10.6 claude root unchanged | IMPLEMENTED | check_siblings unchanged | ::test_claude_root_debugger_copy_still_fails |
| AC-12.1 full suites | PARTIAL | analysis.md Task 18 was recorded at ec9e2933, before the rebase: 1 baseline failure `test_top_level_key_set_still_matches` and 4256 passed. It has not been re-run on the rebased HEAD, and the rebase brought in a changed `h-mad-tdd-gate.sh` and `h-mad/SKILL.md` | — |
| AC-12.2 byte identity | IMPLEMENTED | docs/03-analysis/probes/multi-host-runtime/byte_identity.py | analysis.md Task 16: budget 14, decision 18, install-a 9, install-b 10, all PASS |

**FR-11, outside the denominator.** The V-11.1 and V-11.2 classifier and the rehearsal are implemented:
`smoke_assert.py`, and `rehearse` gives PASS n=92. V-11.1..V-11.5 live runs have not been done. They are an operator step, and `live-smoke.md` is absent.

**Recorded deviation (replay-agy).** This deviation is **not correct against the design's normative text**, but the
design contradicts itself here. I rate it CHANGED, LOW, because both verdicts are FAIL and neither is a false pass.
- **Design text.** Design §D10 "The verdict, decided in this order", step 1, walks up to the first *successful*
  adapter read. The first execution it meets decides `FAIL … a script ran before the adapter was read`. The step says
  nothing about an adapter read *attempt*. Under that text, `replay-agy` (an execution with no adapter read) gives
  "script ran before", which is what the design and plan predicted.
- **The contradiction.** The same section's R3 fixture ("no adapter read") also carries a script run. Every case does
  "unless it says otherwise", and `rehearsal/codex-R3.log` shows it. Yet the design expects R3 to give `no adapter read`.
  No classifier can satisfy step 1, R3 and the replay prediction together.
- **What the code does.** It adds an `adapter_seen` state (smoke_assert.py:274-276, 291-293, 302-304). That state
  exists nowhere in D10. With it, the code satisfies R3 and the replay consistently and departs from step 1.
- **The analysis doc's justification.** It says "R2/R3 requires `no adapter read`". That is an implementer's reading
  of R3, not the normative order.
- **Needed in 6b.** The operator decides which way to go: amend step 1 to "if no adapter read exists, go to step 2",
  or change R3 and the code. A related divergence: when an unclassified mention follows an earlier execution, the code
  returns `UNVERIFIED`, where step 1 says the first-occurring execution decides `FAIL`. Both halt.

## Defects (reproduced)

**D1 — MED — grok adapter TDD reason (i) is stale at the shipped base.**
- **Where:** h-mad/references/grok-runtime.md:71-73, with its pin at h-mad/tests/test_host_runtime_docs.py:29-30.
- **The claim:** The adapter says "The current gate refuses by `exit 1`, which grok treats as fail-open".
- **The measurement:** `h-mad/hooks/h-mad-tdd-gate.sh` refusal form, by counting `^\s*exit 1\s*$` / `^\s*exit 2\s*$` / `permissionDecision`:
  - `3b5c4388`: 5 / 0 / 0.
  - `52a78ca8` and HEAD: 0 / 1 / 1.
- **What the gate does at HEAD:** It denies with stdout `hookSpecificOutput.permissionDecision:"deny"` and exit 0
  (gate.sh:19-21). Its fallback is `exit 2` (gate.sh:24, 35). Both are grok-honoured denies (spec F9).
- **Why it violates the spec:** Spec AC-5.2 requires reason (i) measured at the post-rebase base. A mixed form
  "halts to the operator before the grok adapter is written".
- **Why the test misses it:** The doc test hard-codes `REFUSAL_FORM_AT_BASE="exit1"`, so it enforces the wrong token.
- **Effect:** The halt token `step5:grok_tdd_hook_unverified` still stands, because reasons (ii) and (iii) hold. The gate
  reads `tool_input.file_path` (gate.sh:137), not grok's `toolInput`. So the effect is conservative, but the stated
  reason is false for the tree it ships in.

**D2 — MED (HIGH once the codex gate is armed) — the codex TDD gate refuses the FR-8 inline declaration and allows the undeclared, Claude-branch call.**
- **Where:** h-mad/hooks/h-mad-codex-tdd-gate.py:288-289, which rejects any `argv[0]` containing `=`. The collision is
  with h-mad/references/codex-runtime.md:118 and 135-140.
- **Repro:** Step5 state in a temp git repo `/private/tmp/mhr6a.TcTN/proj`, payload `exec_command`, run through the gate:
  - `HMAD_HOST=codex python3 <W>/h-mad/scripts/h_mad_context_budget.py` → **deny**.
  - `python3 <W>/h-mad/scripts/h_mad_context_budget.py` → **allow**, and that call takes the Claude branch and measures a Claude transcript.
- **Why it matters:** codex-runtime.md:18-20 wires this gate and requires its self-check before Phase 5. So during step5
  the adapter's mandated form is blocked, and the only budget call that gets through is the misclassified one.
- **Attribution:** The `"=" in argv[0]` rule was already present at 3b5c4388. The feature added instructions that the
  gate it names cannot execute. The adapter's `"$HMAD_SKILL_ROOT/…"` and `$(cat …)` forms also fail the gate's
  `SIMPLE_SHELL_COMMAND` regex.
- **Not part of this defect:** `h_mad_resume_decision.py` is denied even without the prefix, but for a pre-existing
  reason: it is absent from `SAFE_HMAD_SCRIPT_OPTIONS`.
- **Exposure today:** Latent. `~/.codex/hooks.json` on this machine does not arm the gate.

**D3 — MED — codex smoke log injection forges input events, giving a false PASS.**
- **Where:** docs/03-analysis/probes/multi-host-runtime/smoke_assert.py:134-145 (`codex_events`).
- **Mechanism:** The function splits the log on any line equal to `exec`, including lines inside a tool's *returned*
  text. V-11.1 requires input events only ("never the text a tool returned").
- **Repro:** `/private/tmp/mhr6a.TcTN/codex-inject.log` holds one exec: `cat …/rehearsal/codex-R1.log`, with that file as
  its output. `v111 --host codex` prints **`PASS V-11.1`**, although the host never read SKILL.md or the adapter and never ran a declared script.
- **Scope:** Codex text logs only. The grok and agy NDJSON readers are structured.

**D4 — LOW — an unexpanded `~` in a root value silently checks nothing (install false PASS).**
- **Where:** h_mad_install_check.py:63-68 and 248-249, which never call `expanduser()`.
- **Repro:** A plain-directory copy at `$HOME/agy/h-mad`:
  - `HMAD_AGY_SKILLS_DIR='~/agy'` or `--agy-skills-dir '~/agy'` (quoted) → `INSTALL: PASS`.
  - The expanded path → `INSTALL: FAIL … SIBLING_NOT_SYMLINK`.
- **Why it passes:** The literal `~` path is absent, and absence passes.
- **Exposure:** The documented commands use an unquoted `~`, which the shell expands. So only an env or config value
  that holds a literal tilde hits this.

## Unverified

- **The rebased HEAD's full coupled suite (AC-12.1).** It was not run, as instructed. The last reading was taken before the rebase, at ec9e2933.
- **The indirect script run** `S=h-mad/scripts/h_mad_x.py; python3 $S` before the adapter read gives `PASS V-11.1`. I
  reproduced it (`/private/tmp/mhr6a.TcTN/codex-indirect.log`). It is **a stated design residual** (D10 "A script name
  assembled at run time … `python3 "$S"`"), not a defect.
  - The name appears only in an assignment-only simple command, which the classifier drops (smoke_assert.py:207-210).
  - Whether a mention in an assignment-only command should count as UNVERIFIED is a design question.
- **Per-event output attribution.** `head -c 0 <adapter>; echo '<adapter heading>'` would count as a content read. This
  is the design's stated per-event residual. I did not reproduce it.
- **Host misclassification.** `classify_host` (h_mad_host.py:11-19) is exact-match, and unknown values fail closed
  (budget `unknown_host`, oracle `cannot_judge`). No marker sniffing exists, so there are no two-host-marker conflicts.
  - An omitted `HMAD_HOST` on a non-Claude host takes the Claude path. That is the spec's stated residual (FR-8), made worse by D2.
  - A globally exported `HMAD_HOST=<non-claude>` in a Claude Code shell makes the advisor-warn hook's budget read `UNKNOWN`. That is the inverse residual, not probed further.
- **Install check, other false-PASS shapes.** I found no false PASS for:
  - a symlink into another checkout, a dangling link, or a copy (all reported);
  - a link to the wrong skill in the same checkout (WRONG_CHECKOUT);
  - a root that is itself a symlink to another checkout (NOT_SYMLINK).

  I did not probe a symlink-loop root, where `check_siblings` returns no issues on an `OSError`. That behaviour pre-dates the feature.
