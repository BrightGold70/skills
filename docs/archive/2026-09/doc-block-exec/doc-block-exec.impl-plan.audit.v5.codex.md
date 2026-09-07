## Summary
The plan is unusually concrete and has strong task-level wire pins, mutation coverage, and transport guidance. One Task 1 wire-revert claim is internally impossible because that mutant necessarily trips a new helper-suite source guard.

## Must-fix
- Task 1's `docsections-delegation-reverted` mutant is required to restore a local old fence toggle while the plan also requires `test_docsections_has_no_second_bounder` to reject any marker-run scanning in `docsections.py`; that test will fail on the mutant's `startswith("```")` toggle, so the stated 5e condition that `test_h_mad_doc_block_exec.py` stays green cannot be met. — This makes the specified wire-revert verification internally contradictory and prevents it from demonstrating the claimed isolated connection failure; revise the mutation/verification claim so the intended additional source-guard failure is allowed, or use a genuinely wire-only revert that does not recreate scanner logic.

## Should-fix
- Task 5 says the Second-surface fence is "today at `SKILL.md:1845`", but the current fence begins at `h-mad/SKILL.md:1809` (the heading is at :1804). — The semantic anchor is clear, but the stale locator undermines the plan's otherwise exact editing guidance.

## Nit
None
