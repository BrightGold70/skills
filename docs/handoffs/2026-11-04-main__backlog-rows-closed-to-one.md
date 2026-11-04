# Handoff — backlog rows 2938/2953/2958/2965/2981/2984/2985/2986 closed; OPEN=1 (row 2856)

**Date:** 2026-11-04
**Branch:** main
**Project:** skills
**Supersedes:** 2026-11-04-main__gate-non-py-plan-design.md
**Next-Session Focus:** Finish H-MAD feature `gate-non-py-production-files` (Row 2856, the sole remaining open candidate row) in `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files` once its in-flight Phase-4 design audit cycle 1 finishes.
**Suggested-Skills:** h-mad (drive `gate-non-py-production-files` through Phase 4–7), verify-hmad-gates (verify worktree hooks in Phase 5 FR-9 via `HMAD_VERIFY_H_MAD_ROOT`), handoff (resume)

## Session Summary

Hawk-MacStudio (`~/orca/skills` on `main`). Reconciled the shared checkout with `origin/main` (dropping the duplicate local row-2924 commit in favor of `949c7e7c`) and landed every remaining open candidate row and quick-fix outside the sibling `gate-non-py-production-files` worktree:
- **Todo #15 (`3f54f955`):** `h_mad_context_budget.py` `last_context_tokens()` now reads the last `type == "message"` entry in `usage["iterations"]` instead of the multi-iteration sum on `advisor()` turns (`context_budget.json` 10/10 caught).
- **Todo #11 (`83015c97`):** wired `h_mad_reanchor_diff.py` into `phase5-substeps.md`, `failure-recovery.md`, and `helper-scripts.md` (`h_mad_doc_consumers.py` PASS 94/4447, `reanchor_diff.json` 7/7 caught).
- **Rows 2938 & 2958 (`29636d34`):** completed the 3-feature × 3-round `implplan-author` Opus-vs-Sonnet A/B (`run2.sh`, 18 author + 18 Opus `doc-auditor` dispatches; verdict: keep `implplan-author` on `opus`) and added per-arm `{{VAR}}` `--run` argv substitution in `h_mad_ab_dispatch.py` (`build_run_arms()`).
- **Row 2953 (`5db87e97`):** added `--onto-default` (`run_onto_default()`, `commit_to_branch_ref()`) and fixed `status_entries()` XY slicing in `handoff_commit.py` (`handoff_commit.json` 5/5 caught).
- **Row 2965 (`83009078`):** added `--replay <red>..<green>` positive control and per-arm detached worktree scoring to `h_mad_ab_dispatch.py` (`ab_dispatch.json` 23/23 caught).
- **Rows 2984, 2981, 2985, 2986 (`3261a746`):** added `--commit -F <msgfile>` to `h_mad_done_gate.py` (`author_done_line.json` 22/22), `suite-at <ref> [--include-dirty]` to `h_mad_failure_diff.py` (`failure_diff_subject_snapshot.json` 10/10), `SUITE-HOLD` tree-lock refusal + `--force` to `h_mad_delta_stage.py` (`delta_stage.json` 40/40), and `HMAD_VERIFY_H_MAD_ROOT` + `claude` verb to `.claude/skills/verify-hmad-gates/bin/hmad-verify.sh` (live-verified against the sibling worktree).

`skill_candidates_census.py` now reads `parsed=354/354`, `LANDED=214`, `OPEN(yes+maybe)=1` (only Row 2856 `gate-non-py-production-files`), and repo-wide `--check-anchors` is `ANCHORS_OK specs=205 mutations=2917 ok=2917 drifted=0`.

## Key Learnings

