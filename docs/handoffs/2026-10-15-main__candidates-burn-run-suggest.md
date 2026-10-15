# Handoff — candidate burn-down, HemaSuite takeover, J50/J51/(f) fixes, 80%/90% run suggestion

**Date:** 2026-10-15
**Branch:** main
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-10-12-main__fence-probe-hmad-todo-rebuild.md, 2026-10-13-main__hemasuite-skills-lane-items.md

## Session Summary

A long session (2026-10-12 → 10-15) that cleared most of the skills-lane backlog. Every change was
committed after a green full suite, and everything is pushed except the closeout commit `2a03ca2b`,
which goes with this handoff.
- **Mutation harness.** It publishes `hollow_kills=` (`96e43e19`). A full 165-spec `--sweep` was run as the negative control, and the refusal was declined (`aa5d79aa`).
- **BashParse.** The false-proof sweep is committed as a test (`8b5de835`).
- **New tool.** `local_only_commits.py` answers "is this branch's work on main?" (`846fcfec`).
- **J50.** The scratchpad exemption is guarded by a not-in-a-work-tree check (`05cc4d0d`).
- **J51.** Sandbox-known failures are declared (`05cc4d0d`).
- **(f).** Version history refuses splitlines-only line breaks (`e39e22a3`).
- **Run suggestion.** It is new: past 80% or 90% context it suggests a `/handoff` close-out and never obliges (`2a03ca2b`).
- **HemaSuite takeover.** The `(a)–(g)/item 12` pointer was resolved (`fec09a63`). 53 of HemaSuite's open candidate rows were reconciled and applied to HemaSuite `main` as `ab94673ea`.

## Key Learnings

- **The site rule cannot make a hollow kill refusable.** The full sweep's only two hollow flags were real kills (`review_evidence_grok.json` e4/e10). The mutation drops an `isinstance(str)` guard, then `x in _SET` raises on the replacement's own line, and that is the property violation itself. Evidence is in `docs/03-analysis/2026-10-12-mutation-sweep-hollow-calibration.md`. `[gotcha, 0.7]`
- **Sweep mutations in a throwaway worktree when a live session shares the skill through a symlink.** All committed spec roots are relative (a test pins this), so a detached worktree in the scratchpad isolates every mutation. A sweep in the live tree would have rewritten scripts that HemaSuite's running harness was executing. `[solution, 0.7]`
- **A fuzz sweep is only as good as its shapes.** The first BashParse sweep (462 positions, 0 false proofs) missed both restored regressions, R13 and R14. Each was caught only after its specific shape was added: a word after `}`, and the backslash `<<E\` heredoc. Mutation-test the sweep itself. `[gotcha, 0.7]`
- **Calibrate a refusal against the real corpus before shipping it.** The splitlines refusal: 0 of 1587 HemaSuite and 1 of 263 skills Version-History docs carry such a character, and that one doc is never bumped. The J50 `$TMPDIR` exemption as filed would have ungated a worktree inside the scratchpad. `[pattern, 0.5]`
- **Apply a cross-repo reconciliation by the census's own open-line, not by name.** HemaSuite `main` had moved on to 409 rows and OPEN 75, against the 389/56 that was reconciled. Name matching refused twice: once on a recurrence bump, once on a declined reinforcement row. Targeting the exact line `--list-open` reports was the rule that held. `[solution, 0.5]`
- **A count pin on a shared doc fails on another session's work in progress.** The census tests read the working-tree `docs/skill-monitoring.md`. Another session's uncommitted J52/J53 made them fail (50 entries, 2 open) while HEAD reads 48/0. Prove it by running the census on `git show HEAD:<file>`. `[gotcha, 0.5]`

## Next Steps

1. **On the other Mac**, unchanged from 2026-10-12 and still a user action there: `git pull --ff-only`, then `git worktree remove .claude/worktrees/expect-screens-oracle && git branch -d worktree-expect-screens-oracle`, and `git worktree remove .claude/worktrees/bashparse-r13 && git branch -d fix/bashparse-r13 fix/coverage-alias-source`. Use `-d`, not `-D`. Also check whether token-weather is registered, whether pytest-subtests is still needed, and the untracked `.codex/`.
2. **Foreign J52/J53 in `docs/skill-monitoring.md`** (uncommitted, another session's): when that session commits them, `handoff/tests/test_skill_candidates_census.py::test_the_non_j_rows_are_reported_but_never_parsed_as_entries` must be bumped to 50/83 (gap stays 33). `test_widening_the_parser_would_be_visible_here` (OPEN=0) fails while they are `MONITORING`. Do not edit that file from here.
3. **Second HemaSuite reconciliation pass** — 22 open rows on HemaSuite `main` were added after the reconciled copy was read. They are listed in `docs/03-analysis/2026-10-13-hemasuite-skill-candidates-reconciliation.md` §Applied. Use the same method: read-only agents, then apply via a throwaway worktree off `origin/main`.

## Open / Blocked Items

**Carried from `2026-10-12-main__fence-probe-hmad-todo-rebuild.md`:**
- Row 2214 hollow-kill detector — **CLOSED** `96e43e19` + `aa5d79aa`. It landed as an annotation; the refusal was declined after calibration.
- Row 1351 version-history `--verify` — **CLOSED** `0d449fd2` (DECLINED: recall 0/4, twice).
- Row 2486 BashParse sweep as a test — **CLOSED** `8b5de835` (LANDED).
- Rows 2364, 2395, 1269 — re-evaluated 2026-10-12 (`86e08e43`): still deferred, no trigger fired.
- Rows 2481, 2496 — re-evaluated: `maybe`, no recurrence. 2476/2478 (squash) — SUPERSEDED, folded into 2495. 2495 — **CLOSED** `846fcfec` (LANDED). 2493 is 2496 (above).
- NS2, other Mac `git pull` + worktree cleanup + pytest-subtests + `.codex/`: open, user action there (Next Step 1).
- NS1 (token-weather band), NS3 (fence probe commit), vancouver watch: closed 2026-10-12, unchanged.
- Deferred rows 1931, 1624, 1679, 1662, 1387, 1348, 2113, 2288: unchanged since 2026-10-05.
- Concurrent HemaSuite session shares the live skill through symlinks: unchanged. Relevant in practice: the sweep was moved to an isolated worktree because of it.
- `#56` residue trichotomy, graft statusline, review residuals on rows 1406/1937/1685, pass-log rotation, accepted over-refusals (2026-10-06), V-11.1 residuals, `tdd-gate-fail-opens` evidence bookkeeping: unchanged.
- Foreign `stash@{0}` (resolved-model): unchanged; do not touch.
- Bash pin blast radius: unchanged (re-measurable with `h_mad_bash4_fence_probe.py`).
- Blind-adjudication 5931-vs-5929 test-count gap: unchanged, not traced. Today's full suite is 6014.
- Memory index: `OK` 19549 B (78%), above the 17500 compaction target; not compacted.

