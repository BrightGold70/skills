# Handoff — grok-audit-surface Task 15: S0b + S1 done; S2 stopped after a grok root escape

**Date:** 2026-10-20
**Branch:** main
**Project:** skills
**Supersedes:** 2026-10-20-feature-218-grok-audit-surface__grok-audit-surface-tasks-4-14.md, 2026-10-02-main__v111-review-loop-closed.md

## Session Summary

I resumed grok-audit-surface and ran Task 15 from `main`.

- **S0b is done.** A fresh-context agent authored the seeds. The calibration sha is `ab2c85dc2e25be31dcc13740ee9e71a0703d8cc7`, and `check-ledger` reads `LEDGER: OK seeds=27 docs=9 C1=6 C2=7 C3=7 C4=7`. All nine `build-root` runs read `ROOT: READY`. It is pushed and confirmed with `git ls-remote`.
- **S1 is done: `SMOKE: PASS`.** grok 1.0.62, agy 1.4.2 and codex 0.163.0 all accepted the root. Wall time was 721 s, so the derived timeout is 1140. The smoke commit is `f7520e72c87e1c3c34e1c5f25fb3807343d84782`, pushed.
- **S2 was stopped and left unscored, by operator decision.** A grok auditor in cycle `s2-d5-v1` (pass 3) changed directory to the real checkout and ran `git checkout -q 1254595a -- .` there. That overwrote 370 paths mid-run, including `h-mad/scripts/`.
  - I saved the full diff and reset the tree to HEAD. The tree is clean.
  - d3, d5 and d6 were re-run as v2 under a tree watcher.
  - `extract` correctly refuses the contaminated data with `cycle_token:d3.v2`.
  - The incident is recorded in `306d1b3f`. The claim is released. State carries `halt_reason=step5:task15:s2_grok_root_escape`, and `phase` stays `step5`, so the TDD gate remains armed.

## Key Learnings

- **An export root bounds what an auditor is shown, not where it can write.** The AC-2.6 reach check and the `GIT_*` unsets only stop git from reaching a repository *from inside* the root. grok issued `cd /Users/kimhawk/orca/skills` followed by a destructive `git checkout <sha> -- .`, then wrote a comment saying not to. A live checkout is never safe while a shell-capable auditor runs against seeded documents that cite shas.
- **A bulk overwrite of a running toolchain shows up as unrelated symptoms.** The overwrite of 370 files in one second came out as `record-cycle REFUSED stem_prefix:0` (the old wrapper staged to `/tmp`), as `assemble_halt:p1`, and as `hmad-dispatch.sh` lacking `HMAD_AUDIT_STEM_DIR`. To recognise it: every changed file has the same mtime, and HEAD hasn't moved.
- **The probe's `stands()` admits a v2 only after an `UNVERIFIED` v1, and it needs a v1 for all nine documents.** It cannot express "v1 voided by an outside event". Renaming v2 to v1 would falsify `command.txt` (`--cycle 2`), so I didn't do it.
- **A tree watcher detects, it does not prevent.** It polled `git status --porcelain` every 5 s. `set -m` in the Bash tool gave `setpgid: Operation not permitted`, so its process-group kill is unproven.
- **This repo's bkit hook blocks `rm -rf`, even on `mktemp` dirs.** Use a scratchpad dir, or delete named files one by one.

## Next Steps

1. **Decide how to contain grok before any further dispatch against seeded documents.** The incident record lists the options: a read-only checkout for the run, a separate clone the auditor cannot name, or an agent-side sandbox. See `docs/03-analysis/grok-audit-surface.incident-2026-10-20-grok-root-escape.md` §"What is still owed".
2. **Then pick one S2 route:**
   - (a) A fresh S2 run, with all nine documents as v1 in a new run dir. The runner is in this session's scratchpad: `s2_doc.sh`, `s2_lanes.sh`, `s2_rerun.sh`. It may be gone; the logic is design D8.
   - (b) A probe amendment for operator-declared void cycles, routed through `spec-author` and `design-author` and then TDD.
3. **After S2:** run `extract --repo . --base-sha f7520e72…`, have a labeller who has not seen the key label the findings, run `commit-data` for the score sha, then Task 16 (`docs/03-analysis/grok-audit-surface.measurement.md`, citing the incident). Task 17 (S4 grok routing) must not run while the escape is uncontained.
4. **Then 5f, 5g, Phase 6 and Phase 7**, as in the predecessor: `h_mad_baseline_sha.py --branch feature/218-grok-audit-surface` (expect `f6820752`), wire registry `verify`, `challenge`, and the full suite.

## Open / Blocked Items

**This session:**
- **grok-audit-surface Tasks 15 (S2) to 17.** Blocked on the containment decision. Location: repo `/Users/kimhawk/orca/skills` · branch `main` (the feature branch `feature/218-grok-audit-surface` is merged into it) · worktree none. The data sits in the kept directory `~/.local/state/h-mad/grok-audit-surface/run-ab2c85dc2e25/`:
  - `data/s1/` has been committed.
  - `data/s2/` holds the d1–d9 records, contaminated v1s included. It is outside git and not committed.
