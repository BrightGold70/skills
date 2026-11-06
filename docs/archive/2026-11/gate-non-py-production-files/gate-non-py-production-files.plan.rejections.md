# Rejections ledger — gate-non-py-production-files plan audits

One entry per rejected (or partly rejected) finding. Never passed to the gate as `--gated`.

## Cycle 1 — agy (`plan.audit.v1.p2.md`), must-fix on D9/M6
- **Claim rejected (evidence only):** the finding quotes two plan bullets (`- **D9 — Prose and doc-derived test …`, `- **M6 — Prose surfaces …`) and a test `test_codex_runtime_names_the_unconditionally_allowed_classes` at `test_h_mad_tdd_gate_docs.py:92-121`. Neither quoted bullet occurs in plan v1.1 (sha256 4293433c…), and `git grep -n test_codex_runtime_names_the_unconditionally_allowed_classes` at e4979ecd matches only the audit report itself.
- **Finding kept:** its substance — `h-mad/references/phase5-substeps.md:230` states the superseded rule and `test_skill_states_the_docs_first_component_rule` pins it verbatim — was verified independently by the orchestrator and is answered by spec v1.3 FR-10.
- Origin tag for the substance: `new-consistency` (recorded in the origins sidecar).
