# Handoff — gate-non-py-production-files: spec, plan audit and design v1.0 done

**Date:** 2026-11-04
**Branch:** main
**Project:** skills
**Supersedes:** 2026-11-03-main__splits-tiers-helper-agents.md, 2026-11-03-main__readtool-caveman-carried-rows.md
**Next-Session Focus:** Resume H-MAD feature `gate-non-py-production-files` at the design audit (Phase 4, round 1). Work in its worktree, not in `~/orca/skills`.
**Suggested-Skills:** h-mad (resume the feature at the Phase-4 design audit), handoff (resume)

## Session Summary

Hawk-MacStudio. Row 2856's gate half (gate non-`.py` production files) runs as the H-MAD feature `gate-non-py-production-files`, in its own Orca worktree. It is through Phase 3:

- brainstorm `0cb7b9b0`;
- spec v1.5 `cfe9781b` (55 ACs, 11 FRs);
- plan v1.3 `4bf4ee4c` (plan audit exited at the 2-round cap plus one corrective revision);
- design v1.0 `767be799` (operator-approved; its audit is not started).

Nothing is implemented yet. The feature branch is local only and not pushed. The claim is released (owner `None`), and the oracle reads `resume_manual`.

Operator rulings this session:
- **Scope:** gate by Task membership and allow unlisted files, on all three gates.
- **Listed doc/data files stay exempt.** The nine suffixes are `.md .yaml .yml .json .toml .txt .rst .cfg .ini`.
- **Parser:** widen `production`.
- **Wire-pin report:** retire the `ungated:` line.
- **Unreadable state:** FR-8 fails closed.
- **FR-9:** drive the worktree's hooks directly by path, using the verify-hmad-gates method.
- **Prose:** add FR-10.

## Key Learnings

- **`git worktree`s share one ref store, so another lane's commits move this worktree's `main` mid-session.** Local `main` went `d655d8cb` → `278a3abd` → `26ac0a6f` during this session, and it has diverged from `origin/main`. Never derive a base from local `main`; use `git merge-base HEAD origin/main`. Spec v1.4 corrected AC-9.4 for this.
- **`hmad-dispatch audit-cycle` runs headless (`_cmd_exec`).** It is safe even when `env` pins the agy pane of another lane's live terminal; here that was the run2.sh A/B lane.
- **Don't run an advisory delta review while the suite runs.** Its report lands in `docs/03-analysis/`, and the suite then flags `tree_moved`. Round 2 carried that flag for this reason. Schedule advisory reviews outside the suite window.
- **agy plan-audit cycle 1 fabricated its quotes but its finding was real.** It quoted plan bullets, and a test `test_codex_runtime_names_the_unconditionally_allowed_classes`, that exist nowhere, while its finding (`phase5-substeps.md:230` + the pinning doc-test) was real. Check quotes and premises separately. Logged in `docs/01-plan/features/gate-non-py-production-files.plan.rejections.md`.
- **The three surfaces found disjoint must sets.** Round 1: codex found incident-replay, agy found the stale prose rule, grok found the false transport and the tie-break. Round 2: codex found the connection mutants both ways, and the doc-auditor delta found the stale `Both gates` token and the process budget. A single surface would have missed most of them.
- **The `verify-hmad-gates` skill can't test a worktree.** It lives in the main checkout's gitignored `.claude/skills/`, and `bin/hmad-verify.sh:32-34` hardwires the installed hook paths with no override and no Claude drive. Hence FR-9 = its method, our driver.
- **zsh again:** `O="python3 x.py …"; $O …` runs nothing ("no such file"). Use an array (`O=(…); "${O[@]}"`).

## Next Steps

1. **Spec v1.6, one-line fixes owed by design v1.0.** In the worktree, dispatch `spec-author`:
   - AC-11.6's first sentence conflicts with FR-11's "or holds a copy pinned equal to it" option. The design chose no copy, so drop the copy option.
   - FR-9's "names `h_mad_mutation_harness.py` only in its safe-command table" is too narrow (PF-2: two sites, no import).

   Then commit with the DONE gate run twice.
