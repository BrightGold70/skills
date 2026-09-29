# Handoff — tdd-gate-fail-opens: Tasks 5–6 green, Task 2 mutation gap found, two HemaSuite briefs taken over

**Date:** 2026-09-30
**Branch:** feature/tdd-gate-fail-opens
**Project:** skills
**Supersedes:** 2026-09-30-feature-tdd-gate-fail-opens__phase5-tasks-0-4.md, 2026-09-30-main__hmad-defects-from-hemasuite.md, 2026-09-30-feature-tdd-gate-fail-opens__hemasuite-tdd-gate-pin-drift.md

## Session Summary

Phase 5 advanced through Task 6.
- **Task 5 (judge-bounded-reap):** RED `30a45084`, GREEN `ed4224b7`. The full suite shows only the known failure. The revert probe, the mutation specs (ALL_CAUGHT) and the anchors all pass.
- **Task 6 (cross-gate differential):** landed as `c39c1cac`, with its three discrimination runs recorded.
- **Task 2 mutation gap:** Task 2 had shipped without its 7 planned mutation rows. They are backfilled in `3220f6b9`, but **CX-CANON survives**: the test does not discriminate, so the row is parked.
- **Also this session:** `docs/skill-candidates.md` was updated and main was pushed (`4ed8127e`). The T9 decision is made. Two inbound HemaSuite briefs were taken over (`714086d7`).
- **Branch state:** pushed and in sync with origin; the tree is clean. Tasks 7–12 remain.

## Key Learnings

- **Task 2 was declared green without its mutation rows.** The previous handoff said "T0–T4 green with mutation checks", but CX-CANON, CX-FOLD, CX-GOV, CX-RESOLVE-M9 and the three CX-FORCE rows never existed.
  - A per-task census, comparing the impl-plan tables against the names in `mutation-specs/*.json`, found the gap. Run it at every task's GREEN.
  - CX-CANON then **survived**: `test_codex_case_root_m8_denies` passes with `_canonical_root` on `Path.resolve()`.
- **Never run the full suite while codex is writing tests.** Task 5 is a timing task (`< 4 s` and `< 6 s` bounds), and concurrent load plus half-written helpers contaminate both readings. The first suite run was aborted for this reason.
- **Do not commit during a harness run.** A commit mid-run makes the harness report `MUTATION: TREE_MOVED` (inner=ALL_CAUGHT), even for a docs-only commit. Re-score after committing.
- **`--test-path` takes exactly one path, which is shell-quoted.** For a task that spans several test files, pass `h-mad/tests` at GREEN, or add a note listing the files and re-run them yourself.
- **Codex's exec sandbox can do more than expected.** It ran `h_mad_mutation_harness.py` and scored ALL_CAUGHT itself 3 times this session. This contradicts HemaSuite brief item (c)'s claim that the sandbox "cannot run" the harness; check it in the triage.
- **The unfixed Codex gate already mismatches M-18/m14.** The Task 6 unfixed-base run showed this beyond the planned set, which is consistent with Task 0's reading (the Codex gate already denies a symlink loop).

## Next Steps

1. **Pin CX-CANON.** Write a discriminating test for Codex root canonicalisation (M-8), like Task 3's TI3 pin (`8db7682d`). Then promote `docs/03-analysis/tdd-gate-fail-opens.pending-mutation-specs/CX-CANON.json.pending` into `h-mad/tests/mutation-specs/codex_gate_judge_wiring.json` and score it: `python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/codex_gate_judge_wiring.json` should report 28/28 ALL_CAUGHT.
2. **Task 7 (documentation-surfaces)**, then **Task 8 (mutation-census)**. They are in `docs/01-plan/features/tdd-gate-fail-opens.impl-plan.md` §"Task 7" and §"Task 8".
   - Stage with `python3 h-mad/scripts/h_mad_assemble_tdd.py --feature tdd-gate-fail-opens --task "Task N" --phase red|green --project-root . --module <slug> --test-path <file> --python /opt/anaconda3/bin/python --prompt <scratchpad>/tN_*.txt …`.
   - Append the orchestrator note, then run `hmad-dispatch exec codex`.
   - Verify it yourself, run the revert probe and the mutation scoring, then run the full suite **on a quiet box**.
   - Task 8's census should now also catch the Task 2 rows.
