IMPLPLAN-AUTHOR: DONE version=v1.0 tasks=23 wiring=2 mutation_rows=76 path=/Users/kimhawk/orca/skills/docs/01-plan/features/agy-coder-fallback.impl-plan.md lines=1666 sha256=ba1beb56946150078689c69680ca816c8f6142d8da9809e79f8c1ad9c4373b5b

Start state: the target did not exist (`ls` → No such file), HEAD 4e4b5ded, tree clean. This was the only author; I wrote no other file in the repository.

## Gates (run on the final bytes)
- `h_mad_precheck_doc.py --phase impl-plan --root /Users/kimhawk/orca/skills --allow 'step5d:red_wrong_reason:<module>'` → `PRECHECK: PASS issues=0`.
  - The allow is deliberate. The string is the literal halt token, quoted as the context sentence of FR-9 copy 3.
  - Advisories I kept on purpose:
    - every PATH/SYMBOL advisory names a new file, symbol or fixture path, or a node ID written relative to `h-mad/`;
    - COUNT advisories at L85/L91/L121/L746/L1473 are phrases ("two FR-3 files", "25 moved names", "6 files; … 7 files", "6 deny rows" with their ids on the next line, "0 Codex-gate rows"). None of them is a count of an adjacent list.
- First precheck run: FAIL issues=7. 6 were `…` slots, which I rewrote as prose. 1 was the literal token, which I allowed.
- `h_mad_wire_pin_gate.py` → `WIREPIN: PASS tasks=23 wiring=2 unpinned=0 mislabeled=0`.

## Counts (derived from the document's own lists)
- Tasks: 23 (`grep -c '^## Task '` = 23). By shape:
  - wiring 2: Tasks 3, 10
  - new-behaviour 14
  - refactor 1: Task 4
  - gate 5: Tasks 0, 8, 14, 18, 19
  - operational 1: Task 21
  - total 2+14+1+5+1 = 23.
- Mutation rows:
  - design rows 59, counted from design §"Mutation rows": FR-1 3, FR-2 4, FR-3 4, FR-6 2, FR-4 18, FR-5 8, FR-7 10, FR-9 10;
  - per-Task design rows: 4+4+4+2+4+10+4+7+1+5+4+8+2 = 59, which matches;
  - plus 3 wire-cut rows (Task 3 ×2, Task 10 ×1) and 14 doc-pin rows (Tasks 15/16/17: 2/6/6), which the plan's §"Success Criteria" requires and the design's list does not;
  - total 76.
- RED nodes per Task (F/P):
  - T1 116 (114/2); T2 47 (47/0); T3 14 (8/6); T4 27 (27/0); T5 29 (29/0); T6 26 (21/5); T7 30 (23/7); T8 51 (0/51)
  - T9 16 (16/0); T10 18 (16/2); T11 13 (13/0); T12 21 (16/5); T13 18 (6/12); T14 7 (0/7); T15 2 (2/0); T16 6 (6/0); T17 12 (6/6)
  - T20: the node count is fixed by the capture
  - T22: 1/0, or 0 if the derived timeout is 1500.
- `test_deny_row_kind` ids: 6 (T5) + 6 (T6) + 4 (T7) = 16, which equals the design's 16-row "Every deny" table.

## Premises verified (command → result, at 4e4b5ded)
- `git diff --stat a8d9ba99 HEAD -- h-mad` → empty, so h-mad/ is unchanged.
- schema: `list(properties)[-4:]` → `['last_marker','substrate','codex_status','fallback_agent']`; additionalProperties False. minLength appears in `_MiniDraft7` (validate.py:45, :101) and in the schema (lines 19, 133).
- h_mad_state_validate.py:
  - `_FORCE_FALLBACK` at :137, `_make_validator` at :140, `classify` at :167 (first statement `isinstance` → "invalid");
  - the `_validators` cache exists;
  - `test_classify_matches_between_backends_on_the_corpus` clears it around the seam (test file :197–207).
- h_mad_state_write.py:
  - `merge_fields` at :195, `apply` at :212, record merge at :215, heartbeat if/assign at :216–217;
  - `_mutate` at :151 with `classify(record) != "strict"`;
  - `_utc_now` at :435 (`%Y-%m-%dT%H:%M:%SZ`);
  - main `--set` loop; the OK line is at :531.
- h_mad_tdd_judge.py:
  - `Record` has 4 fields (:34–38); `KINDS` at :23; `JUDGE_BUDGET_S = 40.0` at :28; `ESCAPE_STATUSES` at :30;
  - `_enc` :80, `_state_at` :84, `_fallback_tag` :110, `_active_records` :122–127, `format_state_line` :402–416;
  - `main`'s loop over ("state","judge") :426–431.
  - `Record(` appears in 2 files (the judge and codex_gate_judge_wiring.json).
