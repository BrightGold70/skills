# Handoff — tdd-gate-fail-opens: Phases 1–4 closed, Phase 5 Tasks 0–4 green

**Date:** 2026-09-30
**Branch:** feature/tdd-gate-fail-opens
**Project:** skills
**Supersedes:** 2026-09-29-main__three-features-merged.md

## Session Summary

This session took `tdd-gate-fail-opens` from its approved Phase 1 brainstorm through Phases 2–4 and into Phase 5.
- **Phases 2–4:** spec v1.4, plan v1.4 and design v1.2 are done. The design was written by grok as a trial. Each document had two audit rounds from codex and agy, then one final correction that was not re-audited.
- **Phase 5:** Tasks 0–4 are green, each with a TDD RED/GREEN pair, a revert probe and a mutation check where it applies. Tasks 5–12 remain, including 10a/10b.
- **Separately:** four carried defects were fixed on main and pushed to origin. The session stopped at about 70% of the context window, on a clean task boundary. `/loop` has stopped.

## Key Learnings

- **Unfixed Codex already refuses a symlink loop.** The Task 0 reading shows the unfixed Codex gate returns `judge-error` for a loop (M-14), even under step3-only state. The spec assumed `no-test-resolved`. So any RED that expects M-14 to change passes immediately, and T9's old-versus-new comparison will flag M-18/M-14/codex/step3 (deny→allow) as a relaxation outside the approved six.
- **Count RED per function, not per case.** Parametrised cases and fixture ImportErrors show up as ERRORs, which makes codex's raw counts look wrong. Codex BLOCKED twice on raw counts that were correct per function.
- **One feature can reverse a guard pinned by an earlier task.** Task 2's guard `test_codex_trailing_space_is_not_folded` asserted behaviour that Task 4's FR-4 trim deliberately changes. It was re-scoped to a unit check of `fold_py_suffix` plus the new end-to-end deny. Expect more of these in Tasks 5–12.
- **The Claude hook runs under `/bin/bash` 3.2.57.** Its shebang is `#!/bin/bash` and it is executed directly. Namerefs, `mapfile`, associative arrays and `${v,,}` are fatal there, which agy caught in the 5b round-1 impl-plan audit. `test_claude_gate_is_bash_3_2_clean` now pins this.
- **The agy audit leg was hollow 4 times out of 7 this session.** Three passes made only 1–3 tool calls and returned "clean", and one declared "0 files opened" while its log showed 14 calls, so the collector refused it. Codex carried every real audit finding. Do not count an agy clean without its Effort line.
- **zsh does not word-split an unquoted `$T`.** A revert probe printed `no tests ran` and read as "passed" until it was re-run with explicit paths. This recurred despite already being in memory.
- **Grok authoring trial (design):**
  - It worked end to end through `hmad-dispatch exec grok` with the full role text: the tree delta was the design file only, and the sha verified.
  - Round 1 had 10 build musts and round 2 had 9. None came from a false premise, but acceptance-criteria coverage was weak.
  - Each grok run took about 50 minutes and nearly hit its 60-minute timeout before editing anything. Budget it, and tell it to edit early.
  - Recorded in memory `project_grok_author_trial.md`.

## Next Steps

1. **Run the full suite on the Task 4 tree first.** It was not run after `f943e818`:
   `cd /Users/kimhawk/orca/skills && /opt/anaconda3/bin/python -m pytest h-mad/tests handoff/tests -q -p no:cacheprovider > /tmp/suite_t4.log 2>&1; tail -1 /tmp/suite_t4.log`
   - Expect only `test_top_level_key_set_still_matches` to fail.
   - `test_a_finishing_slot_is_waited_for_and_then_reused` is a known timing flake under load; if it fails, re-run it alone.
