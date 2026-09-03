## Summary
The design covers all 49 specification acceptance criteria as written; the only blocking issue is that three explicitly named FR-6 guard tests have no mutation binding, contrary to the mutation-verification invariant. Axis C reconciliation follows.

| Spec ACs | Classification |
|---|---|
| AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-1.7, AC-1.8, AC-1.9 | implemented-as-written |
| AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5, AC-2.6, AC-2.7, AC-2.8 | implemented-as-written |
| AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5, AC-3.6, AC-3.7, AC-3.8, AC-3.9, AC-3.10, AC-3.11, AC-3.12, AC-3.13, AC-3.14 | implemented-as-written |
| AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5, AC-4.6 | implemented-as-written |
| AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5, AC-5.6 | implemented-as-written |
| AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5, AC-6.6 | implemented-as-written |

## Must-fix
- The FR-6 wire table explicitly marks `test_exec_block_scan_performs_no_execution`, `test_consumer_calls_the_helper_module_qualified`, and `test_only_the_exec_scan_hand_rolls_extraction` as “(no mutation)”. These are load-bearing guards for the deliberate :412 exemption and spy observability, but none has a named mutant/test binding; this breaches the base Mutation verification invariant. Add mutation-spec rows that respectively make :412 execute, replace the module-qualified import/call form, and widen the remaining hand-rolled extraction, each verified RED by its named test.

## Should-fix
None

## Nit
None

