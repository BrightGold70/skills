# Handoff — five h-mad items handed over from the HemaSuite worktree

**Date:** 2026-08-03
**Branch:** main
**Project:** /Users/kimhawk/orca/skills
**Handover-From:** HemaSuite · feature/196-grounding-shadow-measurement · session d185c497-29e4-4de0-ac43-d3770b39d1d0
**Taken-Over-By:** skills · main · session unknown · backfilled 2026-09-01 — all five worked through the h-mad remediation sequence (waves 1-5, e.g. `5f9ec7c`, `787aecf`); see project_h_mad_remediation_sequence

> **This is a HANDOVER, not a session closeout.** Five items were being tracked in a session
> working `~/orca/HemaSuite`, which consumes the h-mad skill but does not own it. All five are
> skills-repo work. The sending session has dropped them and is not monitoring. Nothing was
> started on any of them, so there is no partial state to unpick.
>
> **All five premises were re-verified against the live tree before writing this brief.** Two
> changed: one is now closed by work you merged today, and one rollup is a duplicate. Do not
> re-litigate the three that survived — the evidence is inline.

## Session Summary

Five items (`#40`, `#66`, `#67`, `#68`, `#86`) move to this repo. After verification the real
queue is **three**: `#67` (confirmed live, and the most consequential — a hook that silently does
nothing in HemaSuite), `#66` **item (2) only** (item 1 was closed by PR #22, which you merged
today), and `#68` (confirmed still open — the finding is genuinely absent from the spec). `#86` is
a pure rollup of `#67`/`#66`/`#68` and should be closed as a duplicate rather than worked. `#40`
carries an evidence-run design that its own instrumentation vehicle has now overtaken.

**No claim was released, because none was held.** `~/orca/skills/docs/.bkit-memory.json` holds 8
features and **zero** live `owner_session_id` values. These are tracker items, not claimed h-mad
features — there was nothing to release, and I did not invent one.

## Key Learnings

- **`#67` is confirmed live and it silently disabled a safety gate for real edits.** The hook reads
  `STATE_FILE="${CLAUDE_PROJECT_DIR:-.}/docs/.bkit-memory.json"`
  (`h-mad/hooks/h-mad-tdd-gate.sh:16`). HemaSuite has **no** `docs/.bkit-memory.json` at its repo
  root — its state lives at `hematology-paper-writer/docs/.bkit-memory.json`. So in HemaSuite the
  gate resolves a path that does not exist and stands down. The consequence is not theoretical:
  the sending session ran a full Phase 5 believing `phase == "step5"` was blocking Claude's own
  production `.py` writes, and it was not. The sender's own handoff doc asserted the gate was
  armed; that assertion has been corrected on their side.
