AUDIT-agy-coder-fallback-plan-v2-BEGIN
## Summary

All ten functional requirements have strategy coverage as written, but three invariant gaps remain in cross-surface consistency and reproducible evidence. The document-shape check passes, the AC census reports `count=18 frs=9`, and M-1–M-5 reproduce, including 6,042 collected tests; the repository remains unchanged.

| Requirement | Classification | Coverage |
|---|---|---|
| FR-1 | implemented-as-written | Stage 1 and DO-4: additive fields and timestamp validation |
| FR-2 | implemented-as-written | Stage 2: shared resolution and recording verb |
| FR-3 | implemented-as-written | Stage 3 and DO-1/DO-1a: precedence, grammar and compatibility |
| FR-4 | implemented-as-written | Stage 5 and DO-2: tool classes and fail-closed gate |
| FR-5 | implemented-as-written | Stage 5 and DO-6: wiring enforcement and exit-code split |
| FR-6 | implemented-as-written | Stage 4 and DO-5: shared shell policy and mutation relocation |
| FR-7 | implemented-as-written | Stage 7 and DO-3: append preservation and universal warnings |
| FR-8 | implemented-as-written | Stage 8: capture, refusal, timeout probe and RED/GREEN |
| FR-9 | implemented-as-written | Stage 6 and DO-7: five rule surfaces, differential corpus and replay |
| FR-10 | implemented-as-written | Stages 6–7 and Success Criteria: documentation and pins |

Evidence: 454 files opened, 12 greps run. The file total includes 446 files read by the automated h-mad content census.

🌱 graft saved ~23,934 tokens this turn, 1 call.

## Must-fix

- Bind the five FR-9 rule copies to one authority — stage 6 updates all five surfaces, but DO-7's wording corpus and the specified presence pins do not require equality between them. One copy could retain a broader or narrower exception while another passes the corpus. The base Single-source contract requires a shared authoritative implementation consumed by all surfaces, or a test asserting byte-equivalence. Add that explicit design and verification obligation, including a control that changes only one copy and makes the check fail.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.plan.md › `the corpus checks the rule's wording, not any one application of it, and the design states`

- Include the existing teammate-audit authorship explanation in the documentation rewrite — `h-mad/SKILL.md:3108` still says the audit-unavailability declaration licenses Claude production authoring. With Codex unavailable and agy available, the new resolver instead selects agy and refuses Claude. The plan's enumerated rewrites omit this competing instruction, leaving the documented contract inconsistent with the changed gate. Preserve audit routing, update this paragraph to distinguish audit selection from resolved authorship, and pin the replacement condition; this is a Single-source contract gap, not a request to change D-8.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.plan.md › `**Deliberately not touched.** The audit-leg routing in Phases 3/4/5b (`codex_status` still routes`
  quote: h-mad/SKILL.md › `made does, and that is one switch with two effects.** This section covers phase *documents*. The`

- Supply the runnable placement probe behind DO-1a's conclusions — the plan publishes which candidate placements satisfy P-1–P-5, but attributes those observations to a deleted scratch script without its command or executable body. The grep locating existing assertions cannot reproduce those candidate results. This violates Behavioural premises carry their command; restore the reproducer and cite its exact invocation and observed output before downstream design relies on the placement conclusions. This changes the evidence artifact, not the feature's required behaviour.
  class: measurement
  quote: docs/01-plan/features/agy-coder-fallback.plan.md › `**What the invariants leave open.** This was probed at `d90decc6` with a scratch script, since`

## Should-fix

None

## Nit

None
AUDIT-agy-coder-fallback-plan-v2-END
