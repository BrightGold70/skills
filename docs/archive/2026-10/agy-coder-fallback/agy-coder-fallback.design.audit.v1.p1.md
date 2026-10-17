AUDIT-agy-coder-fallback-design-v1-BEGIN
## Summary

The design needs corrections to path enforcement, review attribution, and mutation discrimination, plus the spec reconciliation recorded below. Targeted pytest reported `2 passed, 1 error`: teardown could not execute sandbox-blocked `ps`; the repository remains unchanged.

Evidence: 18 files opened, 13 greps run.

| Acceptance criterion | Classification |
|---|---|
| AC-1.1 | restated |
| AC-1.2 | implemented-as-written |
| AC-2.1 | implemented-as-written |
| AC-2.2 | implemented-as-written |
| AC-3.1 | implemented-as-written |
| AC-3.2 | implemented-as-written |
| AC-4.1 | restated |
| AC-4.2 | implemented-as-written |
| AC-5.1 | implemented-as-written |
| AC-5.2 | implemented-as-written |
| AC-6.1 | implemented-as-written |
| AC-7.1 | implemented-as-written |
| AC-7.2 | implemented-as-written |
| AC-8.1 | implemented-as-written |
| AC-8.2 | implemented-as-written |
| AC-9.1 | restated |
| AC-9.2 | implemented-as-written |
| AC-9.3 | implemented-as-written |
| AC-9.4 | implemented-as-written |
| AC-X | restated |

## Must-fix

- AC-1.1 is restated as a narrower timestamp domain — FR-1 requires the RFC 3339 profile, while the design explicitly refuses its valid leap-second case. A controlled execution of the proposed predicate accepted `2016-12-31T23:59:59Z` and refused `2016-12-31T23:59:60Z`. Either support the specified domain or amend FR-1/AC-1.1 to authorize this restriction; recording it as a design residual does not reconcile the spec.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.spec.md › `` `date-time` profile (`YYYY-MM-DDTHH:MM:SS[.fraction]` then `Z` or `±HH:MM`). ``
  quote: docs/02-design/features/agy-coder-fallback.design.md › `RFC 3339 admits a leap second (a seconds field of 60).`

- AC-4.1's production-write guarantee is weakened by the singular target classification — the existing identity module returns all same-parent hard-link names, and the Codex gate checks every name. With a real `src/test_a.py` hard-linked to `src/z.py`, the probe returned `names=('test_a.py', 'z.py')`: classifying only the canonical `target` returned non-production, while the existing all-name policy identified `z.py` as production. Specify iteration over `Identity.names`, including the outside-root Python prohibition, and add the mixed-name regression fixture to the agy gate.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.spec.md › ``a production `.py` without a failing test → deny, with a judge kind;``
  quote: docs/02-design/features/agy-coder-fallback.design.md › `` `_is_production_python(relative)` decides. ``

- AC-4.1's outside-root allowances conflict with the prescribed allowance-file check — `_is_shell_allowance` currently calls `candidate.relative_to(root)` without handling an outside-root candidate. Executing it on a canonical `/tmp/audit-report.txt` raised `ValueError`. Calling this byte-for-byte moved helper before the containment branch therefore produces `judge-error`, preventing the promised non-Python `/tmp` and artifact-directory allowances. Check root containment first, or make the shared helper explicitly safe for outside-root identities, and test both exception roots through the full gate.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.spec.md › `` `/tmp` and `artifactDirectoryPath` non-`.py` → allow, and `.py` there → deny. ``
  quote: docs/02-design/features/agy-coder-fallback.design.md › ``a write to the allowance file denies, through `_is_shell_allowance`;``

- AC-9.1 is restated without the required three-agent prompt-equivalence test — the design's stated satisfaction is the sweep and existing pins; it never specifies extending `test_prompt_file_is_agent_independent` to agy. The current test loops over only Codex and grok and compares only `hashes[0] == hashes[1]`. Specify a WIRED agy fixture and an assertion comparing all three prompt hashes; merely adding agy to that loop would leave its bytes unchecked.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.spec.md › ``covers `codex`, `grok` and `agy`.``
  quote: docs/02-design/features/agy-coder-fallback.design.md › `| AC-9.1 | the union sweep re-run, plus the three pin files staying green |`

- AC-X's proposed append control cannot bite — replacing a copied-list append with an in-place append preserves both earlier entries and produces identical serialized output. The controlled pair passed the proposed earlier-entry byte check in both modes and produced identical persisted observations. This violates Test discrimination: the specified observation cannot distinguish the mutant. Replace that row with a loss/corruption mutant the persistence assertion detects, or, if prior-list immutability itself is required, add an observation of that prior list before and after the callback.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.spec.md › `Every new guard carries a mutation row that bites`
  quote: docs/02-design/features/agy-coder-fallback.design.md › `` `--append` mutating the prior list in place → AC-7.1's two-entry byte check ``

- FR-7 can record a self-review as independent after availability recovers — `implementer_switch.to` is historical, not necessarily the author of the reviewed implementation. For example, Codex unavailable → agy stores a switch; Codex recovers → the resolver dispatches Codex with `switch=none`, leaving that switch untouched. The proposed attribution still says agy, so a Codex reviewer is marked independent. Record the author from the successful implementation dispatch being reviewed and add a switch/recovery fixture; neither a stale switch nor a fresh availability check establishes who wrote that code.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.spec.md › `equals the implementer of the code it reviews.`
  quote: docs/02-design/features/agy-coder-fallback.design.md › `` `implementer` is the resolved author of the reviewed code (`implementer_switch.to`, else ``

- The load-bearing scratch-probe claims lack their runnable commands — the FR-3 Python/bash compatibility pair and FR-6 import-failure controlled pair give outputs and prose methods, but no preserved command or script invocation that reproduces those readings. This breaches Behavioural premises carry their command even though the moved-row census independently reproduces as 31 of 62 mutation rows. Preserve the probe programs with exact invocations, or inline runnable commands beside the respective outputs, before clearing the design gate.
  class: measurement
  quote: docs/02-design/features/agy-coder-fallback.design.md › `scratch scripts that produced these figures were deleted.`

## Should-fix

- Define cumulative semantics for repeated appends to the same key — the operation is repeatable, but the supplied construction rebuilds each appended value from `prior_value`. Taken literally, two appends in one invocation leave only the second new entry. Specify accumulation from the updated record, define interaction with `--set` on the same key, and add a two-appends-in-one-call fixture that preserves the initial entries and both additions.
  class: build
  quote: docs/02-design/features/agy-coder-fallback.design.md › `` `record = {**prior, **fields}`, then each appended key becomes `list(prior_value) + [entry]`. ``

## Nit

None

🌱 graft saved ~42,363 tokens this turn, 1 call.
AUDIT-agy-coder-fallback-design-v1-END