- **`#66` item (1) is already closed by work merged today.** `h_mad_state_write.py` now carries the
  staleness allowance in `--claim` ("once its heartbeat goes stale the claim is treated as
  abandoned", and explicitly notes it "previously lived only in" the router). That is PR #22. Item
  (2) — `h_mad_state_staleness.py` reporting `phase_counter_behind` for a legitimately mid-Phase-5
  record — is **still live and was hit again today** on `grounding-shadow-measurement`
  (`last_completed_phase=4` with 18 feature commits; Phase 5 is genuinely incomplete, so 4 is
  correct and the finding is a false positive).
- **`#68` is still open, despite the feature having shipped.** `tdd-dispatch-verification-discipline`
  merged at `84bf2ad`, and the spec exists at
  `docs/01-plan/features/tdd-dispatch-verification-discipline.spec.md` — but
  `grep -c "92,055\|size ceiling\|size_status\|ARG_MAX"` against it returns **0**. The finding is
  recorded in `docs/skill-monitoring.md`, `docs/learnings.md` and
  `docs/handoffs/2026-07-30-main__dispatch-prompt-size-frontier-92kb.md`, just not in the spec. So
  the open question is narrow: amend a shipped spec, or close `#68` as adequately covered elsewhere.
- **`#40`'s evidence run was overtaken by its own vehicle.** It planned to instrument the
  `grounding-double-measurement-divergence` Phase-5 run to count pane-path vs `exec` dispatches.
  Since then `exec` became the documented default for one-shot 5d/5e, and the
  `grounding-shadow-measurement` Phase 5 (Tasks 3 and 4, 2026-08-01→03) ran **entirely on `exec`** —
  zero pane dispatches, zero `wait --not-while-regex` invocations, so the string
  `Waiting for background terminal` never had an opportunity to appear. By `#40`'s own stated
  criterion ("zero pane-path dispatches across a full Phase 5 → close #38") that is a close signal,
  from a different feature than the one named. Whether one feature's run is sufficient evidence is
  your call — the criterion did not say how many runs.

## Next Steps

1. **`#67` — fix the TDD gate's state-file resolution.** `h-mad/hooks/h-mad-tdd-gate.sh:16`. It
   needs to find the state file in a sub-project layout, not assume repo-root. Per
   `feedback_skills_symlink_couples_repos`: `~/.claude/skills/h-mad` is a symlink into this repo, so
   **run both suites** (skills + HemaSuite) before merging. A natural RED is a test asserting the
   gate blocks a production write when the state file is one directory down.
2. **`#66` — close item (1) as fixed by PR #22; work item (2) only.** The remaining bug is
   `h_mad_state_staleness.py` emitting `phase_counter_behind` for a record that is correctly
   mid-Phase-5. It should not fire when `phase` is a live step marker.
3. **`#68` — decide: amend the spec, or close as covered.** Evidence for both sides is in Key
   Learnings above; the grep result (`0`) is the fact that matters.
4. **`#86` — close as a duplicate** of `#67`/`#66`/`#68`. It adds only the two verification notes
   this brief has now discharged.
5. **`#40` — re-scope or close skills `#38`.** See the Key Learnings note; the pane-path guard is
   unreachable from the `exec` default as written.

## Open / Blocked Items

- **All five items** — status: not started, ownership now here.
  `repo: /Users/kimhawk/orca/skills · branch: main · worktree: /Users/kimhawk/orca/skills (main worktree)`
  - `#67` hook: `h-mad/hooks/h-mad-tdd-gate.sh:16`
  - `#68` spec: `docs/01-plan/features/tdd-dispatch-verification-discipline.spec.md`
  - `#66` scripts: `h-mad/scripts/h_mad_state_write.py` (item 1, closed), `h-mad/scripts/h_mad_state_staleness.py` (item 2, live)
  - `#40` guard: the `wait --not-while-regex` pane path in `h-mad/scripts/hmad-dispatch.sh`
- **No claim to release** — verified, not assumed: `docs/.bkit-memory.json` has 8 features and zero
  live `owner_session_id`. Nothing here was ever claimed by the sending session.
- **Sender-side context, if you want it:** the HemaSuite session that held these is closed out at
  `docs/handoffs/2026-08-03-feature-196-grounding-shadow-measurement__tasks-3-4-green.md` in
  `/Users/kimhawk/orca/HemaSuite`. Its live finding — the same untested design decision shipping at
  two wiring sites, caught only by mutation — is what makes `#67` sting: the gate that should have
  been watching those production edits was the one that was not running.

## In-Flight Processes

None. Nothing was started on any of these five items, and the sending session reaped every dispatch.

## Context for Next Session

**Files this handover concerns (none modified — all five items unstarted):**
- `h-mad/hooks/h-mad-tdd-gate.sh:16` — `#67`, the confirmed no-op
- `h-mad/scripts/h_mad_state_staleness.py` — `#66` item (2)
- `docs/01-plan/features/tdd-dispatch-verification-discipline.spec.md` — `#68`
- `h-mad/scripts/hmad-dispatch.sh` — `#40`'s pane-path guard

**Uncommitted changes:** none from this handover. (At handover time this repo had a pre-existing
`M docs/learnings.md` and an untracked `docs/handoffs/2026-08-03-main__agy-reviews-mutation-harness.md`
— both yours, untouched.)

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main            # @ a6fd01d at handover
# #67 reproduce — the gate resolves a path that does not exist in HemaSuite:
grep -n 'STATE_FILE=' h-mad/hooks/h-mad-tdd-gate.sh
ls /Users/kimhawk/orca/HemaSuite/docs/.bkit-memory.json                      # absent
ls /Users/kimhawk/orca/HemaSuite/hematology-paper-writer/docs/.bkit-memory.json  # present
# #68 reproduce — the finding is not in the spec:
grep -c '92,055\|size ceiling\|size_status\|ARG_MAX' \
  docs/01-plan/features/tdd-dispatch-verification-discipline.spec.md          # 0
```

**Related docs:**
- `docs/handoffs/2026-08-03-main__agy-reviews-mutation-harness.md` — your own session that merged
  the seven PRs, including the `--claim` staleness fix that closes `#66` item (1)
- `/Users/kimhawk/orca/HemaSuite/docs/handoffs/2026-08-03-feature-196-grounding-shadow-measurement__tasks-3-4-green.md`
  — sender-side closeout
