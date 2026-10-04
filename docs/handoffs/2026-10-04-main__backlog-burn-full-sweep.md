# Handoff — backlog burn-down, first full-corpus mutation sweep, row T taken over

**Date:** 2026-10-04
**Branch:** main
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-10-04-main__upstream-sync-gate-fixes.md, 2026-10-04-main__tdd-gate-scope-manuscript-runs.md

## Session Summary

Drained the predecessor's whole Next Steps queue, then burned down `docs/skill-candidates.md` by value:
open rows **52 → 37**, 14 landed with tests and ALL_CAUGHT mutation specs. Ran the **first full-corpus
mutation sweep** (new `--sweep`): 145 specs, 142 ALL_CAUGHT, 3 SURVIVED, 0 unmeasured. It found 5 broken
mutation rows and a harness fail-open; all fixed. Took over HemaSuite's row T: premise **confirmed**
against the current Codex gate; it needs a design decision. Removed token-weather's sparkline on request.
**Final state: 5589 passed / 0 failed / 0 skipped at `a6701e83`, anchors 1428/1428, `INSTALL: PASS`.**
**24 commits are local and NOT pushed** (push was never instructed).

## Key Learnings

- **A corpus that reads ALL_CAUGHT spec by spec can still hold hollow rows.** The first `--sweep` that
  forwarded per-mutation kills found two rows whose replacement never parsed (`IndentationError`), scored
  as kills because tier 1 (did-not-parse = measured nothing) applied only on the TARGETED path. It also
  found three survivors: a row naming a test that cannot see its mutation, a registry test passing on a
  substring elsewhere in the tail, and a host-bound equivalent mutant. Re-read the `kill:` lines on every
  full sweep.
- **Calibrate a detector on the committed corpus before wiring it; three times it changed the design.**
  The AC census's first cut flagged 9 of 29 specs (4 misparsed tags, 5 topic orderings), so document order
  became advisory. The archive check would have moved a probes dir a live test reads. A version-history
  span check missed 13% of spans on clean docs, so it was not built. Now a rule:
  `h-mad/references/measurement-discipline.md` §CALIBRATION.
- **Filling prompt slots one `str.replace` at a time rewrites a token QUOTED inside an already-inserted
  document**, and a residual scan over the filled text reads that quote as an unfilled slot. Fill in one
  pass and scan only the template residue (`fill_slots`, all three assemblers).
- **macOS `/bin/bash` 3.2's `compgen -e` lists non-identifier env names (`CLAUDE-HYPHEN`); bash 4+'s does
  not.** A mutation can therefore be equivalent on one host and discriminating on another. This Mac has
  only bash 3.2, so `scrub-enumerates-compgen` can never be caught here.
- **Run a multi-hour sweep in a detached worktree** (`git worktree add --detach … HEAD`) so the main tree
  stays free. To stop one, SIGTERM only the `--sweep` parent and let the in-flight child spec finish and
  restore its file. Main-tree test runs alongside roughly halve its pace.
- **The Codex TDD gate gates shell commands during Phase 5, project-wide** (`h-mad-codex-tdd-gate.py:212`).
  "Bash is never gated" is true only of the Claude gate (Write|Edit matcher).
- **`.h-mad/telemetry.jsonl` records only COMPLETED features.** A run in flight is visible only as a live
  claim heartbeat in `docs/.bkit-memory.json`.
- **zsh does not word-split an unquoted `$VAR`.** `pytest $FILES` ran "no tests" silently; use `xargs`
  (or `${=VAR}`).

## Next Steps

1. **Decide row T's gate scoping.** Brief: `docs/handoffs/2026-10-04-main__tdd-gate-scope-manuscript-runs.md`.
   With any feature at step5, the Codex gate denies every non-test, non-read-only shell command anywhere in
   the project (replayed: `hpw manuscript run`, `python -m cli …`, a one-liner writing `.md` outside the
   root; a `.py` under `/tmp` is denied by design). Options: scope by the feature's sub-project root, or an
   operator-declared allowance. Keep fail-closed for unreadable state and unidentifiable targets. Code:
   `h-mad/hooks/h-mad-codex-tdd-gate.py:212` (shell allowlist), `:488` (writes with no target).
2. **Push when you choose:** `git push origin main` (24 commits ahead of `origin/main`, suite green).
3. **Decide the 8 archived features with live leftovers.** Run
   `python3 h-mad/scripts/h_mad_archive_feature.py --feature <f> --month <YYYY-MM> --check` for each:
   exec-path-hardening (2026-08, 21), gate-blindness-hardening (2026-08, 17),
   regression-provenance-ledger (2026-08, 30), codex-tdd-gate-defects (2026-09, 20), doc-block-exec
   (2026-09, 6), grok-codex-fallback (2026-09, 7), pin-agents-tail-banner (2026-09, 116),
   tdd-gate-fail-opens (2026-09, 19). Removal was NOT done: the files are tracked docs, and some may be
   deliberately live.
4. **Keep building open rows by value:** `python3 handoff/scripts/skill_candidates_census.py --list-open docs/skill-candidates.md` (37 open).

## Open / Blocked Items

**Carried from `upstream-sync-gate-fixes` (2026-10-04); every item accounted for:**

