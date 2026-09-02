## Summary
The implementation plan is detailed and mostly consistent with the paired design, with the collector, gate, CLI, wrapper, docs, and mutation-spec work ordered coherently. I found no hard invariant breach, but two wording defects could misdirect implementation of the grammar corpus and mutation-spec verification.

## Must-fix
None

## Should-fix
- AC-3.5a still says every non-transport audit name in a fixture covering AC-3.5 names must match `_VERSION_RE` — the paired spec scopes that assertion only to docs audit-artifact names, while AC-3.5 includes `f.report.md` and `<tmp>/x.md`; implemented literally, the fixture would either fail or force the implementer to ignore the plan wording.
- Task 6 says shape and named-test existence are proven by the harness itself — this contradicts AC-6.3a and the harness behavior described in the same plan, where `_mechanism` and required `test` presence need the explicit `test_mutation_spec_shape` check; leaving the false verifier claim invites a weaker mutation-spec implementation.

## Nit
- Task 6 has two consecutive `**Acceptance Criteria**` labels around the mutation table; harmless, but removing the duplicate would make the section easier to scrape and review.
