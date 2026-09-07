## Summary
All six functional requirements are implemented-as-written at plan granularity; the reconciliation is below. The plan still leaves heading identity ambiguous and states a load-bearing preamble premise without the controlled, cited evidence the base invariant requires.

| Requirement | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |

## Must-fix
- FR-1 does not define or test duplicate-heading handling — the plan promises to “Address a block unambiguously” by “document, heading, and explicit tag,” but its only ordinal is for “a heading [that] holds more than one tagged block.” Two same-level ATX headings with the same text therefore have the same stated address; an implementation that selects the first section can execute a tagged block from the wrong section. This is not theoretical: `h-mad/invariants.example.md` already has duplicate `### Unified-facade routing` and `### Data-source priority` headings. Define a refusal or an unambiguous heading locator, add an AC/test/mutation for it, and update the spec if the address shape changes; the opt-in tag cannot repair an ambiguous section selector.
- The fixture-preamble decision lacks the required controlled evidence in the plan — it calls the preamble “load-bearing” and attributes the no-preamble failure to strict bash’s `COLLECT_OUT: unbound variable`, yet its Measurements section cites only fence/extractor counts and records no command/output for that causal claim. Base `Assumption verification` requires cited throwaway evidence, and its causal clause requires the pair. Add the observed same-artifact pair: current gate block without the preamble (unbound-variable refusal) versus with the real collector preamble (delivered case reaches `GATE: PASS`; missing case emits `report_not_collected` without `GATE:`), including the commands and outputs that establish the preamble rather than another fixture difference caused the result.

## Should-fix
None

## Nit
None
