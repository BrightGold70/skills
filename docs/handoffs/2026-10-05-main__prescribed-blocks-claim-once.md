# Handoff — prescribed-block guard check, claim-once report paths, row T in HemaSuite, graft MCP

**Date:** 2026-10-05
**Branch:** main
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-10-04-main__row-t-archive-probe-reviewer.md

## Session Summary

This session took the open backlog from **33 to 29** rows.
- **Row 1372 landed** (`da01cfbd`): `h_mad_prescribed_block_guards.py`, a pre-RED check that runs an impl-plan's prescribed python blocks against their target test module's self-source guards.
- **Row 1666 landed** (`648be1f4`): every staged audit report path is claimed once and never handed out again.
- **Rows 2206 and 2213 declined** after calibration (`b1bcf47f`).

Both landings went through fresh-context `change-reviewer` rounds (1372: two rounds; 1666: five rounds plus a design pivot). Outside the backlog:
- row T went live in HemaSuite (allow file plus a gitignore rule, `4f0c682f` pushed);
- the graft MCP now connects;
- `graft build` indexes the repo.

**Final state:** 5738 passed / 0 failed on `main` at `648be1f4`. Pushed: `main` = `origin/main`.

## Key Learnings

- **When a design keeps growing holes, look for the shared root, not the next patch.** Row 1666's rounds 1–2 let a finished report path be *released* for re-handing. Every must-fix the reviewer found came from that release:
  - a stale `.done` made a live leg read as finished;
  - a refusal deleted the live leg's prompt;
  - a crashed re-dispatch was credited with the old report;
  - collect could drop a newer claim.

  "Claim once, never release" removed all of them at once.
- **A design change needs a fresh reviewer, not the one that reviewed the old design.** After the pivot, a new `change-reviewer` found a must-fix the earlier reviewer had not reached: the `--out` prompt path was unguarded. The resumed reviewer remained useful for confirming closure of its own findings.
- **Calibrate on the real corpus before trusting a selector.**
  - Row 1372's proposed `*_guard` name filter missed 2 of the repo's 3 self-source guards.
  - Selecting on "names `__file__`" produced 24 false collisions in one plan, all from tests that only locate sibling files.
  - Only "reads its own file, directly or via a module-level name" was right.
- **Python 3.14's `Path.exists()` returns False on EACCES**, where 3.11 raises. A fail-closed "can I see this marker" check must use `os.stat` and treat only `FileNotFoundError`/`NotADirectoryError` as absent.
- **An executor's final message can carry no evidence.** One round ended with only "No change." while it had in fact committed `eafa058e`. Always read the branch tip and re-run the verification yourself.
- **The host-parity test flags `Path(` in SKILL.md** as an unregistered host construct. Describe Python forms in prose there ("a path built from `__file__`"), and keep exact forms in script docstrings.
- **graft is a node script.**
  - An MCP entry needs both the absolute binary and `PATH=/opt/homebrew/bin:…`.
  - `claude mcp add -e` is variadic, so the server name must come before `-e`, or it is swallowed as an env value.
- **HemaSuite's `hpw` is a repo-root script (`./hpw`), not on PATH.** A Phase 5 allowance prefix must be `./hpw …`, and the previous handoff's `hpw manuscript run` is not a real subcommand.

## Next Steps

