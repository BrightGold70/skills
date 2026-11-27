# Handoff — phase5-gate-feature-scope: 5a–5c done, Task 1 committed; Task 2 next

**Date:** 2026-11-27
**Branch:** main
**Project:** skills
**Supersedes:** 2026-11-26-main__phase5-gate-arm-5a-next.md
**Next-Session Focus:** phase5-gate-feature-scope Phase 5d/5e, starting at Task 2 (S0, measurement probes + pin census) in the feature worktree. Claim first.
**Suggested-Skills:** h-mad (re-read `references/phase5-substeps.md` and `references/teammate-authors.md` before the first dispatch), handoff (closeout)

## Session Summary

Partial, on track. 5a was armed and the impl-plan was written: v1.0, then v1.1 after cycle 1, then corrective v1.2 and v1.3 after cycle 2. 5b exited on the two-round cap. Every filed finding was fixed, and the sidecar is `impl-plan.audit.v3.md`. 5c is done: the local branch `feature/phase5-gate-feature-scope` was created in the worktree with first commit `bfc1d667` (`BASELINE: OK`), and the 71 wire pins were registered in `6f2b5373`. The full suite there passed 8682. Task 1 (the differential harness) is complete and committed as `b205edd3`. Its evidence: RED 79 failing, GREEN 79 passing, the revert test holds, the mutation spec scored ALL_CAUGHT 14/14 with no crash or hollow kill, the full suite passed 8761, agy's spec review returned COMPLIANT, and the independent anti-gaming review returned VERIFIED. **55 tasks remain**, so the gate fix has NOT landed and the app-profile lane's Phase 4 hold stays.

## Key Learnings

- **Codex declines this feature's gate-weakness fixtures on content grounds.** Task 1 GREEN came back BLOCKED three times: "automate reproduction of enforcement gaps". Even after a defensive-testing framing it skipped exactly the D6 mention case and the D7 git-variable fixtures. agy wrote them without objection. Later tasks that touch FR-5 arming, D6 or D7 will likely hit the same wall. The narrowest working route was `implementer=agy` for that task only, recorded, then set back to codex.
- **A per-call fresh executable shim makes macOS hooks flaky.** syspolicyd/AMFI stalls the first exec of each new inode, which pushed the agy hook's 2 s git `timeout` into `judge-error` intermittently: 1 failure in 79, failing in 13 s on one run and passing in 126 s on the next. The fix was pre-warmed, process-cached shim templates. Expect this wherever a test writes and executes many new scripts.
- **A thin venv breaks one existing h-mad test.** `test_h_mad_failure_diff.py::test_control_importing_subject_code_is_UNREADABLE` fails under any venv, because the venv disables user site-packages and its `.pth` file never loads. It passes under `python3.11`. Run audit and gate suites with `--suite-cmd "python3.11 -m pytest h-mad/tests -q -p no:cacheprovider"`, not the worktree `.venv`. The `.venv` also needed `pyyaml`, which is now installed.
- **Never run the suite concurrently with an audit leg or another pytest in the same tree.** Round 2's suite read FAIL 2, and a solo re-run passed 8682 clean. An agy dispatch that times out can also leave an orphaned pytest that holds the tree lock (seen once: pid with ppid 1). Check `pgrep -fl "pytest h-mad"` after every agy timeout.
- **A dispatch prompt that is not saved is not recoverable.** v1.0 of the impl-plan was recovered byte-exact only because the cycle-1 audit prompt in the scratchpad stems directory had inlined it. Copy each document version to the private directory before revising it.

## Next Steps

1. **Claim and re-check.**
   - `python3 h-mad/scripts/h_mad_resume_decision.py --state docs/.bkit-memory.json --feature phase5-gate-feature-scope --session-id <id>`, then `--claim`. Observed at this closeout: phase `step5`, implementer `codex`, the claim released.
   - Worktree `/Users/kimhawk/orca/workspaces/skills/phase5-gate-feature-scope`: `git log --oneline -1` should print `b205edd3`, and the tree should be clean.
   - Plan assertions 3 and 4: `docs/.bkit-memory.json` is a symlink, and `h_mad_tdd_judge.py state --root <worktree>` prints `TDD-STATE: active`.
