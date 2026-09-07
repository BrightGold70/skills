## Summary
The plan is detailed and aligns on the major task boundaries, paths, wire pins, and verification commands. One mutation binding is internally inconsistent with the paired design, so the promised one-killer-per-row contract cannot currently be implemented unambiguously.

## Must-fix
- `duplicate-heading-takes-first` has two designated killers in the paired design, while this plan requires exactly one full-node-ID `test` key and asserts no other row names two tests — the design matrix names both `test_duplicate_headings_refuse` and `test_bare_form_duplicate_headings_refuse`, but the implementation plan never selects one canonical key or demotes the other to regression-only. This makes the mutation spec's required binding ambiguous and contradicts the plan's claimed sweep; choose and state one full node ID in both documents, with the other explicitly a regression test.

## Should-fix
- The Task 1 `docsections-local-bounder-restored` rationale says its two restored bodies are verbatim from today's `docsections.py`, but today's second body is an inline `re.search` in `titled_section`, not the introduced `_find_heading` function. The replacement is viable, but the literal-source claim should be corrected (or the replacement reshaped) so future anchor/revert review is not based on a false provenance assertion.

## Nit
None
