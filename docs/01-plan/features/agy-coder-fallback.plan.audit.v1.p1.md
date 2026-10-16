AUDIT-agy-coder-fallback-plan-v1-BEGIN
## Summary

The plan covers FR-1 through FR-10 as written, but five build issues remain against the base invariants and verification requirements. The published M-1–M-5 censuses reproduced, including 6,042 collected tests; no repository files were modified.

| Requirement | Classification | Coverage |
|---|---|---|
| FR-1 | implemented-as-written | Stage 1; schema, reference rows, fallback descriptions, DO-4 |
| FR-2 | implemented-as-written | Stage 2; shared resolution function and recording verb |
| FR-3 | implemented-as-written | Stage 3; precedence, closed state line, compatibility exception |
| FR-4 | implemented-as-written | Stage 5; fail-closed gate, tool classes, DO-2 |
| FR-5 | implemented-as-written | Stage 5; wiring check, assembler halt, DO-6 |
| FR-6 | implemented-as-written | Stage 4; shared policy, imported names, mutation relocation |
| FR-7 | implemented-as-written | Stage 7; add-without-loss mechanism and universal warnings |
| FR-8 | implemented-as-written | Stage 8; live tracer, evidence and measured timeout |
| FR-9 | implemented-as-written | Stage 6; neutral prompt and five new-caller rule surfaces |
| FR-10 | implemented-as-written | Stages 6–7; documentation rewrites and discriminating pins |

Evidence: 23 files opened, 15 greps run.

## Must-fix

- Resolve FR-5's inherited exit-2 contract before implementation — the plan adopts the assembler enforcement from a spec that explicitly requires exit 2 for every wiring refusal. A readable configuration with a narrow matcher is a normal FAIL verdict, so this violates the base audit-gate signal discipline even though callers read stdout. The existing assembler also returns 2 on a semantic halt, verified with its read-only-sandbox refusal. Amend the plan and source spec together so the new normal refusal emits its token and exits 0; reserve nonzero exits for operational errors and pin that distinction in tests.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.plan.md › `**agy gate (FR-4), then its wiring check and assembler enforcement (FR-5).**`
  quote: docs/01-plan/features/agy-coder-fallback.spec.md › ``It exits 2, as every `ASSEMBLE-TDD: HALT` already does.``

- DO-4 incorrectly treats `format` as enforced by the library validator — both production validator paths accept a non-date string with `format: date-time`. The command below printed `Draft7Validator: True` and `bundled: True`. This differs from unsupported assertion keywords such as `oneOf`, and leaves the spec's ISO-8601 timestamp requirement without an identified enforcement mechanism. Correct the premise, specify where timestamp syntax is checked, and require an invalid timestamp to fail on both paths; extend the bundled validator and its differential corpus if that is the chosen mechanism.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.plan.md › `it would reject on one validator path and accept on the other.`
  quote: docs/01-plan/features/agy-coder-fallback.spec.md › ```.ts` is ISO-8601.``
  Command: `rtk proxy /opt/anaconda3/bin/python3 -B -c 'import sys;sys.path.insert(0,"h-mad/scripts");import h_mad_state_validate as v;from jsonschema import Draft7Validator; s={"type":"string","format":"date-time"}; x="not-a-date";print("Draft7Validator:",Draft7Validator(s).is_valid(x)); print("bundled:",v._MiniDraft7(s).is_valid(x))'`

- FR-9 lacks the required old/new verdict corpus for a guard relaxation — the plan deliberately admits a previously refused missing-caller RED, but its stated verification preserves literal pins and runs the suite. Neither accounts for every verdict that softens. The base Guard narrowing invariant requires a differential corpus, including missing caller with an existing callee, missing callee, both missing, and unrelated import failures, with the observed changed set restricted to the intended case. Add this verification obligation to stage 6 rather than relying on sentence presence.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.plan.md › ``and a valid new-caller RED is no longer halted as `red_wrong_reason`.``

- FR-9 never requires replay of the motivating incident — real historical artifacts are reachable in the sibling HemaSuite checkout, including the archived analysis and impl-plan and `hematology-paper-writer/tests/test_notebooklm_resolver.py`. The archived F-3 identifies the actual new-caller WIRE-PIN cases, but stage 6 only commits to editing rule surfaces and preserving pins. The base Incident replay invariant requires applying the revised rule to those historical RED cases, retaining their wire-cut evidence, and recording the result; a newly invented corpus alone cannot substitute for this replay.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.plan.md › `**Prompt and doc surfaces (FR-9, FR-10)**, including the WIRE-PIN new-caller rule on every`
  quote: /Users/kimhawk/orca/HemaSuite/docs/archive/2026-10/notebooklm-integration-interface/notebooklm-integration-interface.analysis.md › `**F-3 — WIRE-PIN RED on a new caller (T4/T5/T6 WIRE 2).**`

- The live tracer needs a separate forced-handler-timeout case — the inherited FR-8 refusal step claims to settle handler-timeout behaviour, but asking for one forbidden write need not time out any handler. An ordinary observed deny therefore cannot establish what happens when the hook produces no timely JSON, a load-bearing failure path for the write guarantee. Require a controlled delay beyond the configured handler deadline through the same dispatch transport, separately observe whether the attempted file exists, and record the runtime outcome before treating timeout behaviour as verified.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.plan.md › `**Live tracer (FR-8)**, which also replaces the provisional timeout.`
  quote: docs/01-plan/features/agy-coder-fallback.spec.md › `what agy does when a handler`

## Should-fix

None

## Nit

None

🌱 graft saved ~22,447 tokens (~$0.01) this turn, 1 call.
AUDIT-agy-coder-fallback-plan-v1-END
