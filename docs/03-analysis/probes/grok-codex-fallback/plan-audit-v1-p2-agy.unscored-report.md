## Summary
The plan successfully covers all functional requirements from the spec, providing detailed testing strategies and explicitly adopting all 54 Acceptance Criteria. Axis C reconciliation shows all requirements are implemented-as-written. However, the plan contains a contradiction regarding AC-2.1b test requirements and violates base invariants for behavioral premise commands and connection enforcement force-fire testing.

| Requirement | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |
| FR-7 | implemented-as-written |
| FR-8 | implemented-as-written |
| FR-9 | implemented-as-written |
| FR-10 | implemented-as-written |
| FR-11 | implemented-as-written |

Evidence: 0 files opened, 12 shell commands run (including 6 greps, 1 jq script, and 1 pytest collection run to verify premises).

## Must-fix
- The plan contradicts the spec regarding the requirement to test the 8 `BLOCK-CODEX` cells. The plan claims this is an addition because it states the spec "does not require a test of it". However, Spec AC-2.1b explicitly states "The same 8 values with codex_out false yield BLOCK-CODEX, as the table's first row says", making it a binding acceptance criterion that must be tested.
  class: build
  quote: `# Plan: grok-codex-fallback` › `The plan keeps one addition beyond the spec's assertions: the spec states that the same 8 values with codex_out false yield BLOCK-CODEX (the table's first row) but does not require a test of it`

- Premises P8, P10, and P13 describe the behaviour and state of the system but fail to provide the exact, runnable command used to verify them. Additionally, P11 states a premise about `grok -p --prompt-file` returning rc 2 without running it, but fails to provide a cheap proxy. This violates the base invariant that behavioural premises must carry their command or state a cheap proxy if too expensive to re-run.
  class: measurement
  quote: `# Plan: grok-codex-fallback` › `P8 — the audit-cycle pass loop is surface-agnostic.`
  quote: `# Plan: grok-codex-fallback` › `P10 — resolved-model pass-through.`
  quote: `# Plan: grok-codex-fallback` › `P11 — grok CLI surface (local grok --help, no model call).`
  quote: `# Plan: grok-codex-fallback` › `P13 — the codex write gate does not cover grok.`

- The connection enforcement table lists "—" for the force-fire negative test for wires W1, W3, W8, and W11. The "Connection enforcement" base invariant strictly requires that a connection must be mutated in both directions, and forcing it to fire unconditionally must fail a negative test (e.g., forcing the grok arm in `_cmd_exec` unconditionally must fail existing codex/agy tests, forcing `_cmd_audit_cycle` to use grok unconditionally must fail agy surface tests). Leaving the force-fire direction untested is a violation.
  class: build
  quote: `# Plan: grok-codex-fallback` › `| W1 | _cmd_exec agent dispatch → grok argv builder | AC-3.1 fails: argv lacks --prompt-file, carries --print | — (grok arm unreachable for codex/agy by the case) |`
  quote: `# Plan: grok-codex-fallback` › `| W3 | _cmd_exec → grok segmenter, scoped by pre_lines | AC-4.1 fails; with scoping dropped, AC-4.7 recovers the old STATUS: DONE | — |`
  quote: `# Plan: grok-codex-fallback` › `| W8 | _cmd_audit_cycle --surfaces → _cmd_exec grok | AC-7.1 fails | — |`
  quote: `# Plan: grok-codex-fallback` › `| W11 | h_mad_resolved_model choices → grok reader | AC-9.1 fails (argparse refuses grok) | — |`

## Should-fix
None

## Nit
None
