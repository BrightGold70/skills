# Handoff — handoff live-test fixes, carried rows 2924/2890, HemaSuite releases

**Date:** 2026-11-03
**Branch:** main
**Project:** skills
**Supersedes:** 2026-11-03-main__splits-tiers-helper-agents.md
**Next-Session Focus:** First `git pull` the shared checkout once the other lane commits, then pick from Next Steps; no feature is in flight from this lane.
**Suggested-Skills:** handoff (resume), h-mad (2856 gate half as a full /h-mad feature), verify-hmad-gates (drive the write gates for 2856)

## Session Summary

Hawk-MacStudio. Ran the live `/handoff read` test of the split and fixed both frictions it found: stubs now say to load references with `Read`, not `cat` (`5ad42b74`), and READ Step 0b no longer sets a caveman level (`f9b71630`, plus the stale `skill-call` registry entry and three handoff adapter rows). Landed carried rows **2924** failure-diff `--subject-snapshot`/`--include-dirty` (`949c7e7c`) and **2890** mutation harness `--append-row` (`d2868889`); stamps `d655d8cb`, `94cfebf4`. Measured the cut-only first turn (82.7k vs 99.1–101.3k), released HemaSuite's two dead claims, dropped an obsolete stash. Every commit is on `origin/main` (`94cfebf4`), full suite green each time (8302 / 8308 / 8318). **The shared checkout `~/orca/skills` is 3+ commits behind on purpose** — a live lane has 12 uncommitted files there (see Open Items).

## Key Learnings

- **A model-invoked `Skill(caveman, ultra)` lasts one turn.** caveman's level is one machine-wide flag (`~/.claude/.caveman-active`) written only by a user-typed `/caveman <level>` or SessionStart; its per-prompt hook re-injects the flag's level. Writing the flag from a skill changes every concurrent session.
- **On a turn that calls `advisor()`, top-level `usage` is the SUM of `usage.iterations`** (`message` + `advisor_message` + `message`, ~1.99x). Live context = the last `type == "message"` iteration. This is the 68%-vs-36% context-budget overstatement; another lane holds the fix uncommitted.
- **`git pull` aborts over an untracked file even when it is byte-identical to the incoming one** (measured in a scratch repo). Never drop a copy of a file you pushed into a shared tree another lane will pull — this handoff was committed from a temp worktree for that reason.
- **pytest prints collected ids relative to its rootdir (`pytest.ini` at repo top), not a mutation spec's root (`h-mad/`).** Found by building `--append-row`'s own spec with it; the tidy fixture had no `pytest.ini`.
- **Staging only your own hunks in a shared tree:** build the index blob from `git show HEAD:<path>` + your hunks, `git hash-object -w`, `git update-index --cacheinfo`. Used three times this session to commit around a live lane's uncommitted edits in the same files.
- **A full suite running on the live tree makes it un-editable for ~45 min** (`SUITE: BUSY` lock, and a mid-run edit measures a mixed tree). Run it on a detached worktree at the exact commit instead — and now `h_mad_failure_diff.py run --subject-snapshot` does that for failure-diff.
- **ai-memory's "session never ended, probably cut off" was wrong**: `b1a99532` is a live agy lane running `run2.sh` (row 2938's A/B). A quiet log is not a dead session (memory `feedback_idle_session_is_not_a_dead_session`).

## Next Steps

