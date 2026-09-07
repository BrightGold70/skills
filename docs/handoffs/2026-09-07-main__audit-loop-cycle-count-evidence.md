# Handoff — why the audit loop ran to 105 cycles: the Phase-4 dataset, and what is left of it

**Date:** 2026-09-07
**Branch:** `main`
**Project:** orca/skills (h-mad)
**Handover-From:** HemaSuite · main · session `6a09584b-3a59-4069-bae9-c8c902ff7247`
**Taken-Over-By:** skills · main · session e07f76b9 · 2026-09-07
**Supersedes:** none — first on this topic

## Session Summary

HemaSuite's `#18 gateway-consolidation` ran **105 design audit cycles and 31 plan cycles** and exited
Phase 4 on 2026-09-07 with the exit gate **UNMET** — the two-consecutive-both-clean streak was **zero
across all 105**. Those sessions built a purpose-made dataset to answer *why*, and it is the thing
being handed over: `gateway-consolidation.audit-ledger.{md,jsonl}`, 136 rows, regenerable from a
committed script, with six measured findings and nine hypotheses (H1–H9) already framed as h-mad
changes.

**The reason this is worth your time is not the findings — it is that eight of the nine hypotheses
have since SHIPPED into h-mad, and none of them has been validated against a run.** I verified the
shipped/unshipped split against this checkout today (table below). H7 alone is unbuilt. The open
question is no longer "what causes long loops" but "did the eight fixes work", and the first feature
to run under them is in flight now.

Nothing in this repository was touched.

## Key Learnings

### What the Phase-4 data actually measured (ledger §"What the data says so far")

1. **Σmust tracks the number of LEGS, not document quality.** Last twelve cycles ran
   `3 3 7 5 3 5 4 3 8 4 7 12`, against a c60–c86 run of mostly 0–2. Every rise coincided with a
   surface being added or returning — teammate at c87, doc-auditor+crossdoc at c92, codex at c97 —
   and each new surface opened a class the others never filed. I re-derived this from the jsonl
   today as a mean: **1 leg → 0.8 · 2 legs → 2.0 · 3 legs → 7.9** (n = 10 / 116 / 10). Adding a
   third leg nearly quadruples the mean. **Observational, not causal** — leg count is confounded with
   cycle age and with the orchestrator choosing more legs when it suspected trouble. Do not quote the
   means as an effect size.
2. **Correction mass migrated from the specification into narrative about the specification.**
   Version-History share of bytes: design 0 % → **34 %**, spec 14 % → **45 %**, plan 18 % → **41 %**.
   All three documents went 333 KB → 761 KB in the **seven** cycles c92–c98, having taken 91 cycles
   to reach 333 KB. Records were ~130 chars each at c88–c90 and 3,000–12,500 chars from c91.
3. **The audit began auditing its own audit trail.** Five Version-History records were wrong at the
   commit that published them (c91, c94, c95, c96, c97 — four consecutive revisions). Each record is
   new gated bytes, so each is new surface for the next leg.
4. **Fix-introduced defects are the majority of the tail** — at least **17 of 98** cycles, a seeded
   lower bound.
5. **Disagreement carried the signal; agreement carried little.** agy reported clean while codex
   filed must-fixes in **42 of 78** shared cycles (Phase 3: 24 of 31). Rejections ledger: 18 agy
   findings, 1 codex. Three of seven crossdoc reports were schema-INVALID **and were gated anyway**.
6. **Cycles are cheap, which is why it ran to 98.** Median **6 minutes** between cycle commits
   (Phase 3: 4). Nothing made "cycle 60 with the same shape of finding" a stop.

### The shipped/unshipped split — verified against this checkout today, not assumed

