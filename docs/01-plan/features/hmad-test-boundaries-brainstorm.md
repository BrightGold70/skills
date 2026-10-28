# Brainstorm: hmad-test-boundaries

## Executive Summary
Add a first-class `## Test Boundaries` table (including explicit oracle fields) to H-MAD design documents, enforced deterministically at the Phase 4 design audit gate by a standalone validator script and reviewed for oracle independence and boundary placement during Phase 4 design audits.

## Problem Statement
H-MAD requires testable acceptance criteria, a design Test Strategy, mock boundaries, meaningful RED evidence, and checks against vacuous tests, but it does not make two things first-class, written down before Phase 5, and checked by a script:
1. **The test boundary**: which public interface a test drives and observes, and what it does *not* establish.
2. **The oracle**: where the expected result comes from. When an expected value is computed the same way the implementation computes it ("a test helper that re-implements cannot fail"), tests stay green against broken code.

Prose-only rules in `SKILL.md` or templates decay without a deterministic script enforcing them at the gate.

## Proposed Approach
1. Add a `## Test Boundaries` section to the Phase 4 design template in `h-mad/references/inline-protocols.md`, with a five-column markdown table:
   - `Public interface` — where behaviour is exercised and observed (or `verified by: audit | live-run | operator | doc-review` for non-test rows)
   - `Acceptance criteria` — which spec `AC-X.Y` ids this row proves
   - `Expected result source` — spec, independent worked example, known-good fixture, or another named oracle (or the proving artifact path/name for a non-test row)
   - `Mocked dependencies` — the external or system boundary substituted, or `none`
   - `Exclusions` — important behaviour this row does not establish
2. Build a standalone deterministic checker (`h-mad/scripts/h_mad_test_boundaries_check.py`) that runs alongside `h_mad_doc_shape_check.py` (without modifying the bkit-mirrored `REQUIRED_SECTIONS` in `h_mad_doc_shape_check.py`) and is wired into the Phase 4 design audit gate (`h_mad_audit_gate.py` / `hmad-dispatch.sh`).
3. Enforce in the checker:
   - Presence of `## Test Boundaries` and a well-formed 5-column table for non-exempt features.
   - No empty cells and no placeholder values (`TBD`, `TODO`, `n/a`, `N/A`, `-`, `...`, `see code`, etc.).
   - Disallow tautological oracle sources (`implementation`, `the code`, `computed`, `production code`, `same function`, etc.) in `Expected result source`.
   - Every active `AC-X.Y` in `docs/01-plan/features/<feature>.spec.md` appears in at least one row (either a test row or an explicit non-test row `verified by: audit | live-run | operator | doc-review` that names the proving artifact).
   - Exemption for pre-existing/archived/in-flight features created before the gate ships so existing features are not blocked retroactively.
4. Update the Phase 4 design audit prompt (`h-mad/scripts/h_mad_assemble_audit.py` / `h-mad/agents/doc-auditor.md`) so auditors challenge oracle independence and boundary placement.
5. Calibrate the checker against 2–3 archived, already-passed designs augmented with `## Test Boundaries` tables as test fixtures, plus seeded broken copies (missing table, placeholder cell, uncovered AC, `implementation` as an oracle, non-test row naming no artifact).

## Alternatives Considered
- **Confirmation gate at Phase 5 entry**: Matt Pocock's skill pauses before testing to confirm boundaries with the user; rejected because H-MAD Phase 5 is autonomous and operator checkpoints end at Phase 4.
- **Modifying `REQUIRED_SECTIONS` inside `h_mad_doc_shape_check.py`**: Rejected because `TestMirrorFidelity` diffs `REQUIRED_SECTIONS` against bkit's live validator (`bkit-claude-code`), so H-MAD-specific sections must live in a separate H-MAD layer.
- **Placing `## Test Boundaries` in the Spec (`.spec.md`) instead of Design (`.design.md`)**: Rejected because the spec defines *what* (`FR-N` / `AC-N.M`) before module boundaries and public interfaces exist; the design defines the public interfaces and test strategy that cross-reference the spec's AC ids.

## Risks & Mitigations
| Risk | Likelihood | Mitigation |
|---|---|---|
| Retroactive breakage of archived or in-flight features lacking `## Test Boundaries` | M | Gate enforcement on feature creation / opt-in cutoff or explicit exemption check so pre-existing features pass without retroactive edits |
| False-positive rejection of legitimate oracle descriptions | M | Use word-bounded / normalized matching on the disallowed oracle blocklist and calibrate on 2–3 archived designs before wiring |
| Spec AC retirement (`~~AC-3.7~~` or `AC-3.7 (retired)`) causing false "uncovered AC" failures | M | Parse only active (non-struck-through, non-retired) AC ids from `.spec.md` |

## Dependencies
- `h-mad/scripts/h_mad_doc_shape_check.py` (co-exists beside it; must preserve `TestMirrorFidelity`)
- `h-mad/scripts/h_mad_audit_gate.py` and `h-mad/scripts/h_mad_assemble_audit.py` (Phase 4 design audit gate & prompt)
- `h-mad/references/inline-protocols.md` (Phase 4 design template)

## Open Questions
- None — all operator scope decisions and `*(my call)*` defaults were approved on 2026-10-28 (`docs/superpowers/specs/2026-10-27-hmad-test-boundaries-design.md`).

## Version History
- v1.0: Initial brainstorm draft derived from operator-approved scope (`docs/superpowers/specs/2026-10-27-hmad-test-boundaries-design.md`).
