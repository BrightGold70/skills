# Brainstorm: grok-audit-surface

## Executive Summary
Grok becomes a standing third audit leg on a document's first gating cycle (codex + agy + grok, three model families), but only after a seeded-defect calibration shows it beats agy on both recall and fabrication rate on the same seeds.

## Problem Statement
Grok joins an H-MAD audit today only when codex is out and `fallback_agent=grok` (`SKILL.md` §"Teammate audit leg"), and its audit precision is labelled **unmeasured** (D4, `SKILL.md:624`, `:3035`). So a third, independent model family sits idle on every normal run, and when it does run, its verdicts can't be weighed.

## Proposed Approach
1. **Calibrate first (gating prerequisite).**
   - Build a seeded-defect set: copies of archived, already-audited phase documents with N known build-class defects planted. Each defect has a ground-truth label (location, class, expected finding).
   - Dispatch **grok and agy** through the normal `audit-cycle` path on the same seeded prompts. codex runs as the reference ceiling when available.
   - Score per surface: recall = seeded defects found; fabrication = must-fixes whose premise fails against source.
   - The scorer is a committed probe and the result a committed measurement doc, so the run can be repeated after a grok upgrade.
2. **Promotion bar, relative to agy.** Grok is promoted only if, on the same seeds, its fabrication rate is ≤ agy's and its recall is ≥ agy's. On a miss, grok stays a fallback and the numbers are published anyway, which retires "unmeasured" either way.
3. **Routing change (only on pass).**
   - `SKILL.md` §"Which two surfaces" / §"Never gate on one audit pass": the first gating cycle of a document runs `--surfaces codex,agy,grok`.
   - Revision cycles are unchanged: codex gates and doc-auditor reviews the diff.
   - The "never three reports" sentence is reworded. Its rationale was two reports sharing a model family, and three distinct families don't violate it.
4. **Driver / exit check.** Grok log scanning and effort scoring already exist (`h_mad_audit_cycle.py:586-596`, `:726-732`). The remaining work is checking `--passes 3` with three distinct surfaces end to end, and making sure the stamped leg set `codex+agy+grok` behaves correctly under `--exit-check` (see Open Questions).
5. **Audit-path re-smoke on grok 1.0.62.** Re-verify `exec grok` audit dispatch, NDJSON event types (`_GROK_TYPES_RE`), `scan_grok` evidence, and report-file delivery. Update the version line in `references/grok-runtime.md` for the audit path only.

## Alternatives Considered
- **Grok replaces the doc-auditor delta review on revisions**: rejected for now. The delta review is where fix-introduced musts surface, and it is cheap and same-context-aware. Swapping it is a separate experiment once grok's numbers exist.
- **Grok replaces agy as the standing second surface**: rejected. agy is not uniformly hollow; a 58-tool-call agy pass found a defect both teammate passes missed. Dropping it loses real findings.
- **Calibrate by replaying the real gateway-consolidation corpus**: deferred. Those prompts sit near the 1,048,576-char exec ceiling, and the ground truth there is reviewer-verified, not planted. Seeded defects give exact labels and are cheap to rerun.
- **Absolute pass bar (match codex 0/25)**: rejected as preset. It is likely unreachable and would leave grok idle forever. Relative-to-agy is the honest bar, because agy already holds a gating leg at its measured rate.

## Risks & Mitigations
| Risk | Likelihood | Mitigation |
|---|---|---|
| Seeds are easier or harder than real defects, so recall doesn't transfer | M | Seed only build-class defects drawn from real must-fix shapes in the origins ledger (fix-introduced, new-mechanism); state the transfer residual in the measurement doc |
| Small N makes "beats agy" noise | M | Fix N up front in the spec; report counts with denominators, not just rates; a tie on fabrication counts as pass only if recall is strictly higher |
| Grok runs are slow (~50 min authoring trial) and blow the dispatch timeout | M | Audits are read-only and shorter, but measure wall time in the smoke and set `--timeout` from it |
| Leg-set change resets the exit streak | H | Decide in the spec how `codex+agy+grok` (first gate) and `codex` (revision) interact with `--exit-check` `legs_changed` |
| Grok 1.0.62 changed NDJSON event types and the scanner reads truncated | L | The smoke checks `_GROK_TYPES_RE` against a live log; `grok-truncated` already fails closed |
| Grok 1.0.62 needs a different model or auth than 1.0.41 | L | Record the resolved model via `h_mad_resolved_model.py grok` in the measurement |

## Dependencies
- `grok` CLI 1.0.62 on PATH (present: `~/.grok/bin/grok`)
- `agy` CLI for the comparison arm; codex optional (reference ceiling)
- Existing: `hmad-dispatch exec grok`, `h_mad_audit_cycle.py` grok effort scoring, `h_mad_review_evidence.scan_grok`, `h_mad_audit_origins.py` (defect-shape source)

## Open Questions
- **Exit streak across leg sets:** first gate stamps `codex+agy+grok`, revision cycles stamp `codex`. Today `--exit-check` blocks `legs_changed` between consecutive cycles. Does the two-clean-cycle streak only count among revision cycles (which is true today for codex+agy → codex anyway), or does the spec need an explicit rule?
- **Seed count N and source documents:** which archived features supply the base documents (plan, design, impl-plan mix), and what N gives a usable denominator per surface?
- **Fabrication scoring:** is it automated (quote: span not found in source → candidate fabrication, then confirmed by hand), or fully manual? The evidence-gate measurement refused an automatic span check (4 of 6 caught cost 13 of 31 real musts), so a hand confirmation step is likely required.
- **Union with three surfaces:** the gate stays on the union of must-fixes. Confirm grok's must-fixes are falsified against source before acting, same as the other legs.
- **Cost line:** +1 dispatch per document's first gate. Is that acceptable unconditionally, or only for design/impl-plan (not plan)?

## Version History
- v1.0: Initial brainstorm draft — operator decisions 2026-10-18: third leg on first gate; seeded-defect calibration; promotion bar relative to agy; audit-path-only re-smoke on grok 1.0.62.
