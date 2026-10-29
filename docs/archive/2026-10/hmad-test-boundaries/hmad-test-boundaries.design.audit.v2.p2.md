## Summary
The revised Phase 4 Design (`docs/02-design/features/hmad-test-boundaries.design.md` `v1.1`) resolves all Cycle 1 (`v1.p1` and `v1.p2`) findings: project-root inference (`infer_project_root`) and `--root` propagation into `h_mad_test_boundaries_check.py`, two-branch paired `.spec.md` resolution (`resolve_spec_path`), fail-closed handling of unreadable design/spec files in `should_activate_design_check`, host-independent `<skill_dir>` self-check paths in `h-mad/agents/design-author.md`, and self-bootstrapping `## Test Boundaries` Row 1 public interfaces and oracle citations. All 17 acceptance criteria (`AC-1.1`..`AC-6.3`) in `docs/01-plan/features/hmad-test-boundaries.spec.md` (`v1.4`), as well as repository invariants in `h-mad/invariants.base.md` and `.h-mad/invariants.md`, are satisfied without blocking or non-blocking defects.
Evidence: 20 files opened, 4 greps run.

| Spec item | Classification | Design location | Notes |
|---|---|---|---|
| `AC-1.1` | `implemented-as-written` | `Section 1.1`–`Section 1.2` (`h-mad/references/inline-protocols.md`, `h-mad/scripts/h_mad_doc_shape_check.py`) | `## Test Boundaries` template with 5 columns added to `inline-protocols.md`; `REQUIRED_SECTIONS["design"]` unchanged; verified by `test_h_mad_doc_templates.py` and `test_h_mad_test_boundaries_check.py`. |
| `AC-1.2` | `implemented-as-written` | `Section 1.2`, `Section 2.4` (`Rule 6`) | 4 non-unit verification categories (`verified by: audit \| live-run \| operator \| doc-review`) with concrete proving artifact enforced by `NON_UNIT_VERIFIED_RE` + `ARTIFACT_TOKEN_RE`. |
| `AC-1.3` | `implemented-as-written` | `Section 1.3` (`h-mad/agents/design-author.md`) | Authoring rules and pre-return self-check command using `<skill_dir>/scripts/h_mad_test_boundaries_check.py` specified. |
| `AC-2.1` | `implemented-as-written` | `Section 2.2`–`Section 2.5` (`h-mad/scripts/h_mad_test_boundaries_check.py`) | Exit code `0`/`1`/`2` contract, two-branch `resolve_spec_path`, and `TEST-BOUNDARIES: PASS\|FAIL\|EXEMPT\|NO-SPEC\|UNREADABLE` output format. |
| `AC-2.2` | `implemented-as-written` | `Section 2.3` (`find_unhedged_headings`), `Section 2.4` (`Rules 1–5`) | Fenced-code-block-aware heading scan, 5-column header check, and `extract_ac_sets` active vs. retired AC set comparison (`MISSING-AC`, `RETIRED-AC`, `UNKNOWN-AC`). |
| `AC-2.3` | `implemented-as-written` | `Section 2.4` (`Rules 6–9`) | Placeholder rejection (`PLACEHOLDER-CELL`), lexical tautology rejection (`TAUTOLOGICAL-ORACLE`), self-mocking rejection (`SELF-MOCK`), and ungrounded exclusion rejection (`UNGROUNDED-EXCLUSION`). |
| `AC-2.4` | `implemented-as-written` | `Section 2.1`, `Section 2.3` (`PRE_EXISTING_FEATURES`, `is_exempt_design`) | Explicit 10-stem `PRE_EXISTING_FEATURES` frozenset and `docs/archive/` exemption returning `TEST-BOUNDARIES: EXEMPT` (`0`), overridden by `--no-exempt`. |
| `AC-3.1` | `implemented-as-written` | `Section 4.1` (`h-mad/audit-prompt.template.md`) | Phase 4 design audit instructions require verifying `## Test Boundaries` against the 4 review dimensions and emitting `Must-fix` (`class: build`) on failure. |
| `AC-3.2` | `implemented-as-written` | `Section 4.2` (`h-mad/agents/doc-auditor.md`) | Phase 4 Design Audit Rubric extended with items 5–8 covering public boundary vs. private helpers, oracle independence, mock boundary discipline, and exclusion honesty. |
| `AC-4.1` | `implemented-as-written` | `Section 3.1`–`Section 3.2` (`h-mad/scripts/h_mad_audit_gate.py`) | `_run_design_boundaries_checks` runs before `.gated.json` stamp write; non-zero exit flips `verdict = "FAIL"`, prevents `.gated.json` creation, and preserves the `stamped = ""` mutation anchor. |
| `AC-4.2` | `implemented-as-written` | `Section 2.3` (`should_activate_design_check` Arm 2), `Section 3.2` | Arm 2 inspects unhedged H2 headings against `REQUIRED_SECTIONS["design"]` (or `## Test Boundaries`) and fails closed on unreadable files for renamed/staged/tmp design paths. |
| `AC-4.3` | `implemented-as-written` | `Section 2.3` (`should_activate_design_check` Arm 3), `Section 3.2` | Arm 3 detects paired `.spec.md` via `infer_project_root` or sibling directory even when all 10 bkit H2 headings are stripped, while skipping non-design artifacts (`plan`, `spec`, `impl-plan`). |
| `AC-5.1` | `implemented-as-written` | `Section 5.1`, `Section 6.2` (`TestArchivedDesignCalibration`) | Calibration against the 3 archived design+spec pairs under `--no-exempt`, asserting `TEST-BOUNDARIES: FAIL` (`1`) with `MISSING-SECTION` and wall-clock runtime `< 200ms` per design. |
| `AC-5.2` | `implemented-as-written` | `Section 5.1`, `Section 6.2` (`TestArchivedDesignSyntheticTables`) | Synthetic valid `## Test Boundaries` tables for all 3 archived pairs (`26`, `25`, and `15` active ACs; `4` retired ACs in `hmad-Reliable-execution` excluded) pass with `0` under `--no-exempt` in `< 200ms`. |
| `AC-6.1` | `implemented-as-written` | `Section 5.2`, `Section 6.2` (`TestSeededBrokenFixtures`) | All 5 seeded broken fixture classes (`missing_ac`, `tautological_oracle`, `self_mock`, `placeholder_cell`, `retired_ac`) fail with exit `1` and emit their exact rule code. |
| `AC-6.2` | `implemented-as-written` | `Section 5.3` (`h-mad/tests/mutation-specs/test_boundaries_gate.json`) | Validated by `h_mad_mutation_harness.py --validate-only` (`SPEC-VALID: PASS`) and `run_spec` (`MUTATION-HARNESS: PASS killed=3/3`) with 2 checker mutations and 1 gate call-site bypass mutation. |
| `AC-6.3` | `implemented-as-written` | `## Test Boundaries` (lines 740–771), `Section 6.2` (`TestSelfCompliance`) | This design's own `## Test Boundaries` table covers all 17 active ACs (`AC-1.1`..`AC-6.3`) across 11 rows and is verified by `TestSelfCompliance` (`--no-exempt` -> `0`). |

## Must-fix
None

## Should-fix
None

## Nit
None
