# Handoff — skill-candidate backlog reconcile (342 rows, four stores)

**Date:** 2026-08-20
**Branch:** main
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Handover-From:** HemaSuite · main · session 97490faf-189a-4e27-9693-08e15dab804c

## Session Summary

HemaSuite's skill-candidate backlog is being handed to this repo, because the question every
remaining row asks — *should this pattern become a skill?* — is a skills-repo decision, and a
promoted candidate lands here. The mechanical half is already done and committed on the HemaSuite
side (`1c871ba6`, 56 rows closed with measured evidence). What moves is the **judgment half: 245
open rows across three HemaSuite stores, plus the 97 already sitting in this repo's own store** —
342 in total. No code change is owed; the deliverable is a reconciled backlog and whatever skills
the survivors justify.

## Key Learnings

- **The ticket's census was wrong twice, in the same direction.** The original said 87 rows in one
  file; a later handoff said 236 across two. Measured: **301 across three** HemaSuite files. Do not
  trust any count in a carried note here — re-measure with the anchored grep below before planning
  the work.
- **The two large stores are near-disjoint** — `docs/skill-candidates.md` (200 names) and
  `hematology-paper-writer/docs/skill-candidates.md` (102 names) share **3**. They are not a copy and
  its duplicate; they are two stores that accumulated from different sessions. Reconciling one says
  nothing about the other, and a fix applied to one relocates the problem rather than closing it.
- **A single blanket supersession stamp would have been wrong.** The 56 closed rows needed *three*
  different resolutions: 50 superseded by `hmad-dispatch exec`, 3 by `tools/hpw_run_substrate.sh`
  (the "launch a long run on a surface and watch it" family — a different replacement entirely), and
  3 that describe *using* `hmad-dispatch exec` and therefore postdate the pane-era candidates rather
  than being replaced by them.
- **Printing the matched set before writing is what caught the error.** The keyword regex selecting
  the supersession class was wrong in **both** directions — it swept in the three run-substrate rows
  and the three exec-era rows, and it matched two rows that are *disciplines rather than mechanisms*.
  Do the same before any bulk stamp.
- **Disciplines are not superseded by tools.** `real-end-to-end-verify` ("drive the real CLI") and
  `codex-build-then-hard-verify` ("never trust a reported green") were deliberately left open. A
  dispatch wrapper does not replace a practice, and marking them superseded would be false.
- **Name-similarity clustering does not compress this.** Jaccard ≥ 0.5 on token sets leaves **224 of
  245 as singletons**. There is no mechanical shortcut remaining; the rest is reading.

## Next Steps

1. **Re-measure the four stores before anything else** — the counts below are from 2026-08-19 and
   this backlog has been miscounted twice already:
   ```bash
   for f in /Users/kimhawk/orca/HemaSuite/docs/skill-candidates.md \
            /Users/kimhawk/orca/HemaSuite/hematology-paper-writer/docs/skill-candidates.md \
            /Users/kimhawk/orca/HemaSuite/clinical-statistics-analyzer/docs/skill-candidates.md \
            /Users/kimhawk/orca/skills/docs/skill-candidates.md; do
     printf '%-70s ' "$f"
     grep -cE '^- \*\*.*candidate: \**yes' "$f"
   done
   ```
2. **Follow the scout's own reconcile protocol** — it is already written and is the contract this
   work should satisfy: `handoff/references/automation-scout.md` §"Reconcile the open rows FIRST".
   It specifies the anchored grep, verifying each claim against source rather than against the label
   (`git log -S`, `grep -rn` into the skill dir), and the terminal verdicts
   `**LANDED**` / `**SUPERSEDED**` / `**DECLINED**` with a named location.
3. **Start with this repo's own 97 rows** — `/Users/kimhawk/orca/skills/docs/skill-candidates.md`.
   They are the ones whose verdicts you can settle without leaving the repo, and several are likely
   already LANDED given how much shipped here in the last week (`h_mad_context_budget.py`,
   headless `exec` dispatch, the report-file transport).
4. **Then the HemaSuite three.** Editing files in that repo is expected — that is where the rows
   live; only the *judgement* moved.
5. **Update the summary table at the top of each file in the same pass.** A flipped row and a stale
   table disagree, and the table is what the next reader trusts.

## Open / Blocked Items

- **The 245 HemaSuite rows** — status: open, needs judgement, no blocker.
  `repo: /Users/kimhawk/orca/HemaSuite · branch: main · worktree: none`
  - `docs/skill-candidates.md` — 170 open of 204 rows
  - `hematology-paper-writer/docs/skill-candidates.md` — 69 open of 113
  - `clinical-statistics-analyzer/docs/skill-candidates.md` — 6 open of 12
- **This repo's 97 rows** — status: open, already yours, never counted alongside the others until now.
  `repo: /Users/kimhawk/orca/skills · branch: main · worktree: none` · `docs/skill-candidates.md`
- **No h-mad claim to release.** Checked `hematology-paper-writer/docs/.bkit-memory.json` (20
  features): nothing matching skill-candidates/#69 is recorded, so this was a todo and never a
  claimed feature. You inherit a free claim because there was never one to inherit — do **not** reach
  for `--claim --force` on the strength of this line.
- **Two rows are deliberately open and should stay that way unless you disagree on the merits** —
  `real-end-to-end-verify` and `codex-build-then-hard-verify` in
  `hematology-paper-writer/docs/skill-candidates.md`. See Key Learnings.

## In-Flight Processes

None. The one long-running job this session launched (a HemaSuite manuscript run) exited at 18:22 on
2026-08-19 and is unrelated to this handover.

## Context for Next Session

**What already landed (do not redo):** HemaSuite `1c871ba6` — 56 rows stamped across the three
HemaSuite stores, plus `ed067925` which appended a fresh scout block dated 2026-08-20 carrying five
new candidates, one of them already marked `**SUPERSEDED**` by this repo's own
`h_mad_context_budget.py` work.

**Verdict vocabulary to match** (this is the existing convention, not a new one): keep `yes`/`maybe`
unbolded; reserve bold for the terminal states `**LANDED**` / `**SUPERSEDED**` / `**DECLINED**`, each
naming where it landed or what removed the need.

**Uncommitted changes:** none in either repo at handover time.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main && git pull --ff-only
grep -cE '^- \*\*.*candidate: \**yes' docs/skill-candidates.md   # your own 97
```

**Related docs:**
- `handoff/references/automation-scout.md` — the reconcile protocol this work should follow
- `/Users/kimhawk/orca/HemaSuite/docs/handoffs/2026-08-20-main__advisor-context-and-backlog-sweep.md`
  — the sender's closeout, which carries the full measurement trail for the 56 already-closed rows