3. **Before T9:** carry out the operator decision (see Open Items).
   - Add `M-18/M-14/codex/step3` to `APPROVED` in `docs/03-analysis/probes/tdd-gate-fail-opens/compare_readings.py`.
   - Add it to spec FR-1's "Verdict changes toward ALLOW" list (spec v1.5, via spec-author).
   - Update the T9 line in the impl-plan, which expects `approved=6`; it becomes 7.
4. **Tasks 9, 10a, 10b, 11, 12.** Same loop. Tasks 10b and 11 have mutation rows that are not yet present (RD-*, CX-SAFE/EQ/OPT-*), which is expected; they are written at those tasks' GREEN.
5. **Decide the HemaSuite pin-drift side** (brief `2026-09-30-feature-tdd-gate-fail-opens__hemasuite-tdd-gate-pin-drift.md`). Check whether `h_mad_tdd_judge.py`'s `resolve` passes the name map a basename instead of the root-relative path.
   - The acceptance check is `cd /Users/kimhawk/orca/HemaSuite/hematology-paper-writer && .venv/bin/python -m pytest tests/test_h_mad_tdd_gate.py::test_phase5_active_blocks_production_without_test -q`.
   - Note that HemaSuite runs whatever branch this checkout is on, because the hook is symlinked.
6. **Triage HemaSuite items (a), (c) and (d)** (brief `2026-09-30-main__hmad-defects-from-hemasuite.md`). File each as a `docs/skill-candidates.md` or `docs/skill-monitoring.md` row, then fix or park it.
7. **Close out Phase 5, then Phases 6–7.**
   - **5f:** run `python3 h-mad/scripts/h_mad_baseline_sha.py --branch feature/tdd-gate-fail-opens --trunk main` (baseline `15681a53`), then wire-registry `verify` and `challenge`.
   - **5g:** set `phase=null`.
   - **Phase 6:** 6a-prime `exec agy`, then a versioned `docs/03-analysis/tdd-gate-fail-opens.analysis.v1.md`.
   - **Phase 7:** preconditions, then integrate.

## Open / Blocked Items

- **tdd-gate-fail-opens, Phase 5** — status: in progress. Tasks 0–6 are done; Tasks 7–12 remain.
  - repo: `/Users/kimhawk/orca/skills` · branch: `feature/tdd-gate-fail-opens` · worktree: none (main worktree checked out on it)
  - State: `docs/.bkit-memory.json` has `phase=step5`, which means the Claude TDD gate is armed for production `.py` in this repo. The claim is held by session `bf7373d5`; plain `--claim` takes it once it is stale.
  - Prompts and reports are in the scratchpad `/private/tmp/claude-501/-Users-kimhawk-orca-skills/bf7373d5-4abf-4023-9aaf-a20cfdd3be27/scratchpad` (`t5_{red,green}.*`, `t6.*`, `t2_rows.*`).
  - The previous session's scratchpad is `…/47ce8444-5019-4009-9971-03670b4cb85e/scratchpad`.