2. **Design audit, round 1** (first gate: three surfaces). From the worktree, with `PATH="$W/h-mad/bin:$PATH"`:

   ```bash
   W=/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files; cd $W
   hmad-dispatch audit-cycle --feature gate-non-py-production-files --phase design --cycle 1 --passes 3 --surfaces codex,agy,grok --project-root $W --timeout 1800 --gated docs/02-design/features/gate-non-py-production-files.design.md --legs codex --legs agy --legs grok --project-tests $W --suite-cmd "python3.11 -m pytest -q -p no:cacheprovider" --suite-timeout 5400
   ```

   Run it in the background. The suite takes ~45 min; hold all writes to the tree until `SUITE:` prints.
   - Verify every must-fix premise against the tree.
   - Tag each one with `h_mad_audit_origins.py`.
   - Route revisions to `design-author` (and to `spec-author`/`plan-author` where a finding lands there).
   - Cap: 2 rounds plus one corrective revision.
3. **Phase 5:** after the design exits, 5a dispatches `implplan-author` from design §"Implementation Order" (8 Tasks: parser → doc/data definition → judge → codex → agy → Claude → prose → FR-9 proof plus mutation run). Carry notes P5-1, P5-2, PF-1 and PF-2 (design §Risks).
4. **Phase 7 integration target:** local `main` (`h_mad_phase7_integrate.py --base main --route merge`, plan first, then `--apply --suite …`). Apply only on the operator's go-ahead, because `main` is checked out in `/Users/kimhawk/orca/skills`, another lane's tree.

## Open / Blocked Items

**This session:**
- **`gate-non-py-production-files` (row 2856 gate half).** Status: in progress at Phase 4, with design v1.0 approved and the audit not started. Location: `repo: /Users/kimhawk/orca/skills · branch: BrightGold70/gate-non-py-production-files · worktree: /Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files` (Orca selector `47c13b8f-e5c5-4169-8038-1c413c982778`).
  - **State:** `docs/.bkit-memory.json` in that worktree (gitignored): `current_phase=4`, `last_completed_phase=3`, owner `None`.
  - **Docs:** `docs/01-plan/features/gate-non-py-production-files{-brainstorm,.spec,.plan}.md`, `docs/02-design/features/gate-non-py-production-files.design.md`, the plan audits `.plan.audit.v1.p{1,2,3}.md` / `.v2.p1.md`, `docs/03-analysis/gate-non-py-production-files.{audit-origins.jsonl,plan.delta-review.a469d56-20261103T233158Z.md}`, and `.plan.rejections.md`.
  - **Not pushed to origin.**
  - **Author reports (scratchpad, not durable):** `/private/tmp/claude-501/-Users-kimhawk-orca-skills/9496e1f6-01fb-495c-ac4c-72c013730290/scratchpad/author_gate-non-py_*.report.md`.
- **Shared checkout `~/orca/skills` has diverged from `origin/main`.** At handoff it was 4 behind and 5 ahead. The other lane's local-only, unpushed commits are:

  | commit | what | owner |
  |---|---|---|
  | `c9a49f3c` | context-budget last-message-iteration fix | the predecessor's todo #9 |
  | `46cc5f85` | reanchor_diff wiring | the predecessor's reanchor item |
  | `278a3abd` | per-arm `--run` | todo #4 |
  | `88a53a40` | `handoff_commit.py --onto-default`, row 2953 | — |
  | `26ac0a6f` | a **second** row-2924 implementation | duplicates origin's `949c7e7c`; expect conflicts on rebase |

  The tree was clean. Status: blocked on that lane rebasing onto `origin/main` and pushing. It is not this lane's to do. The operator said 2924 needs no action from this lane (2026-11-04).

