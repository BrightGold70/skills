# Handoff — seven h-mad tooling findings from the WSG lane

**Date:** 2026-09-11
**Branch:** `main`
**Project:** orca/skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** none — first on this branch from the WSG lane
**Handover-From:** HemaSuite-wsg · feature/website-source-grounding · session 8574638e-b72b-4367-b00c-c774f69c9839
**Taken-Over-By:** orca/skills · main · session 0392c2be-3d8e-4fbf-9c33-0a3320fb90e8 · 2026-09-11

## Session Summary

`website-source-grounding` ran to Phase 7 closure in `/Users/kimhawk/orca/HemaSuite-wsg`,
which is now being deleted. Along the way it accumulated seven findings that belong to the
**h-mad skill**, not to HemaSuite. They are collected here so they survive that deletion.
None is a HemaSuite defect and none blocks HemaSuite.

Two of them (the first two) are the reason a fabricated architectural review nearly closed
a Phase-7 gate, so they are the ones worth reading first.

## Key Learnings

- **The two review gates fail in the same direction: they cannot tell a review that read
  nothing from one that read everything.** One counts the reviewer's own report write as
  evidence of reading; the other hands the reviewer a prompt so large it fabricates. Both
  produce a fluent, schema-correct, confident `READY_TO_MERGE`.
- **`archreview_cycle score` runs evidence → verdict → record.** A fabricated verdict is
  therefore *written into state*, where `h_mad_phase7_preconditions.py` reads it as a
  satisfied gate. Nothing downstream re-checks. That chain is why finding 1 is not cosmetic.
- **A documented rule is not an enforced one.** The `git-hooks/pre-push` anchor hook exists,
  is correct, and was simply never installed in the clone that needed it — three mutation
  anchors then drifted undetected through an entire feature and its Phase 7.

## Next Steps

1. **`h_mad_review_evidence.py` counts the agent's OWN report write as evidence of reading.**
   Measured: a 6a-prime cycle made exactly one tool call — `write_to_file`, its own report —
   and returned `ASSESSMENT: READY_TO_MERGE` in **132 bytes** over a 128-file diff. The gate
   said `EVIDENCE: PASS tools=1`. Proposed fix: discount writes whose `TargetFile` is the
   known report path (the caller already passes `--report-file` to `stage`), then adopt
   `h_mad_audit_cycle.py`'s low-evidence floor, which already encodes "at or below the calls
   the delivery contract itself costs".
2. **`h_mad_archreview_cycle.py stage` has no oversize halt and no `--vh-tail`.** It inlines
   the WHOLE design: measured **572,123 B** (442 KB body + 130 KB of 18 Version History
   entries) = **98.4%** of a 581,564 B prompt, ~2.2x agy's confirmed-answered frontier of
   266,342 B. That is what *caused* finding 1's fabrication. `h_mad_assemble_audit.py`
   already HALTs on oversize and offers `--vh-tail`; `stage` has neither. Re-staged by hand
   at 226,531 B — architectural sections only, production diff **inlined**, 24 production
   files instead of 128 paths including PDFs — cycles 2-4 then all produced substantive
   reviews. **Second defect in the same command:** the template passes only a *path list*
   where the reviewer needs the diff inlined.
3. **`.done` marker never written by `exec agy`** on any of five 6a-prime cycles, though the
   report file was. `report-wait` would block forever; the report path had to be read
   directly. Unattributed between the dispatch template's instruction and agy's behaviour —
   **determine which before proposing a fix.**
4. **The mutation harness cannot distinguish a crash-kill from a guard kill.** A mutant that
   dies on an unrelated exception scores identically to one the guard caught. Mitigated
   today only by giving every mutation a `test` key and reading the `mechanism:` line;
   without one, a wrong-catcher ships as `ALL_CAUGHT`.
5. **`h_mad_baseline_sha.py` is wrong on a branch whose first commit is not the impl-plan
   commit.** On `feature/website-source-grounding` it returns
   `UNVERIFIED candidate=43d2a012`; the real 5c is **`83851636`**, independently corroborated
   by reading that commit's subject ("impl-plan v1.0 — Phase 5a, 18 tasks"). The
   `candidate=` spelling is correct and did its job — the value was not scraped as an answer
   — but the by-hand value was needed twice in this feature.
6. **h-mad state file vanished mid-session, cause UNDETERMINED; did not recur.** Proposal
   unchanged: treat an ABSENT state file as *cannot-judge* for the TDD gate rather than as a
   clean read, so the gate stands down loudly instead of silently.
7. **Three `h_mad_precheck_doc.py` findings** — PINDRIFT bare-L, LINEPIN else-arm,
   version-history; (b) confirmed live again this session. And the **remaining tooling
   backlog: #57** (5e spec-reviewer template has no READ-ONLY clause), **#33**
   (`h_mad_wire_registry.py --registry` default follows cwd — bit this lane, two registries
   are live and out of sync in HemaSuite), **#37** (`<slot>` inside prose backticks), **#38**
   (`--trunk main` unreadable on that branch — same root as item 5), **#56** (eleven
   impl-plan rows naming a different AC).

## Open / Blocked Items

- **Nothing here is blocked**, and nothing here is claimed. No h-mad feature record was
  created for any of these; they are findings, not in-flight work.
- **Items 1 and 2 are coupled** — fixing the evidence gate without fixing the prompt size
  makes 6a-prime *fail* rather than fabricate, which is correct but will read as a
  regression to whoever meets it first. Fix them together, or land 2 before 1.
- **The `--vh-tail` remedy already exists** in `h_mad_assemble_audit.py`; item 2 is largely
  a matter of routing `stage` through the same guard rather than writing a new one.

## In-Flight Processes

**None.**

## Context for Next Session

**Where the evidence lives.** The WSG clone is being deleted, but every artifact cited
above was archived and pushed to HemaSuite before deletion, under
`hematology-paper-writer/docs/archive/2026-09/website-source-grounding/` on
`feature/18-gateway-consolidation` (origin tip `85d3af6d`):

- `website-source-grounding.6a-prime.v{2,3,4,5}.agy.2026-09-10.md` — the five cycles,
  including the 132-byte fabrication and the three real defects cycle 3 found
- `website-source-grounding.design.rejections.md` — the rejections ledger, incl. the
  operator override of the `archreview` gate and its reasoning
- `website-source-grounding.report.md` — the Phase 7 report

**The skill is a symlink and this repo is live.** `~/.claude/skills/h-mad` resolves into
this checkout, so editing the working tree edits the running skill. Edit in a git worktree
while any run is in flight, and run **both** coupled suites before merging — a change here
can fail a suite in a repo you did not touch.

**Related state:** a `pre-push` anchor hook from this repo's `git-hooks/` was installed into
`/Users/kimhawk/orca/HemaSuite/.git/hooks/` on 2026-09-11. It currently blocks pushes from
HemaSuite `main` for two pre-existing reasons documented in that repo's handoff of the same
date. That is the hook working as designed, but it is the first place it has ever run, so
expect first-contact friction there rather than assuming a hook defect.
