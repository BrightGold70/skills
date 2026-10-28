# Report: grok-audit-surface

## Executive Summary
`grok-audit-surface` measured the `grok` audit leg across 27 build-class defects on a 3-design calibration set (`SEEDSCORE: PASS` — grok recall `21/27` vs agy `25/27`, fabrication `0/34` vs agy `0/33`, unique grok recall `2`), hardened `exec grok` containment and per-pass isolation, and promoted `grok` to the third audit surface on the first gate of each phase (`--passes 3` and `--surfaces codex,agy,grok`) with 100% spec match rate and 7,497/7,497 passing tests.

## Summary
Built the end-to-end Grok audit-surface calibration probe (`docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py`), containment and canary guards (`h-mad/scripts/h_mad_grok_containment.py`, `h-mad/scripts/h_mad_tool_calls.py`, `h-mad/scripts/hmad-dispatch.sh`), path-scope calibration prompt clause (`h-mad/scripts/h_mad_assemble_audit.py`), and 445-mutation spec (`h-mad/tests/mutation-specs/grok_audit_surface.json`). Published the empirical measurement (`docs/03-analysis/grok-audit-surface.measurement.md`) and routed `S4` (`PASS`) into `h-mad/SKILL.md` §"Never gate on one audit pass" with explicit availability/twice-UNVERIFIED fallback rules and a mandatory falsification check for grok-surfaced `must-fix` findings. Closed Phase 6 with `ARCHREVIEW: READY_TO_MERGE` and 100% FR/AC match rate without iterate cycles.

## Metrics

| Metric | Value |
|---|---|
| Plan audit cycles | 6 |
| Design audit cycles | 4 |
| Impl-plan audit cycles | 4 |
| Iterate cycles (Phase 6b) | 0 |
| Final match rate | 100% |
| 6a-prime architectural review | `READY_TO_MERGE` |
| Tests | 7497 passing / 0 failing |
| Phases with back-propagation | Phase 5 → Phase 2/3/4: empirical containment & toolscan incident findings (Runs 1–8) back-propagated into spec v1.8, plan v1.5, design v1.15, and impl-plan v1.4 |

### Phase-7 Precondition Gate Output & Review-Independence Warnings

```text
PHASE7: READY blockers=0
  WARNING review_non_independent: 5e-verify module=probe-cli was implemented and reviewed by codex
  WARNING review_non_independent: 5e-verify module=ledger-checks was implemented and reviewed by codex
  WARNING review_non_independent: 5e-verify module=build-root was implemented and reviewed by codex
  WARNING review_non_independent: 5e-verify module=root-reset was implemented and reviewed by codex
  WARNING review_non_independent: 5e-verify module=record-cycle was implemented and reviewed by codex
  WARNING review_non_independent: 5e-verify module=smoke was implemented and reviewed by codex
  WARNING review_non_independent: 5e-verify module=extract was implemented and reviewed by codex
  WARNING review_non_independent: 5e-verify module=score was implemented and reviewed by codex
  WARNING review_non_independent: 5e-verify module=rescore-main-leak was implemented and reviewed by codex
  WARNING review_non_independent: 5e-verify module=stub-knob was implemented and reviewed by codex
  WARNING review_non_independent: 5e-verify module=gate-pins was implemented and reviewed by codex
  WARNING review_non_independent: 5e-verify module=skill-s0-text was implemented and reviewed by codex
  WARNING review_non_independent: 6a-prime module=s4-route was implemented and reviewed by agy
[H-MAD] grok-audit-surface phase7 READY
```

## What Went Well
- Empirical containment probes (canary plant/judge, per-pass export roots, no-checkout git plumbing, and `TOOLSCAN:` shell/write path-scope classification) surfaced real sandbox escape vectors during calibration Runs 1–8 before `grok` was promoted into production audit gates.
- The 445-mutation spec (`h-mad/tests/mutation-specs/grok_audit_surface.json`) and every-outcome document pins (`h-mad/tests/test_grok_audit_surface_docs.py`) caught subtle prose and token-grammar mismatches immediately during Task 16 and Task 17 RED/GREEN cycles.

## What To Improve Next Time
- `h_mad_archive_feature.py` checks `probe_readers()` for `docs/03-analysis/probes/<feature>/` directories read by live tests, but does not yet check whether top-level `docs/03-analysis/<feature>.*` files (such as `docs/03-analysis/grok-audit-surface.measurement.md`) are read by live test files (`test_grok_audit_surface_docs.py`). Extend `h_mad_archive_feature.py` so any `DOC_DIRS` artifact referenced by non-markdown tracked code is also reported as `KEPT:` rather than moved away from live tests.
- Untracked state backup directories created in the repo root (e.g. `kimhawk@Hawui-Macmini.local/` with >52k files) slow down `tree_lock_plugin.py` (`git status -uall`) across every `pytest` invocation; keep calibration state backups outside the git working tree or under `.git/info/exclude`.

## Carry Items
- Seed-shape transfer residual (`AC-2.1`): calibration seeds are build-class shapes from the four classes of spec AC-2.1, and whether recall on real defects matches is unmeasured.
- Path-scope clause transfer residual (`AC-3.9`): calibration prompts included the calibration-only path-scope clause; production grok legs do not receive it, and whether production grok legs without it behave identically is unmeasured.
- Extend `h_mad_archive_feature.py` reader detection to cover `docs/03-analysis/<feature>.measurement.md` files pinned by live tests.

## Version History
- v1.0: Initial report draft.