- h-mad-tdd-gate.sh:
  - `_read_state` :150–189; `STATE_ACTIVE_RE` :248; `BLOCKER_RECORD=$record` :187;
  - authorship `if` at :324 after `_read_state --target … # M:H3` :323; the fallback comment at :336.
- Gate tests:
  - `_tree_b(`: 9 lines (1 def + 8 calls); `_stub_outcome(`: 6 lines (1 def + 5);
  - the `_tree_b` default state_line, `RECORD` and `ACTIVE_RE` literals were read;
  - the fallback_agent test imports `HOOK, TARGET, _bin, _gate, _root, _tree_b`; `_bin(codex=True)` exists.
- Codex gate (ast):
  - all 17 functions and 8 constants exist at module level;
  - `_load_identity` 525–529, `main` 532–556, `_main_guarded` 559–628;
  - M:G2 :555, M:G5 :596, M:F2-WIRE :581, M:SA-WIRE :585;
  - the `unsafe` tuple has 4 members (:541);
  - `_is_production_python` calls `_load_identity().fold_py_suffix` (:277); so does `_tmp_report_target` (:271), which does not move.
- identity module:
  - docstring line 1 as quoted;
  - `Identity` fields include `names` and `unresolvable`;
  - `canonical_directory` :30, `canonicalise` :56, `fold_py_suffix` :187.
- h_mad_hook_wiring.py: `main` :192 takes only `--project-root`; there is no `check_agy`.
- h_mad_assemble_tdd.py:
  - docstring "2 on any HALT" :50; `Halt` :87; `assemble` :361; the WIRE-PIN literal :473–475;
  - choices line :664; timeout line :674;
  - `        agent=args.agent,` occurs once.
- Mutation rows:
  - w10a / t1 / wr3 / two heartbeat rows were read with their find, replace and test;
  - M-2, M-3 (8 rows/3 specs) and M-4 (31/62, 4 specs, 0 absent, 0 non-unique) were re-derived at HEAD and match the design;
  - the FR-3 region census gave 13, but only with the authorship block starting at the `# M:H3` line (H3 = the 13th row). Starting at the `if` gives 12. The plan states this and leaves the definition to Task 0's probe.
- Harness: `--check-anchors` prints `ANCHORS: ANCHORS_OK …`; the verdict token is `MUTATION: …`. Rows use the key `name`. The spec header keys are root/command/target_command/mutations.
- DO-1a line census: 6 files; the four-pattern variant: 7 files.
- Inventory log: 58 distinct names, split as all 11 (a), all 5 (b), run_command, and 41 remaining.
- FR-9 locators L1–L4/L6 each select 1 span containing its context sentence. Each of the six context sentences has count 1. The L3 block count is 1.
- SKILL.md:
  - each of these prefixes has count 1: `- **5d** — RED dispatch`, `- **5e** — GREEN dispatch`, `- **5f** —`, `- **6a-prime** — architectural review via agy`, `7. **Closure (autonomous)**`, the `### Codex authors…` heading, `Phase 5 implementation is **Codex's job**`, the teammate bullet anchor;
  - `\n## Phase 5` has count 2, and the first one follows item 7.
- Prompt: `You are Codex implementing` is pinned by 0 test files; there is 1 `Hook: ` line.
- agy-runtime.md: SessionStart appears on 2 lines. Installed hooks.md: 3 lines. `agy --version` → 1.4.0.
- `.agents/hooks.json` is absent. HemaSuite HEAD is 02d52e4e7; 531a6296b, 7aa0d9dec and c2d671f6b are each ancestors.
- All 5 new test files and the new spec do not exist yet. Existing test names are cited exactly as found by grep:
  - test_codex_gate_kind (12 ids, judge-error included), test_codex_gate_judge_timeout_reason, test_unsearchable_…, test_a_workdir_outside_…, test_a_present_but_malformed_…;
  - run_cli, test_prompt_file_is_agent_independent (`hashes[0] == hashes[1]`), test_agent_grok_explicit_timeout_wins;
  - TestWiringShape.test_the_pin_is_told…, TestCli.test_a_clean_assembly…, TestHeartbeatBeats;
  - _phase_5e_text, test_skill_documents_the_precheck_is_automatic, test_implementer_scopes_…, HALT_TOKENS;
  - titled_section, _hook_block, _skill_gate_bullet.

