AUDIT-doc-block-exec-plan-v77-BEGIN
## Summary

Plan audit: Reviewer.adversarial_consistency. The audit verified measurements, counts, and assertions in the plan document. The review identified one stale/incorrect measurement citation for a command count. Additionally, a full test suite run discovered a failing test in the repository.

## Must-fix

- The plan contains an incorrect measurement citation for the number of `_gate_bash_block` callers. It asserts the command output is 3 at `335f535`, but the command returns 4 because the pattern matches the function definition itself (`def _gate_bash_block() -> str:`).
  quote: docs/01-plan/features/doc-block-exec.plan.md › `    (Verified at \`335f535\`: \`git grep -c '_gate_bash_block(' -- h-mad/tests/test_h_mad_collect_report_docs.py\``
- A failing test was found during the repository suite execution: `test_control_todays_impl_plan_dropped_the_six_stale_SKILL_pins` in `h-mad/tests/test_h_mad_precheck_doc.py` fails with an assertion error (`assert 'SKILL.md:' not in ...`).

## Should-fix

None.

## Nit

None.
AUDIT-doc-block-exec-plan-v77-END