- **CX-CANON survives (Task 2 defect)** — status: parked in `docs/03-analysis/tdd-gate-fail-opens.pending-mutation-specs/CX-CANON.json.pending`. It needs a discriminating pin (Next Step 1).
- **T9 approved-set** — status: **DECIDED by the operator on 2026-09-30: add to APPROVED.** The change is not yet applied (Next Step 3).
- **Task 5 minor deviation** — status: accepted. `judge` reads `reap_failed` after the `# M:K3` line; the impl-plan said before it. The resulting kind is the same, K3 is unchanged, and JT-PY catches it. Note it in the Phase 6 gap analysis.
- **Impl-plan "new findings for 5d"** (plan author's v1.2 report) — status: unchanged since 2026-09-30, low severity.
  - T0 has no control for an absent `agent-cli-reachable` line.
  - T11's cat-subst test is refused by `SIMPLE_SHELL_COMMAND`.
  - T4 has no mutation row for the empty-path equality rule.
- **HemaSuite TDD-gate pin drift** — status: taken over (`714086d7`); the premise reproduces. The side is not yet decided.
  - Handover-From: HemaSuite · main · session e4aeb3fb
  - repo: `/Users/kimhawk/orca/HemaSuite` · branch: main · test: `hematology-paper-writer/tests/test_h_mad_tdd_gate.py:112-116`
  - Claim record: `hemasuite-tdd-gate-pin-drift`.
- **h-mad defects (a), (c), (d) and the graft note, from HemaSuite #10** — status: taken over (`714086d7`); premises re-verified. None is filed yet.
  - Handover-From: HemaSuite · main · session 7c01aa37
  - Evidence: repo `/Users/kimhawk/orca/HemaSuite` · `docs/archive/2026-09/asset-legend-native-citations/`
  - Claim record: `hmad-defects-from-hemasuite`.
  - (a) The zero-evidence refusal is at `h-mad/scripts/h_mad_audit_cycle.py:216`.
  - (c) The assembler has no mutation-spec section. Its "sandbox cannot run the harness" half is contradicted by this session (see Key Learnings).
  - (d) `worker_done` failed with EPERM under `exec codex`; this session saw it 2/2 times. `h-mad/references/codex-implementer-prompt.md` asks for it.
  - (b) is the same item as the pin drift.
- **Live smoke runs** — status: unchanged since 2026-09-29. mhr V-11.1–V-11.5 is an operator step, and the skills repo has no `.codex/`.
- **Pre-existing failure `test_top_level_key_set_still_matches`** (live-binary drift) — status: unchanged. It was the only failure in the full suite this session (4994 passed).
- **grok-author trial** — status: unchanged. Decide whether it becomes routine; see memory `project_grok_author_trial.md`.
- **Leftover locked worktree** `.claude/worktrees/agent-ae2695dac68faa13d` — status: still locked.
  - Once it is unlocked: `git worktree remove .claude/worktrees/agent-ae2695dac68faa13d && git branch -d worktree-agent-ae2695dac68faa13d`.
- **`exec-pane` wrapper leak** (open row `docs/skill-candidates.md:2186`) — status: unchanged.
- **HemaSuite pointer `2026-09-14-main__wsg-backlog-two-items-owed-here.md`** — status: answered; ownership stays here. Unchanged.
- **Foreign stash `stash@{0}` ("resolved-model")** — status: untouched.
- **Closed this session (from the predecessor):**
  - Next Step 1: the full suite ran on the T5 tree, with 1 known failure.
  - Next Step 2: Task 5 done.
  - Next Step 6: `docs/skill-candidates.md` rows updated in `4ed8127e` on main.
  - Next Step 7: main pushed (`644f8bf6..4ed8127e`), and the feature branch has an upstream and is pushed.
  - The T9 OPEN-DECISION is decided (application still owed).

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/h_mad_tdd_judge.py`
- `h-mad/hooks/h-mad-tdd-gate.sh` (`JUDGE_DENY_RE`)
- `h-mad/tests/{tdd_gate_support,test_h_mad_tdd_judge,test_h_mad_tdd_gate_judge,test_h_mad_codex_tdd_gate_judge}.py`
- `h-mad/tests/test_h_mad_tdd_gate_differential.py` (new)
- `h-mad/tests/mutation-specs/{tdd_judge_scoring,claude_gate_judge_wiring,codex_gate_judge_wiring}.json`
- `docs/03-analysis/probes/tdd-gate-fail-opens/t6-*.txt`
- `docs/03-analysis/tdd-gate-fail-opens.pending-mutation-specs/CX-CANON.json.pending`
- On main: `docs/skill-candidates.md`
- `docs/handoffs/` (two briefs stamped)

**Uncommitted changes:** none.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout feature/tdd-gate-fail-opens
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
/h-mad "tdd-gate-fail-opens"      # continue Phase 5: Next Step 1 (CX-CANON pin), then Task 7
```

**Related docs:**
- The impl-plan (v1.2): `docs/01-plan/features/tdd-gate-fail-opens.impl-plan.md`
- The design (v1.2): `docs/02-design/features/tdd-gate-fail-opens.design.md`
- Probes: `docs/03-analysis/probes/tdd-gate-fail-opens/`
- The two taken-over briefs, as named in Supersedes.