- **Multi-round `implplan-author` A/B (`MAX_ROUNDS=3`) reverses the r1 cost impression:** Sonnet closed more findings in r2 (`12→5` must-fix) at 31% of Opus author cost (`$9.56` vs `$31.00`), but its r3 revisions were shallow (`+4`/`+36`/`+9` lines) and regressed on 2 of 3 features (`5→8` must-fix via fix-introduced contradictions and syntax-invalid bash mutation rows), whereas Opus converged monotonically (`14→13→5` must-fix, `25→28→10` build findings) and verified its r3 patches in scratch builds. Because each Opus `doc-auditor` pass costs `$3.70–$4.85`, one extra audit round from a shallow revision wipes out the Sonnet author savings.
- **Unpinned single-line mutation anchors in `failure_diff.json` collide when new functions reuse local variable names:** adding `if not removed:`, `if leaked:`, and `for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):` in `suite_at_mode` caused 3 anchors in `failure_diff.json` to match twice (`ANCHORS_DRIFTED 3/44`). Distinct local names (`wt_removed`, `wt_leaked`, `sig_num`) preserve single-match anchors without touching existing rows.
- **`argparse` `nargs="*"` positional after `ref` swallows empty `selection` before trailing flags:** in `h_mad_failure_diff.py suite-at <ref> --subject ... -- tests`, a positional `selection` (`nargs="*"`) matched `[]` immediately after `<ref>` and caused `-- tests` to fail as unrecognized arguments. Splitting `raw_argv` on `"--"` before `parser.parse_args()` lets flags appear in any order before `-- <selection...>`.
- **Claude TDD hook (`h-mad-tdd-gate.sh`) requires `tool_input.file_path`, not `tool_input.command`:** unlike the Codex/agy Bash gates, `h-mad-tdd-gate.sh` is a `Write|Edit|MultiEdit` hook and fails closed (`kind=judge-error: could not identify the write target`) unless the JSON stdin payload supplies `tool_input.file_path`.

## Next Steps

1. **Collect Phase-4 design audit cycle 1 for `gate-non-py-production-files` (Row 2856) in the sibling worktree** once PID 85325 / 95978 finishes:
   ```bash
   cd /Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files
   export PATH="$PWD/h-mad/bin:$PATH"
   ```
   - Verify every must-fix premise against the worktree, tag with `h-mad/scripts/h_mad_audit_origins.py`, and route revisions to `design-author` (and `spec-author`/`plan-author` as needed), committing each author turn with the new one-call gate:
     ```bash
     /opt/anaconda3/bin/python3.11 /Users/kimhawk/orca/skills/h-mad/scripts/h_mad_done_gate.py --done-line "<DONE line>" --commit -F <msgfile>
     ```
2. **Drive Phase 5 (`implplan-author` + 8 TDD Tasks) of `gate-non-py-production-files`** in `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/docs/02-design/features/gate-non-py-production-files.design.md` (§"Implementation Order": parser → doc/data definition → judge → codex → agy → Claude → prose → FR-9 proof + mutation run). For FR-9, use the newly upgraded `hmad-verify.sh` with `HMAD_VERIFY_H_MAD_ROOT`:
   ```bash
   HMAD_VERIFY_H_MAD_ROOT=/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad \
     /Users/kimhawk/orca/skills/.claude/skills/verify-hmad-gates/bin/hmad-verify.sh doctor
   ```
3. **Integrate `gate-non-py-production-files` at Phase 7 onto `main`** (which now has `3261a746` cleanly in sync with `origin/main`) and stamp Row 2856 `LANDED` in `docs/skill-candidates.md`:
   ```bash
   /opt/anaconda3/bin/python3.11 h-mad/scripts/h_mad_phase7_integrate.py --base main --route merge
   ```
4. **[suggested] Review or retire draft plan `backlog-row-cycle`** — `docs/01-plan/features/backlog-row-cycle.plan.md` (`Status: Draft`, source row `docs/skill-candidates.md:2661`).
5. **[suggested] Review draft plan `hpw-duplicate-copy-retirement`** — `docs/01-plan/features/hpw-duplicate-copy-retirement.plan.md` (`Status: Draft`, retiring the stale 195-file copy of `hematology-paper-writer/` in this repo).

## Open / Blocked Items

