# Handoff — 36 h-mad-domain skill-candidate rows sitting in HemaSuite's store

**Date:** 2026-08-29
**Branch:** main
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Handover-From:** HemaSuite · main · session f419d046-63a7-4e32-bac0-040f9bcabb04

> **Parked, not dispatched.** Nothing was sent to a terminal. This brief is filed here so the next
> `/handoff read` in this worktree picks it up through the takeover path. Pick it up when it suits;
> nobody is waiting on it and nobody is watching.

## Session Summary

HemaSuite's `docs/skill-candidates.md` carries **199 open rows**, of which roughly **36 are about
h-mad tooling** — the wire-pin gate, the mutation harness, `audit-cycle`, state writes, dispatch —
i.e. code that lives in *this* repo, not that one. They are handed over because this lane owns the
code they describe and can verify each against source; that lane cannot. The remaining ~163 are
HemaSuite-domain (engine, grounding, NLM, manuscript) and stay there. Nothing is claimed: both
`.bkit-memory.json` files under this repo have an empty `orchestrator_state`, checked.

**This is not a comment on this repo's own hygiene.** `skills/docs/skill-candidates.md` reads 131
candidates, **91 terminal, 12 open, zero open `yes`** — 69% closed. HemaSuite's reads 265 / 48
terminal / 200 open — 18%. The two stores are entirely separate (zero shared section headers, 267
rows vs 136). This is HemaSuite's debt that happens to be *about* your code.

## Key Learnings

- **Re-filing happens, but it is rare — corrected within the hour of first writing this.**
  `mutation-anchor-preverify` is re-filed at rows ~354, ~416 and ~662, each a fresh re-proof citing
  the earlier ones, and flipping ~416 to `LANDED` left a sibling open. This brief originally
  generalised from that one row to "the store re-files rather than updates" and told you the 199
  figure **overstates distinct concerns**. Measured across the whole open set, that is false: **199
  open rows carry 199 distinct names, zero duplicates, and exactly one row cites an earlier one.**
  So the count is honest, and a sibling sweep is worth a glance at a row header (`(row ~N)`) rather
  than a step in the method. The generalisation was n=1; the correction is the full set.
- **The keyword split below is a heuristic and needs confirming.** It matched on
  `h-mad|hmad|h_mad|handoff skill|audit-cycle|hmad-dispatch|orca-cli|mutation harness|mutation-anchor|audit gate|skill`.
  Expect both directions of error — a HemaSuite row that merely mentions "skill", and an h-mad row
  phrased without any of those words. Re-derive before trusting the set.

## Next Steps

1. **Confirm the 36 are yours**, then work them under the automation-scout rules
   (`handoff/references/automation-scout.md` §"Reconcile the open rows FIRST"): verify each against
   source rather than against its label, and flip to `LANDED — <file> §<section>` /
   `SUPERSEDED — <what removed the need>` / `DECLINED — <reason>`.
   ```bash
   H=/Users/kimhawk/orca/HemaSuite/docs/skill-candidates.md
   python3 handoff/scripts/skill_candidates_census.py "$H"    # OPEN(yes+maybe)=200 as of today
   sed -n '<line>,+6p' "$H"                                    # read a row plus its continuations
   git log --oneline -S'<distinctive symbol>' -- .             # did it ship here, and where?
   ```
2. **Sweep for siblings before flipping any row** — see the re-filing note above. A row's header
   often names them (`(row ~354, ~416)`).
3. **Write the flips into HemaSuite's file**, since that is where the rows live; commit there. This
   is the one part of the work that lands outside this repo.

## Open / Blocked Items

