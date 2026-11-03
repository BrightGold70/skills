# Handoff — SKILL.md splits done, effort/model tiers measured, narrow helper agents

**Date:** 2026-11-03
**Branch:** main
**Project:** skills
**Supersedes:** 2026-11-02-main__row2910-landed-token-audit.md
**Next-Session Focus:** Live-test the handoff split with `/handoff read` in a fresh session, and take the clean first-turn context measurement in that same session.
**Suggested-Skills:** handoff (live test of the split), h-mad (`h_mad_failure_diff.py`, the mutation harness, `h_mad_ab_dispatch.py`)

## Session Summary

Hawk-MacStudio. Everything is committed and pushed (`main` = `origin/main` = `6d6f5bf4`); the last full suite was 8,297 passed, 0 failed (at `92e8e685`).

- **Row 2936 LANDED** (`e6da0758`): the `grok-tmp-env-ambient` mutant was masked inside a work tree by the nested-`--cd` branch; a new export-root test kills it.
- **Row 2930 LANDED, both halves.**
  - h-mad half: `e92c4a06` + `2120d5a5`. `h_mad_new_gate.py` reads the token registry through a split-aware reader; §"Helper scripts" moved to `h-mad/references/helper-scripts.md`; `h-mad/SKILL.md` 249,318 → 166,634 B (now 168.5 KB).
  - handoff half: `92e8e685`. READ/HANDOVER/TAKEOVER bodies moved to `handoff/references/*-mode.md`; `handoff/SKILL.md` 122,469 → 50,641 B.
- **Row 2932 LANDED** (`2cf3b7bb`): `task-executor` (Sonnet) and `task-labeller` (Haiku) helper agents, plus SKILL.md §"Helper work".
- **Row 2938 (model tier), partly landed:**
  - `91cfebcb`: codex GREEN dispatches at `--effort medium`, with a one-step `--escalate` to high.
  - `2cf3b7bb`: judge model floor test.
  - A/B evidence is recorded on the row.

## Key Learnings

- **zsh does not word-split an unquoted `$var`, and this shell is zsh.** It cost three runs this session: `${A:+--agent $A}` became one argument; `control.sh $x` passed a triple as one argument; `pytest $F` saw one path. The worst case: the empty commit argument made `git worktree add` fail, `cd` failed, and pytest ran the FULL suite in the main repo 12 times (~8 h). Use `${=x}`, or bash arrays, or `set -- ${=x}`; and give every script `set -u` plus argument guards.
- **A split must re-check every reader by kind, not only the tests that break.**
  - The h-mad slices silently removed four sections from `host_parity.py`'s host-construct scan; it read only the raw SKILL.md. No test failed: the registered tokens still appear in the raw file. Fixed in `92e8e685`.
  - `h_mad_new_gate.py` was the one production reader; 29 of 55 verdict tokens lived only in Helper scripts.
- **An inserted `###` can blow a sibling section's size guard.** `test_h_mad_context_budget_docs.py` caps "Run-context ceiling" at 160 lines; placing "Helper work" there failed 25 tests. It became its own `##` section.
- **Effort A/B (n=4 GREEN tasks):** codex medium matched high on every observed measure at −13% tokens. **implplan-author A/B (n=3 features):** Sonnet drew 12 must-fix against Opus's 14, at −62% author cost; defect classes (non-discriminating checks, one-direction wire mutation) appeared in BOTH tiers. Default stays Opus.
- **`claude -p --output-format json` can start with a stdin warning line**, and on a hook re-wake its `num_turns`/`usage` describe only the last turn. Parse from the first `{`, and trust the DONE gate, not `turns`.
- **The h-mad context-budget hook overstates.** It reported 68% when the operator saw 36%, because it assumes a 1M window (`HMAD_CONTEXT_WINDOW`). Not investigated.

## Next Steps

