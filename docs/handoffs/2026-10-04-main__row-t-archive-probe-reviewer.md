# Handoff — row T gate allowance, archive completion, probe verb, change-reviewer agent

**Date:** 2026-10-04
**Branch:** main
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-10-04-main__backlog-burn-full-sweep.md

## Session Summary

Cleared the predecessor's queue: row T, the push, and the 8 archived features. Then kept building backlog rows: open rows **37 → 32**.
- **Row T:** the Codex Phase 5 gate admits command prefixes the operator declares in `.h-mad/phase5-shell-allow` (`81920a9d`).
- **Archives:** all 8 archived features with live leftovers are now complete. Two hidden readers that the archive tool could not see were found and fixed (`19b1da41`).
- **New verb:** `hmad-dispatch probe` (`30f6963e`).
- **New agent:** `change-reviewer`, which writes its own report file (`1b8543c8`).
- **Closed by calibration, not built:** three rows (1333, 1365, 1669).

**Final state: 5640 passed / 0 failed / 0 skipped at `1b8543c8`, anchors 1443/1443, `INSTALL: PASS`, pushed: `main` = `origin/main`.**

## Key Learnings

- **Agent definitions hot-load mid-session.** A new `~/.claude/agents/*.md` symlink was refused as an unknown type
  at first dispatch, then appeared in the available agent list a few turns later, in the same session. An
  instruction claiming "next session only" was written, found wrong, and removed. Dispatch again before
  concluding it is unavailable.
- **The archive tool's reader search missed relative paths.** `probes/multi-host-runtime/rehearsal/cases.json`
  reads `../../grok-codex-fallback/*.log` and never spells `probes/<feature>`. `probe_readers` now also searches
  the probes tree for `../<feature>`. A census that looks clean before a move is not proof: the full suite after
  the move is what found it.
- **A test can pass only because cleanup is incomplete.** `test_corpus_old_fields_unperturbed` drew its corpus
  from impl-plans outside `docs/archive/`, so completing the archive emptied it. A corpus test should read a set
  that only grows; it now includes archived plans.
- **Doc-section tests carry runaway guards.** `test_h_mad_context_budget_docs.py` caps its section at 160 lines.
  A paragraph added to the wrong section tripped 25 tests at once. Read the error ("section boundary ran away")
  as "wrong section", not as a cap to raise.
- **Scoping by sub-project would not have fixed row T.** A feature whose state lives in the ROOT
  `docs/.bkit-memory.json` governs every directory, because `read_chain` includes ancestors. Only an operator
  allowance fixes it, and the gate must refuse codex writes to that file, or a worker grants itself any command.
- **Calibrate before building, and say so in the backlog tag.** Two rows came from one plan's one-off format, and
  one was concentrated in a single arc. `skill_candidates_census` requires `(triage: …)` on every DECLINED;
  `(calibrated, not built)` alone fails `test_the_live_backlog_has_no_unqualified_declined`.
- **A fresh reviewer earns its cost.** Round 1 of `change-reviewer` mutated my new tests and found 4 that
  survived. Round 2, on the real agent type, confirmed the fixes and found one more unpinned sentence.

## Next Steps

1. **Keep building open rows by value:** `python3 handoff/scripts/skill_candidates_census.py --list-open docs/skill-candidates.md` (32 open).
   The "yes" rows not yet attempted or deferred:
   - 1370: run prescribed test-helper blocks against the module's guards;
   - 2202: blinded adjudication set.
   Most remaining rows are "maybe".
2. **Optionally run `hmad-dispatch probe codex --timeout 60` against the live pinned codex pane.** It has only
   been run against a fake `orca`. It types one arithmetic question into that pane, so pick a moment when codex
   is idle.
3. **To land row T in HemaSuite:** create `HemaSuite/.h-mad/phase5-shell-allow` (gitignored, per machine)
   with a line such as `hpw manuscript run`. `deck-guided-narrative-assets` is at step5 there, so manuscript
   runs are blocked until this exists.

## Open / Blocked Items

**Carried from `backlog-burn-full-sweep` (2026-10-04); every item accounted for:**

- Next Step 1, row T gate scoping: **CLOSED `81920a9d`**. Operator allowance, chosen by the user. 25 tests;
  `codex_gate_shell_allowance.json` 9/9 ALL_CAUGHT.
