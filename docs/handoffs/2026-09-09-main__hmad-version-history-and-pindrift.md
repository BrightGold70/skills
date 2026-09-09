# Handoff — two h-mad tooling defects found while driving a real feature loop

**Date:** 2026-09-09
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Handover-From:** HemaSuite · feature/18-gateway-consolidation · session 7fa8b629-4146-41a1-8585-3a7d0a2d22c6
**Supersedes:** none — first on this branch for these two items

## Session Summary

Two defects in `h-mad` scripts, both found by using them on a live Phase-5 loop in HemaSuite
(`#18 gateway-consolidation`), not by reading them. Neither is a HemaSuite defect and neither is
fixable from that repo, so ownership moves here. **Item 1 is new and unfiled and has already cost
one document a wrong version label. Item 2 is HemaSuite backlog `#46`, carried, but this session
added independent measured evidence and a third option that was not on the original filing.**

Nothing is claimed in this repo's state file by the sending session — checked, 36 records, none
owned by me. The only live owner is `pin-agents-tail-banner` (session `f70b9d62`, heartbeat
2026-09-02), which is untouched and unrelated.

## Key Learnings

- **A gate that validates the resulting STATE rather than the incoming WRITE gives the caller no
  signal at the only moment the caller can act on it.** Item 1 is exactly this shape: the append
  that creates the disorder returns `OK`, and the *next* call refuses. Both authors who hit it read
  the `OK` as validation of the label they passed, because that is what an `OK` on a write means
  everywhere else in h-mad.
- **A precheck whose findings are scoped to a provenance sha gets quieter as the feature ships more
  commits** — so its green is strongest exactly when the document is most likely to have rotted.
  That is item 2, and it is a property of the design, not a bug in the detector.

## Next Steps

1. **`h_mad_version_history.py` — refuse a series-breaking version at the WRITE, not on the next
   read.** Reproduce against any document carrying two version series:

   ```bash
   # a doc whose newest entry is v2.03
   python3 ~/.claude/skills/h-mad/scripts/h_mad_version_history.py <doc> \
     --version v1.100 --text "probe"
   # observed: VERSION-HISTORY: OK … placement=append      <-- accepted
   # then any subsequent call on the same doc:
   #           VERSION-HISTORY: REFUSED … reason=mixed_order
   ```

   `v1.100` appends last but sorts **before** `v2.00`, so the document is left disordered and the
   only signal arrives after the damage. Suggested fix: evaluate the `mixed_order` predicate against
   the post-insertion sequence *before* writing, and refuse with the same `reason=mixed_order`.
   Note the existing refusal is correct and must stay — this adds a check, it does not replace one.

   **Real cost, measured:** a `design-author` on `gateway-consolidation.design.md` scoped its
   "what is the newest version" grep to `^- v1\.`, could not see the four `v2.xx` entries, wrote
   `v1.100`, and got `OK`. A later round had to re-label it to `v2.04` by hand. A second author,
   independently, flagged the same script behaviour as "worth a look by whoever owns the script; it
   is in `orca/skills`, not in this repository, and I did not touch it."

   Consider also: a `--version` that does not extend the series the document already uses could
   warn on its own, since the scoped-grep mistake is what produces the bad label in the first place.

2. **`h_mad_precheck_doc.py` PINDRIFT — decide which of three options, then implement.** A `PINDRIFT`
   finding fires when a pin points into a file that changed since the document's own provenance
   commit. Because the finding is scoped to that sha, **raising the provenance silences the findings
   without repairing a single pin.**

   Measured on `gateway-consolidation.design.md`:
   - v1.15's bytes at that tree → `FAIL issues=41`
   - v1.16 → `PASS issues=0`, **purely because it names HEAD** — 26 body-scoped findings went
     advisory, zero pins repaired.
   - Re-confirmed independently this session by a `design-author`: 20 findings, all pre-existing,
     all provenance drift; document provenance `7a2630e` against HEAD `3f09641`.

   **So a green PRECHECK on a document is not evidence its pins are current, and it degrades with
   every commit the feature ships.** The three options, none chosen:
   (a) freeze the provenance sha; (b) repair the historical pins; (c) teach the checker a
   deliberate-historical marker so a knowingly-stale pin is distinguishable from a rotted one.

   The author who re-measured it declined to re-anchor, with the right reason: "re-anchoring
   provenance would clear them but would also silence any *real* pin rot behind the same mechanism,
   which is what #46 is about."

3. **Re-probe both premises before implementing.** They were measured on 2026-09-09 against
   HemaSuite `feature/18-gateway-consolidation` at `ab6b625e`; the scripts live here and may have
   moved. This is not boilerplate — in the originating session three carried premises were falsified
   on re-probe, including two that would have caused a wrong edit if applied verbatim.

## Open / Blocked Items

- **Item 1 — `h_mad_version_history.py` series-break** — status: not started, unfiled anywhere until
  now. `repo: /Users/kimhawk/orca/skills · branch: main · worktree: /Users/kimhawk/orca/skills`
  Script: `scripts/h_mad_version_history.py`. Tests: `tests/test_h_mad_version_history.py` if it
  exists — verify, do not assume.
- **Item 2 — `h_mad_precheck_doc.py` PINDRIFT masking** — status: blocked on a design decision
  (which of the three options). `repo: /Users/kimhawk/orca/skills · branch: main · worktree:
  /Users/kimhawk/orca/skills`. Script: `scripts/h_mad_precheck_doc.py`. Tracked in HemaSuite's
  backlog as `#46`; that entry stays as a pointer and the fix is owned here.
- **Evidence lives in the sender's repo and is committed**, so it survives independently of this
  brief: `HemaSuite/hematology-paper-writer/docs/03-analysis/gateway-consolidation.design_author_ac64.report.md`
  (§"Tooling observation worth passing on") and
  `…/gateway-consolidation.design_author_ac64_residual.report.md` (§5c), at HemaSuite `ab6b625e`.

## Context for Next Session

**Files touched this session:** none in this repo. This brief is the only write.

**Uncommitted changes:** none introduced here. Note the target tree already carried ~5 untracked
`pin-agents-tail-banner.impl-plan.audit.v*.codex.md.done` markers before this brief was written —
they are not mine and I did not stage or remove them.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main
# Item 1 — reproduce first, on a scratch copy of a two-series document:
python3 scripts/h_mad_version_history.py <doc> --version v1.100 --text "probe"   # expect OK (the bug)
python3 scripts/h_mad_version_history.py <doc> --version v2.05 --text "probe"    # expect REFUSED mixed_order
# Item 2 — read the PINDRIFT branch and decide (a)/(b)/(c) before writing code:
grep -n 'PINDRIFT' scripts/h_mad_precheck_doc.py
```

**Related docs:**
- `h-mad/SKILL.md` §"Precheck before you dispatch" — the PINDRIFT contract, including its own
  statement that hard findings are only the provably-wrong ones
- `h-mad/SKILL.md` §"Audit prompt assembly" — where the version bump is prescribed as the
  per-cycle edit, which is why item 1 is the most-repeated write in the loop
