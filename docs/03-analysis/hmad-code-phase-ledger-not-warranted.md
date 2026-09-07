# The code-phase ledger has no population — measured, and not built

**Date:** 2026-09-07 · **Lane:** `orca/skills` @ `main` · **Corpus:** HemaSuite
`hematology-paper-writer`, `docs/archive/**` and `docs/03-analysis/`, read in place. Nothing in
that lane was edited.

## The ask, and why it was open

The `gateway-consolidation` audit ledger's §"Scope caveats" says: "Phase 4 is documents only;
nothing here measures corruption of **code** by an audit fix. The same instrument applied to
Phase 5–6 artifacts (5e mutation runs, 6a-prime reports) is the code-phase ledger; candidates with
recorded evidence: `#46 grounding-evidence-coverage` (62 cycles, Critical missed),
`manuscript-model-provenance` (a clean cycle falsified four times)."

H7 shipped the instrument for the document phase (`h_mad_audit_origins.py`) and it is
phase-agnostic — `--phase` is already a field. So the question was never "can we build it"; it was
"is there anything to tag".

## The measurement

| | |
|---|---|
| archived features | **136** |
| features that ever ran a SECOND Phase-6 analysis (a 6b iterate round) | **2** |
| 6a-prime archreview reports in the whole repo | **28** |
| median archreview size | **2,114 B** |
| `Major` severity mentions across all 28 | **0** |
| `Critical` mentions across all 28 | 11 |

And for `#46 grounding-evidence-coverage`, the brief's prime candidate:

| artifact | count |
|---|---|
| impl-plan audit cycles | 56 |
| design audit cycles | 9 |
| plan audit cycles | 6 |
| **document cycles total** | **71** |
| Phase-6 analysis versions | 3 |
| 6a-prime archreviews | **0** |

**Roughly 24 document-phase measurements for every code-phase one, on the feature chosen because
its code-phase evidence was the strongest.**

Every figure above was derived twice, by `ls | grep -c` and independently by `find`. Four agreed
exactly; the fifth did not, and the disagreement was mine: the first pass asked only for
`impl-plan.audit` and `design.audit` and so enumerated **65**, missing 6 `plan` audits it had never
asked about. `find … -name '*.audit.v*.md'` returned 71. Not a miscount — an incomplete population,
which is the failure a second derivation exists to catch and the reason the ratio here is 24:1 and
not the 22:1 the first pass would have published.

## Why that answers the question

The document-phase ledger exists because a population accumulated: **152 origin-tagged must-fixes
across six cycles of one feature**, enough that `fix-introduced` could be shown to be 51 of them and
`new-mechanism` only 10. The tail was the finding.

The code phase has no tail. It does not loop: **2 of 136 features** ever produced a second Phase-6
analysis. A ledger over that population would be tagging single-digit events spread across months,
and any rate computed from it would move by whole percentage points on one record. That is not an
instrument, it is a number that will be quoted.

**So: not built, deliberately.** Same disposition the 2026-09-01 triage gave the live-e2e verb
sweep — measured out of existence rather than carried forward as perpetual open work.

## Two claims in the brief that the corpus does not support

- **"Corruption of code by an audit fix" is not what the named candidates evidence.** `#46`'s
  recorded story is 62-odd *document* cycles that certified clean while a Critical survived to be
  found later; `manuscript-model-provenance`'s is a clean cycle falsified four times. Both are
  *document audits failing to prevent a code defect* — the opposite direction from a fix corrupting
  code. That phenomenon is already quantified from the other side by H7: only **6.6%** of `#18`'s
  tagged must-fixes were `new-mechanism`, i.e. the late document loop was not finding design
  defects at all.
- **A hypothesis of mine, refuted.** 14 of the 28 archreviews carry no `READY_TO_MERGE` /
  `WITH_FIXES` / `NO` token in their text, so I expected the Phase-7 gate to read absence as
  success — the failure family this session has found repeatedly. It does not.
  `h_mad_phase7_preconditions.py:192` is an explicit `else: # absent, None, or any unrecognised
  value` that raises the `archreview_not_run` blocker, and it reads `record["archreview"]` from
  **state**, which the orchestrator writes from the extracted assessment, not from the report text.
  Fail-closed, correctly. Recorded because a plausible defect that dies against the code is worth
  exactly as much as one that survives, and the next reader should not re-derive it.

## What would have to change first

A code-phase ledger becomes worth building when the code phase *loops* — when 6b iterate rounds are
routine rather than 2-in-136, so that "a fix for finding N produced finding N+1" has instances to
count. Until then the honest instrument is the one that already exists: H7 over document cycles,
plus Phase 5's own gates (5e mutation runs, the suite) which fail loudly and immediately rather than
accumulating a tail worth mining.

The secondary observation, if anyone does revisit this: the 6a-prime corpus is **not structured
enough to tag** as it stands — median 2 KB, `Major` never used once across 28 reports, and half
carrying no in-text verdict. Structuring those reports is the prerequisite, and it is a smaller and
more useful piece of work than the ledger itself.