**Carried from `2026-11-03-main__readtool-caveman-carried-rows.md` (read from `origin/main` 5cc9e270; not on local disk) and `2026-11-03-main__splits-tiers-helper-agents.md`:**
- **Row 2938, implplan-author rounds-to-clean A/B:** BLOCKED on the agy `run2.sh` lane. Unverified this session: PID 5601 is the `agy` process itself (started Oct 29), not `run2.sh` (`pgrep run2.sh` found nothing). Result folders exist under `/private/tmp/claude-501/-Users-kimhawk-orca-skills/b1a99532-4a45-4a59-960c-b1e71280ec1b/scratchpad/abip/{dispatch-resolve-verb,preflight-read-enforcement,exec-path-hardening}/`. Check them before assuming it is still running. `repo: /Users/kimhawk/orca/skills · branch: main · worktree: none`.
- **Row 2856 gate half:** now the in-progress feature above, no longer deferred.
- **Row 2952** (commit docs to the default branch from a feature checkout): unchanged. Note that `88a53a40`'s `--onto-default` (row 2953, local-only) may cover part of it; check after the other lane pushes.
- **Todo #4** (`--run-a/--run-b` / `build_run_arms`) and **todo #9** (context-budget fix): landed locally (`278a3abd`, `c9a49f3c`), not on origin. Verify on origin after that lane pushes, with `git log --oneline -S'build_run_arms' origin/main -- h-mad/scripts` and `git log --oneline -S'msg_iters' origin/main -- h-mad/scripts`.
- **Reanchor_diff wiring:** landed locally (`46cc5f85`), not on origin. Same check.
- **Hawui-Macmini sync:** unchanged since 2026-11-02 (`git pull`; drop the 2026-11-01 assemble_tdd stash; optionally apply the config cuts; compare its 9 Macmini-only env failures with `h_mad_failure_diff.py`).
- **Watch-only triage rows; residuals of the 2026-10-31 stamps and 2026-11-01 landings; Run 8 attempts 1–2:** unchanged since their dates.
- **HemaSuite-owned items** (drafting quality without CLAUDE.md, the judge-sdk branch, unconditional restores): unchanged, and not owned here.
- **Closed in the predecessors, not re-emitted:** row 2936, 2930, 2932, 2890, 2924 (origin `949c7e7c`); config cuts; Serena; `stash@{0}`; HemaSuite stale claims; the ai-memory inbox. Each closure is recorded in the superseded docs.

## Context for Next Session

**Files touched this session (all committed on `BrightGold70/gate-non-py-production-files`, HEAD `767be799`):**
- `docs/01-plan/features/gate-non-py-production-files-brainstorm.md`, `.spec.md`, `.plan.md`, `.plan.rejections.md`, `.plan.audit.v1.p1.md`, `.v1.p2.md`, `.v1.p3.md`, `.v2.p1.md` (+ `.effort.json`)
- `docs/02-design/features/gate-non-py-production-files.design.md`
- `docs/03-analysis/gate-non-py-production-files.audit-origins.jsonl`, `docs/03-analysis/gate-non-py-production-files.plan.delta-review.a469d56-20261103T233158Z.md` (+ `.md.txt`)
- No code under `h-mad/` changed.

**Worktree:**
- Worktree root: `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files`, branch `BrightGold70/gate-non-py-production-files` (based on `origin/main` `5cc9e270`).
- Parent repo: `/Users/kimhawk/orca/skills`, branch `main` (diverged from origin; another lane's tree; never write there).

**Uncommitted changes:** the worktree has none. `~/orca/skills` has only pre-existing untracked files (`.codex/config.toml`, three `docs/03-analysis/*`, `hemasuite/docs/research/`).

**To resume:**
```bash
cd /Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files
export PATH="$PWD/h-mad/bin:$PATH"
python3 ~/.claude/skills/h-mad/scripts/h_mad_resume_decision.py --state docs/.bkit-memory.json --feature gate-non-py-production-files --session-id "$CLAUDE_CODE_SESSION_ID"   # expect resume_manual
python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py docs/.bkit-memory.json --feature gate-non-py-production-files --claim "$CLAUDE_CODE_SESSION_ID"
hmad-dispatch env | tail -2      # PREFLIGHT: PASS; audits run headless via exec
```

**Related docs:**
- The design's §"Implementation Order", §"Phase 7 integration target" and §"Risks" (P5-1/P5-2/PF-1/PF-2)
- Spec v1.5 §Assumptions (operator rulings) and the FR-9 replay (Task 1 of `docs/01-plan/features/exec-missing-report-recovery.impl-plan.md`)
- `docs/skill-candidates.md` row "wire-pin and TDD gates see only `.py`" (row 2856)
