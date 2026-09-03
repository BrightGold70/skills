## Summary
The design meticulously translates the plan's requirements, maintaining strict alignment on the exit code partition, process group reaping, and substitution contracts. However, it drops the two specific tests required by the plan to verify the bounder's handling of tilde and indented fences.

## Must-fix
- The design drops the two `fence_aware_end` tests specifically required by the plan (`test_bounder_ignores_a_heading_inside_a_tilde_fence` and `test_bounder_ignores_an_indented_literal_fence`), binding the `tilde-fence-not-tracked` and `indented-opener-accepted` mutations to extractor tests instead (`test_tag_quoted_inside_a_tilde_fence_is_not_an_opener` and `test_indented_literal_tag_is_not_a_candidate`). Since `fence_aware_end` is exported for `docsections` to use as a section bounder, its behavior on headings inside tilde/indented fences must be explicitly tested as required by the plan, not just the extractor's tag-skipping behavior.

## Should-fix
- The docstring for `fence_aware_end` in the API section only mentions "skipping fenced blocks with backtick-run tracking", omitting the tilde-fence and 0–3 space indentation rules that the plan explicitly specifies for its contract. It should reflect the full CommonMark rule as defined in the plan.

## Nit
None