1. **When the other lane has committed, fast-forward the shared checkout** — `git -C ~/orca/skills pull --ff-only`. It will refuse while that lane's uncommitted `helper-scripts.md` / `skill-candidates.md` edits overlap this session's commits; that lane resolves them (different paragraphs).
2. **Row 2856 gate half as a full /h-mad feature** — gate non-`.py` production files by Task. Blast radius: `graft callers _parse_tasks --depth all` (`h_mad_assemble_tdd.assemble`, `h_mad_tdd_judge.resolve`, `h_mad_wire_pin_gate.check`/`main`, `h_mad_wire_registry.challenge`) plus the Claude/Codex/agy write gates; drive them with the `verify-hmad-gates` skill. Row: `docs/skill-candidates.md` "wire-pin and TDD gates see only `.py`".
3. **Row 2952** (commit docs to the default branch from a feature checkout) — this session hand-rolled the same thing three times (index construction + temp worktree + `push origin <sha>:main`); a `handoff_commit.py`-style generalisation would cover it.
4. **Once the other lane commits:** verify todo #4 (`h_mad_ab_dispatch.py` per-arm `--run`, row "vary the dispatch argv per arm", stamped LANDED only in its uncommitted tree) and #9 (context-budget iterations fix) actually landed — `git log --oneline -S'build_run_arms' -- h-mad/scripts`, `git log --oneline -S'msg_iters' -- h-mad/scripts`.

## Open / Blocked Items

**Carried from `2026-11-03-main__splits-tiers-helper-agents.md`:**