- Next Step 1a, re-pin four `:1277` citations: **CLOSED `3fa10115`**. The pin was never right (the row sat at 1319 in the writing commit).
- Next Step 1b, `HARD_KINDS` never read: **CLOSED `cd05768e`**. `hard()` now refuses an unlisted kind.
- Next Step 1c/1d, lesson-only rows and the misfiled PARTIAL note: **CLOSED `d052cb3c`**.
- Next Step 2, build open rows by value: **in progress**, 52 → 37 (see Next Step 4).
- Next Step 3, the 2 skipped `test_scoring_kinds[*-with-subtest]`: **CLOSED**. `pytest-subtests` 0.15.0 installed into `/opt/anaconda3`; 0 skipped.
- token-weather on the other Mac: **unchanged, user action**. Also pull `634a9441` there (sparkline removed).
- token-weather TypeScript not type-checked: **CLOSED**. `npx -p typescript@5 tsc --noEmit -p mods/token-weather` is clean on all 3 hook files.
- A concurrent session shares this working tree: **unchanged; no recurrence observed** (HEAD steady across every suite run).
- `#56`'s residue trichotomy reads as three live options: **unchanged, deliberate.**

**Carried from the taken-over brief `tdd-gate-scope-manuscript-runs` (Handover-From: HemaSuite · main · session 156b7445):**

- Row T, the H-MAD gate blocking a manuscript run during an unrelated Phase 5: **open, premise CONFIRMED**, blocked on your design decision (Next Step 1).
  - Location: `repo: /Users/kimhawk/orca/skills · branch: main · worktree: /Users/kimhawk/orca/skills`.
  - Source record: HemaSuite `docs/03-analysis/anemia-jmj-improvement-triage-2026-10-04.md` row T.
  - Not claimed: this repo has no root state file; the only two are vendored sub-projects'.

**New this session:**

- Pushing 24 commits: **user decision** (Next Step 2).
- 8 archived features with live leftovers: **user decision** (Next Step 3).
- On the other Mac, three things are needed for this setup to hold there:
  - `h-mad/git-hooks/install.sh`, to get the new advisory pre-commit hook;
  - `pip install pytest-subtests`, for 0 skips;
  - `git pull`.
- Deferred rows, each with its reason recorded on the row:
  - 1924, the evidence gate counting distinct targets: needs a real captured agy transcript first, per the new invariant.
  - 1620, `audit-cycle --delta`: an Orca dispatch build.
  - 1675, `expect 0` screens: one archived user.
  - 1658, suffixed report paths: a design call (slow originals have not written yet; `audit-cycle` clears paths).
  - 1384, concurrent-suite guard: would need a root `conftest.py`.
  - 1347, version-history claims: calibrated at 13% noise, not built.
  - 2106, hollow-kill refusal: no signature hits in the full sweep, so unbuilt.
  - New row, host-equivalent mutants: needs a `requires` probe plus a `HOST_EQUIVALENT` verdict.
- `.codex/` untracked at the repo root: **unknown origin, not created by this session**; left untouched.

## Context for Next Session

**Files touched this session (all committed):**
- New scripts in `h-mad/scripts/`: `h_mad_ac_census.py`, `h_mad_archive_feature.py`, `h_mad_doc_consumers.py`, `h_mad_live_runs.py`.
- Changed scripts in `h-mad/scripts/`: `h_mad_mutation_harness.py` (`--sweep`, no-arg `--check-anchors`, untargeted tier 1, kill forwarding), `h_mad_assemble_audit.py` / `h_mad_assemble_tdd.py` / `h_mad_archreview_cycle.py` (`fill_slots`), `h_mad_precheck_doc.py`, `h_mad_delta_review.py`, `h_mad_phase7_integrate.py` (`--suite`).
- Git hooks: `h-mad/git-hooks/pre-commit` (new, advisory) and `install.sh`. The hook is installed in this clone.
- Docs:
  - `h-mad/SKILL.md`
  - `h-mad/invariants.base.md` (captured-sample rule)
  - `h-mad/references/measurement-discipline.md` (§CALIBRATION)
  - `h-mad/references/inline-protocols.md` (7c)
  - `h-mad/references/phase-table.md` (7e)
  - `handoff/SKILL.md` (a cited sha must resolve)
  - `docs/skill-candidates.md`
- Mod: `mods/token-weather/**` (sparkline removed).
- Tests and mutation specs under `h-mad/tests/` and `handoff/tests/` (new: `ac_census`, `archive_feature`, `doc_consumers`, `live_runs`, `fill_slots`, `harness_sweep`, `harness_check_anchors_discovery`, `delta_review_data_files`, `integrate_merged_suite`, `precheck_hard_kinds_enforced`).
- Outside the repo: `/opt/anaconda3` got `pytest-subtests`; the auto-memory `skills-repo-verification-shape.md` was updated.

**Uncommitted changes:** none (besides this handoff); `.codex/` untracked, not ours.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch               # expect: ahead 24 (or 0 if pushed)
python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors | tail -1   # ANCHORS_OK (no spec arg = every committed spec)
python3 h-mad/scripts/h_mad_install_check.py | head -1                      # INSTALL: PASS
python3 -m pytest -q                      # ~15 min; expect 0 failed, 0 skipped
python3 h-mad/scripts/h_mad_mutation_harness.py --sweep   # hours; run in a detached worktree
```

**Related docs:**
- `docs/handoffs/2026-10-04-main__tdd-gate-scope-manuscript-runs.md`: the row T brief (taken over)
- `h-mad/references/measurement-discipline.md` §CALIBRATION
- `docs/skill-candidates.md` §"2026-10-04 — first full-corpus sweep"
