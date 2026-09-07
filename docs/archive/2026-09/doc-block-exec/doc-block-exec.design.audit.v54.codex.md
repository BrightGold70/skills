## Summary

Axis C reconciliation finds every spec acceptance criterion implemented as written by the design; the compact table classifies each identifier below. The design is internally consistent, but the paired plan and implementation plan still prescribe the pre-`find_heading` `docsections.titled_section` wiring, leaving the newly required section-start delegation unimplementable and unpinned.

| Spec ACs | Classification |
|---|---|
| AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-1.7, AC-1.8, AC-1.9 | implemented-as-written |
| AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5, AC-2.6, AC-2.7, AC-2.8 | implemented-as-written |
| AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5, AC-3.6, AC-3.7, AC-3.8, AC-3.9, AC-3.10, AC-3.11, AC-3.12, AC-3.13, AC-3.14 | implemented-as-written |
| AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5, AC-4.6 | implemented-as-written |
| AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5, AC-5.6 | implemented-as-written |
| AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5, AC-6.6 | implemented-as-written |

## Must-fix

- The paired plan and implementation plan retain the deleted-local-regex implementation for `docsections.titled_section`: they prescribe `text[match.end():_dbe.fence_aware_end(text, match.end(), level)]`, while this design deletes that regex and requires `_dbe.find_heading(text, heading)` to supply both `start` and `level` before calling `_dbe.fence_aware_end`. `match` and `level` therefore no longer exist, and following the written plan omits the required section-start connection; update the exact pseudocode/WIRE to call `find_heading`, preserve the existing loud missing-heading path, then pass its returned `(start, level)` to the bounder.
- The implementation plan's `test_docsections_delegates_to_the_authoritative_bounder` scaffold and WIRE-PIN only fake/record `_dbe.fence_aware_end`; the design assigns that same pin to `docsections-heading-lookup-reverted` and requires it to spy both `_dbe.find_heading` and `_dbe.fence_aware_end`. A revert to the local `re.search` heading lookup would still satisfy the current scaffold, so the declared connection mutation has no discriminating test, violating Connection enforcement and Mutation verification. Make the fake/spy expose and assert one `find_heading` call as well as the bounder call, and align the plan's mutation description with that two-edge wire.

## Should-fix

None

## Nit

None
