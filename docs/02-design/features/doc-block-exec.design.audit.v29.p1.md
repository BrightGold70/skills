AUDIT-doc-block-exec-design-v29-BEGIN
## Summary
The design and plan documents are highly detailed, correctly model the problem, and provide strong invariant compliance. However, there are two cross-document inconsistencies where the Plan has fallen behind the Design regarding mutation counts and explicitly enumerated tests.

## Must-fix
- The Plan's Deliverables section claims a total of 41 mutations (39 source, 2 registry rows), while the Design specifies and enumerates 43 total mutations (41 source, 2 registry). — The Plan carries a stale mutation count that contradicts the Design's exact accounting.
- The Plan's AC-6.4 states that the feature's test additions are bounded by a tuple of "the seven enumerated in the plan," but the Plan only explicitly enumerates five of these named node IDs (four in the FR-6 table, one for the `docsections` delegation). — The Plan promises a fully enumerated list of seven tests but fails to name `test_consumer_calls_the_helper_module_qualified` and `test_only_the_exec_scan_hand_rolls_extraction`, leaving the tuple definition incomplete compared to the Design.

## Should-fix
None

## Nit
- In the Plan's FR-4 Description, `BAD_SUBST` is omitted from the prose list of refusals that exit 0 ("NOT_FOUND, AMBIGUOUS, AMBIGUOUS_HEADING, BAD_INDEX, BAD_TIMEOUT, BAD_INFO, SUBST_MISSING, SUBST_OVERLAP"), though it is correctly included in the Design's list and in the Plan's own AC-4.2.
AUDIT-doc-block-exec-design-v29-END