- **HemaSuite `pytest tests/` (PID 70888) read the reverted h-mad scripts** between 08:08:54 and about 08:42 KST, through the skills symlink. Its result is suspect and should be re-run. That run belongs to HemaSuite, so this is only a note here.
- **Diff backup of the escape:** `/private/tmp/claude-501/-Users-kimhawk-orca-skills/d00c4d73-f82c-4f9a-8bfd-7b4fcac2b3b1/scratchpad/grok-escape-1254595a.patch` (3.0 MB). It is session-scoped and may be cleaned up; it is only needed if the restore is ever questioned.
- **Two artefacts S1/S2 surfaced for the measurement doc:**
  - agy and codex delivered `delivered=out`, not `report-file`.
  - On codex legs the `Effort:` block reads "not measured (codex-text log)".

**Carried from the feature-218 tasks-4-14 handoff:**
- Task 15 is now partly done: S0b and S1 are complete and S2 is blocked, as above. Tasks 16 and 17 and Phases 5f–7 are re-emitted in Next Steps.
- The 7 older open `candidate: yes` rows in `docs/skill-candidates.md` (lines 2666, 2667, 2672, 2673, 2677, 2678, 2682) are unchanged and deferred.
- The h-mad state record still reads `phase=step5`, and now also carries `halt_reason`. Intended.
- The Codex Phase-5 gate refuses read-only checks that the prompts tell agents to run. Filed in `e39f15c5`; unchanged.
- The agy install-check gap at `skill-candidates.md:2673` is unchanged.
- `INSTALL: PASS` and the advisory `AGY_SIBLING_COLLISION ~/.gemini/config/skills/debugger` are unchanged. Re-seen this session.
- The backlog row "mutation harness interpreter override" (`:2666`) is unchanged.
- Deferred, unchanged: the backlog_cycle LOW review residuals; the census `--help` FileNotFoundError; the `h_mad_mutation_harness.py:2300` SyntaxWarning.
- HemaSuite feature/204 `no-mutation-spec` is HemaSuite's call; unchanged.
- The foreign `stash@{0}` (`resolved-model`) is still present. Do not touch it.
- The Bash pin blast radius, the `.git/info/exclude` entries, the row 1412 liveness limits and the agy-coder-fallback `review_independence_unrecorded`: all unchanged, watch-only or accepted.
- "Advisor ceiling exceeded" is unchanged: no `advisor()` call this session, and context passed 45% near the end.
- "Handoff WRITE does not verify claimed state" and "Plan audit exit stamp never written": both unchanged.

**Carried from `2026-10-02-main__v111-review-loop-closed.md` (not re-verified this session):**
- [task #28] `test_h_mad_check_memory_index.py::TestAgainstTheLiveBinary::test_the_warn_and_target_fractions_still_match` was red after a Claude Code auto-update. Unverified. The tasks-4-14 run reported the full h-mad suite at 7007 passed, so it may already be resolved; confirm by running that one test.
- [optional] Re-run the agy live smoke with canonical declaration (`docs/archive/2026-09/multi-host-runtime/multi-host-runtime.plan.md` §"The smoke script"). Unchanged since 2026-10-01.
- [suggested] Exercise `h_mad_assemble_tdd.py --phase green --mutation-spec` live at a 5e. Unchanged.
- The V-11.1 accepted residuals and the round-22 F2 fix: no fresh review; unchanged, deferred.
- The tdd-gate-fail-opens evidence bookkeeping (`docs/archive/2026-09/tdd-gate-fail-opens/tdd-gate-fail-opens.report.md` §"Residual disposition"): unchanged, deferred.
- The skill-candidates reconcile (33 open `yes` rows at the time): not run this WRITE either (`--skip-scout`): context was above 45%, and recording the incident came first.
- The HemaSuite pointer `2026-09-14-main__wsg-backlog-two-items-owed-here.md`: unchanged, and ownership stays here.

## Context for Next Session

**Commits this session (all on `main`, pushed):**
- `d4b03fd9`: merge of the feature-218 handoff commit.
- `306d1b3f`: the incident record.

**Calibration branch (pushed):**
- `ab2c85dc` (S0b)
- `f7520e72` (smoke)

**Files touched:**
- `docs/03-analysis/grok-audit-surface.incident-2026-10-20-grok-root-escape.md`
- `docs/.bkit-memory.json` (state, not tracked)
- `~/.local/state/h-mad/grok-audit-surface/` (outside the repo)

**Uncommitted changes:** none besides this closeout.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main && git pull --ff-only
git ls-remote origin refs/heads/calibration/grok-audit-surface   # expect f7520e72…
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
/h-mad "grok-audit-surface"     # oracle will route to halted (halt_reason set) — decide containment first
```

**Related docs:**
- `docs/03-analysis/grok-audit-surface.incident-2026-10-20-grok-root-escape.md`
- `docs/01-plan/features/grok-audit-surface.impl-plan.md` §Task 15–17 (line ~1661)
- `docs/02-design/features/grok-audit-surface.design.md` §D8, §D9; the probe `stands()` is in `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py`
- `docs/01-plan/features/grok-audit-surface.spec.md` FR-1, FR-2 and AC-2.6