1. **Keep building open rows by value:** `python3 handoff/scripts/skill_candidates_census.py --list-open docs/skill-candidates.md` (32 open: 29 plus the three `maybe` rows this session's scout added; 5 "yes"). Suggested order:
   - **1628**, a delta-self-review verb: six hand dispatches recorded, and the naming constraint is the part to enforce;
   - **1936**, an evidence gate that counts targets, not calls;
   - **2118**, a hollow-kill detector;
   - **1684**, `expect 0` screens at the freeze sha;
   - **1349**, version-history claim grep.

   Calibrate each on the corpus before building, the way 1372 and 2206 were.
2. **Live codex probe:** `hmad-dispatch probe codex --timeout 60`. It is deferred because the pinned codex pane (`term_61254299…`) was idle but holding its own pending question about adding `graft build --deep` to a `.h-mad` file. Check `hmad-dispatch env`'s `last=` first, and probe only when that is not a question.
3. **Watch HemaSuite's live h-mad runs for `report_path_handed` HALTs** now that `648be1f4` is live through the symlinks. The remedy printed is to mint a fresh `RUN`. A HALT on an old fixed `/tmp/audit_…_cycle<N>…` path that already exists is expected and is not a bug.

## Open / Blocked Items

**Carried from `row-t-archive-probe-reviewer` (2026-10-04); every item accounted for:**

- **Next Step 1, build open rows:** in progress, 33 → 29 this session.
  - LANDED: 1372 (`da01cfbd`) and 1666 (`648be1f4`).
  - DECLINED after calibration: 2206 and 2213 (`b1bcf47f`).
- **Next Step 2, live codex probe:** **deferred, at the user's choice.** The codex pane held a pending question (see Next Step 2).
- **Next Step 3, row T in HemaSuite:** **CLOSED.**
  - `HemaSuite/.h-mad/phase5-shell-allow` = `./hpw revise`.
  - `**/.h-mad/phase5-shell-allow` was added to HemaSuite `.gitignore` (`4f0c682f`, pushed). It had not been ignored, contrary to the handoff.
  - Live gate replay with `deck-guided-narrative-assets` at step5: `./hpw revise …` ALLOW; `./hpw launch` and bare `hpw revise` DENY.
- **token-weather on the other Mac:** unchanged since 2026-10-04; user action.
- **Other Mac setup:** unchanged; user action. Run `h-mad/git-hooks/install.sh`, `pip install pytest-subtests` and `git pull`, then re-run the h-mad bootstrap agent registration.
- **A concurrent session shares this working tree:** **recurred, handled.**
  - A HemaSuite session pushed `d63d6539` and asked for a fast-forward while my SKILL.md edit was uncommitted. I stashed only SKILL.md, pulled `--ff-only` and popped the stash; it auto-merged.
  - The HemaSuite checkout also switched branches under me mid-session.
- **`#56`'s residue trichotomy reads as three live options:** unchanged, deliberate.
- **Deferred rows:** unchanged. Reasons are on each row: 1931, 1624, 1679, 1662, 1387, 1348, 2113, 2288.
- **`.codex/` untracked at the repo root:** now explained. It is codex's own `graft` MCP registration (`.codex/config.toml`). Still untracked, still left out of every commit.
- **graft MCP failed to connect:** **CLOSED.** User- and local-scope entries now run `/opt/homebrew/bin/graft` with `PATH=/opt/homebrew/bin:/usr/bin:/bin`. The tracked `.mcp.json` keeps a bare `graft`, which stays portable. Takes effect at the next Claude Code start.
- **The live h-mad run in HemaSuite received every skill change through the symlinks:** **one behaviour change this time.** `648be1f4` adds refusals for a re-handed or pre-existing report path; see Next Step 3. Live runs observed: `preflight-command-aware` (owner `e28cd8f0`), then `failed-round-diagnostic-letter` (owner `ab9bd347`).

**New this session:** none beyond the above.

## Context for Next Session

**Files touched this session (all committed and pushed):**
- `h-mad/scripts/h_mad_prescribed_block_guards.py`, `h-mad/tests/test_h_mad_prescribed_block_guards.py` (55 tests) and `h-mad/tests/mutation-specs/prescribed_block_guards.json` (27 rows). All new.
- `h-mad/scripts/h_mad_assemble_audit.py`: claim-once guard.
- `h-mad/scripts/hmad-dispatch.sh`: fresh `_run<UTC>-<pid>` stem per audit-cycle run.
- `h-mad/tests/test_h_mad_report_path_handed.py` and `h-mad/tests/mutation-specs/report_path_handed.json` (25 rows): new.
- `h-mad/tests/conftest.py`: a private `XDG_CACHE_HOME` per test; cleanup of the tests' own fresh-stem `/tmp` files.
- `h-mad/SKILL.md`: the §5d pre-RED check, two inventory entries, the claim-once rule and recipes.
- `h-mad/references/measurement-discipline.md` and `h-mad/references/orchestration-mode.md`.
- `docs/skill-candidates.md`: two LANDED notes and two DECLINED notes.
- Outside the repo:
  - HemaSuite `.gitignore` and `HemaSuite/.h-mad/phase5-shell-allow`, which is ignored;
  - `~/.claude.json` graft MCP entries;
  - `graft/` (gitignored index).

**Uncommitted changes:** none besides this handoff. `.codex/` is untracked and not ours.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch               # expect: in sync with origin/main
python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors | tail -1   # ANCHORS_OK
python3 h-mad/scripts/h_mad_install_check.py | head -1                      # INSTALL: PASS
python3 -m pytest -q                      # ~15.5 min; expect 0 failed (5738 at 648be1f4)
python3 handoff/scripts/skill_candidates_census.py --list-open docs/skill-candidates.md
graft build                               # refresh the index after code changes
```

**Related docs:**
- `docs/handoffs/2026-10-04-main__row-t-archive-probe-reviewer.md` (predecessor)
- `h-mad/SKILL.md` §5d (pre-RED prescribed-block check) and the "Never re-dispatch to a report path" rule
- `docs/skill-candidates.md` LANDED notes for 1372 and 1666, which record what each review round ruled out
