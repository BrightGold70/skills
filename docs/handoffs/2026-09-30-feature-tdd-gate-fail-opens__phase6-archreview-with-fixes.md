# Handoff — tdd-gate-fail-opens: Phase 5 closed, 6a-prime cycle 1 WITH_FIXES (triaged)

**Date:** 2026-09-30
**Branch:** feature/tdd-gate-fail-opens
**Project:** skills
**Supersedes:** 2026-09-30-feature-tdd-gate-fail-opens__phase5-tasks-5-6.md

## Session Summary

Phase 5 finished and closed:
- **Tasks done:** CX-CANON was pinned, then T10a, T10b, T11, T12, T7, T8 and T9, each test-first through Codex.
- **Checks:** the wire registry passes 44/44 at step 5f. The full suite showed only the known failure plus one load flake per run.
- **State:** 5g set `phase=null` and `last_completed_phase=5`.

6a-prime cycle 1 (agy, tools=27) returned **WITH_FIXES**, and state records `archreview=WITH_FIXES`, so Phase 7 is blocked. The three findings are triaged with evidence below: F1 is accepted and not yet fixed, F2 needs one spec check, F3 is rejected. The loop was stopped at an 80.8% context budget. Everything is pushed except `6aa29a51` (the archreview report), which is 1 ahead.

## Key Learnings

- **The handoff's recommended order was wrong.** It said "Task 7 next", but the impl-plan §Execution order is T10a→T10b→T11→T12→T6→T7→T8→T9, and T7 depends on T12. Re-derive order from the plan, not from a handoff.
- **T0's probe never measured FR-8.** `reproduce.py` `fr8()` ran `python3` under the fixture PATH. That PATH has a private python3 shim, which the Codex gate refuses as an untrusted executable. All three FR-8 cells were therefore denied on both trees for that reason. Fixed in `196f4d70` by using `sys.executable`. The unfixed tree was re-measured at `a737962a` and gave 64/64 identical values. After the fix, the comparison reads `COMPARE: PASS softened=7 approved=7`.
- **Wire pins registered at 5c were h-mad-relative (`tests/…`).** `verify --rootdir . --testpath h-mad/tests` resolves repo-relative node ids, so all 4 pins were reported "missing". Parametrised tests need every case listed as a multi-pin. Fixed in `106421f0`.
- **`test_no_agent_output_is_byte_identical_to_base` pinned the template bytes as well as the script.** Any edit to `codex-implementer-prompt.md` breaks it. Fixed in `f61bb908` so both runs use the base template. A positive control confirmed a script change still fails the test.
- **Two load flakes appeared in the full suite, one per run.** Both pass 10/10 in isolation.
  - `test_run_bounded_plain_timeout_is_not_reap_failure`: `REAP_GRACE_S=1.0` is load-sensitive, and a plain timeout gets classified as reap_failed.
  - `test_timeout_kind` (older than this feature): the sleeper races its 1 s budget before writing its pidfile.
  - Expect one of these on any future full-suite run.
- **The Claude TDD gate blocked a Claude edit to `compare_readings.py` during step5 (`codex-authorship`), which is correct.** Phase-5 `.py` changes go through Codex.

## Next Steps

1. **F2 — settle it with spec AC-3.6 / FR-3 arm 2** (`docs/01-plan/features/tdd-gate-fail-opens.spec.md:337`).
   - The reviewer says the Claude gate's root-refuse at `h-mad/hooks/h-mad-tdd-gate.sh:243-246` violates design line 334 ("governed-only … including an ungoverned allow").
   - Evidence: disabling that check fails only `test_unenterable_project_dir_refuses` (`h-mad/tests/test_h_mad_tdd_gate_judge.py:392`). That test is older than this feature (`b10078b2`), so flipping it counts as a design stop-and-report.
   - An unenterable root means state cannot be read, which is different from an ungoverned write. If AC-3.6 says refuse, reject F2 and cite it.
   - If the design literally prescribes allow, that is a design defect: run design-author for a correction and ask the operator (AskUserQuestion). No hook edit either way this cycle.
2. **F1 — accept and fix through Codex, test-first.**
   - Design lines 403-405 say the canonical cwd must go back through `_payload_cwd_base`. `h-mad/hooks/h-mad-codex-tdd-gate.py` `_relative_target` (around line 228) canonicalises the cwd and stops there.
   - Fix: after `base = Path(identity.canonical_directory(...))`, re-run `_payload_cwd_base(root, str(base))`.
   - RED test: a spy asserting `_payload_cwd_base` receives the canonical string. Say in the docstring that a real escape may not be constructible on this host.
   - First re-arm `phase=step5` (Phase 6b iterate; read `references/inline-protocols.md §Phase 6b`), then run the same assemble → exec codex → verify loop, then return to `phase=null`.
