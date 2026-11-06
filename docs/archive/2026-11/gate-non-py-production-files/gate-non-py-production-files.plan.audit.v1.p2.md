AUDIT-gate-non-py-production-files-plan-v1-BEGIN
## Summary
The plan accurately captures the 11 functional requirements from the spec, the existing parser/judge/gate architecture, and the wire-pin `ungated` retirement across `h-mad/`. However, its FR-10 prose inventory (Deliverables D9, Measurements M6, Risks R8) omits `h-mad/references/phase5-substeps.md` (which `doc_text(SKILL)` restores into `SKILL.md` and which states `Test files, docs, config, and shell are never gated; only production `.py`.`) and its pinning test `test_skill_states_the_docs_first_component_rule` in `h-mad/tests/test_h_mad_tdd_gate_docs.py`.

Evidence: 27 files opened, 19 greps run.

| Spec FR | Plan Disposition | Notes |
| --- | --- | --- |
| FR-1 | implemented-as-written | Covered in Requirements FR-1, Goals, Deliverables D2, Measurements M1. |
| FR-2 | implemented-as-written | Covered in Requirements FR-2, Goals, Deliverables D3, Measurements M2, Risks R7. |
| FR-3 | implemented-as-written | Covered in Requirements FR-3, Goals, Deliverables D4, Measurements M3, Risks R1/R4/R12. |
| FR-4 | implemented-as-written | Covered in Requirements FR-4, Deliverables D4, Measurements M3, Risks R9. |
| FR-5 | implemented-as-written | Covered in Requirements FR-5, Deliverables D5, Measurements M4, Risks R2/R5. |
| FR-6 | implemented-as-written | Covered in Requirements FR-6, Deliverables D6, Measurements M5, Risks R2/R3/R5. |
| FR-7 | implemented-as-written | Covered in Requirements FR-7, Deliverables D7, Measurements M5, Risks R2/R3/R5. |
| FR-8 | implemented-as-written | Covered in Requirements FR-8, Deliverables D4/D5/D6/D7, Risks R3. |
| FR-9 | implemented-as-written | Covered in Requirements FR-9, Deliverables D5/D6/D7, Risks R11. |
| FR-10 | implemented-as-written | Covered in Requirements FR-10, Deliverables D9, Measurements M6, Risks R8 (prose surface inventory incomplete; see Must-fix). |
| FR-11 | implemented-as-written | Covered in Requirements FR-11, Deliverables D1, Measurements M4/M5, Risks R6/R13. |

## Must-fix
- Deliverables D9, Measurements M6, and Risks R8 omit `h-mad/references/phase5-substeps.md` (restored into `h-mad/SKILL.md` by `doc_text(SKILL)`) and `test_skill_states_the_docs_first_component_rule` in `h-mad/tests/test_h_mad_tdd_gate_docs.py` — `h-mad/references/phase5-substeps.md:230` states the exact superseded rule (`Test files, docs, config, and shell are never gated; only production `.py`.`, and `:214` states `refuses Claude's production-\`.py\` write`), which `h-mad/tests/test_h_mad_tdd_gate_docs.py:124-131` pins verbatim via `anchor = "Test files, docs, config, and shell are never gated; only production `.py`."`. Leaving `phase5-substeps.md` out of D9 violates FR-10 (`Every h-mad prose surface that states which files the Phase-5 write gates judge is updated to the rule this spec ships`) and project invariant `## Skill manifest integrity` (`SKILL.md` corpus continues to claim shell is never gated and only production `.py` is gated); conversely, updating `phase5-substeps.md:230` causes `test_skill_states_the_docs_first_component_rule` in `test_h_mad_tdd_gate_docs.py` (which AC-10.2 requires to pass as a whole module) to fail without the plan establishing regression provenance under base invariant `## Regression provenance` (`When a change makes an existing test fail, the plan or design MUST establish whether that test asserts current behaviour that the change is fixing before proposing to edit it`).
  class: build
  quote: docs/01-plan/features/gate-non-py-production-files.plan.md › `- **D9 — Prose and doc-derived test (`h-mad/references/codex-implementer-prompt.md`, `h-mad/references/codex-runtime.md`, gate headers in `h-mad/hooks/h-mad-tdd-gate.sh` and `h-mad/hooks/h-mad-codex-tdd-gate.py`, `h-mad/tests/test_h_mad_tdd_gate_docs.py`).** Update the prose surfaces that state which files the Phase-5 write gates judge, and update `test_codex_runtime_names_the_unconditionally_allowed_classes` to derive the doc/data suffix set and the listed-non-`.py` rule from the updated prose (FR-10, AC-10.1, AC-10.2).`
  quote: docs/01-plan/features/gate-non-py-production-files.plan.md › `- **M6 — Prose surfaces (`h-mad/references/codex-implementer-prompt.md`, `h-mad/references/codex-runtime.md`, `h-mad/tests/test_h_mad_tdd_gate_docs.py`).** `codex-implementer-prompt.md:25` says "Non-\`.py\` files and \`test_*.py\` / \`*_test.py\` / \`conftest.py\` are allowed unconditionally"; `:37` says "Because \`.json\` is not \`.py\`, creating or editing a mutation spec is never blocked by the TDD gate". `codex-runtime.md:149` says "Test files (\`test_*.py\`, \`*_test.py\`, \`conftest*.py\`) and non-\`.py\` files (\`.md\`, \`.json\`, \`.sh\`, …) are allowed unconditionally — no pytest record is needed to write them." `test_h_mad_tdd_gate_docs.py:92-121` (`test_codex_runtime_names_the_unconditionally_allowed_classes`) locates that sentence via the marker `"allowed unconditionally"` and asserts `".md"`, `".json"`, `".sh"` appear in it.`
  quote: docs/01-plan/features/gate-non-py-production-files.spec.md › `- **FR-10.** Every h-mad prose surface that states which files the Phase-5 write gates judge is updated to the rule this spec ships:`
  quote: h-mad/references/phase5-substeps.md › `Test files, docs, config, and shell are never gated; only production `.py`.`
  quote: h-mad/tests/test_h_mad_tdd_gate_docs.py › `anchor = "Test files, docs, config, and shell are never gated; only production `.py`."`

## Should-fix
None

## Nit
None
AUDIT-gate-non-py-production-files-plan-v1-END