**From the taken-over brief `2026-10-13-main__hemasuite-skills-lane-items.md`** (Handover-From HemaSuite · main · session 255f4977; claim released at closeout):
- Item 1, the `(a)–(g)/item 12` pointer — **CLOSED** `fec09a63`. Item 12 is the 09-30 brief, all of it closed. (a) LANDED as J50 and (c) was already landed before it was filed. (g) was declined because bkit is a vendor plugin. (f) LANDED in `e39e22a3`.
  - New open rows from it: (b) the Codex Phase-5 shell allowlist, (d) per-task guards vs every-5d-first, (e) the judge's 40 s budget. All are `maybe` in `docs/skill-candidates.md`.
- Item 2, HemaSuite skill-candidates reconciliation — **CLOSED for 53 rows**: decisions `2ea13ee7`/`4a334f36`, applied as HemaSuite `ab94673ea` on `main` (LANDED 4, SUPERSEDED 5, DECLINED 1, OPEN 43). Not covered:
  - 22 newer rows on main (Next Step 3);
  - `land-on-main-from-worktree` and `pid-and-log-watcher`, which exist only on HemaSuite `feature/10-asset-legend-native-citations`;
  - `jev-blind-label-desk-sheet`, still **uncommitted** in HemaSuite's canonical checkout (`/Users/kimhawk/orca/HemaSuite`, on that feature branch) and HemaSuite's to commit.
  - repo: /Users/kimhawk/orca/HemaSuite · branch: main · worktree: none (applied from a throwaway, removed).

**New this session:**
- Census: skills OPEN=8 (yes 0, maybe 8) after (f) landed. J-entries: 48 at HEAD, 0 open.

## Context for Next Session

**Files touched this session (committed):**
- `h-mad/scripts/h_mad_mutation_harness.py`, `h-mad/tests/test_h_mad_mutation_harness.py`, `h-mad/tests/mutation-specs/{hollow_kill,mutation_harness}.json`
- `h-mad/tests/test_h_mad_expect_screens.py`, `h-mad/tests/mutation-specs/bashparse_sweep.json`
- `h-mad/tests/test_h_mad_check_plugin_hooks.py` (found by use: CC 2.1.296 moved the constants)
- `handoff/scripts/local_only_commits.py`, `handoff/tests/test_local_only_commits.py`, `handoff/tests/mutation-specs/local_only_commits.json`, `handoff/SKILL.md` (READ Step 3 pointer)
- `h-mad/hooks/h-mad-tdd-gate.sh`, `h-mad/tests/test_h_mad_tdd_gate_judge.py`, `h-mad/tests/mutation-specs/tdd_gate_scratchpad.json`
- `h-mad/scripts/h_mad_assemble_tdd.py`, `h-mad/tests/test_h_mad_assemble_tdd.py`, `h-mad/tests/mutation-specs/assemble_tdd_env_known.json`
- `h-mad/scripts/h_mad_version_history.py`, `h-mad/tests/test_h_mad_version_history.py`, `h-mad/tests/mutation-specs/version_history_separators.json`
- `h-mad/hooks/h-mad-advisor-warn.sh`, `h-mad/tests/test_h_mad_advisor_warn.py`, `h-mad/tests/mutation-specs/{advisor_warn,run_suggest}.json`
- `h-mad/SKILL.md`, `docs/skill-candidates.md`, `docs/skill-monitoring.md` (J50/J51 FIXED), `handoff/tests/test_skill_candidates_census.py` (pin 46→48)
- `docs/03-analysis/2026-10-12-mutation-sweep-hollow-calibration.md`, `docs/03-analysis/2026-10-13-hemasuite-skill-candidates-reconciliation.md`
- `docs/handoffs/2026-10-13-main__hemasuite-skills-lane-items.md` (Taken-Over-By stamp)

**Uncommitted changes:** `docs/skill-monitoring.md` carries ANOTHER session's J52/J53 work in progress. It is not mine and was not staged.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch                    # expect main...origin/main; skill-monitoring.md M is foreign
python3 handoff/scripts/skill_candidates_census.py --list-open docs/skill-candidates.md   # OPEN=8
/opt/anaconda3/bin/python3 -m pytest -q h-mad/tests/test_h_mad_advisor_warn.py           # 40 passed
```

**Related docs:**
- `docs/03-analysis/2026-10-12-mutation-sweep-hollow-calibration.md`
- `docs/03-analysis/2026-10-13-hemasuite-skill-candidates-reconciliation.md`
- `h-mad/SKILL.md` §"Run-context ceiling — halt the run at 80%" (now documents the hook's suggestion)
