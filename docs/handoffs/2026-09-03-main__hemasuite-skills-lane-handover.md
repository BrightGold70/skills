# Handoff — skills-lane work routed out of HemaSuite: wrapper bugs, a false revert invariant, leaked panes, and 101 classified backlog rows

**Date:** 2026-09-03
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Handover-From:** HemaSuite · main · session `cfc79129-d676-4858-9792-3069dbdd2283`
**Taken-Over-By:** skills · main · session 023f6eeb-e188-431b-9dfb-785e80736304 · 2026-09-03
**Supersedes:** none — first on this branch from this sender

## Session Summary

Four items that describe `orca/skills` behaviour have been riding HemaSuite's handoff chain as
documented-but-undriven open items across several sessions. HemaSuite's own 2026-09-03 closeout said
so explicitly and recommended running HANDOVER for them rather than letting them take another hop.
This is that handover. Nothing here is claimed — the h-mad state file at
`docs/.bkit-memory.json` has no record for any of these, so the receiver inherits a free claim and
should NOT need `--force`. Two unrelated features in that file are held live by other sessions
(`pin-agents-tail-banner`, `doc-block-exec`); neither overlaps this work.

The fourth item is new and is the largest: HemaSuite completed the first at-scale reconcile of its
skill-candidate stores, and **101 open rows now carry a classification but still need an
authoring-or-decline decision that only this repo can make.**

## Key Learnings

- **A tool candidate swept into the "useful, not codable" DECLINE bucket is a buildable artefact
  recorded as an unbuildable habit.** That conflation is why six consecutive reconcile passes in
  HemaSuite were logged as "not attempted at scale" — the rows were unclassifiable in the shape they
  were in. Splitting them is what unblocked the pass.
- **I made that exact error mid-pass and had to revert it.** A blanket "practice-only" label went
  onto 24 rows by pattern rather than by reading; 7 were tool candidates. `codex-capacity-backoff`
  is the worked example — it asks `hmad-dispatch exec` to detect the capacity string, back off and
  surface `CAPACITY`, which is code, not a habit. If you re-triage, read each row.
- **A zero-hit probe against this repo needs a file-existence control.** Every "not implemented"
  claim below was paired with one, because a wrong path and an absent feature produce the same
  empty result.

## Next Steps

1. **Fix the two `hmad-dispatch.sh` wrapper bugs** — `h-mad/scripts/hmad-dispatch.sh:3619`
   (unmatched quote / EOF) and `:3597` (`ame: command not found`). Both fire *after*
   `codex exec rc=0` and turn a good dispatch into rc=2/127; the report still lands, so the
   symptom is a false failure verdict on successful work. HemaSuite task #20.
2. **Correct the h-mad revert-sequence invariant** — the documented `git add -N` + `git stash push`
   sequence silently no-ops on the HemaSuite repo: the stash was refused with
   `Entry not uptodate`, and the prescribed `git diff --quiet` guard then printed
   `revert landed` anyway. That is a guard that fails OPEN and reports success. The form that
   actually worked, used throughout HemaSuite's 2026-09-02/03 sessions, is explicit `mv` aside →
   assert absent → run → `mv` back. Note this repo's own store already carries the row
   (`committed-file-revert-helper`) describing the same trap. HemaSuite task #21.