- Next Step 2, push 24 commits: **CLOSED**. Pushed with `81920a9d`; every later commit is pushed too.
- Next Step 3, 8 archived features with live leftovers: **CLOSED `19b1da41`**. All `COMPLETE left=0`;
  grok-codex-fallback's probes are `KEPT` (they have a live reader).
- Next Step 4, build open rows: **in progress**, 37 → 32 (see Next Step 1).
  - LANDED: 1607 (`probe`), 2333 (`change-reviewer`).
  - DECLINED after calibration: 1333, 1365, 1669.
- token-weather on the other Mac: **unchanged since 2026-10-04, user action**.
- A concurrent session shares this working tree: **unchanged; no recurrence observed**.
- `#56`'s residue trichotomy reads as three live options: **unchanged, deliberate.**
- Row T, taken over from HemaSuite (Handover-From: HemaSuite · main · session 156b7445): **CLOSED `81920a9d`**.
  Using it there is Next Step 3.
  - Location: `repo: /Users/kimhawk/orca/skills · branch: main · worktree: /Users/kimhawk/orca/skills`.
- Other Mac setup: **unchanged, user action**. Run `h-mad/git-hooks/install.sh`, `pip install pytest-subtests`
  and `git pull`. Then re-run the h-mad bootstrap agent registration (SKILL.md item 3), which now links six
  agents including `change-reviewer`.
- Deferred rows: **unchanged**, reasons on each row: 1931 (was 1924), 1624, 1679, 1662, 1387, 1348, 2113, and the
  host-equivalent-mutants row (2288). 1669 is now DECLINED alongside 1679.
- `.codex/` untracked at the repo root: **unchanged**. Unknown origin; it registers a `graft` MCP server. Left out
  of every commit.

**New this session:**

- The `graft` MCP server failed to connect (`Executable not found in $PATH: graft`). AGENTS.md tells agents to
  use it first, so the work here used `grep`/`git grep`. **Not investigated.**
- The live h-mad run in HemaSuite `preflight-command-aware` (owner `e28cd8f0`) received every skill change live
  through the symlinks. **No action needed**: these changes only add or admit, and refuse nothing new.

## Context for Next Session

**Files touched this session (all committed):**
- `h-mad/hooks/h-mad-codex-tdd-gate.py`: shell allowance, plus the guard on writes to the allowance file.
- `h-mad/scripts/hmad-dispatch.sh`: `probe` verb.
- `h-mad/scripts/h_mad_archive_feature.py`: searches for relative `../<feature>` readers.
- `h-mad/scripts/h_mad_done_gate.py`: comment only.
- `h-mad/agents/change-reviewer.md`: new agent.
- `h-mad/SKILL.md`: six-agent install lists and §"Teammate change review".
- `h-mad/references/codex-runtime.md`, `h-mad/references/agent-substrate.md`.
- Tests:
  - `test_h_mad_codex_gate_shell_allowance.py`, `test_hmad_dispatch_probe.py` and `test_h_mad_change_reviewer_agent.py` (new);
  - `test_h_mad_archive_feature.py`, `test_h_mad_parse_tasks_paths.py`, `test_h_mad_done_gate.py` and `test_h_mad_agent_definitions.py`.
- Specs: `codex_gate_shell_allowance.json` and `dispatch_probe.json` (new), and `archive_feature.json`.
- `docs/archive/**`: 164 files moved; `docs/skill-candidates.md`.
- Outside the repo: the `~/.claude/agents/change-reviewer.md` symlink.

**Uncommitted changes:** none besides this handoff; `.codex/` is untracked and not ours.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch               # expect: in sync with origin/main
python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors | tail -1   # ANCHORS_OK
python3 h-mad/scripts/h_mad_install_check.py | head -1                      # INSTALL: PASS
python3 -m pytest -q                      # ~15 min; expect 0 failed, 0 skipped
python3 handoff/scripts/skill_candidates_census.py --list-open docs/skill-candidates.md
```

**Related docs:**
- `docs/handoffs/2026-10-04-main__backlog-burn-full-sweep.md` (predecessor)
- `docs/handoffs/2026-10-04-main__tdd-gate-scope-manuscript-runs.md` (row T brief, now closed)
- `h-mad/references/codex-runtime.md` Phase 5 paragraph (the allowance)
- `h-mad/SKILL.md` §"Teammate change review"
