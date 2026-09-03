## Summary

The design is otherwise detailed and tracks the specification, but it expands the specification's stated mock allowance without reconciling the source-of-truth text. It also changes `docsections.json` without scheduling that changed mutation spec for the verification harness, leaving its exact-once anchors and named-RED bindings unproved.

| Spec AC identifiers | Classification |
|---|---|
| AC-1.1–AC-1.9 | implemented-as-written |
| AC-2.1–AC-2.8 | implemented-as-written |
| AC-3.1–AC-3.14 | implemented-as-written |
| AC-4.1–AC-4.6 | implemented-as-written |
| AC-5.1–AC-5.4, AC-5.6 | implemented-as-written |
| AC-5.5 | restated |
| AC-6.1–AC-6.6 | implemented-as-written |

## Must-fix

- AC-5.5 is silently restated on mock policy — the spec says its `os.killpg` monkeypatch is “the one permitted mock in this suite,” whereas the design says “Three named exceptions, all fault injections … via pytest's `monkeypatch`,” including `killpg`, `rmtree`, and `mkdtemp`. This materially broadens the stated test strategy (even though other spec ACs also call for fault injection); reconcile the spec's contradictory wording with the intended bounded exception list before implementation, rather than letting the design override it silently.
- The changed `h-mad/tests/mutation-specs/docsections.json` is not included in the design's verification commands — the design re-points two mutations and changes all four to named-test form, but only runs the new helper and wire specs. This leaves the modified anchors and named-RED attribution unverified, contrary to mutation verification; add a harness invocation for `docsections.json` and require its `ALL_CAUGHT` result.

## Should-fix

None

## Nit

None
