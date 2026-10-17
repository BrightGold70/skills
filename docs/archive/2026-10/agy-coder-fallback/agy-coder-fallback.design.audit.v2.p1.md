AUDIT-agy-coder-fallback-design-v2-BEGIN
## Summary

The design still conflicts with AC-4.1 and contains gaps in resumed review attribution and mutation discrimination. Both committed probes passed; targeted pytest reported `2 passed, 1 error`, with teardown blocked by the sandbox's restriction on `ps`; repository files remain unchanged.

Evidence: 22 files opened, 13 greps run.

| Acceptance criterion | Classification |
|---|---|
| AC-1.1 | implemented-as-written |
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
| AC-9.1 | implemented-as-written |
| AC-9.2 | implemented-as-written |
| AC-9.3 | implemented-as-written |
| AC-9.4 | implemented-as-written |
| AC-X | restated |

## Must-fix

- AC-4.1 is restated more restrictively: the workspace cross-check refuses even when step5 is inactive — FR-4 step 5 precedes the inactive allowances and makes its denial unconditional. A valid `run_command` call with `CommandLine="ls"`, an inactive state, and `workspacePaths=[]` therefore receives `judge-error`, whereas the spec explicitly requires the cross-check to stand down outside active step5. Preserve that inactive behavior and test this case, or reconcile the restriction in the spec before implementation; retain the separate per-target unreadable-chain protection.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.spec.md › `With step5 inactive, the agy gate allows every tool.`
  quote: docs/02-design/features/agy-coder-fallback.design.md › ``the gate denies `kind=judge-error`.``

- FR-7's recovery procedure loses earlier authors and can mark a self-review independent — the stored 5e entries are a lossy projection, not a complete dispatch-author history. Executing the specified procedure with successful authors `[agy, codex]`, a grok 5e-review and a Codex 5e-verify stores `implementer=codex` in both entries. After dispatch context is lost, recovery yields only `{codex}`, so an agy 6a-prime is incorrectly recorded independent. Preserve a durable source covering every successful implementation author, or treat incomplete provenance as unknown rather than reconstructing a complete set from these entries; add this multi-author resume case. The single switch/recovery fixture does not exercise this loss.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.spec.md › `` `false` if the reviewer is any of them, and `implementer` names that agent.``
  quote: docs/02-design/features/agy-coder-fallback.design.md › ``from the module's own 5e entries (their `implementer` values)``

- AC-X is restated with a mutation fixture that cannot bite — removing T4's non-empty-string check is paired with an empty artifact path and a target outside the root, but FR-4 step 3 first executes `os.chdir(root)`. Consequently the empty artifact path resolves to the root, and containment remains false for that target with or without the check. The controlled pair using the existing `_path_within` returned `False` in both modes. Starting the handler in a directory containing the outside target cannot change this because step 3 replaces that directory. Specify a reachable mutation with a different full-gate observation, or explicitly reconcile an equivalent-mutant exception; a helper-only fixture bypassing the required directory change would not establish discrimination.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.spec.md › `Every new guard carries a mutation row that bites`
  quote: docs/02-design/features/agy-coder-fallback.design.md › ``  - T4's non-empty-`str` check on `artifactDirectoryPath` removed → `artifactDirectoryPath: ""` ``

## Should-fix

- Correct the phase used to identify a successful implementation dispatch — FR-7 calls it a GREEN dispatch accepted at 5d, while the implementer contract assigns GREEN to 5e. Attribution should use the accepted 5e implementation and subsequent accepted fixes; a 5d RED dispatch is not evidence of production authorship.
  class: build
  quote: docs/02-design/features/agy-coder-fallback.design.md › `implementation dispatches: the GREEN dispatch the orchestrator accepted at 5d, and any later`
  quote: h-mad/references/codex-implementer-prompt.md › `For GREEN phase (5e):`

## Nit

None

🌱 graft saved ~41,203 tokens this turn, 2 calls.
AUDIT-agy-coder-fallback-design-v2-END