- **36 h-mad-domain rows in HemaSuite's skill-candidates store** — status: handed over, parked, not
  started. 20 `yes`, 16 `maybe`.
  · repo: `/Users/kimhawk/orca/skills` (this one) · branch: `main` · worktree: `/Users/kimhawk/orca/skills`
  · the rows themselves: `/Users/kimhawk/orca/HemaSuite/docs/skill-candidates.md` (line numbers below,
    valid as of HemaSuite `a2d35999`; re-derive if that file has moved on)
  · nothing claimed — both `.bkit-memory.json` files here have an empty `orchestrator_state`

| line | row | verdict |
|---|---|---|
| 52 | `h-mad-phase-state-bump` | maybe |
| 93 | `h-mad-post-compile-port` | yes |
| 122 | `measure-before-implementing-a-filed-finding` | yes |
| 134 | `staged audit-prompt assembler with size guard` | maybe |
| 145 | `h-mad-state-seed-from-gates` | yes |
| 162 | `post-dispatch tree-clean assertion` | maybe |
| 196 | `audit-the-mutation-harness-itself` | yes |
| 255 | `reap-orphaned-children-of-a-dead-dispatch` | yes |
| 264 | `reconcile-skill-candidates-is-now-its-own-task` | yes |
| 268 | `exec-audit-cycle-with-out-fallback` | yes |
| 302 | `purge-pycache-after-a-RESTORE_FAILED` | yes |
| 304 | `create-the-state-a-gate-can-honestly-read` | yes |
| 346 | `h-mad-audit-cycle` | yes |
| 383 | `callee-reachability-check-in-wire-pin-gate` | maybe |
| 393 | `measure-the-prescription-not-just-the-premise` | maybe |
| 405 | `audit-report-must-be-gate-legible` | yes |
| 413 | `provenance-baseline-by-production-revert` | yes |
| 415 | `two-pass-review-with-disjoint-angles` | maybe |
| 446 | `wire-registry-invocation-needs-four-flags` | yes |
| 492 | `grep-def-not-name-for-line-pins` | maybe |
| 514 | `wire-pin-must-be-a-bare-node-id` | yes |
| 550 | `gate-path-resolution-is-cwd-relative` | yes |
| 552 | `atomic-state-write-refuses-on-one-bad-key` | maybe |
| 561 | `mutation-spec-per-module` | yes |
| 563 | `wire-scoped-revert-via-harness` | maybe |
| 569 | `realpath-before-routing-a-todo` | maybe |
| 599 | `print-the-matched-set-before-a-bulk-edit` | yes |
| 643 | `five-surface-correction-sweep` | maybe |
| 644 | `mutual-discrimination-mutation-run` | maybe |
| 645 | `audit-cycle-genuineness-check` | yes |
| 653 | `read-the-diff-after-a-dispatch-timeout` | maybe |
| 662 | `mutation-anchor-preverify` | yes |
| 683 | `shell-probe-failure-must-not-look-like-absence` | maybe |
| 705 | `contract-tests-must-track-tool-output-shapes` | maybe |
| 708 | `revert-a-NEW-file-by-moving-it-aside` | yes |
| 709 | `derive-dispatch-counts-only-where-the-plan-fixes-them` | maybe |

- **Two of these overlap work already handed to this lane today** —
  `wire-registry-invocation-needs-four-flags` (row 446) and
  `atomic-state-write-refuses-on-one-bad-key` (row 552) are the same subjects as the two defects in
  `2026-08-29-main__hmad-tooling-defects.md`, which was delivered to the live session here. Read that
  brief first; these two rows may close as `LANDED` or `SUPERSEDED` off the back of it rather than
  needing separate work.

## Context for Next Session

**Files touched this session:** none in this repo beyond this brief.

**Uncommitted changes:** none in this repo.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main && git pull --ff-only
# Next Step 1 — the census command is in this doc
```

**Related:**
- `docs/handoffs/2026-08-29-main__hmad-tooling-defects.md` — the earlier handover from the same
  session; **delivered to a live terminal here**, unlike this one.
- The sender's closeout: `HemaSuite/docs/handoffs/2026-08-29-main__202-merged-phase7-closed.md`.
