# Handoff — grok-audit-surface: Phase 3 exited, Phase 4 next

**Date:** 2026-10-18
**Branch:** main
**Project:** skills
**Supersedes:** 2026-10-18-main__grok-audit-surface-phase3.md

## Session Summary

Repaired the agy install. `~/.gemini/config/skills/{h-mad,handoff}` were missing, so the project TDD-gate hook refused every agy tool call.

Then drove `grok-audit-surface` Phase 3 to exit under the two-gating-round cap:

| Cycle | Legs | Result |
|---|---|---|
| c2 | codex + agy | 4 build-class must-fixes |
| c3 | codex, plus an advisory doc-auditor delta review | 2 + 2 must-fixes |

Spec moved v1.2 → v1.5 and plan v1.1 → v1.3. The last revision of each is a corrective revision that fixes only filed findings and is not re-audited. Phase 3 is complete (`last_completed_phase=3`, `current_phase=4`). Next is Phase 4, the design.

## Key Learnings

- **agy reviews come back fluent but hollow when its hook target is missing.** A project `.agents/hooks.json` naming a missing `~/.gemini/config/skills/...` path makes agy refuse every tool call, and its review returns `RESULT SUCCESS` with `tools=4 ok=0`. The `Effort:` low-evidence line in `audit-cycle` is what exposed it. The install check is silent on an absent agy root (backlog row filed).
- **Round-cap corrective revisions can need a spec change first.** Codex round 2 found that plan v1.2 had moved the AC-3.2 authority (to the wrapper) without the spec agreeing. Spec-author ran first, and plan-author then quoted the settled spec text verbatim.
- **Fix-introduced defects are measurable.** The origins ledger shows 3 of 8 must-fixes (37.5%) were introduced by the previous cycle's fix. The cheap advisory delta review caught 2 of them.
- **Orchestrator writes during the cycle suite spoil it.** Writes made while the suite runs (handoff commits, origins appends) yield `SUITE: … tree_moved=`. Hold all writes until `audit-cycle` returns (backlog row filed).
- **The suite reads `FAIL passed=6685 failed=39` on this Mac.** The 221 tests that consume this feature's documents all pass (`h_mad_doc_consumers.py --run`), so the 39 failures are environmental, not this feature's. The memory says 36, which is likely stale.

## Next Steps

0. **Commit shas in the phase docs predate a rebase.** The spec, plan and delta review cite pre-rebase shas. Read them through `docs/03-analysis/grok-audit-surface.sha-remap.md`, and tell design-author about the remap.
1. **Resume the feature.** Run `/h-mad "grok-audit-surface"`; the resume oracle routes to Phase 4. Re-claim with `h_mad_state_write.py docs/.bkit-memory.json --feature grok-audit-surface --claim <sid>`.
2. **Dispatch `design-author`.** It writes `docs/02-design/features/grok-audit-surface.design.md` from spec v1.5 (`2f7bf7ae`) and plan v1.3 (`ab3c9f32`). The design owes the items below; the full lists are in the scratchpad reports `author_grok-audit-surface_{spec_v1.3,spec_v1.4,spec_v1.5,plan_v1.2,plan_v1.3}.report.md`.
   - **Probe:** the probe module name, its modes, and the fixture layout.
   - **Calibration data:** how the probe fetches, checks ancestry and runs `git archive` on `calibration/grok-audit-surface`. Also where each cycle's `AUDITCYCLE:` line is recorded into the calibration directory.
   - **Leak control:** an `HMAD_AUDIT_STEM_DIR` location outside the export roots.
   - **Cycle and pass semantics:** the AC-3.4 whole-cycle re-dispatch semantics, and the AC-10.1 pass-index mapping (not time order).
   - **Mutation specs:** the interpreter the new mutation specs use. 166 of 177 committed specs pin the absent `python3.11`.
   - **Carried from the delta review** (six should-fixes):
     - R12 tests only the combined check, not each branch.
     - The `_leg_key` mutation row kills at random.
     - The S1 smoke by-products have no location.
     - S0b checks the branch out in an unnamed work tree.
     - The kept-pin mutation rows are assigned to no stage.
     - The probe has no refusal when the exclusion list changes.
   - **General rule:** the opposed-fixture rule applies to every other token-read check.
3. **Owed by the spec**, optional, for a later spec revision:
   - an AC-5.4 refusal for the exclusion-list version;
   - an AC-3.6 citation for the exclusion-list version;
   - AC-2.7 listing reports, pass logs and kept prompts explicitly.
