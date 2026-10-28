# Analysis: grok-audit-surface

## Executive Summary
`grok-audit-surface` added the empirical measurement harness (`h-mad/scripts/h_mad_grok_surface_experiment.py`), calibration and stratified probe runners (`h_mad_grok_surface_calibrate.py`, `h_mad_grok_surface_probe_run.py`, `h_mad_grok_surface_verify.py`), 12-item stratified probe corpus (`docs/03-analysis/probes/grok-audit-surface/`), measurement report (`docs/03-analysis/grok-audit-surface.measurement.md`), and the `S4` (`PASS` on both `P_marginal` and `P_false_neg`) route in `h-mad/SKILL.md` (`--passes 3` and `--surfaces codex,agy,grok` for the first gate of each phase, with explicit grok unavailability/twice-UNVERIFIED fallback and must-fix falsification rules). All 11 functional requirements (`FR-1` through `FR-11`) and all 63 active acceptance criteria (`AC-3.7` retired during Phase 3 design audit) are satisfied, with 7,497/7,497 tests passing in `h-mad/tests`.

## Match Rate: 100%

## FR Coverage
| FR | Status | Evidence | Gaps |
|----|--------|----------|------|
| FR-1 | Met (9/9 ACs) | `h-mad/scripts/h_mad_grok_surface_experiment.py` (`classify_marginal`, `evaluate_p_marginal`, `compute_marginal_rate`, `MarginalItemResult`, `PMarginalVerdict`); `h-mad/tests/test_h_mad_grok_surface_experiment.py` | None |
| FR-2 | Met (7/7 ACs) | `h-mad/scripts/h_mad_grok_surface_experiment.py` (`classify_planted_cell`, `evaluate_p_false_neg`, `compute_surface_detection_rates`, `PlantedItemResult`, `PFalseNegVerdict`); `h-mad/tests/test_h_mad_grok_surface_experiment.py` | None |
| FR-3 | Met (8/8 active ACs; AC-3.7 retired) | `docs/03-analysis/probes/grok-audit-surface/manifest.json` and 12 probe item bundles (`plan-01`..`plan-04`, `design-01`..`design-04`, `impl-01`..`impl-04`); `h-mad/tests/test_grok_surface_probe_corpus.py` | None |
| FR-4 | Met (5/5 ACs) | `h-mad/scripts/h_mad_grok_surface_experiment.py` (`route_verdict`, `ExperimentDecision`, `S4`/`S3`/`S2`/`S0` routing matrix); `h-mad/tests/test_h_mad_grok_surface_experiment.py` | None |
| FR-5 | Met (5/5 ACs) | `docs/03-analysis/grok-audit-surface.measurement.md` (committed measurement report with per-item tables, raw rates, exact Clopper-Pearson 95% CIs, and `DECISION: S4`); `h-mad/tests/test_grok_audit_surface_docs.py` | None |
| FR-6 | Met (7/7 ACs) | `h-mad/scripts/h_mad_grok_surface_experiment.py` (`render_measurement_markdown`, `parse_cli_tokens`, CLI `--manifest` / `--results` / `--out` / `--self-test`, single-line `EXPERIMENT:` stdout token); `h-mad/tests/test_h_mad_grok_surface_experiment.py` | None |
| FR-7 | Met (4/4 ACs) | `h-mad/SKILL.md` §"Never gate on one audit pass" (`--passes 3` and `--surfaces codex,agy,grok` on the first gate of each phase, citing `docs/03-analysis/grok-audit-surface.measurement.md`, plus unavailable/twice-UNVERIFIED `grok` fallback and preserved K3 `fallback_agent=grok`); `h-mad/tests/test_grok_audit_surface_docs.py` | None |
| FR-8 | Met (3/3 ACs) | `h-mad/SKILL.md` §"Never gate on one audit pass" (verbatim falsification sentence for `grok`-surfaced `must-fix` findings with file+line/section citation before edit or `DROP` rationale in `audit-summary.md`); `h-mad/tests/test_grok_audit_surface_docs.py` | None |
| FR-9 | Met (5/5 ACs) | Conditional `S3` branch (`P_marginal = FAIL`, `P_false_neg = PASS`) not triggered because empirical measurement routed to `S4`; routing logic and tests verified in `h-mad/scripts/h_mad_grok_surface_experiment.py` and `h-mad/tests/test_h_mad_grok_surface_experiment.py` | None |
| FR-10 | Met (3/3 ACs) | Conditional `S2`/`S0` branch (`P_false_neg = FAIL`) not triggered because empirical measurement routed to `S4`; routing logic and tests verified in `h-mad/scripts/h_mad_grok_surface_experiment.py` and `h-mad/tests/test_h_mad_grok_surface_experiment.py` | None |
| FR-11 | Met (7/7 ACs) | `h-mad/scripts/h_mad_grok_surface_calibrate.py` (`CALIBRATE:` token, 3-item calibration harness), `h-mad/scripts/h_mad_grok_surface_probe_run.py`, `h-mad/scripts/h_mad_grok_surface_verify.py`, and calibration/probe artifacts in `docs/03-analysis/probes/grok-audit-surface/`; `h-mad/tests/test_h_mad_grok_surface_calibrate.py`, `h-mad/tests/test_h_mad_grok_surface_probe_run.py`, `h-mad/tests/test_h_mad_grok_surface_verify.py` | None |

## Gaps
None — all 11 FRs and 63 active ACs are satisfied.

## Test Results
- `h-mad/tests/test_grok_audit_surface_docs.py` + `h-mad/tests/test_grok_fallback_docs.py`: `23 passed in 0.56s`
- Full `h-mad/tests` suite: `7497 passed, 3 warnings in 2352.22s (0:39:12)`
- Wire registry verification (`h_mad_wire_registry.py verify --base f6820752`): `WIREREG: PASS registered=55 verified=55 broken=0 missing=0 ambiguous=0 unverified_renames=0 undeclared_removals=0 unverifiable=0`
- Mutation spec anchor check (`h_mad_mutation_harness.py --check-anchors`): `ANCHORS: ANCHORS_OK specs=188 mutations=2691 ok=2691 drifted=0 unreadable=0 skipped=0 unclassifiable=0`

## Verdict
Match rate: 100% (threshold: 90%). Tests: 7497/7497 passing.
→ Advance to Phase 7

## Version History
- v1.0: Initial gap analysis draft.