1. **Live-test the handoff split:** `/clear`, then `/handoff read`. Expect the core (~50 KB) to load and then `handoff/references/read-mode.md` to be read before Step 0a. Report anything the agent skips.
2. **Take the clean first-turn measurement in that session** (task #10). Run the one-liner from the predecessor handoff's Next Step 2 against the newest `~/.claude/projects/-Users-kimhawk-orca-skills/*.jsonl`. Baselines:
   - pre-cut, plain first prompt: 99.1–101.3k;
   - pre-split, `/handoff read` first: 140.3–142.6k.
   - A `/handoff read` session should now drop by roughly 20k (the HANDOVER and TAKEOVER bodies no longer load). For a cut-only reading, start with a one-word prompt instead.
3. **Row 2938, last open item:** an `implplan-author` rounds-to-clean A/B per tier. The runner is in the scratchpad: `run2.sh <feature> <commit-that-added-docs>`. It needs a revise-and-re-audit loop added.
4. **Row 2952 / tooling:** consider `--run-a/--run-b` on `h_mad_ab_dispatch.py`. Three per-arm wrappers this session had to vary argv outside the tool's UNCONTROLLED check.

## Open / Blocked Items

**Carried from `2026-11-02-main__row2910-landed-token-audit.md`:**

- **Row 2936:** closed, LANDED `e6da0758`.
- **Row 2930 (SKILL.md slice 2 + handoff half):** closed, LANDED `2120d5a5`, `92e8e685`.
- **Rows 2932 / 2934 (now 2938):** 2932 closed, LANDED `2cf3b7bb`. The model-tier row (census line 2938) is partly landed; the open item is the implplan-author rounds-to-clean A/B (Next Step 3).
- **Confirm config cuts (101k):** open, not measurable yet.
  - This session started with `/handoff read`; its 142.3k minus the ~41k handoff body gives ~101.3k, i.e. no measurable cut.
  - Needs a fresh session (Next Step 2).
  - Serena still shows as "configured but failed to connect" here despite the handoff saying it was removed from user MCP; check which scope re-adds it.
- **Hawui-Macmini sync:** unchanged since 2026-11-02.
  - `git pull`;
  - `git stash drop` of the 2026-11-01 assemble_tdd stash;
  - optionally apply the config cuts;
  - the 9 Macmini-only env failures are still uninvestigated (compare with `h_mad_failure_diff.py`, never counts).
- **Studio stash `stash@{0}` (`7541628 feat(h-mad): add resolved-model …`):** found this session. Not in any handoff; not inspected. Check with `git stash show -p stash@{0}` before dropping.
- **HemaSuite stale owned records:** unchanged.
  - `jev-todo-handover` and `carried-backlog` in `~/orca/HemaSuite/docs/.bkit-memory.json`, owner `255f4977`, heartbeat 2026-10-12.
  - Operator's call; run the oracle and `h_mad_lane_liveness.py` before any `--release`.
  - `repo: /Users/kimhawk/orca/HemaSuite · branch: main · worktree: none`.
- **Row 2856 gate half** (`.sh` production files in the TDD/wire-pin gates): unchanged since 2026-11-01.
- **Row 2890** (append mutation rows without reformatting): open, recurrence +1 this session. Rows were appended and re-pointed by ad-hoc scripts at least eight times:
  - the effort, helper-agent, judge, host-parity and budget specs;
  - 19 handoff re-points;
  - 4 h-mad re-points.
- **Row 2924** (`--subject-snapshot` for failure-diff): unchanged; failure-diff was not used this session.
- **Row 2952** (commit docs to the default branch from a feature checkout): unchanged.
- **[suggested] Wire `h_mad_reanchor_diff.py` into the re-anchor step:** unchanged since 2026-11-01.
- **Watch-only triage rows; residuals of the 2026-10-31 stamps and 2026-11-01 landings; Run 8 attempts 1–2:** unchanged since their dates.
- **HemaSuite-owned items** (drafting quality without CLAUDE.md, the judge-sdk branch, unconditional restores): unchanged; not owned here.
- **ai-memory inbox:** one cross-project message in `default/brightgold70-skills`, still unread.

**New this session:**

- **h-mad context-budget hook overstatement** (68% shown, 36% real): not investigated.
- **The `oh-my-claudecode` autopilot keyword hook fired on "end to end"**, and its stop hook then blocked turns until `/oh-my-claudecode:cancel`; cleared this session.

## Context for Next Session

**Files touched this session (all committed):**
- `h-mad/scripts/{h_mad_new_gate,h_mad_skill_corpus,h_mad_assemble_tdd}.py`
- `h-mad/SKILL.md`, `h-mad/references/{helper-scripts,failure-recovery,phase5-substeps,host-constructs.json,agy-runtime,codex-runtime,grok-runtime}.md`
- `h-mad/agents/{task-executor,task-labeller}.md`
- `h-mad/tests/`: `test_grok_audit_surface_wrapper.py`, `test_h_mad_new_gate.py`, `test_h_mad_assemble_tdd.py`, `test_h_mad_helper_agents.py`, `test_h_mad_judge_model_floor.py`, `host_parity.py`, `test_host_construct_parity.py`, plus the ~12 switched to `doc_text`, and 9 mutation specs
- `handoff/SKILL.md`, `handoff/references/{read,handover,takeover}-mode.md`, `handoff/tests/{handoff_corpus,test_handoff_skill_budget}.py` and 7 switched handoff tests
- `docs/skill-candidates.md`

**Outside the repo:** `~/.claude/agents/task-executor.md` and `~/.claude/agents/task-labeller.md`, symlinked to the repo. They are dispatchable by name from the next session.

**Uncommitted changes:** none. Untracked, all pre-existing: `.codex/config.toml`, three `docs/03-analysis/*` files, `hemasuite/docs/research/`.

**To resume:**
```bash
cd ~/orca/skills && git checkout main && git pull --ff-only
python3 handoff/scripts/skill_candidates_census.py --list-open docs/skill-candidates.md   # OPEN 7 (5 carried + 2 filed by this session's scout)
```

**Related docs:**
- `docs/skill-candidates.md`: rows 2930, 2932, 2936 (LANDED), the handoff-split row (LANDED), 2938 (model tier, with three A/B evidence blocks)
- `docs/01-plan/features/skill-md-split.plan.md`
- Scratchpad A/B material (not durable): `/private/tmp/claude-501/-Users-kimhawk-orca-skills/b1a99532-4a45-4a59-960c-b1e71280ec1b/scratchpad/{ab2934,abip}/`