4. **Then audit the design.** Phase 4 runs the same dual-surface audit (codex + agy first gate), with a cap of 2 gating rounds. Hold all writes while `audit-cycle` runs.

## Open / Blocked Items

**New this session:**
- **grok-audit-surface:** in progress; Phase 3 done, Phase 4 next.
  - Location: repo `/Users/kimhawk/orca/skills` · branch `main` · worktree none.
  - Claim held by session `1f39eb76-d775-4dc8-b33d-b680f83a32ee`; it goes stale after 2h.
  - Spec v1.5: `2f7bf7ae`, sha `d5af08f6…`. Plan v1.3: `ab3c9f32`, sha `ebcf8456…`.
  - Audit reports: `docs/01-plan/features/grok-audit-surface.plan.audit.v{1,2,3}.*.md` and the delta review `docs/03-analysis/grok-audit-surface.plan.delta-review.5b2df07-20261018T130440Z.md`.
  - Origins ledger: `docs/03-analysis/grok-audit-surface.audit-origins.jsonl` (8 records).
- **Untracked delta-review prompt** `docs/03-analysis/grok-audit-surface.plan.delta-review.5b2df07-20261018T130440Z.md.txt`: a staging artifact, left untracked. Delete it or commit it as provenance; the report beside it is committed.
- **The plan audit exit stamp was never written** (`STAMP: NOT-EXPECTED reason=no_passing_leg` every cycle), so `--exit-check` has nothing to read. That's expected when exiting via the round cap; Phase 5 is the gate.

**Carried from 2026-10-18-main__grok-audit-surface-phase3.md:**
- **agy hook target missing (step 0 there):** CLOSED this session. `~/.gemini/config/skills/{h-mad,handoff}` are now symlinked, and an agy smoke passed with `EVIDENCE: PASS tools=2 ok=2`. The install-check gap stays an OPEN backlog row.
- **Plan audit cycle 1 collect:** CLOSED. Cycle 1 was UNVERIFIED (hollow agy pass), was superseded by cycles 2 and 3, and its codex report was committed.
- **`INSTALL: FAIL issues=2` (pdf, skill-creator vendor installs):** known false positive, unchanged. Backlog row OPEN.
- **`h-mad-advisor-warn.sh` not wired:** deferred, unchanged.
- **`docs/.bkit-memory.json` loss:** CLOSED, unrecoverable; unchanged.
- **Stale-copy backups** in `/private/tmp/claude-501/-Users-kimhawk-orca-skills/1f39eb76-d775-4dc8-b33d-b680f83a32ee/scratchpad/skill-copy-backup/`: safe to delete; unchanged.
- **Backlog row "mutation harness interpreter override":** OPEN, unchanged.
- **backlog_cycle LOW review residuals:** deferred, unchanged.
- **Census `--help` `FileNotFoundError`:** deferred, unchanged.
- **`h_mad_mutation_harness.py:2300` SyntaxWarning:** deferred, unchanged.
- **NS2 HemaSuite feature/204 `no-mutation-spec`:** HemaSuite's call, unchanged. Repo `/Users/kimhawk/orca/HemaSuite`.
- **Foreign `stash@{0}` (`resolved-model`):** unchanged. Do not touch.
- **Bash pin blast radius:** unchanged and inert.
- **`.git/info/exclude` entries:** keep; unchanged.
- **Row 1412 liveness limits:** watch-only; unchanged.
- **Agy-coder-fallback `review_independence_unrecorded`:** accepted; unchanged.

## Context for Next Session

**Files touched this session:**
- `docs/01-plan/features/grok-audit-surface.spec.md` (v1.3–v1.5), `.plan.md` (v1.2–v1.3), `.plan.audit.v{2,3}.*`
- `docs/03-analysis/grok-audit-surface.audit-origins.jsonl`, `…plan.delta-review.5b2df07-….md`
- `docs/skill-candidates.md` (2 scout rows), `docs/learnings.md`
- `~/.gemini/config/skills/{h-mad,handoff}` (new symlinks), `~/.claude/projects/-Users-kimhawk-orca-skills/memory/python-interpreters-this-mac.md`

**Uncommitted changes:** one untracked delta-review prompt `.txt`. Everything else is committed by this closeout.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
/h-mad "grok-audit-surface"     # → Phase 4: dispatch design-author
```

**Related docs:**
- `docs/01-plan/features/grok-audit-surface.spec.md`, `.plan.md`
- `h-mad/SKILL.md` §"Document-audit round cap", §"Teammate authors", §"Delta self-review"
- `h-mad/references/agy-runtime.md` §Install