## Findings applied (orchestrator carry items)
1. Every Task declares its shape. Tasks 3 and 10 carry WIRE/WIRE-PIN. Task 3 has two numbered wires, and the gate parses both. Each Task states RED F/P counts and labels its regression guards.
2. Owed items:
   - AC-7.3's surface is OD-1 on Task 17;
   - the E7 re-anchors are in the Task 10 (FR-5) Anchors section: w10a is re-anchored, t1 and wr3 are kept;
   - the heartbeat rows are in Task 11 (FR-7), with `--check-anchors` in every Task;
   - the new design rows are all placed. Step-5 S is in T5. Class (c) S is in T7. The target test is in T6. The three kinds are spread over T6 (two) and T7 (one). The dict guard is in T1. T4 non-str is in T6. APPEND_ONLY is per key in T11;
   - AC-4.1 `unknown` fixtures: T5, T6, T7;
   - AC-4.2: one `test_deny_row_kind` id per deny row (16), plus a kind scan on every deny inside `_decide`;
   - the AC-1.2 leap second is in T1 on both paths; the AC-1.3 fixtures are in T1, with the store-unchanged bullet in T11;
   - committed probes: censuses in T0, re-run in T3, T4 and T18; class inventory in T0 and T20; FR-9 corpus reading in T14; replay in T19, stamping both shas.
3. FR-8 is post-merge: Tasks 20–22. COMPLETE only after Task 22. `.agents/hooks.json` is committed only after Task 21's refusal.
4. The implementer is Codex. Tasks are sized for one RED/GREEN dispatch each; the FR-4 gate is split across T5, T6 and T7, with T8 holding the differentials.
5. A directory TargetFile is OD-2 on Task 6. It is not designed.
6. Every path, symbol and pin was re-verified at 4e4b5ded (above).

## Decisions taken in the plan, open for the reviewer to dispute
- FR-2 tests go in a new `test_h_mad_tdd_judge_implementer.py`, not `test_h_mad_tdd_judge.py` as the design's Test Plan says. Reason: AC-3.2 allows only the `ACTIVE_RE` literal to change in that file against a8d9ba99. For the same reason, FR-3's today-shape fixture goes in the new `test_h_mad_tdd_gate_peers.py`.
- Task 3's three fixture-consequence literals (the `_tree_b` default, `RECORD`, `ACTIVE_RE`) land in the GREEN commit, not RED. That keeps the RED counts exact and the RED reasons legible. The verifier diffs the files against a8d9ba99.
- In Tasks 5 and 6, classes (b) and (c) take class (d)'s rule until their own Task lands. This is fail-closed. It is what makes T6's and T7's RED P/F counts derivable.
- The differentials sit in a `gate` Task (T8) whose RED is all-pass. A failing cell is a finding, not something that Task fixes. I did this because the per-cell RED of a two-gate differential cannot be predicted without running the Codex gate.
- Step-5's S row is killed in T5 by `test_workspace_paths_cross_check[inactive-stands-down]` (call_mcp_tool). The design's `run_command ls` fixture needs class (c), so T7 adds it as a second killer. The design's fixture is still used, not replaced.
- The design's single "UNWIRED returning 2" row is placed on the assembler (T10). The check's exit 0 on UNWIRED is asserted by T9's tests but has no row of its own; adding one would make the total 60 instead of the design's 59.
- New seams are named: `AGY_WIRING_TIMEOUT_S = 60` (the design states the 60 s bound but gives no name), `CLASS_A`, `CLASS_B`, `PATH_KEYS`, `GATE_KINDS`, `AGY_HOOK_COMMAND`. `property_valid` builds its validator per call, because the existing seam clears the `_validators` cache.

## Contradictions found
- **OD-1.** A code surface for AC-7.3 contradicts spec FR-1 ("implementation_authors is read by the orchestrator's FR-7 attribution step only; no script reads it", spec.md:177) and design FR-7 ("The writer does not check attribution"). Spec AC-7.3 demands a surface or an OPEN-DECISION. The plan builds option (A): a transcription test on the FR-9 corpus precedent, with a test tying it to the SKILL.md text. Option (B), a script surface, is offered and needs spec and design revisions first. This is the operator's call.
- Not a contradiction, but noted: spec AC-9.2 names four corpus cases; the design and the plan have five (+ other-symbol). The plan states the pass condition over five.

## Placeholder scan
Clean: `PRECHECK: PASS issues=0`, with one deliberate `--allow` for the literal tree token `step5d:red_wrong_reason:<module>`.

## Owed by other documents
- Spec/design: resolve OD-1. If the answer is (B), spec FR-1 drops "no script reads it" and design FR-7 names the surface. The spec also still owes the APPEND_ONLY rule, or a reason it is out of scope (from the design v1.3 Owed list; unchanged).
- Design: OD-2. The directory TargetFile needs an analysis, or an accepted residual.