| | hypothesis | state | where |
|---|---|---|---|
| H1 | measurement layer out of the gated bytes | **shipped** | SKILL §"The measurement layer lives in probes" |
| H2 | cycle cap + mandatory gate redesign | **shipped, stronger** | SKILL §"Document-audit round cap" — **TWO** rounds, not the proposed 20 |
| H3 | leg-set stability in the exit gate | **shipped** | `h_mad_audit_gate.py`, `EXIT: BLOCKED reason=legs_changed` (#11/H3) |
| H4 | delta self-review as a script | **shipped** | `h_mad_delta_review.py` |
| H5 | single-sourced shared sentences, adoption checked pre-commit | **shipped** | `SKILL.md:1318` (#11/H5) |
| H6 | hollow legs INVALID, not clean | **shipped** | `h_mad_audit_cycle.py`, `UNVERIFIED reason=low_evidence:pN` |
| H7 | **origin tagging per must-fix** | **NOT SHIPPED** | no `by_cycle` / `propagation-gap` / `record-stale` / `author-self-caught` anywhere; no ledger or origins tooling in `h-mad/scripts/` |
| H8 | no bare count of an instrument the document contains | **shipped** | `measurement-discipline.md` §"SELF-COUNTING SCREENS" |
| H9 | prompt size is a leg-killer | **shipped** | `h_mad_assemble_audit.py:254`, `AGENT_TOOL_WARN_BYTES = 700 * 1024` |

**Two of these I first reported wrong**, and the failure mode is worth more than the answer: single
literal probes (`bare count`, `origin tagging`) returned nothing for H8 and H4, both of which are
built under different wording. A one-spelling sweep for absence is how a receiver gets sent to
rebuild what exists. Re-probe with several spellings before acting on any "not shipped" here —
including on H7, where I did that and it held.

### First evidence from a run under the shipped fixes (HemaSuite `#18` Phase 5b, today)

This is n=1 and the round is still in flight, so treat it as a first data point, not a result.

- **Finding 5 reproduced on a FRESH document, with the confound removed.** impl-plan v1.0, never
  audited, one assembled prompt, one commit, two legs: **agy must=0, codex must=3** (all
  `class: build`). Zero overlap. The ledger's version of this finding is confounded by document
  maturity and by leg-choice bias; this one is not.
- **H6 does not explain it.** agy's clean pass scored `EVIDENCE: PASS tools=41 ok=41 failed=0
  thinking=18471` — far above the low-evidence floor. The hollow-leg instrument would have called
  that pass trustworthy. **So there is a second mechanism behind surface disagreement that H6 does
  not touch**, and it is the one that matters now that H6 ships.
- **A vacuous pin survived a full gating cycle and neither leg saw it.** The impl-plan's AC-2.5b
  spied on `is_cli_available` *returning* `False`; the forced-`True` mutation emits an identical
  record and returns the same value, so the criterion could not discriminate in either direction.
  The **revising author** found it while fixing an unrelated must. A document audit reads prose and
  cannot ask "does this pin discriminate?" — candidate class for a new instrument, and arguably the
  Phase-5 analogue of H8.
- **Prompt growth is now measured per revision**: 836,337 B → 857,318 B, **+20,981 B** for one
  revision, against the 1,048,576 exec ceiling. ~9 revisions of headroom. H9 warns at 700 KB for an
  in-process `Agent` leg and that warning **fired correctly** today at 816.7 KB.
- **A fix-introduced defect appeared in the revision that answered cycle 1, and TWO independent
  arithmetic checks missed it the same way.** v1.1 moved the mutation count 88 → 94 (M89–M94
  appended). Cycle 2's first must-fix: Task 25's **AC-7.5d still requires 88 rows**, making the AC
  unsatisfiable against a document that enumerates 94. The author's own re-derivation reported
  "88 → 94, Exec Summary and the spec section and task rows 4 and 12 all updated" — it swept the
  sites it had edited. My independent verification confirmed "ids M1–M94 contiguous, per-task
  `**Mutations (N)**` headers summing 94" — I checked the enumeration and never asked whether any
  **acceptance criterion asserts a literal count**. Same blind spot, reached from two directions.
  This is H8's class one level out: not a count of an instrument the document *contains*, but a
  **contract elsewhere in the document that pins a count the revision moved**. A sweep by value finds
  only sites that already carry the old number in the form you grep for; a sweep by *role* (every AC
  that asserts a cardinality) would have found it. Worth considering as an H8 extension.
- **AC-7.5c came back deeper on the second read.** Cycle 1 said it was mis-counted as RED; I accepted
  the fix of relabelling it a regression guard. Cycle 2 says a guard that "does not discriminate the
  deletion in either direction" and carries no permissive mutation of the `testpaths` protection is
  not a validated guard at all — relabelling moved it from a wrong count to an unfalsifiable claim.
  Same vacuous-pin class as AC-2.5b above, found only because a second cycle ran.
- **Authors leave probe files in the tree.** An author wrote `test_env_sleep.py` at the sub-project
  root — a legitimate throwaway check, but it matched pytest's `test_*.py` glob, called
  `asyncio.run()` at module level (so collection executes it), and contained
  `asyncio.create_subprocess_exec`, which would have entered the boundary census that same feature's
  ACs count. SKILL §"Confirming a suspected defect" tells the ORCHESTRATOR to delete probes; the
  four author agents inherit no such rule.

## Next Steps

1. **Build H7 — it is the only unshipped hypothesis, and it is the one that measures whether the
   other eight worked.** The schema is already specified in the ledger's §"Per-cycle capture", with
   its origin vocabulary (`new-mechanism` · `new-consistency` · `fix-introduced` + `by_cycle` ·
   `propagation-gap` · `instrument` · `record-stale` · `author-self-caught` + `caught_by` ·
   `rejected`). Read it there rather than re-deriving:
   `/Users/kimhawk/orca/HemaSuite/hematology-paper-writer/docs/03-analysis/gateway-consolidation.audit-ledger.md`
   lines 88–106. A working sidecar exists at `gateway-consolidation.audit-origins.jsonl` (64 KB).
2. **Validate the eight shipped hypotheses against a run.** None has been. `#18` Phase 5b is the
   first feature to execute under the two-round cap (H2), and **both rounds are now complete**:
   - cycle 1 — agy `PASS must=0`, codex `FAIL must=3` (all build). Union FAIL.
   - revision → impl-plan v1.1 (`3d63c646`).
   - cycle 2 — codex `FAIL must=3 should=2` (build=4, measurement=1), **one of the musts created by
     the cycle-1 fix itself** (the 88-vs-94 contract above).

   **So the cap is reached with real build-class findings outstanding — which is exactly the case it
   was designed for, and the first time its exit terms have been exercised for real.** H2's
   prescription is that the phase exits anyway: measurement-class findings go to
   `## Acknowledged-not-fixed` with re-run commands, and open build-class musts become
   `OPEN-DECISION` entries on their impl-plan Tasks, settled in 5d where a wrong choice is a failing
   test rather than another document round. Note the cap forbids a third **gating round**, not a
   final corrective revision — shipping a provably unsatisfiable AC (88 vs 94) as an OPEN-DECISION
   would be a misreading of it. How that judgement is drawn is worth capturing in the SKILL, because
   the text does not currently say which of the two readings it means.
3. **Investigate the second disagreement mechanism.** H6 ships and does not explain a 41-tool-call
   clean sitting beside a 3-must FAIL on one prompt. Until that is characterised, "two surfaces,
   union" remains a cost with an unmodelled benefit.
4. **Consider a probe-hygiene rule for the four author agents** (`agents/*-author.md`), mirroring
   SKILL §"Confirming a suspected defect before fixing it". See the `test_env_sleep.py` case above.
5. **The code-phase ledger does not exist.** Ledger §"Scope caveats" is explicit: Phase 4 is
   documents only, and nothing measures corruption of **code** by an audit fix. Named candidates with
   recorded evidence: `#46 grounding-evidence-coverage` (62 cycles, a Critical missed) and
   `manuscript-model-provenance` (a clean cycle falsified four times).

## Open / Blocked Items

- **The dataset lives in the OTHER repository and is not moving.** Read it in place:
  `repo: /Users/kimhawk/orca/HemaSuite · branch: main · worktree: none`
  - `hematology-paper-writer/docs/03-analysis/gateway-consolidation.audit-ledger.md` (775 lines —
    findings at §13, hypotheses at §54, per-cycle capture at §88, caveats at §107, aggregates at
    §278, and the regeneration script in the appendix at §320)
  - `…/gateway-consolidation.audit-ledger.jsonl` (136 rows: design 105, plan 31)
  - `…/gateway-consolidation.audit-origins.jsonl` (64 KB, the H7 sidecar, hand-edited)
  - `HemaSuite_Project_Document.md` §43 (line 1596) — the B9 origination record, which states the
    gate as **unmet** rather than closed
- **Do not hand-edit the ledger tables** — regenerate with the appendix script. The origins sidecar
  is the only hand-edited part. The `fix-introduced-by` column is a **seed from recorded evidence**;
  a blank cell means *unclassified*, never *new*.
- **Known extractor caveat, already fixed but worth knowing**: the cycle→commit binder matches commit
  subject lines, and c103's commit was titled `cycle 103 fix round` rather than the
  `design audit cycle N` shape, so it bound to no cycle and carried no size row. A fourth pattern was
  appended last so no existing binding could change.
- **No claim was released, because none existed.** This is a new topic with no feature record.
  `docs/.bkit-memory.json` in this repository holds 34 records; the only owned one is
  `pin-agents-tail-banner` → session `f70b9d62`, heartbeat `2026-09-02T02:44:21Z`. **That is not part
  of this handover** — leave it alone.
- **This lane had uncommitted work at handover time** (`h-mad/references/failure-recovery.md`,
  `h-mad/scripts/hmad-dispatch.sh`, plus `pin-agents-tail-banner` audit `.done` markers) and a live
  session, so the brief was **not delivered into its terminal**. It is expected to surface via
  `pending-handovers`.

## Context for Next Session

**Files touched this session:** this brief only, in this repository.

**Uncommitted changes:** this brief, until committed.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch
# the dataset is in the other repo; read it in place
sed -n '13,106p' /Users/kimhawk/orca/HemaSuite/hematology-paper-writer/docs/03-analysis/gateway-consolidation.audit-ledger.md
# re-verify the shipped/unshipped table before acting on it — use SEVERAL spellings per hypothesis
grep -rl 'low_evidence\|legs_changed\|SELF-COUNTING\|AGENT_TOOL_WARN_BYTES' h-mad/
```

**Related docs:**
- `h-mad/references/measurement-discipline.md` §"SELF-COUNTING SCREENS" — H8 as shipped
- `h-mad/SKILL.md` §"Document-audit round cap" (H2), §"Never gate on one audit pass" (the union rule
  the whole dataset is about), `:1318` (H5)
- `h-mad/scripts/h_mad_delta_review.py` (H4), `h_mad_audit_cycle.py` (H6), `h_mad_audit_gate.py` (H3)
