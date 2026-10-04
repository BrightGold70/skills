## Summary
The implementation plan is extremely thorough and successfully addresses the prior audit's findings, perfectly mapping ACs to reject-direction mutations and establishing sound testing practices. A single contradiction remains where a newly added mutation targets a test that the test-runner's filter explicitly excludes, which will silently break the mutation suite.

## Must-fix
- T6 test selection filter excludes a targeted test — The mutation spec's `"command"` array uses `"-k", "test_tail_"` to run the suite. However, the newly added `skill-md-frontmatter-renamed` mutation targets `tests/test_hmad_dispatch.py::test_skill_md_frontmatter_unchanged`. Because the test name lacks the `test_tail_` prefix, `pytest` will skip it, causing the mutation to "survive" (or fail the harness) and breaking the Test Discrimination invariant. Fix: Either rename the T5 test to `test_tail_skill_md_frontmatter_unchanged`, or widen the `-k` selector (e.g., `"test_tail_ or test_skill_md"`), and remove the contradictory T6 prose claiming "The three T5 names fall outside the selection deliberately — no mutation targets them".

## Should-fix
None

## Nit
None
