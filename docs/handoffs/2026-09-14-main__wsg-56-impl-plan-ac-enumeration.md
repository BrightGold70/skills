# Handoff — #56: enumerate the eleven impl-plan rows naming a different AC

**Date:** 2026-09-14
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Handover-From:** HemaSuite · main · session efbc446c-ae09-4611-a3f5-52e3c7628d41
**Taken-Over-By:** skills · main · session 1291f941-11a3-4314-bcc5-c04c8c80b36c · 2026-09-14
**Supersedes:** none — first on this branch

## Session Summary

`#56` is being handed **back** to this repo by operator instruction. It originated here, was handed
to HemaSuite on 2026-09-14 in `2026-09-14-main__wsg-backlog-two-items-owed-here.md` (session
`d4352d63`) on the stated ground that it is *"not answerable from that repo"*, was taken over by
HemaSuite session `efbc446c`, and is now returned **unstarted**. The claim has been released, so it
arrives unowned. Item 2 of that original two-item brief is **closed** — see Key Learnings — so #56 is
all that remains of it.

**Read the circularity flag in Key Learnings before starting.** This lane already concluded it lacks
the information to settle #56, and nothing about that has changed. Returning it does not supply what
was missing.

## Key Learnings

- **The original brief's item 2 is FALSIFIED and must not be re-worked.** It asked to reconcile two
  divergent wire registries. The root `/Users/kimhawk/orca/HemaSuite/.h-mad/wires.jsonl` **no longer
  exists**: it was migrated and retired in HemaSuite commit `c8b0ed79` on **2026-09-13**, one day
  *before* the brief was written. All 17 of its rows were proven subsumed into
  `hematology-paper-writer/.h-mad/wires.jsonl` (73 lines) under both `(owning_feature, id)` and
  `(caller, callee, kind, owning_feature, pin)` before anything was deleted, and the reconciliation
  is recorded at `hematology-paper-writer/docs/03-analysis/wire-registry-reconciliation.md`. The
  retirement was a tombstone, not a delete. Verified by HemaSuite session `efbc446c` on 2026-09-14.

- **The circularity, stated plainly.** The sending brief's own reason for moving #56 out of this repo
  was that the enumeration *"exists only in [HemaSuite's] notes"* — and HemaSuite has now searched and
  **not found it there either**. The eleven rows were never enumerated in any of the four handoffs
  that carried the row, in the WSG audit reports, or anywhere in either repo. So neither lane holds
  the list. **#56 is not a lookup — it is a re-derivation**, and whichever lane does it is reading
  6651 lines of impl-plan against a spec. Do not spend a round re-searching for a list that does not
  exist; the prior probe already did that and filed `CANNOT PROBE` rather than guess, which was the
  right call (`docs/04-report/features/wsg7-carried-claims.probe.v1.md` §8, commit `c21e63e`).

- **`#NN` keys are NOT unique across HemaSuite's handoffs — resolve this row by TEXT, never by
  number.** `#56` names *"eleven impl-plan rows naming a different AC"* in the WSG carriers AND
  *"nccn.org subdomain gap"* in
  `HemaSuite:docs/handoffs/2026-08-07-feature-199-guideline-source-grounding__phase5-tasks-5-12-shipped.md:112`.
  `#57` collides the same way at `:131`. The backlog was renumbered at some point.

- **The available mechanical proxy produces a confident FALSE refutation.** Prefix-vs-test-name
  disagreement finds **1** candidate row, not eleven — and it measures a *different property* than the
  claim, which is prefix-vs-AC-**semantics**. Reporting "FALSE, only 1" off that instrument would close
  a real row on evidence that cannot bear it. Settling #56 needs each row read against the spec's AC
  text; there is no cheap screen.

## Next Steps

