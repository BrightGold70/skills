# Handoff — Row 2910 slice 1 landed (SKILL.md split), Studio baseline, token audit and config cuts

**Date:** 2026-11-02
**Branch:** main
**Project:** skills
**Supersedes:** 2026-11-01-main__rows-2903-2914-studio-move.md
**Next-Session Focus:** Pick the next open row. Candidates: 2930 (SKILL.md slice 2, `Helper scripts`), 2936 (diagnose the `grok-tmp-env-ambient` survivor), or 2932/2934 (helper agents and the model-tier table).
**Suggested-Skills:** handoff (resume and carry-forward), h-mad (`h_mad_failure_diff.py`, the mutation harness)

## Session Summary

Hawk-MacStudio session; everything is committed and pushed (`main` = `origin/main` = `66d1936f`).

**Row 2910 slice 1: LANDED.** `004b33fd` (corpus helper + 35 test files), `b06eba3e` (split + 25 re-anchored rows + budget test + doc_consumers), `de75366b` (review fixes), `66d1936f` (stamp + as-built).
- `h-mad/SKILL.md` 393,620 → 249,128 B.
- Full suite `FAILDIFF: SAME`: 8,092 vs 8,073 passed, 0 failed on both sides.
- Fresh-context change-review: must=1 should=3 nit=3, all fixed.

**Studio baseline:** 0 environment-only failures (main at `7256be26`, 8,073 passed).

**Housekeeping:**
- Both `origin/park/*` branches deleted: superseded by `8beda5d4` and `af943118`.
- HemaSuite null-heartbeat check: none found.

**Token investigation.** The operator asked, after HemaSuite's `claude -p` fix, whether h-mad wastes tokens the same way. It does not: h-mad spawns no `claude -p`, and codex children are cheap. Config cuts were applied. Four rows were filed (2930/2932/2934/2936).

## Key Learnings

- **The skill listing is budget-capped.** Moving 140 skills out of `~/.claude/skills` saved ~0.4k tokens, not the ~5k estimated. Disabling 6 LSP/telegram/docs plugins saved nothing measurable. All 29 plugins off = −14.5k headless, and bkit (~6k) is the only big one. Measure with `claude -p --model claude-haiku-5-5 --output-format json --no-session-persistence` from an empty dir; never estimate by count. Memory: `reference_session_startup_token_breakdown.md`.
- **To split a doc without breaking its pins, reconstruct rather than concatenate.**
  - Each reference keeps the original `## ` heading, then a split-body marker line, then the body verbatim. `skill_text()` restores the pre-split file byte for byte, so slice, order, count and `not in` pins keep measuring the same text.
  - Keeping the heading also keeps mutation `symbol` pins valid. For `.md` files the harness derives `symbol` from the nearest preceding heading, and with a new `# title` instead, 2 rows drifted.
- **Find the breaking set empirically.** A trial split plus `h_mad_failure_diff.py run --subject <trial>` found 128 tests in 36 files. The plan's `ast` scan missed 3 of those files and over-listed 10.
- **`open(p,'w').write(f(p))` truncates p before f reads it.** My first paste-back positive control therefore wrote an empty file, and the budget test looked like it failed to discriminate. Compute first, then open.
- **Editing any file in a tree under a mutation sweep ends it `TREE_MOVED`**, the same as failure-diff's `subject-changed`. Do side work in a separate copy (`git archive` or a worktree).
- **Shell traps on this Studio.** `ls -t` is aliased (it is parsed as `--time`), and rtk-wrapped `find -mtime` returned 0. Use Python `max(glob, key=getmtime)` or `command find`.
- **graft indexes code only**, and `graft/` is gitignored, so there is never an index to commit. Archived probes that read SKILL.md by heading (e.g. `docs/archive/2026-10/agy-coder-fallback/probes/census_doc_pins.py:157`) are invisible to the suite. One now points at a moved section; it was left as historical.

## Next Steps