**Active in sibling worktree:**
- **`gate-non-py-production-files` (Row 2856 gate half — the sole remaining open candidate row in `docs/skill-candidates.md`).** Status: in progress at Phase 4, design audit cycle 1 running in-flight (PID 85325 / 95978 / 95984).
  - **Location:** `repo: /Users/kimhawk/orca/skills · branch: BrightGold70/gate-non-py-production-files · worktree: /Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files` (Orca selector `47c13b8f-e5c5-4169-8038-1c413c982778::/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files`).
  - **Observed state (`docs/.bkit-memory.json` + `h_mad_resume_decision.py`):** `current_phase=4`, `last_completed_phase=3`, `owner_session_id="29681318-7f86-45ed-b6e4-d1528da3d634"`, `owner_heartbeat_ts="2026-11-04T01:53:38Z"`, oracle `owned_elsewhere`.
  - **Progress since `2026-11-04-main__gate-non-py-plan-design.md`:** Next Step 1 of predecessor (`spec v1.6` owed by design v1.0) completed in `119d2b7d`, followed by `3d2bd886` (design v1.1), `b4c6a538` (spec v1.7), and `b9c705c3` (plan v1.4, current HEAD).
  - **Key artifacts:** `docs/01-plan/features/gate-non-py-production-files{-brainstorm,.spec,.plan}.md`, `docs/02-design/features/gate-non-py-production-files.design.md`, and in-flight audit files `/tmp/audit_gate-non-py-production-files_design_cycle1_run20261104T020338Z-85325_p{1,2,3}.{report.md,out.txt,log}`.

**Closed this session (from `2026-11-04-main__gate-non-py-plan-design.md` and `2026-11-03-main__readtool-caveman-carried-rows.md`):**
- **Shared checkout `~/orca/skills` divergence from `origin/main`** — CLOSED: rebased onto `origin/main`, dropped duplicate local row-2924 commit (`26ac0a6f`) in favor of `origin/main` `949c7e7c`, verified, and pushed cleanly (`3261a746`).
- **Todo #9 / #15 (`h_mad_context_budget.py` `last_context_tokens` advisor-turn multi-iteration sum fix)** — CLOSED: LANDED `3f54f955` on `origin/main` (`context_budget.json` 10/10 caught).
- **Todo #11 (Wire `h_mad_reanchor_diff.py` into `phase5-substeps.md`, `failure-recovery.md`, `helper-scripts.md`)** — CLOSED: LANDED `83015c97` on `origin/main` (`reanchor_diff.json` 7/7 caught).
- **Row 2938 (`implplan-author` 3-round A/B across 3 features)** — CLOSED: LANDED `29636d34` on `origin/main` (`implplan-author` stays `opus`; stamped `LANDED 2026-11-03`).
- **Todo #4 / Row 2958 (line 2963, `build_run_arms()` per-arm `{{VAR}}` `--run` in `h_mad_ab_dispatch.py`)** — CLOSED: LANDED `29636d34` on `origin/main` (`ab_dispatch.json` caught; stamped `LANDED 2026-11-03`).
- **Row 2952 / 2953 (line 2956, `handoff_commit.py --onto-default` + `status_entries()` XY slicing)** — CLOSED: LANDED `5db87e97` on `origin/main` (`handoff_commit.json` 5/5 caught; stamped `LANDED 2026-11-04`).
- **Row 2965 (`h_mad_ab_dispatch.py --replay <red>..<green>`)** — CLOSED: LANDED `83009078` on `origin/main` (`ab_dispatch.json` 23/23 caught; stamped `LANDED 2026-11-04`).
- **Row 2984 (`h_mad_done_gate.py --commit -F <msgfile>`)** — CLOSED: LANDED `3261a746` on `origin/main` (`author_done_line.json` 22/22 caught; stamped `LANDED 2026-11-04`).
- **Row 2981 (`h_mad_failure_diff.py suite-at <ref> [--include-dirty]`)** — CLOSED: LANDED `3261a746` on `origin/main` (`failure_diff_subject_snapshot.json` 10/10 caught; stamped `LANDED 2026-11-04`).
- **Row 2985 (`h_mad_delta_stage.py` `SUITE-HOLD` tree-lock check + `--force`)** — CLOSED: LANDED `3261a746` on `origin/main` (`delta_stage.json` 40/40 caught; stamped `LANDED 2026-11-04`).
- **Row 2986 (`verify-hmad-gates` `HMAD_VERIFY_H_MAD_ROOT` + `claude` verb)** — CLOSED: LANDED `3261a746` on `origin/main` (stamped `LANDED 2026-11-04`).

