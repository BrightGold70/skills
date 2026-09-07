## Summary

All 49 acceptance criteria are covered in their spec form; the audit found three invariant-level evidence or test-design gaps and two measurement contradictions. Read-only filesystem restrictions prevented writing the report and completion marker.

Evidence: 13 files opened, 12 greps run.

| Acceptance criteria | Classification |
|---|---|
| AC-1.1–1.9 | implemented-as-written |
| AC-2.1–2.8 | implemented-as-written |
| AC-3.1–3.14 | implemented-as-written |
| AC-4.1–4.6 | implemented-as-written |
| AC-5.1–5.6 | implemented-as-written |
| AC-6.1–6.6 | implemented-as-written |

## Must-fix

- The exhaustive substitution search lacks its executable derivation — independently reconstructed enumeration reproduces 13,104 cases and 194 additional refusals, but neither the document nor its four committed probes supplies that search. Publish the command and output to satisfy **Behavioural premises carry their command**.
  quote: docs/02-design/features/doc-block-exec.design.md › `13,104 (text, pair) cases, run rather than reasoned — neither scan ever missed a case where a key`

- The negative-timeout premise is false — on Python 3.11.8, the controlled pair returned `TimeoutExpired` for `communicate(timeout=-1)` and success for `timeout=1`. Correct the claimed exception and publish the paired probe; the existing timeout-validation requirement remains appropriate.
  quote: docs/02-design/features/doc-block-exec.design.md › `clean up, so the refusal can neither leak a directory nor need the read-back — `communicate(timeout=-1)` raises`
  quote: docs/02-design/features/doc-block-exec.design.md › `ValueError` only after the child exists, and `inf` is no bound at all.

- The specified cleanup-error fake does not discriminate `cleanup-errors-ignored` — an injected function that raises still raises when called with `ignore_errors=True`; my paired calls retained the identical injected error on both paths. Specify a fake that models suppression when that keyword is true, or another discriminating fixture, before claiming this mutation is killed. Otherwise the **Test discrimination** invariant is unmet.
  quote: docs/02-design/features/doc-block-exec.design.md › `` `test_cleanup_failure_carries_the_os_error`, which fault-injects an `rmtree` that raises and ``
  quote: docs/02-design/features/doc-block-exec.design.md › `` asserts `cleanup_error` is that error — under the mutation nothing is recorded, the read-back ``

## Should-fix

- The earlier AC census contradicts the new coverage paragraph — executing its published command verbatim returns **0**, not 7. Remove or historically stamp the earlier reading and its assertion that the seven identifiers remain unlisted; the expanded coverage check correctly returns 49 covered.
  quote: docs/02-design/features/doc-block-exec.design.md › `Over the whole document it prints **7** of the **49** the spec carries at `cf3a862`: seven ACs`
  quote: docs/02-design/features/doc-block-exec.design.md › `**The seven are deliberately not listed here.** Writing them out would put each identifier into`

- The current ordinal-screen series retains a stale value — the published `$P` predicate returns **40** over the shipped head, agreeing with the nearby headline but contradicting the series’ 37. Reconcile the two current readings.
  quote: docs/02-design/features/doc-block-exec.design.md › `` head is published beside that stamp rather than withheld — `$P` **40** and `$W` **12**, both ``
  quote: docs/02-design/features/doc-block-exec.design.md › `` and `fbc2ea0`, 30 at `cb4fe99` and `cac6edc`, and 37 on the ``

## Nit

None
