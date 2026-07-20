# Impl-Plan Audit v1 — worktree-parallel-multi-module-tdd

Reviewer: agy (Gemini 3.1 Pro High), Reviewer.adversarial_consistency (writing-plans focus). Cycle 1.

## Summary
The implementation plan accurately translates the paired design into concrete bash code blocks and acceptance criteria. It fails the "exact file paths" requirement by offering a choice of test files for Task 2, and drifts slightly from the design's testing strategy regarding the engage-conjunction assertion.

## Must-fix
- Task 2 test file path is ambiguous (`h-mad/tests/test_hmad_dispatch.py` OR a new `h-mad/tests/test_fanout_docs.py`) — impl plans must give exact paths with no "OR"; the implementing agent should not have to make a structural choice. Select exactly one.

## Should-fix
- Task 2 AC-4.5 drops the design's `test_skill_documents_fanout_conjunction` requirement — the design asserts the engage-conjunction is present in the docs; AC-4.5 asserts `worktree-create` + serial fallback instead. Update AC-4.5 to include the engage-conjunction assertion to match the design test plan.

## Nit
None
