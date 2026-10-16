IMPLPLAN-AUTHOR: DONE version=v1.1 tasks=23 wiring=2 mutation_rows=85 path=/Users/kimhawk/orca/skills/docs/01-plan/features/agy-coder-fallback.impl-plan.md lines=1997 sha256=68d840551343e52a555d261b3fcf30fc28b9ee3ab83f6850fa6a51fd2b60da2d

Second file written, as the dispatch allowed: docs/03-analysis/probes/agy-coder-fallback/fr3_state_line_grammar.py, sha256=33d103c81585dec9929e2b01aa4c562b8b226930cac1ee25c937cecbb5189945. I updated the probe now rather than leaving the update to Task 3. That way both of its modes could be run before the plan states them. Both files are uncommitted.

Before writing I checked the impl-plan: sha ba1beb56…, newest VH v1.0, mtime 1792147665. All matched the dispatch. I was its only writer.

## Gates (run after the last write)
- precheck --phase impl-plan (--allow 'step5d:red_wrong_reason:<module>'): PRECHECK: PASS issues=0. Advisories kept:
  - The PATH advisories are new files, or `tests/...` paths relative to h-mad/.
  - 6 COUNT advisories: v1.0 also gave 6, on the same pre-existing lines (L105/L111/L141 Task 0 census lists, L867 "6 deny rows", L1743 Task 18). I checked each and they are heuristic hits.
  - 1 SYMBOL advisory: check_agy is new in Task 9.
- h_mad_wire_pin_gate.py (no --feature): WIREPIN: PASS tasks=23 wiring=2 unpinned=0 mislabeled=0.
- h_mad_ac_census.py spec impl-plan: ACS: OK count=21 frs=9.
- VH bump through h_mad_version_history.py: VERSION-HISTORY: OK version=v1.1 placement=append.