**Carried unchanged from predecessors:**
- **Hawui-Macmini sync** — status: unchanged since 2026-11-02 (`git pull`; drop the 2026-11-01 `assemble_tdd` stash; optionally apply config cuts; compare its 9 Macmini-only env failures with `h_mad_failure_diff.py`). `repo: /Users/kimhawk/orca/skills (Hawui-Macmini) · branch: main · worktree: none`.
- **Watch-only triage rows; residuals of the 2026-10-31 stamps and 2026-11-01 landings; Run 8 attempts 1–2** — status: unchanged since their dates.
- **HemaSuite-owned items** (drafting quality without CLAUDE.md, the judge-sdk branch, unconditional restores) — status: unchanged since their dates; not owned here (`repo: /Users/kimhawk/orca/HemaSuite · branch: main · worktree: none`).

## In-Flight Processes

| PID | Command | Log | Started | Elapsed @ handoff | ETA | What to check on exit |
|---|---|---|---|---|---|---|
| 85325 / 95978 / 95984 | `hmad-dispatch audit-cycle --feature gate-non-py-production-files --phase design --cycle 1 --passes 3 --surfaces codex,agy,grok --project-root /Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files --timeout 1800 --gated docs/02-design/features/gate-non-py-production-files.design.md --legs codex --legs agy --legs grok --project-tests /Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files --suite-cmd "python3.11 -m pytest -q -p no:cacheprovider" --suite-timeout 5400` (sibling Claude worktree lane) | `/tmp/audit_gate-non-py-production-files_design_cycle1_run20261104T020338Z-85325_p{1,2,3}.log` | 11:03 | ~48m | ~10–15m more | `SUITE:` and `AUDIT-GATE:` lines in the sibling worktree terminal output |

## Context for Next Session

**Files touched this session (all committed and pushed to `origin/main` at `3261a746`):**
- `h-mad/scripts/h_mad_context_budget.py`, `h-mad/tests/test_h_mad_context_budget.py`, `h-mad/tests/mutation-specs/context_budget.json`
- `h-mad/references/phase5-substeps.md`, `h-mad/references/failure-recovery.md`, `h-mad/references/helper-scripts.md`, `h-mad/tests/test_h_mad_reanchor_diff.py`, `h-mad/tests/mutation-specs/reanchor_diff.json`
- `h-mad/scripts/h_mad_ab_dispatch.py`, `h-mad/tests/test_h_mad_ab_dispatch.py`, `h-mad/tests/mutation-specs/ab_dispatch.json`
- `handoff/scripts/handoff_commit.py`, `handoff/scripts/test_handoff_commit.py`, `handoff/tests/mutation-specs/handoff_commit.json`
- `h-mad/scripts/h_mad_done_gate.py`, `h-mad/tests/test_h_mad_done_gate.py`, `h-mad/tests/mutation-specs/author_done_line.json`
- `h-mad/scripts/h_mad_failure_diff.py`, `h-mad/tests/test_h_mad_failure_diff.py`, `h-mad/tests/mutation-specs/failure_diff_subject_snapshot.json`
- `h-mad/scripts/h_mad_delta_stage.py`, `h-mad/tests/test_h_mad_delta_stage.py`, `h-mad/tests/mutation-specs/delta_stage.json`
- `.claude/skills/verify-hmad-gates/bin/hmad-verify.sh`, `.claude/skills/verify-hmad-gates/SKILL.md`
- `docs/skill-candidates.md`, `docs/learnings.md`

**Uncommitted changes:** tracked files clean; pre-existing untracked files untouched (`.codex/config.toml`, three `docs/03-analysis/2026-10-2*.analysis.md` files, `hemasuite/docs/research/`).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git fetch && git status --short
/opt/anaconda3/bin/python3.11 handoff/scripts/skill_candidates_census.py --list-open docs/skill-candidates.md
```

**Related docs:**
- `docs/skill-candidates.md` — Row 2856 (sole open candidate), Rows 2938, 2956, 2963, 2965, 2981, 2984, 2985, 2986 (all `LANDED`)
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/docs/02-design/features/gate-non-py-production-files.design.md`
- `/private/tmp/claude-501/-Users-kimhawk-orca-skills/b1a99532-4a45-4a59-960c-b1e71280ec1b/scratchpad/abip/summary_r1_r3.json` (3-round `implplan-author` A/B data)
