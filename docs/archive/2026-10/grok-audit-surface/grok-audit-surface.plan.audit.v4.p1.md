## Summary
The plan covers all eleven functional requirements, but FR-11 narrows the current quarantine contract. Several containment and verification instructions also conflict with the mandatory invariants. The Phase 5 hook blocked graph/history queries and shell searches; verification used direct file reads.

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
| FR-11 | restated |

Evidence: 16 files opened, 0 greps run.

## Must-fix
- FR-11 is restated with a closed five-reason quarantine contract, omitting spec v1.13's sixth form and its exception/usage fixtures. This narrows AC-11.7 and AC-11.6; propagate the internal refusal and both fixtures through S0c, the containment contract and deliverables.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.plan.md › `It ends on one token line; a refusal is exactly one of `quarantine_exists`, `move_failed:<n>`, `residue:<n>`, `count_mismatch`, `unreadable`, in that order (R21), and the guarded stage does not start.`
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `A usage error or an exception that escapes the step prints `QUARANTINE: REFUSED reason=internal:<ExceptionName>`, which is a refusal like the five above. It is the sixth form, a last resort that none of the five names (added in v1.13 from design v1.6).`

- The canary makes every normal negative verdict a process failure. Outcomes such as escaped, read_escaped and no_denial are measured check results, not missing/unreadable-input errors. Returning nonzero for them violates base Audit-gate signal discipline; retain the refusal token and halt, but return zero for normal verdicts. The spec repeats this conflict and must be reconciled with the non-overridable base rule too.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.plan.md › `It exits 0 only on `PASS`; no line is a refusal.`
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `It exits 0 only with `PASS`, and any other outcome exits non-zero.`

- S0c ships the new runtime wrapper before its first live canary invocation. Synthetic stub fixtures and the incident's direct CLI observations do not exercise the newly composed grok-canary → exec path. Base Wrapper–runtime reconciliation requires that live round trip before shipping. Add an operator-run, non-seeded pre-merge canary verification; the existing prohibition concerns seeded dispatches and does not prevent this check.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.plan.md › `S0c merged to `main` with its suite and `MUTATION:` tokens green; the codex tracer read (pass, or the codex-unavailable shape); `QUARANTINE: VERIFIED`; `GROK-CANARY: PASS``
  quote: docs/01-plan/features/grok-audit-surface.plan.md › `**The canary.** `hmad-dispatch grok-canary` prints `GROK-CANARY: PASS`, as the run's first grok call.`

- The unconditional strict-default change has no corresponding unconditional SKILL.md contract update. The enumerated SKILL.md edits cover the teammate command, streak, measurement and conditional routing, while S0c changes every production exec grok invocation. Project Skill manifest integrity requires the entry contract to describe the new strict default, override and applicable staging refusals when that behavior ships, including outcomes that publish no measurement.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.plan.md › `**Edited text only**: `h-mad/SKILL.md` (AC-6.2a and AC-9.5 at S0; AC-6.2 or its AC-1.8 replacement at S3; AC-7.1 and AC-8.3 on PASS)`
  quote: h-mad/SKILL.md › `- **`exec grok`** — an explicit RED/GREEN implementer fallback when both peers are out`

- The codex tracer attributes any failed reply check to inability to write outside system temp, without the controlled pair required by base Assumption verification. Authentication, dispatch, model or other failures can produce the same observation. Either compare otherwise identical temp and beside-log cases and inspect their artifacts before making that causal claim, or report the tracer failure with its cause unverified.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.plan.md › `It passes when `exec` prints the reply and no `EMPTY final message` line. If it fails, the re-smoke and S2 run the codex-unavailable shape, and the spec is told that codex cannot write its last message outside system temp.`

- The observed three-shape prompt-divergence premise has no exact runnable reproduction command. Helper names and flags do not reconstruct the deleted scratch probe, and the Readings command block does not reproduce these observations. Base Behavioural premises carry their command requires the retained script or complete inline invocation beside its outputs; this is an evidence repair, not a change to the wrapper rule.
  class: measurement
  quote: docs/01-plan/features/grok-audit-surface.plan.md › `The wrapper's verdict on each raw shape was observed, not reasoned: driving the real `_cmd_audit_cycle` at `--passes 2` through `install_audit_cycle_stubs` and `run_audit_cycle` from `h-mad/tests/test_hmad_dispatch_audit_cycle.py``
  quote: docs/01-plan/features/grok-audit-surface.plan.md › `scratch probe, deleted after the run`

## Should-fix
- Close the stale production-staging debt against the current documents. The plan still says D16 uses checkout .tmp and spec v1.13 is owed, although spec v1.13 and design v1.7 already encode production staging and the subdirectory refusal. Update the references and remaining-work list so implementers do not repeat completed document work.
  class: measurement
  quote: docs/01-plan/features/grok-audit-surface.plan.md › `D16 "What reaches production" still describes `<cd>/.tmp/` for every `exec grok`, which conflicts with the orchestrator's `<git toplevel>/.h-mad/` ruling for production. That is owed to spec v1.13 and then to the design.`
  quote: docs/02-design/features/grok-audit-surface.design.md › `In a git checkout, `exec grok` stages under `<top level>/.h-mad/tmp/hmad_exec_grok.XXXXXX/` and removes it, so `git status` is unchanged (v1.7).`
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `Its staged prompt and its `TMPDIR` must then sit under `<git toplevel>/.h-mad/``

## Nit
None