2. **Task 2 (S0):** impl-plan §"Task 2" (`docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md:330`).
   - Stage with `h_mad_tdd_judge.py implementer --record`, then `h_mad_assemble_tdd.py --phase red --task "Task 2" --python <worktree>/.venv/bin/python --expect-fail/--expect-pass` (use the task's stated counts). Dispatch with `hmad-dispatch exec codex … --timeout 1800`.
   - Each task then follows the Task 1 recipe below.
3. **Per-task recipe** (Task 1 showed which steps catch defects):
   1. Run RED yourself and classify the failure reasons.
   2. GREEN.
   3. Re-run GREEN yourself.
   4. Revert test: `git stash push -u` on the production paths only, using the skill's exact sequence.
   5. `--append` the implementation_authors.
   6. Write the spec from the GREEN rows: paths relative to `../..`, symbols derived, `--append-row` for every row after the first. Then `--check-anchors`.
   7. Run the harness, and do not accept hollow kills.
   8. agy spec review (`--phase review --base-ref <task base>`), plus an independent anti-gaming review by `change-reviewer`.
   9. Full suite under python3.11, solo.
   10. Commit 5g with the skill's pathspec.
   11. Record review_independence.
4. **If codex declines again** (BLOCKED citing gate weakness or reproduction): set `implementer=agy` for that task with `h_mad_state_write --set implementer=agy --session-id`, then set it back to codex after the task. Record each switch in the decision sheet. If agy also declines: halt and hand off (orchestrator decision 2026-11-27, Q2 a).
5. **OD-9 fixtures:** every RED or GREEN prompt that builds the scope fixture (AC-8.1), the Scan.write fixtures or the AC-10.1 corpus needs the private addendum, `/Users/kimhawk/orca/_worktree-backups/2026-11-24/phase5-gate-feature-scope/od9_green_addendum.txt` (and the defensive framing `t01_green_frame.txt` beside it). Its source is the private dir's `residual-3.12.private.md`: mode 000, named neutrally `inaccessible-docs`. Both are copied into the private dir.
6. **Tell the app-profile coordinator (session `66c92789`) when the gate fix lands.** It has not landed. Only Task 1 of 56 is done.

## Open / Blocked Items

**phase5-gate-feature-scope** (repo: `/Users/kimhawk/orca/skills` · branch: `feature/phase5-gate-feature-scope` (local, not pushed) · worktree: `/Users/kimhawk/orca/workspaces/skills/phase5-gate-feature-scope`):
- Status: Phase 5, 1 of 56 tasks done. Commits `bfc1d667` (5c baseline: 28 docs), `6f2b5373` (wires), `b205edd3` (Task 1).
- Private run log: `/Users/kimhawk/orca/_worktree-backups/2026-11-24/phase5-gate-feature-scope/plan-cycle1-decision-sheet.md`. Read its 2026-11-26/27 sections; they cover every decision of this session.
- Private evidence: `implplan-cycle1/` (impl-plan v1.0–v1.3 copies, audit reports, delta reviews), the author reports `author_*_implplan_v1.{1,2,3}*`, and `review_task01_antigaming*.md`.
- Owed text to spec, plan and design (author reports v1.1–v1.3, "owed" sections): the narrowed OD-1 residual (spec AC-6.6 and design §7), the AC-4.9 reading of discovered files (spec and design §3), design §5 (`Applied.record`), design §9 (the step contract), `mixtures.py` and the `timing.py` options. Status: apply at landing.
- NEW-FINDING-FOR-PHASE-5 items: 7 in the v1.2 author report and 5 in the v1.3 author report. One of them: `phase5-substeps.md` 5e tells GREEN to `--append-row`, but the codex gate refuses that, so the orchestrator appends instead. Status: settle each one in its task.
- Landing-risk tests (`h-mad/tests/test_h_mad_tdd_gate_judge.py:472`, `test_h_mad_tdd_gate_peers.py:113`): unchanged since 2026-11-25. Phase 5 must run them.
- Public text: the 3 impl-plan audit reports (`impl-plan.audit.v1.p1/p2`, `v2.p1`) and the OD-9 fixture code have had no pre-commit public-text review yet. Status: the final public-text pass at landing (option C) covers them. Nothing is pushed.

**Carried from 2026-11-26, unchanged unless noted:**
- #36: create the private landing-residuals record before landing. Not started.
- #33: privately probe the unverified audit claim (decision sheet, "Open, private"). Not started.
- At landing:
  - the final public-text pass with option A's Security wording (spec Security sentence, plan L479)
  - the should-fixes ruled for landing (spec L13/L14/L194, design L108/L212, plan L395/L404, design.audit.v1.p2 L25, plan.audit.v1.p3 L25)
  - deleting the local tag `phase5-gate-docs-backup-20261126`
- Plan sidecar `plan.audit.v3.md` needs the exact text of the findings. Blocks nothing.
- Field evidence for the repo-wide arming problem: unchanged.
- OMX 0.21.5 → v0.22.24, then run `omx setup` once.
- Code 127 check in codex pane `term_39f30d1a-…`.
- P16: confirm closed.
- Reason Network: `folder <path> off` for private folders.
- Macmini steps after `git pull` to ≥ `0975a796`.
- Private gate follow-ups S4, S5, R2, R3, T1 and one new item (`_worktree-backups/2026-11-23/skills-p14-gate-exception/open-gate-finding.md`).
- The Codex/Reason Network, owned-elsewhere, codex-environment, memory-store and accepted/informational blocks: see the 2026-11-25 handoff.
- The HemaSuite `contested-claims-author-report` lane must use `--surfaces codex,agy`.
- Memory index near target.
- 12 Stitch skills need a Stitch MCP setup. Deferred.
- Orca worker `5bf0f3f6`'s pane may still be holding.
- Code mode is on (`CLAUDE_CODE_EXPERIMENTAL_CODE_MODE=1`).

**Closed this session (from the predecessor):**
- Next Step 1 (claim and arm 5a): done. Armed 2026-11-26 09:23Z. Plan L393 assertion 4 holds: `TDD-STATE: active`.
- OD rulings Q1–Q6: all (a), recorded in the decision sheet (bot `msg_697d85240d28`).
- The h-mad-app-profile lane check: done. Its record shows Phase 3 complete and Phase 4 current. Its owner was LIVE at 09:2xZ and holding under its coordinator. It was not touched.

**New this session:**
- `test_h_mad_failure_diff.py::test_control_importing_subject_code_is_UNREADABLE` assumes the user site is enabled, so it fails under any venv. Status: candidate skill-monitoring row, not filed.
- The agy hook's 2 s `timeout` on its root-discovery git call (`h-mad/hooks/h-mad-agy-tdd-gate.py:112-115`) turns exec latency into `judge-error`. This is a pre-existing hook property. Status: note for the feature (agy root lookup), not filed.
- Run `run_2213ee14c295` has no coordinator: questions sent to it get "decide yourself". Implementer decisions in this session were made by the orchestrator and are recorded.

## Context for Next Session

**Files touched this session:**
- Worktree, committed on `feature/phase5-gate-feature-scope`:
  - `docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md` and its audit reports, plus the cap-exit sidecar `impl-plan.audit.v3.md`
  - `.h-mad/wires.jsonl`
  - `docs/03-analysis/probes/phase5-gate-feature-scope/differential.py`
  - `h-mad/tests/tdd_gate_support.py`
  - `h-mad/tests/test_h_mad_phase5_scope_differential.py`
  - `h-mad/tests/mutation-specs/phase5_scope_differential.json`
- Worktree `.venv`: `pyyaml` installed (ignored).
- Main checkout: `docs/.bkit-memory.json`. Holds the claim (released at closeout), `phase=step5`, `autonomous_entry_ts`, `implementer=codex`, `implementation_authors`, `review_independence`.
- Private dir: the decision sheet, plus the reports and copies listed above.

**Worktree:**
- Worktree root: `/Users/kimhawk/orca/workspaces/skills/phase5-gate-feature-scope`, branch `feature/phase5-gate-feature-scope` at `b205edd3` (local, no upstream)
- Parent repo: `/Users/kimhawk/orca/skills`, branch `main`

**Uncommitted changes:** none in either tree, apart from this handoff before its commit.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills && git status --short --branch
WT=/Users/kimhawk/orca/workspaces/skills/phase5-gate-feature-scope
git -C $WT log --oneline -1          # b205edd3
python3 h-mad/scripts/h_mad_resume_decision.py --state docs/.bkit-memory.json --feature phase5-gate-feature-scope --session-id <id>
python3 h-mad/scripts/h_mad_tdd_judge.py state --root $WT     # TDD-STATE: active
```

**Related docs:** `h-mad/references/phase5-substeps.md` (5d L142, 5e L147, revert sequence L152), the worktree's `docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md` (conventions L10–80, Task 2 at L330), and the private decision sheet.
