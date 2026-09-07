## Summary
The design covers all 49 source-spec acceptance criteria as written; I found no silent specification narrowing or omission. Two required enforcement claims are not backed by a mutation that isolates the relevant guard/connection, which breaches the base Mutation verification and Connection enforcement invariants.

| Spec AC | Classification |
|---|---|
| AC-1.1 | implemented-as-written |
| AC-1.2 | implemented-as-written |
| AC-1.3 | implemented-as-written |
| AC-1.4 | implemented-as-written |
| AC-1.5 | implemented-as-written |
| AC-1.6 | implemented-as-written |
| AC-1.7 | implemented-as-written |
| AC-1.8 | implemented-as-written |
| AC-1.9 | implemented-as-written |
| AC-2.1 | implemented-as-written |
| AC-2.2 | implemented-as-written |
| AC-2.3 | implemented-as-written |
| AC-2.4 | implemented-as-written |
| AC-2.5 | implemented-as-written |
| AC-2.6 | implemented-as-written |
| AC-2.7 | implemented-as-written |
| AC-2.8 | implemented-as-written |
| AC-3.1 | implemented-as-written |
| AC-3.2 | implemented-as-written |
| AC-3.3 | implemented-as-written |
| AC-3.4 | implemented-as-written |
| AC-3.5 | implemented-as-written |
| AC-3.6 | implemented-as-written |
| AC-3.7 | implemented-as-written |
| AC-3.8 | implemented-as-written |
| AC-3.9 | implemented-as-written |
| AC-3.10 | implemented-as-written |
| AC-3.11 | implemented-as-written |
| AC-3.12 | implemented-as-written |
| AC-3.13 | implemented-as-written |
| AC-3.14 | implemented-as-written |
| AC-4.1 | implemented-as-written |
| AC-4.2 | implemented-as-written |
| AC-4.3 | implemented-as-written |
| AC-4.4 | implemented-as-written |
| AC-4.5 | implemented-as-written |
| AC-4.6 | implemented-as-written |
| AC-5.1 | implemented-as-written |
| AC-5.2 | implemented-as-written |
| AC-5.3 | implemented-as-written |
| AC-5.4 | implemented-as-written |
| AC-5.5 | implemented-as-written |
| AC-5.6 | implemented-as-written |
| AC-6.1 | implemented-as-written |
| AC-6.2 | implemented-as-written |
| AC-6.3 | implemented-as-written |
| AC-6.4 | implemented-as-written |
| AC-6.5 | implemented-as-written |
| AC-6.6 | implemented-as-written |

## Must-fix
- AC-4.5’s registry/detail-line bidirectional pin has no corresponding mutation in the enumerated 35-row `doc_block_exec.json` spec — none mutates a registry remedy row or makes an emitted detail line undocumented. The design claims every guard is mutation-tested, but this load-bearing manifest-integrity guard is only planned green; add isolated, named-test mutations for both directions and require them to be observed RED.
- The new `docsections.py` → `h_mad_doc_block_exec.fence_aware_end` delegation is a connection, but the re-pointed `docsections.json` mutations alter the callee’s fence/heading logic rather than removing that connection with the callee intact. A source assertion and normal tests do not meet Connection enforcement’s required isolated, observed-red wire mutation; add a delegation-wire mutation and named pin (and the applicable negative discrimination) before crediting AC-1.8’s single-source guarantee.

## Should-fix
- Make the timeout drain state machine branch-explicit for a non-`ESRCH` `killpg` failure — the general drain text says a second drain timeout closes pipes then calls `proc.wait()` because the leader was SIGKILLed, while the reap-failure policy correctly says not to wait on an unsignalable child. State and test that the `LAUNCH_FAILED stage=reap` branch never takes that `wait()` path, or it can violate the promised bounded return.

## Nit
- Correct the claim that only two test files import `docsections`: `test_h_mad_wire_registry.py` also imports `titled_section`. The proposed delegation remains compatible, but the cited consumer census is stale.
