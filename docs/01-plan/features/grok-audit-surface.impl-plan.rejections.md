# grok-audit-surface — impl-plan audit rejections ledger

Findings rejected after their premise failed against the tree. Never passed as `--gated`.

## Cycle 1 · surface agy (p1) · audited v1.1 (sha 5490674354db…)

- **Should-fix: "Task 17's expected RED/GREEN counts for `h-mad/tests/test_grok_fallback_docs.py` (`RED: 2 failed, 6 passed` / `GREEN: 8 passed`) are off by one after Task 16 adds `test_grok_runtime_documents_audit_surface_s1`."**
  - Verdict: REJECTED. The quotes are fabricated.
  - Evidence (orchestrator re-ran this at v1.2 on 2026-10-19; the author ran it at v1.1):
    - `grep -c 'Expected pytest result' docs/01-plan/features/grok-audit-surface.impl-plan.md` printed 0.
    - `grep -c 'test_grok_runtime_documents_audit_surface_s1' …impl-plan.md` printed 0.
    - The test name appears only in `…impl-plan.audit.v1.p1.md`, the report itself.
  - Carry item 8 is a measurement acknowledgement and adds no test.
  - Task 17's RED split is stated over its own 4 new nodes, not over `test_grok_fallback_docs.py`.
