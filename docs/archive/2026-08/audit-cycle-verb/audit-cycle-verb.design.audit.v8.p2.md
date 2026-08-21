## Summary
The design is exceptionally rigorous, applying tight signal discipline and defensive checks (e.g., asserting file removals by re-reading, raising operational errors on missing tokens). Its handling of the no-pass path and the runtime assertion for `premise_items` count matching are particularly strong. However, there is one Must-fix related to the testing strategy for `premise_items`, which is a reimplementation of the gate's finding-counting logic and must be tested differentially against the real gate.

### Axis C: Spec Reconciliation
| AC Group | Classification |
|---|---|
| AC-1.1 to 1.4 | `implemented-as-written` |
| AC-2.1 to 2.5 | `implemented-as-written` |
| AC-3.1 to 3.5 | `implemented-as-written` |
| AC-4.1 to 4.6 | `implemented-as-written` |
| AC-5.1 to 5.7 | `implemented-as-written` |
| AC-6.1 to 6.4b | `implemented-as-written` |
| AC-7.1 to 7.5 | `implemented-as-written` |
| AC-8.1 to 8.4 | `implemented-as-written` |
| AC-9.1 to 9.5 | `implemented-as-written` |
| AC-10.1 to 10.5b | `implemented-as-written` |

## Must-fix
- `test_premise_items_match_gate_count` MUST be exempt from the gate stub and run against the real gate — `premise_items` is explicitly described as mirroring the gate's prose fall-back logic, making it a reimplementation of the gate's finding-counting logic. Under the **Reimplementation parity** and **Single-source contract** base invariants, a reimplementation MUST be verified by a differential test asserting identical results against the original implementation. However, the design states "Every other helper test keeps the stub" (except `test_prose_plus_bullet_not_concatenated`). If `test_premise_items_match_gate_count` uses the stub, it only proves that `premise_items` matches the test author's hardcoded stub output, leaving the reimplementation unverified against the real gate's behavior.

## Should-fix
None

## Nit
- The design lists `§6.6 correction` under Components Changed, but does not explicitly confirm the inclusion of the "8 of 8 impl-plan cycles" measurement required by spec AC-9.2. Ensure this specific measurement is included in the actual edit.