3. **Reap 4 leaked `exec-pane agy` processes** — PIDs 82161 / 85642 / 90677 / 91239, confirmed
   still alive 2026-09-03 at 2d 13–15h elapsed, state `S`. Their cwds are already-deleted pytest
   tmpdirs (`pytest-of-kimhawk/pytest-91xx/test_unresolvable_panekey_fall0`). Two came from
   `/Users/kimhawk/orca/skills`, one from `/Users/kimhawk/orca/workspaces/skills/j1-residual-probes`.
   This is the wedged-terminal shape the h-mad docs describe — `worker-abandon`/`worker-stop`
   answer `dispatch_not_found` (stablyai/orca#13005). Plain `kill 82161 85642 90677 91239` clears
   them; the interesting half is that a pytest run leaks panes at all.
4. **Decide the 101 classified skill-candidate rows** (see Open Items for the split and where they
   live). This is the item with no owner and no deadline, and it is the one that decays.

## Open / Blocked Items

All four items live in this repo. Location for every one of them:
`repo: /Users/kimhawk/orca/skills · branch: main · worktree: /Users/kimhawk/orca/skills`

- **Two `hmad-dispatch.sh` wrapper bugs** (`:3619`, `:3597`) — status: open, unchanged across
  several HemaSuite handoffs, never driven. Reproduce by running any `hmad-dispatch exec codex`
  that succeeds and reading the wrapper's exit code against the report that landed.
- **The revert-sequence invariant is wrong as documented** — status: open. See Next Step 2. The
  failing pair is `git add -N` + `git stash push` on a tree where the entry is not up to date;
  the `git diff --quiet` guard then confirms a revert that never happened.
- **4 leaked `exec-pane agy` PIDs** — status: open, still alive at handover time.
- **101 open skill-candidate rows needing an authoring-or-decline decision** — status: classified,
  not decided. HemaSuite's 2026-09-03 reconcile (`84bb73c3` in that repo) went through every open
  `yes`/`maybe` row in all three of its stores and split them:
  - **29 TOOL-CANDIDATE** — the row proposes an artefact to BUILD (a script, a verb, or a flag on
    one that exists). These must NOT be swept into the recurrence-threshold DECLINE bucket.
  - **72 PRACTICE** — an operator habit with no artefact and no code hook. This is the bucket a
    recurrence-threshold decline is actually for.
  - Stores: `/Users/kimhawk/orca/HemaSuite/docs/skill-candidates.md` (36 h-mad-domain rows open),
    `…/hematology-paper-writer/docs/skill-candidates.md` (59), `…/clinical-statistics-analyzer/…` (5).
    Census after the pass: 443 candidates, OPEN 189, verdict-less 0.
  - Three rows were flipped **LANDED against source in that pass** and need no further action:
    `audit-report-must-be-gate-legible` (`h_mad_do_preconditions.py:70` now gates on the shared
    `has_gate_sections`, fix #39, so the unscoreable case fails CLOSED),
    `atomic-state-write-refuses-on-one-bad-key` (a refusal now names the offending keys and
    `drop_undeclared()` is the sanctioned repair, J48), and `learn-py-length-retry`
    (`handoff/scripts/learn.py` is at `MAX_KERNEL = 240` with `--trim`).
  - Twelve h-mad rows were **re-verified INTACT** with the probe result recorded in each row —
    among them: no `--agent`/`--agents` in `h_mad_audit_cycle.py`; no `evidence=` anywhere in
    `hmad-dispatch.sh`; `--cd <project-root>` still hardcoded at `h_mad_assemble_tdd.py:296` with
    no `production_path_outside_cd` halt; `_purge_bytecode(root)` still single-root at
    `h_mad_mutation_harness.py:247`/`:276`; `h_mad_assemble_audit.py` still emits no CANONICAL-TREE
    preamble; no `--verify-stamp` in `h_mad_version_history.py`; no `--report-file` or dual-surface
    mode in `h_mad_audit_cycle.py`; no node-id resolvability check in `h_mad_wire_pin_gate.py`.
    Those eight are the shortest path from "classified" to "built".

**Premises worth re-running before you act** — every claim above was verified on 2026-09-03 against
this repo, but a brief is a claim made by a session that has stopped. The wrapper-bug line numbers
in particular are the ones most likely to have moved.

## Context for Next Session

**Files this handover points at (none were modified by the sender):**
- `h-mad/scripts/hmad-dispatch.sh` — `:3619`, `:3597`
- `h-mad/scripts/h_mad_audit_cycle.py`, `h_mad_assemble_tdd.py`, `h_mad_assemble_audit.py`,
  `h_mad_mutation_harness.py`, `h_mad_wire_pin_gate.py`, `h_mad_version_history.py`
- `docs/.bkit-memory.json` — no record for any of this work; the claim is free

**Uncommitted changes:** none from this sender.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch
# the 101 rows live in HemaSuite; read them there, they are annotated in place:
grep -c 'TOOL-CANDIDATE' /Users/kimhawk/orca/HemaSuite/docs/skill-candidates.md \
  /Users/kimhawk/orca/HemaSuite/hematology-paper-writer/docs/skill-candidates.md \
  /Users/kimhawk/orca/HemaSuite/clinical-statistics-analyzer/docs/skill-candidates.md
# re-run the census before trusting any carried number:
python3.11 handoff/scripts/skill_candidates_census.py \
  /Users/kimhawk/orca/HemaSuite/docs/skill-candidates.md \
  /Users/kimhawk/orca/HemaSuite/hematology-paper-writer/docs/skill-candidates.md \
  /Users/kimhawk/orca/HemaSuite/clinical-statistics-analyzer/docs/skill-candidates.md
# the leaked panes:
ps -p 82161 -p 85642 -p 90677 -p 91239 -o pid,etime,stat,comm
```

**Related docs:**
- `/Users/kimhawk/orca/HemaSuite/docs/skill-candidates.md` § "2026-09-03 — CODE-8 reconcile
  (all three stores)" — what the reconcile did, and what it deliberately did not do.
- `/Users/kimhawk/orca/HemaSuite/docs/handoffs/2026-09-03-main__nlm-pin-shipped-and-handover-taken.md`
  § "Routed elsewhere" — the sender's reasoning for handing these over rather than carrying them.