1. **Pick the next open row** in `docs/skill-candidates.md` (census OPEN 8: 2856, 2890, 2924, 2930, 2932, 2934, 2936, plus the scout's `maybe` row for committing docs to main from a feature checkout). Suggested order:
   - 2936 (cheap diagnosis: `--only grok-tmp-env-ambient` on `grok_audit_surface.json`);
   - 2930 (SKILL.md slice 2: `Helper scripts`, 84.6 KB; production reads it via `h_mad_new_gate.py`'s template, so settle that first);
   - 2932 + 2934 together (narrow helper agents plus the model-tier table; A/B with `h_mad_ab_dispatch.py` before changing defaults).
2. **Confirm the config cuts in a live session.** Compare the first interactive turn's context against today's 101k:
   ```bash
   python3 -c "import json,glob,os;D=os.path.expanduser('~/.claude/projects/-Users-kimhawk-orca-skills');J=max(glob.glob(D+'/*.jsonl'),key=os.path.getmtime);r=next(json.loads(l) for l in open(J) if '\"assistant\"' in l and json.loads(l).get('type')=='assistant');u=r['message']['usage'];print(u['input_tokens']+u['cache_creation_input_tokens']+u['cache_read_input_tokens'])"
   ```
   Expect roughly 96–98k. The caveman/graft dedupe and the AGENTS.md exclude are not measurable headless.
3. **Hawui-Macmini sync, when you next use it:**
   - `git pull` in `orca/skills`;
   - `git stash drop` of the 2026-11-01 assemble_tdd stash, which is superseded;
   - optionally apply the same config cuts: `claudeMdExcludes`, removing the duplicate caveman hooks, and the graft duplicate if its untracked `.claude/settings.json` has one.

## Open / Blocked Items

**Carried from `2026-11-01-main__rows-2903-2914-studio-move.md`:**

- **Mac Studio HemaSuite daemon restart:** handed to the operator. They said 2026-11-02 that it does not belong to this worktree, so it was dropped from this lane's list. HemaSuite `main` already contains `520d3a1e1`.
- **Studio null-heartbeat check:** closed. Neither HemaSuite state file has owned records with a null heartbeat.
  - Two owned records carry STALE heartbeats: `jev-todo-handover` and `carried-backlog` in `~/orca/HemaSuite/docs/.bkit-memory.json`, owner `255f4977`, last heartbeat 2026-10-12.
  - They were not released; that is the operator's call. Run the oracle and `h_mad_lane_liveness.py` before any `--release`.
  - `repo: /Users/kimhawk/orca/HemaSuite · branch: main · worktree: none`.
- **Row 2910 (split h-mad/SKILL.md):** closed. LANDED (h-mad slice 1), see Session Summary. The handoff/SKILL.md half and later slices moved to row 2930.
- **Studio full-suite baseline:** closed. 0 env-only failures, 8,073 passed at `7256be26`.
- **Both park branches:** closed and deleted from origin.
  - `park/grok-14h-home-rstrip`: its fix and test were already on main (`8beda5d4`).
  - `park/stash-assemble-tdd-json-2026-11-01`: base landed as `af943118`; the stash only deleted 6 live rows.
  - The local stash on Hawui-Macmini is still in its `git stash list` (Next Step 3).
- **Row 2856 gate half:** `.sh` production files gated by Task; an `/h-mad` feature. Unchanged since 2026-11-01.
- **Row 2890** (`maybe`, append mutation rows without reformatting): unchanged; recurrence +1 this session. Rows were appended to `doc_consumers.json` and re-anchored in 11 specs by text-preserving edits; the scratchpad `reanchor.py` is the shape a tool would take.
- **Row 2924** (`--subject-snapshot` for failure-diff): unchanged; recurrence +1. This session used `--subject <trial worktree>` as a workaround and still lost one sweep to `TREE_MOVED`.
- **[suggested] Wire `h_mad_reanchor_diff.py` into the re-anchor step:** unchanged since 2026-11-01.
- **Watch-only triage rows (19, 51, etc.):** unchanged since 2026-10-27.
- **Residuals of the 2026-10-31 stamps:** unchanged since 2026-10-31.
- **Run 8 attempts 1–2:** evidence only, never a score. Unchanged since 2026-10-27.
- **Residuals of the 2026-11-01 landings** (git config under admitted `git diff`, `--text` refused, the re-anchor rule's rewrite blind spot): unchanged since 2026-11-01.
- **Environment-only failures on Hawui-Macmini (9):** unchanged, not investigated; Macmini only. The Studio has 0, so the 9 are Macmini-specific. Compare with `h_mad_failure_diff.py`, never counts.
- **HemaSuite drafting quality without the project CLAUDE.md:** HemaSuite-owned. Unchanged; to be measured on the next manuscript run.
- **HemaSuite per-call judge model (`HemaSuite-judge-sdk`, branch `feat/judge-provenance-non-agent`):** not owned here. Unchanged, including the heads-up about the rebase conflict with `e410554da` in `agent_executor.py`.
- **HemaSuite suite-wide search for other unconditional restores:** HemaSuite-owned residual. Unchanged.
- **Token config change on this Mac:** superseded by this session's cuts. On the Studio:
  - 6 plugins disabled; caveman ×2 and graft ×5 duplicate hooks removed; `claudeMdExcludes` covers `~/AGENTS.md`; serena removed from user MCP; 140 skills moved to `~/.claude/skills-disabled/`.
  - Backups: `~/.claude/settings.json.bak-2026-11-02` and `~/orca/skills/.claude/settings.json.bak-2026-11-02`.
  - Revert a skill by moving it back from `~/.claude/skills-disabled/`.

**New this session:**

- **Rows 2930 / 2932 / 2934 / 2936:** filed, open (see Next Step 1).
- **The archived probe `census_doc_pins.py:157`** reads `### Codex authors Phase 5` from SKILL.md, which has moved. Historical; left unchanged deliberately.

## Context for Next Session

**Files touched this session (skills `main`):**
- `h-mad/SKILL.md`
- `h-mad/references/{phase5-substeps,teammate-authors,audit-prompt-assembly}.md` (new)
- `h-mad/tests/skill_corpus.py` (new)
- `h-mad/tests/test_h_mad_skill_budget.py` (new)
- 35 switched test files: see `004b33fd`
- `h-mad/scripts/h_mad_doc_consumers.py`, `h-mad/tests/test_h_mad_doc_consumers.py`
- 12 mutation specs
- `docs/skill-candidates.md`, `docs/01-plan/features/skill-md-split.plan.md`

**Outside the repo:**
- `~/.claude/settings.json`, `~/.claude.json` (serena removed)
- `~/orca/skills/.claude/settings.json` (untracked)
- `~/.claude/skills` → `~/.claude/skills-disabled`
- memory `reference_session_startup_token_breakdown.md`

**Uncommitted changes:** none. Untracked, all pre-existing: `.codex/config.toml`, three `docs/03-analysis/*` files, `hemasuite/docs/research/`.

**To resume:**
```bash
cd ~/orca/skills && git checkout main && git pull --ff-only
python3 handoff/scripts/skill_candidates_census.py docs/skill-candidates.md | grep '^TOTAL'   # OPEN 8
```

**Related docs:**
- `docs/01-plan/features/skill-md-split.plan.md` (§"As built")
- `docs/skill-candidates.md` rows 2910 (LANDED), 2930, 2932, 2934, 2936
- Review report (scratchpad; not durable). Its findings are summarized in `de75366b`'s message.