2. **Task 5, judge-bounded-reap (5d/5e).** It is §"Task 5" in `docs/01-plan/features/tdd-gate-fail-opens.impl-plan.md`.
   - Stage it with `python3 h-mad/scripts/h_mad_assemble_tdd.py --feature tdd-gate-fail-opens --task "Task 5" --phase red --project-root . --module judge-bounded-reap --test-path <file from the Task section> --python /opt/anaconda3/bin/python --expect-fail N --expect-pass M --guard ...`, taking N, M and the guard names from the Task's RED/GREEN line.
   - Append the house notes: score per function, report the failure mode, end with an exact STATUS line with concerns on a `Concerns:` line, never invoke the codex binary.
   - Run it with `hmad-dispatch exec codex`.
3. **Tasks 6, 7, 8, 9, 10a, 10b, 11, 12** follow the same loop. For each task:
   - verify the RED split per function and require WIRE-PINs to fail on the decision;
   - commit the RED;
   - run GREEN, then the revert probe (wire-scoped for wiring tasks), then the mutation harness on the task's spec;
   - commit, then run the full suite.
4. **T9 decision, before running T9's comparison.** Settle the OPEN-DECISION on the approved-softening set; the details are in the Open Items below.
5. **Close out Phase 5, then Phases 6–7.**
   - **5f:** run `python3 h-mad/scripts/h_mad_baseline_sha.py --branch feature/tdd-gate-fail-opens --trunk main` (baseline `15681a53`), then wire-registry `verify` and `challenge`.
   - **5g:** set `phase = null`.
   - **Phase 6:** 6a-prime `exec agy` archreview, then gap analysis written as a versioned `docs/03-analysis/tdd-gate-fail-opens.analysis.v1.md`. Phase 7 now blocks an unversioned-only analysis.
   - **Phase 7:** preconditions, then integrate.
6. **Update `docs/skill-candidates.md`** for this session's four fixed rows, since the scout was skipped.
   - Mark these LANDED: conftest (`5ca8f97e`), iterate_cycles (`0e50ce9d`), grok D3/D4 (`6c8a0a34`).
   - Reword the iterate_cycles row to its real cause: 6b never versioned `analysis.md`, and telemetry reads the files by design.
   - Mark the codex resume denial "folded into tdd-gate-fail-opens FR-8 / Tasks 10a–12".
7. **Push.**
   - main is 6 ahead of origin: spec v1.4 through design v1.2 (`644f8bf6..48d639f7`).
   - `feature/tdd-gate-fail-opens` has no upstream yet.

## Open / Blocked Items

- **tdd-gate-fail-opens, Phase 5** — status: in progress, Tasks 0–4 done.
  - repo: `/Users/kimhawk/orca/skills` · branch: `feature/tdd-gate-fail-opens` · worktree: none (main worktree checked out on it)
  - State: `docs/.bkit-memory.json` has `phase=step5` and `current_phase=5`, substrate orca/exec, `codex_status=available`. The claim is released at this closeout.
  - Note: `phase=step5` keeps the Claude TDD gate armed for this repo, so the Claude write gate governs production `.py` edits here until 5g.
  - Prompts and reports are in the scratchpad `/private/tmp/claude-501/-Users-kimhawk-orca-skills/47ce8444-5019-4009-9971-03670b4cb85e/scratchpad` (`t{0..4}_*.txt|out|log`, `author_*.report.md`).
- **OPEN-DECISION for T9** — status: needs a decision before T9 runs.
  - Background: FR-3/OD-4 (governed-only) turns M-18/M-14/codex/step3 from deny judge-error into allow. That key is outside the approved six in `compare_readings.py` `APPROVED`, so `COMPARE: FAIL` is guaranteed.
  - Recommended: add that key to the approved set, since it is an OD-4-intended relaxation, and record it in spec FR-1's "Verdict changes toward ALLOW" list via spec-author (v1.5).
