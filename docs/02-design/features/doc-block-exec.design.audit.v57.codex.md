## Summary

The design covers every source-spec acceptance criterion as written; the only blocking issue is inconsistent evidence for the load-bearing CommonMark grammar. The spec identifies the reference probe as `markdown-it-py 4.2.0`, while the design and paired plan identify the same grammar corpus as `markdown-it-py 2.2.0`, so the cited verification cannot be treated as one reproducible observation.

| Spec ACs | Classification |
|---|---|
| AC-1.1–AC-1.9 | implemented-as-written |
| AC-2.1–AC-2.8 | implemented-as-written |
| AC-3.1–AC-3.14 | implemented-as-written |
| AC-4.1–AC-4.6 | implemented-as-written |
| AC-5.1–AC-5.6 | implemented-as-written |
| AC-6.1–AC-6.6 | implemented-as-written |

## Must-fix

- The cited CommonMark grammar evidence conflicts across the source documents — the spec says the reference-port probe used `markdown-it-py 4.2.0`, whereas the design and plan say the 14-case scanner corpus used `markdown-it-py 2.2.0`. The opener/closer, indentation, de-indentation, and ATX-heading rules are load-bearing selection boundaries; two incompatible provenance statements mean the claimed observed output is not reproducible evidence for either. Re-run the corpus and tagged-fence probe, then cite one actual version, command, and output consistently in spec, design, and plan; until then this violates the base Assumption verification invariant.

## Should-fix

None

## Nit

None