3. **F3 — reject.** Removing the scandir block in the Codex unresolvable branch fails `test_codex_unreadable_component_step5[a]` (`h-mad/tests/test_h_mad_codex_tdd_gate_judge.py:575`), so the block is load-bearing and not dead code.
4. **Run 6a-prime cycle 2** on the fixed tree.
   - Use `python3 h-mad/scripts/h_mad_archreview_cycle.py stage --base 15681a53 --head <new HEAD> …`, then `hmad-dispatch exec agy`, then `score`.
   - Do not put the F2/F3 rejections in the prompt (#153).
   - If cycle 2 raises F2 or F3 again, that is the cap: take it to the operator.
   - It must record `READY_TO_MERGE`; read the value back.
5. **Write the Phase 6 gap analysis** at `docs/03-analysis/tdd-gate-fail-opens.analysis.v1.md`. Record in it:
   - the F2 design-vs-test conflict
   - the two load flakes
   - T10a's `UnicodeDecodeError` escape (a non-UTF-8 id file raises ValueError, not OSError, so it escapes `session_id_from_git_dir`)
   - Task 5's `reap_failed` ordering deviation
   - the 3 feature mutation specs with an absolute `/opt/anaconda3/bin/python` `command[0]`, which predates `15681a53`
   - the T0 probe defect
   - the missing R-4/R-5 `MANUAL:` lines in `reading-fixed.txt` (operator re-measure)
   - the impl-plan's low-severity 5d items (T0 has no control for an absent `agent-cli-reachable` line; T11's cat-subst test is refused by `SIMPLE_SHELL_COMMAND`; T4 has no mutation row for the empty-path equality rule)
   - T7's unfinished re-read of the adapters' other gate sentences
6. **Phase 7:** preconditions, then integrate.
7. **HemaSuite pin-drift side** (brief `2026-09-30-feature-tdd-gate-fail-opens__hemasuite-tdd-gate-pin-drift.md`), and triage of HemaSuite items (a), (c) and (d) (brief `2026-09-30-main__hmad-defects-from-hemasuite.md`). Both are unchanged and still claimed by `bf7373d5` (dead); take them with a plain `--claim`.

## Open / Blocked Items

- **tdd-gate-fail-opens, Phase 6** — in progress; 6a-prime is WITH_FIXES and Phase 7 is blocked.
  - Location: repo `/Users/kimhawk/orca/skills` · branch `feature/tdd-gate-fail-opens` · worktree: none.
  - Claim: held by session `9cfdf8ab-7fb8-41fc-bdcd-99d249e45247` (this one), taken over from dead `bf7373d5` with operator confirmation.
  - Scratchpad: `/private/tmp/claude-501/-Users-kimhawk-orca-skills/9cfdf8ab-7fb8-41fc-bdcd-99d249e45247/scratchpad`, which holds `ar_prompt.txt`, `ar_review.log`, the `t10a`/`t10b`/`t11`/`t12` prompts, and `reading-fixed.txt`.
- **F1, F2, F3** — see Next Steps 1-3.
- **Commit `6aa29a51` is unpushed** (the archreview report).
- **HemaSuite TDD-gate pin drift** — unchanged since 2026-09-30.
  - Handover-From: HemaSuite · main · session e4aeb3fb
  - Claim record `hemasuite-tdd-gate-pin-drift` (bf7373d5, dead).
- **h-mad defects (a), (c), (d) from HemaSuite #10** — unchanged since 2026-09-30.
  - Handover-From: HemaSuite · main · session 7c01aa37
  - Claim record `hmad-defects-from-hemasuite` (bf7373d5, dead).
- **Pre-existing `test_top_level_key_set_still_matches`** (live-binary drift) — unchanged.
- **Live smoke runs** (mhr V-11.1–5, operator) — unchanged.
- **grok-author trial decision** — unchanged.
- **Leftover locked worktree `agent-ae2695dac68faa13d`** — unchanged.
- **`exec-pane` wrapper leak** (`docs/skill-candidates.md:2186`) — unchanged.
- **Foreign `stash@{0}`** ("resolved-model") — untouched.
- **HemaSuite pointer `2026-09-14-main__wsg-backlog-two-items-owed-here.md`** — unchanged; ownership stays here.
- **Closed this session** (from the predecessor):
  - Next Step 1 (CX-CANON pin): `3183480b`.
  - Next Step 2 (T7, T8): `f61bb908`, `a9d60c52`.
  - Next Step 3 (T9 decision applied): spec v1.5, design v1.3, impl-plan v1.3, plan v1.5, and the comparator (`196f4d70`, `be39a146`).
  - Next Step 4 (T9 through T12): `315ae4fb`, `aeeb8c77`, `641dc9c6`, `d01b9df3`, `196f4d70`.
  - Phase 5 closure (5f/5g) was also done; the Phase 6/7 remainder is carried as Next Steps 4-6.
  - Task 5's minor deviation and the impl-plan's low-severity 5d items: carried into Next Step 5.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/h_mad_resume_decision.py`
- `h-mad/hooks/h-mad-codex-tdd-gate.py`
- `h-mad/references/{codex,grok,agy}-runtime.md`, `h-mad/references/codex-implementer-prompt.md`, `h-mad/SKILL.md`
- `h-mad/tests/{test_h_mad_codex_tdd_gate_judge,test_h_mad_resume_decision,test_h_mad_codex_runtime,test_host_runtime_docs,test_h_mad_assemble_tdd_agent}.py`
- `h-mad/tests/mutation-specs/{codex_gate_judge_wiring,resume_decision_git_dir}.json`
- `.h-mad/wires.jsonl`
- `docs/03-analysis/probes/tdd-gate-fail-opens/{reproduce.py,compare_readings.py,reading-fixed.txt,compare-fixed.txt,t8-census.txt}`
- `docs/03-analysis/tdd-gate-fail-opens.archreview.v1.md`
- The spec, design, plan and impl-plan.

**Uncommitted changes:** none (this handoff aside).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout feature/tdd-gate-fail-opens && git push origin HEAD
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
# Next Step 1: read spec AC-3.6 (line 337) to settle F2, then F1 via Codex (re-arm phase=step5)
```

**Related docs:** `docs/03-analysis/tdd-gate-fail-opens.archreview.v1.md`; the design (v1.3), spec (v1.5), impl-plan (v1.3) and plan (v1.5).