1. **Re-derive the enumeration once, against the spec, and re-file with the eleven rows named.**
   Both documents are co-located in the HemaSuite archive:
   - impl-plan: `/Users/kimhawk/orca/HemaSuite/hematology-paper-writer/docs/archive/2026-09/website-source-grounding/website-source-grounding.impl-plan.md`
     — **6651 lines, 202 `AC-x.y` occurrences** (re-derived 2026-09-14, not carried)
     — **CORRECTION, appended 2026-09-14 (the doc above is otherwise left as written).** "202
     occurrences" is the borrowed measurement this very handoff's own probe flags in the brief:
     202 is `grep -c`, the count of LINES that match. The real figures are **202 matching lines,
     341 occurrences, 96 distinct AC ids**, re-derived against both HemaSuite checkouts (the file
     is byte-identical, `sha 8e21804d2028`). The `# expect 202` in the reproduce block below is
     CORRECT — it sits under `grep -c`, which is a line count; only the prose label was wrong.
   - spec: `/Users/kimhawk/orca/HemaSuite/hematology-paper-writer/docs/archive/2026-09/website-source-grounding/website-source-grounding.spec.md`

   The claim to settle: **eleven** rows whose `AC-x.y` PREFIX names a different AC than the row
   actually implements; **six** of those already shipped as test functions. Read each row against the
   spec's AC text. If the true count is not eleven, that is a finding worth filing — report the number
   you measured and the rows behind it, rather than forcing the figure.

2. **If the re-derivation cannot be completed, say so with the rows you did classify** rather than
   filing another `CANNOT PROBE`. A second identical refusal moves nothing; a partial enumeration with
   its method stated is progress the next reader can build on.

## Open / Blocked Items

- **`#56` — eleven impl-plan rows naming a different AC** — status: **open, unowned, unstarted**.
  `repo: /Users/kimhawk/orca/HemaSuite/hematology-paper-writer · branch: n/a (archived under
  docs/archive/2026-09/website-source-grounding) · worktree: none`.
  The **documents are identified** (paths and sizes above) and both are present on disk, verified
  2026-09-14. What blocks it is the enumeration itself, which exists in neither repo. Do not close it
  as done without the rows named. The claim on the covering feature
  `wsg-backlog-two-items-owed-here` was **released** in
  `/Users/kimhawk/orca/HemaSuite/hematology-paper-writer/docs/.bkit-memory.json` by session
  `efbc446c` before this brief was written, so it is free to take — in whichever state file this lane
  works from.

- **Original brief item 2 (two divergent wire registries)** — status: **CLOSED, do not re-work**.
  Falsified above; evidence `c8b0ed79` + `wire-registry-reconciliation.md`. Recorded here only so it
  does not silently re-enter the chain as owed work.

## Context for Next Session

**Files touched this session:** none in this repo — this is a brief, not a change.

**Uncommitted changes:** none by this handover. Note the receiving tree carries pre-existing untracked
`docs/01-plan/features/pin-agents-tail-banner.impl-plan.audit.v*.codex.md.done` files from a live
lane; they are not mine and were not touched.

**To resume:**
```bash
cd /Users/kimhawk/orca/HemaSuite/hematology-paper-writer/docs/archive/2026-09/website-source-grounding
wc -l website-source-grounding.impl-plan.md          # expect 6651
grep -c 'AC-[0-9]\+\.[0-9]\+' website-source-grounding.impl-plan.md   # expect 202
```

**Related docs:**
- `skills:docs/04-report/features/wsg7-carried-claims.probe.v1.md` §8 — the #56 probe and the command
  output behind its `CANNOT PROBE` verdict, commit `c21e63e`
- `skills:docs/handoffs/2026-09-14-main__backlog-drained-and-two-review-lanes.md` — the closeout #56
  was originally carried out of
- `HemaSuite:docs/handoffs/2026-09-14-main__wsg-backlog-two-items-owed-here.md` — the inbound brief
  this returns half of, stamped `**Taken-Over-By:**` and committed at `e7c69f0f`