## Counts (derived from the document's own lists)
- Shapes are unchanged: wiring 2 (Tasks 3, 10), new-behaviour 14, refactor 1, gate 5, operational 1, total 23.
- Mutation rows: 59 design (equals the design's list) + 5 wire + 18 doc-pin + 3 discipline/decision = 85.
  - Wire rows: Task 3 has 2 cut + 1 converse; Task 10 has 1 cut + 1 converse.
  - Doc-pin rows: Task 15 has 4, Task 16 has 8, Task 17 has 6.
  - Discipline/decision rows: Task 5 signal discipline, Task 6 OD-2, Task 10 marker.
- RED splits that changed:
  - Task 5: 31 nodes, 31 F (+2: item 9).
  - Task 6: 32 nodes, 23 F / 9 P (+6: item 10, of which 2 F and 4 P).
  - Task 15: 4 nodes, 4 F (+2).
  - Task 16: 9 nodes, 8 F / 1 P (+3).
  - Task 20: 13 nodes. F = new key mappings, derived from the committed capture; capture-only when F=0.
  - Task 22: 2 F, or 0 when the derived figure is 1500.
  - Every other stated RED count is unchanged, including Tasks 9, 10 and 11, whose node counts did not move.
- Per-spec row counts:
  - agy_tdd_gate.json 20 (= 18 design + 2).
  - tdd_gate_peers.json 7.
  - assemble_tdd_agy.json 4.
  - implementer_neutral_prompt.json 4.
  - agy_authorship_docs.json 8.

## Premises verified (each re-run against the tree)
- Harness path: from h-mad/, `python3 h-mad/scripts/h_mad_mutation_harness.py` fails with "can't open file …/h-mad/h-mad/scripts/…". `python3 scripts/h_mad_mutation_harness.py --check-anchors tests/mutation-specs/hook_wiring.json` prints ANCHORS_OK specs=1 mutations=12.
- hook_wiring.json has 12 rows: 10 on scripts/h_mad_hook_wiring.py and 2 on SKILL.md.
- The grammar probe defect is real by construction: NEW_TAIL ends with OLD_TAIL. The updated probe gives these readings:
  - tree hook: mode=derived, PROBE: PASS.
  - tree hook with --control: PROBE: FAIL.
  - scratch hook carrying the plan's grammar (impl-plan L394 text): mode=shipped, "shipped literal == grammar derived from a8d9ba99", PROBE: PASS.
  - same scratch hook with --control: PROBE: FAIL.
  - drifted literal: PROBE: FAIL, exit 0.
  - unreadable --hook: exit 2.
  - The control was run separately in each mode.
- CX-FOLD: `find` is `    path = Path(_load_identity().fold_py_suffix(relative))`, at codex gate L277 in _is_production_python. Confirmed.
- NEW, found by the class sweep: CX-FORCE-SCRIPT. Its `find` is in _safe_argv (a moved function, L478–513), and its `replace` calls `_load_identity().canonical_directory`. After the move that mutant would be killed by a NameError (a hollow crash-kill). Task 4 now rewrites its `replace`.
- Sweep of the 31 M-4 rows (ast): 31 rows sit in moved spans, matching M-4. Only CX-FOLD and CX-FORCE-SCRIPT reference a name the identity module will not define. Among the moved functions, only _is_production_python references an unmoved gate name (_load_identity).
- Codex #9 reproduced on a scratch store: `--set production_paths_needing_red_tests=[] --append …` gives "error: unrecognized arguments: --append …", rc=2, store unchanged. production_paths_needing_red_tests is a schema array of strings and is not in APPEND_ONLY.
- _refusal's text "would not validate … The store is unchanged." is used for Task 11 item 8.
- OD-2: canonicalise(root, ".", root), (root, "src/", root), (root, "src", root) and (root, root, root) all return unresolvable=False, names=(). Confirmed.
- Task 10 converse killer: test_agent_grok_block_names_exec_grok_with_1500 runs run_cli with root=tmp_path, which has no .agents/hooks.json. test_agent_codex_default_timeout_is_900 exists at L137.
- The assembler's existing HALT branches print no [H-MAD] marker (L710–719). Only PASS prints one (L742).
- Spec FR-2 L219–221: "The caller halts step5:implementer_switch_unrecorded".
- Spec FR-8 step 1, L628: "one real toolCall per class-(b) tool and per run_command … whether workspacePaths is present".
- Spec FR-9, L683–686: the three prompt requirements. Confirmed.
- Design L100: reason enum is ["env","status","cli-absent"].
- Anchor sweep, per Task (each row's `find` mapped to its enclosing def/section at 4e4b5ded):
  - Tasks 1, 12, 13, 15, 16 and 22 touch no existing row.
  - Task 2 touches only g3-reads-another-feature.
  - Task 9 touches only unknown-exits-0, which is left byte for byte.
  - Task 11 touches the two heartbeat rows (as stated).
  - Task 17 touches only the 3 closure-7 rows. The baseline_sha row starts exactly at "- **5f** —".
  - The failure-recovery.md rows are on line 48, not the 5d row (line 35).

## Findings applied
- codex M1 / agy M1: probe updated (above). Task 3 states its readings and the post-GREEN command, with --control, and has an AC.
- codex M2: a Working-directory rule. Anchor and mutation commands are given from h-mad/ with scripts/ and tests/mutation-specs/ paths. Class swept: every other documented command uses h-mad/-prefixed paths from the repo root.
- codex M3: Task 5 --self-check:
  - verdict FAILs (classification, shell-policy) print their token with exit 0;
  - policy-import exits 2 (operational);
  - new item 9 and row selfcheck-verdict-fail-exits-2.
  - Class swept with a "Verdict exits" rule covering every new or changed script and probe.
- codex M4: Task 16 staging bullet.
  - Command with --record.
  - record=failed is checked first → do not dispatch, halt step5:implementer_switch_unrecorded with an [H-MAD] marker.
  - All six token branches.
  - Items 7–9, including a discriminating control over 4 doctored bullets.
  - Rows fr10-staging-drops-record-flag and fr10-staging-dispatches-after-record-failed.
- codex M5 / M6: Task 20 rewritten.
  - All 6 samples required, each with its envelope, its instruction and workspacePaths presence. Capture gate: no subset.
  - RED split derived from the captured keys: write_to_file→TargetFile is P when matched.
  - Capture-only gate when F=0.
- codex M7: Task 10 converse row wire-check-runs-for-every-agent, killed by an existing guard, so RED counts are unchanged. Class swept: Task 3 got wire2-every-author-is-a-peer. WIRE 1 converse is stated as vacuous, because the resolver is called unconditionally.
- codex M8: Task 10 halt paths print `[H-MAD] {feature} tdd-assemble halt agy_tdd_hook_unverified {task}` after the token. Items 1–5 assert it, and there is row halt-marker-dropped. Class swept: Task 16's three halts carry markers. A Halt-markers rule was added.
- codex M9: Task 11 item 3 uses production_paths_needing_red_tests and the exact diagnostic, with no "unrecognized arguments". Class swept (RED from what is absent):
  - Task 11 items 6–8 assert the refusal text.
  - Task 9 item 2 asserts the UNREADABLE line.
  - Task 10 items 3–5 assert the HALT lines.
  - All of these would otherwise pass at RED on argparse's exit 2.
- codex S1: Task 2 status-unavailable and status-exhausted expect reason == "status".
- codex S2 + OD-2 (operator): Task 6 T2a (existing directory → judge-error under S, allow under inactive). Item 10 has 6 ids, and there is row od2-directory-target-check-dropped. Task 8 notes the difference from the Codex gate. OD-2 is closed.
- codex S3: Task 22 has 2 F (both timeout tests change at RED), or 0 when the figure is 1500.
- agy M2: Task 15 adds "the Phase-5 implementer", the agy class-(b) tools on the Hook line, and grok "no write-time gate". Items 3–4 and 2 rows were added. Re-read against FR-9 in full: Claude's gate is kept, the slots stay, and there is no ->.
- agy S1: CX-FOLD's `find` is re-anchored in Task 4, and CX-FORCE-SCRIPT's `replace` (see above). Each Task now states which existing rows it touches.
- agy S2 (measurement): hook_wiring.json is 12 rows = 10 (M-2's file) + 2 SKILL.md.
- OD-1 (operator): closed as (A). Task 17 text and the Decisions section updated.
- VH v1.1 line names audit cycle 1.

## Contradictions / owed by other documents (not edited; the dispatch forbade it)
- Design §"FR-4" --self-check (L729) says "a nonzero exit" for every FAIL. The plan now gives exit 0 for the two verdict FAILs, per the orchestrator's sheet. The design owes a line.
- Spec and design owe a line recording OD-2: a directory target is refused under S and allowed under inactive (T2a). Residual: a trailing-"/" path that names no existing directory is not covered.
- Spec FR-2 says "halt" / "never dispatch" for the no-record, unreadable and invalid tokens but names no halt. The plan names them step5:implementer_unresolved and step5:implementer_invalid. Spec and design owe adoption, or a rename. Also open: whether failure-recovery.md should get rows for step5:implementer_switch_unrecorded and these two. The plan adds none.
- The Codex gate's existing --self-check FAIL shell-policy returns 2 for a verdict, which goes against the class rule. It is pre-existing and out of this feature's scope. It is recorded as a residual, not changed. The operator may want it in a later feature.
- Spec FR-9's Hook-line bullet lists Codex, agy and grok but not Claude. The plan keeps Claude's h-mad-tdd-gate.sh because test_hook_line_names_both_gates pins it. This is not a contradiction, but the spec's list is incomplete.

## Placeholder scan
Clean (PRECHECK: PASS issues=0). The only allowed span is step5d:red_wrong_reason:<module>, quoted from SKILL.md in Task 13. `[H-MAD] <feature> halt …` in Task 16 is the SKILL.md text being prescribed, and the precheck did not flag it.

## Probes
My scratch anchor-sweep script is deleted. The scratch store and the hook copies are deleted. One file in the scratchpad, mrows.py, is not mine and was left alone.
