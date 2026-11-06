AUDIT-gate-non-py-production-files-plan-v2-BEGIN
## Summary
The plan addresses every functional requirement as written, including the corrected replay base in spec v1.4. The AC census reproduces `ACS: OK count=55 frs=11`, and the replay parser result, blob SHA and base SHA reproduce; two base-invariant gaps remain.

Evidence: 20 files opened, 18 greps run.

| Requirement | Axis C classification | Plan coverage |
|---|---|---|
| FR-1 | implemented-as-written | D1, D3, D10 |
| FR-2 | implemented-as-written | D1–D3 |
| FR-3 | implemented-as-written | D4, D7, D8, D10, D11 |
| FR-4 | implemented-as-written | D5, D10 |
| FR-5 | implemented-as-written | D6, D10 |
| FR-6 | implemented-as-written | D7, D10 |
| FR-7 | implemented-as-written | D8, D10 |
| FR-8 | implemented-as-written | D4, D6–D8, D10 |
| FR-9 | implemented-as-written | D11, D12, D14 |
| FR-10 | implemented-as-written | D9 |
| FR-11 | implemented-as-written | D6–D8, D10, D11, D13 |

## Must-fix
- Require connection-only mutation verification for each host in D11 — the named AC-3.1 control mutates the shared matcher, whereas the base Connection enforcement invariant requires removing the connection with the callee intact and forcing the connection unconditionally. Explicitly require both host-local mutations, verify they landed, and observe the positive and negative tests fail respectively; the generic promise of a mutant for every guard does not specify these required controls.
  class: build
  quote: docs/01-plan/features/gate-non-py-production-files.plan.md › `AC-3.1's per-host mutation, each host run alone, is the control for that.`
  quote: docs/01-plan/features/gate-non-py-production-files.spec.md › `A mutation that makes that function always return "not listed" turns AC-5.1, AC-6.1 and AC-7.1 from DENY to ALLOW on all three hosts.`
  quote: h-mad/invariants.base.md › `Mutate the connection in **both directions**: remove it → the wire test must fail; force it to fire`
- Publish M12's complete parser probe command beside its result — it supplies only an interpreter prefix and a description of the call. I independently reproduced the stated Task fields, but the base Behavioural premises carry their command invariant requires the exact runnable command in the document; recording it changes evidence, not implementation.
  class: measurement
  quote: docs/01-plan/features/gate-non-py-production-files.plan.md › ``a read-only `python3 -I -c` call of `_parse_tasks` on that file gives Task 1``
  quote: h-mad/invariants.base.md › `runnable, beside the observed output. An output recorded without its command is not`

## Should-fix
None

## Nit
None
AUDIT-gate-non-py-production-files-plan-v2-END
