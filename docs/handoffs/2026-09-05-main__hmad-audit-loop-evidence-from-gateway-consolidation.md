# Handoff — h-mad: measured evidence from a 99-cycle design audit, nine proposals and two tooling defects

**Date:** 2026-09-05
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Handover-From:** HemaSuite · main · session `cab14393-84ea-4753-9183-9c9a1946c239`
**Supersedes:** none — first on this topic

## Session Summary

The HemaSuite feature `gateway-consolidation` (#18) reached design audit cycle 99 with the exit streak at zero (31 plan cycles before that). At the operator's request the sending session measured the loop from committed artifacts and built a per-cycle ledger with origin tagging of every must-fix. This brief hands the h-mad-side conclusions to the skill's owner: nine testable proposals and two tooling defects. Nothing here is a code change to h-mad; it is the evidence and the asks. Ownership of acting on them moves with this brief; the ledger and its regeneration stay in HemaSuite.

## Key Learnings

- **Σmust tracks the leg count, not document quality.** Last 13 cycles: `3 3 7 5 3 5 4 3 8 4 7 12 6`; each rise coincides with a leg added or returning (teammate c87, doc-auditor+crossdoc c92, codex c97). The "two consecutive both-clean" exit was reset by new legs, never approached by the documents.
- **Correction mass migrated into narrative.** Three gated documents 333 KB → 761 KB in cycles 92–98 (91 cycles to reach 333 KB); Version-History share 34/45/41 %; records ~130 chars at c88–90 → 3–12 KB from c91; five records wrong at their own commit (c91, c94–c97). The audit began auditing its own audit trail.
- **A fix round introduces the class it hunts.** The pre-c99 delta self-review fixed 3 defects; its three authors introduced 4 musts, all bare present-tense counts (`unanchored -S returns two`, `ls-tree 14 before and after`) moved by the commit publishing them. ≥17 of 98 cycles are fix-introduced (seeded lower bound); 60 origin-tagged lines exist from c98 on, re-derived from the file: instrument 17, fix-introduced 13, author-self-caught 12, record-stale 6, propagation-gap 5, new-consistency 4, new-mechanism 3.
- **Disagreement carried the signal.** agy clean while codex found musts in 42 of 78 shared cycles (Phase 3: 24/31); rejections agy 18 vs codex 1; 3 of 7 crossdoc reports schema-INVALID yet gated; c99 legs filed the same fact as Must (doc-auditor) and Nit (crossdoc).
- **Cycles are cheap**: median 6 min between cycle commits. Nothing in the loop made cycle 60 a stop.

## Next Steps

1. Read the ledger: `/Users/kimhawk/orca/HemaSuite/hematology-paper-writer/docs/03-analysis/gateway-consolidation.audit-ledger.md` (tables, aggregates, hypotheses H1–H9, per-cycle capture protocol, extraction script in the appendix) and `…/gateway-consolidation.audit-origins.jsonl`.
2. Decide which of H1–H9 become h-mad changes (each with the measurement that would confirm it): **H1** revision records and rejections out of the gated bytes (non-gated sidecar) → records-wrong-at-own-commit → 0; **H2** cycle cap per phase (e.g. 20) that forces a gate redesign checkpoint; **H3** clean streak counts only over an unchanged leg set; **H4** delta self-review as a script that re-executes every command/count in the diff hunks before dispatch (the hand-rolled version failed twice in one sitting); **H5** shared sentences single-sourced and adoption-checked pre-commit, same cycle; **H6** hollow legs (no tree reads / schema-INVALID) scored INVALID and excluded from the union; **H7** origin tagging per must in the protocol; **H8** a document may not publish a bare count of an instrument it contains (anchored `<rev> -- <path>` form + residual, body-scoped counts re-derived after the write); **H9** assembled-prompt size: >~740 KB kills an Agent-tool leg ("Prompt is too long") — `h_mad_assemble_audit.py` warns only about the pane path (89.9 KB) and the codex 1,048,576-char cap; emit a windowed reading guide (contract lines + rubric lines; documents from the tree) or split the prompt.
3. Tooling defect A — `handoff/scripts/handover_landed.py` reports `LANDED` when the target worktree's comment is a **sibling session's own `handoff:` stamp** (measured 2026-09-05 on the skills main worktree, whose comment was `handoff: doc-block-exec-rounds-fifteen-sixteen …`, for a brief nobody picked up: no `Taken-Over-By`, no claim). "Stamp is gone and something else is there" is not pickup when the sender never stamped that worktree. Gate the comment signal on the sender having stamped, or require the replacement to reference the brief's slug.
4. Tooling defect B — `h_mad_assemble_audit.py` `size_status=unverified` is the wrong axis for Opus legs; add an explicit "Agent-tool leg ingestion limit" warning at ~700 KB, and print the line ranges of contract / documents / rubrics so a windowed leg can be briefed mechanically (measured layout at 818 KB: contract 1–87, design 88–3297, spec 3298–4629, plan 4630–5683, base invariants 5684–5986, project invariants + rubrics + repeated contract 5987–6195).
5. The earlier brief `docs/handoffs/2026-09-05-main__audit-loop-never-runs-repo-suite.md` (`df04e8e`) is still unpicked — take both together.

## Open / Blocked Items

- **Acting on H1–H9 and defects A/B** — status: handed over. `repo: /Users/kimhawk/orca/skills · branch: main · worktree: /Users/kimhawk/orca/skills` (h-mad checkout; `~/.claude/skills/h-mad` is a symlink into it — edits are live, use a worktree while a run is in flight). Evidence lives in HemaSuite at the paths in Next Step 1; the extraction script is embedded in the ledger's appendix and at the sending session's scratchpad `audit_ledger.py`.
- No feature claim existed for this work; nothing to release.

## Context for Next Session

**Files touched this session:** this brief only (in this repo).
**Uncommitted changes:** none from this brief after its commit.
**To resume:**
```bash
cd /Users/kimhawk/orca/skills
sed -n '1,120p' /Users/kimhawk/orca/HemaSuite/hematology-paper-writer/docs/03-analysis/gateway-consolidation.audit-ledger.md
```
**Related docs:** `docs/handoffs/2026-09-05-main__audit-loop-never-runs-repo-suite.md` (sibling brief, same sender lane).