- **Impl-plan "new findings for 5d"** (plan author's v1.2 report) — status: open, low severity.
  - T0 has no control for an absent `agent-cli-reachable` line. The orchestrator measured it ad hoc as rc=1 but it is not committed.
  - T11's cat-subst test is refused by `SIMPLE_SHELL_COMMAND` rather than by the option check.
  - T4 has no mutation row for the empty-path equality rule.
- **Live smoke runs** — status: unchanged since 2026-09-29.
  - mhr V-11.1–V-11.5 is an operator step.
  - OQ-D1's Codex half was open because the Codex gate was believed unregistered. In fact HemaSuite's `.codex/hooks.json` registers it, it is trusted, and it was measured blocking on 2026-09-29. The skills repo itself still has no `.codex/`.
- **Pre-existing suite failure `test_top_level_key_set_still_matches`** (live-binary drift) — status: unchanged. It also makes every Phase-3/4/5b `SUITE:` line red, so the exit streak can never go READY until it is fixed.
- **grok-author trial** — status: design phase done. Decide whether grok authoring becomes routine; the data is in memory `project_grok_author_trial.md`.
- **Leftover locked worktree** `.claude/worktrees/agent-ae2695dac68faa13d` (branch `worktree-agent-ae2695dac68faa13d`, merged as `6c8a0a34`) — status: locked by the agent harness.
  - Remove it once unlocked: `git worktree remove .claude/worktrees/agent-ae2695dac68faa13d && git branch -d worktree-agent-ae2695dac68faa13d`.
- **Carried from 2026-09-15, unchanged:**
  - The `exec-pane` wrapper leak (open row `:2186`).
  - The HemaSuite pointer `2026-09-14-main__wsg-backlog-two-items-owed-here.md`: answered, and ownership stays here.
- **Foreign stash `stash@{0}` ("resolved-model")** — status: untouched.
- **Closed this session (from the predecessor):**
  - Brainstorm approved (`c83c62fe`).
  - Untracked files resolved: graft committed `effe449b`, Jev doc `1a77e1c4`, TypeSafe excluded locally.
  - Merged worktrees removed.
  - HemaSuite hook: nothing needed re-arming. The docs were corrected (`5e3a8238`).
  - Carried defects fixed: conftest (`5ca8f97e`), iterate_cycles (`0e50ce9d`), grok D3/D4 (`6c8a0a34`). The codex resume denial was folded into FR-8.
  - telemetry `iterate_cycles`: its root cause was wrong, and it is fixed upstream.

## Context for Next Session

**Files touched this session:**
- `docs/01-plan/features/tdd-gate-fail-opens{-brainstorm,.spec,.plan,.impl-plan}.md` plus their audits
- `docs/02-design/features/tdd-gate-fail-opens.design.md` plus audits
- `docs/03-analysis/probes/tdd-gate-fail-opens/*`
- `h-mad/scripts/h_mad_target_identity.py` (new)
- `h-mad/hooks/h-mad-tdd-gate.sh`
- `h-mad/hooks/h-mad-codex-tdd-gate.py`
- `h-mad/tests/{test_h_mad_target_identity,test_h_mad_codex_tdd_gate_judge,test_h_mad_tdd_gate_judge,tdd_gate_support}.py`
- `h-mad/tests/mutation-specs/{target_identity,claude_gate_judge_wiring,codex_gate_judge_wiring}.json`
- `.h-mad/wires.jsonl`
- On main: `h-mad/references/{codex,grok}-runtime.md` and the four defect fixes

**Uncommitted changes:** none.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout feature/tdd-gate-fail-opens
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
/h-mad "tdd-gate-fail-opens"      # resume_manual → continue Phase 5 at Task 5 (after Next Step 1)
```

**Related docs:**
- The Task 0 reading and controls: `docs/03-analysis/probes/tdd-gate-fail-opens/`
- The impl-plan (v1.2): `docs/01-plan/features/tdd-gate-fail-opens.impl-plan.md`
- The design (v1.2): `docs/02-design/features/tdd-gate-fail-opens.design.md`