- **Row 2938 (model tier), implplan-author rounds-to-clean A/B** — BLOCKED on the agy `run2.sh` lane (Orca terminal, pid 5601 at 16:24 KST), which is running it across dispatch-resolve-verb → preflight-read-enforcement → exec-path-hardening. Results land in `/private/tmp/claude-501/-Users-kimhawk-orca-skills/b1a99532-4a45-4a59-960c-b1e71280ec1b/scratchpad/abip/`. Do not write there or re-run. `repo: /Users/kimhawk/orca/skills · branch: main · worktree: none (scratch worktrees under that scratchpad)`.
- **Confirm config cuts** — CLOSED: fresh Orca-launched session `ff66a23e`, first prompt `ok`, first model call **82,654** vs baseline 99.1–101.3k (n=1). `/handoff read` first turn now 116.4k vs 140.3–142.6k pre-split.
- **Serena "configured but failed to connect"** — CLOSED: absent from every scope now, this session `failedMcpServers: []`. The 2026-11-02 06:17Z reappearance is unattributable (only removal: `e31fe0f6` 01:58Z; backups start 2026-11-03 06:31Z). If it recurs: `ls -t ~/.claude/backups/`.
- **Hawui-Macmini sync** — unchanged since 2026-11-02: `git pull`; drop the 2026-11-01 assemble_tdd stash; optionally apply config cuts; compare its 9 Macmini-only env failures with `h_mad_failure_diff.py` (ids, never counts).
- **Studio `stash@{0}` (`7541628 …`)** — CLOSED: dropped (was `b0683740`). Content was an old `handoff/SKILL.md` draft deleting Step 3.6 text that is still current; `resolved-model` itself landed in `7541628`.
- **HemaSuite stale owned records** — CLOSED: `jev-todo-handover` and `carried-backlog` (owner `255f4977`, dead: no process, transcript 2026-10-14, workspace gone) released with plain `--release` at 16:58 KST after HemaSuite went quiet; oracle re-run `resume_manual` first; owner/heartbeat now `None`/`None`. `repo: /Users/kimhawk/orca/HemaSuite · branch: main · worktree: none`.
- **Row 2856 gate half** — still DEFERRED to a dedicated /h-mad feature (operator re-confirmed 2026-11-03); see Next Step 2.
- **Row 2890** (append mutation rows without reformatting) — CLOSED: LANDED `d2868889`.
- **Row 2924** (`--subject-snapshot` for failure-diff) — CLOSED: LANDED `949c7e7c`.
- **Row 2952** — unchanged; see Next Step 3.
- **[suggested] Wire `h_mad_reanchor_diff.py` into the re-anchor step** — owned by the other lane: its uncommitted `test_skill_wires_reanchor_diff_into_the_reanchor_step` plus `reanchor_diff.json` / `phase5-substeps.md` / `helper-scripts.md` edits on `~/orca/skills` main. Verify after it commits.
- **Row "vary the dispatch argv per arm" (`--run-a/--run-b`, todo #4)** — other lane's uncommitted work (`build_run_arms()`, stamped LANDED in its tree only); see Next Step 4.
- **Watch-only triage rows; residuals of the 2026-10-31 stamps and 2026-11-01 landings; Run 8 attempts 1–2** — unchanged since their dates.
- **HemaSuite-owned items** (drafting quality without CLAUDE.md, the judge-sdk branch, unconditional restores) — unchanged; not owned here.
- **ai-memory inbox** — CLOSED: empty under `default/brightgold70-skills` (explicit and session-resolved scope); likely claimed by another session after SessionStart reported 1. Probable topic per the worktree comment (unverified): `hmad-test-boundaries` `3c34bba8` vs main `278fc850`.
- **h-mad context-budget hook overstatement** — root cause found (advisor-turn iterations sum, see Key Learnings); BLOCKED: the fix (`h_mad_context_budget.py` last-message-iteration + test + `context_budget.json` row `sum-across-iterations-on-advisor-turn`) is uncommitted in the shared tree, written 15:30 KST by another live writer. Verify after it commits (Next Step 4).
- **oh-my-claudecode autopilot keyword hook firing on "end to end"** — CLOSED in the predecessor session; nothing recurred.

**New this session:**

- **Shared checkout `~/orca/skills` behind `origin/main`** — 3 of this session's commits (`949c7e7c`, `d2868889`, `94cfebf4`) plus this handoff's commit are on origin only; the live lane's 12 uncommitted files (`docs/skill-candidates.md`, `h-mad/references/{failure-recovery,helper-scripts,phase5-substeps}.md`, `h_mad_ab_dispatch.py`, `h_mad_context_budget.py`, three specs, three tests) block a fast-forward. Not this lane's to resolve. Until then a `/handoff read` in that checkout finds this doc only after the pull.

## Context for Next Session

**Files touched this session (all committed, on `origin/main`):**
- `handoff/SKILL.md`, `handoff/references/{read-mode,agy-runtime,codex-runtime,grok-runtime}.md`
- `handoff/tests/test_handoff_skill_budget.py`, `handoff/tests/test_handoff_read_output_style.py`, `handoff/tests/mutation-specs/{skill_budget,read_output_style}.json`
- `h-mad/references/host-constructs.json`, `h-mad/references/helper-scripts.md`
- `h-mad/scripts/h_mad_failure_diff.py`, `h-mad/tests/test_h_mad_failure_diff.py`, `h-mad/tests/mutation-specs/failure_diff_subject_snapshot.json`
- `h-mad/scripts/h_mad_mutation_harness.py`, `h-mad/tests/test_h_mad_mutation_append_row.py`, `h-mad/tests/mutation-specs/mutation_append_row.json`
- `docs/skill-candidates.md` (rows 2965/2966 filed + stamped, 2924/2890 stamped, 2856 note)
- Outside the repo: `~/orca/HemaSuite/docs/.bkit-memory.json` (two releases; gitignored)

**Uncommitted changes (this lane):** none. The shared checkout's 12 modified files belong to another live lane.

**To resume:**
```bash
cd ~/orca/skills
git fetch && git rev-list --left-right --count @{u}...HEAD   # behind until the other lane commits
git status --short                                           # its 12 files, if still there
python3 handoff/scripts/skill_candidates_census.py --list-open docs/skill-candidates.md
```

**Related docs:**
- `docs/skill-candidates.md` — rows 2856 (note 2026-11-03), 2890/2924 (LANDED), 2938, 2952, 2965/2966 (LANDED)
- `h-mad/references/helper-scripts.md` — `h_mad_failure_diff.py` and `h_mad_mutation_harness.py` entries (new flags)
- Scratchpad (not durable): `/private/tmp/claude-501/-Users-kimhawk-orca-skills/457f3c5a-5cec-4b25-a607-f982ec746ba2/scratchpad/` — `release_when_quiet.sh`, `release.log`, suite logs `full2.log`, `full2924.log`, `full2890.log`
