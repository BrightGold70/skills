## Summary
The design still has blocking gaps in halt signaling, canary state/capture, reading namespaces, tracer attribution, and publication requirements. Axis C below classifies all 63 acceptance-criterion items; coverage labels describe the stated contract, while the findings identify defects in its mechanics. This was a static audit, with no live containment result claimed.

| Spec identifiers | Classification | Design coverage / divergence |
|---|---|---|
| AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-1.7, AC-1.8 | implemented-as-written | D8, D11, D14–D15 |
| AC-1.9 | restated | Namespaced re-smoke paths disagree (finding below) |
| AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5 | implemented-as-written | D4–D6, S0b, Test Plan |
| AC-2.6 | restated | Exclusion-list publication is omitted |
| AC-2.7 | restated | Later readings cannot use the prescribed fixed parent |
| AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5, AC-3.6, AC-3.7, AC-3.8 | implemented-as-written | D3, D8–D13, D17; AC-3.7 remains retired |
| AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5 | implemented-as-written | D12–D13, Test Plan |
| AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5 | implemented-as-written | D1–D13, Test Plan's binding per-trigger rule |
| AC-6.1, AC-6.2a, AC-6.3, AC-6.4, AC-6.5, AC-6.6 | implemented-as-written | D8–D15, D19–D20 |
| AC-6.2 | restated | INCONCLUSIVE replacement omits measured fractions |
| AC-7.1, AC-7.2, AC-7.3, AC-7.4 | implemented-as-written | D14, Doc pins |
| AC-8.1, AC-8.2, AC-8.3 | implemented-as-written | D14, Gate pins |
| AC-9.1, AC-9.2, AC-9.3, AC-9.4, AC-9.5 | implemented-as-written | D14, Gate pins |
| AC-10.1, AC-10.2, AC-10.3 | implemented-as-written | Wrapper pins, W/G mutation rows |
| AC-11.1, AC-11.2, AC-11.3, AC-11.4, AC-11.5, AC-11.6, AC-11.7 | implemented-as-written | D5, D8, D14–D20; mechanical gaps below |

Evidence: 17 files opened, 4 greps run.

## Must-fix

- The new halt gate violates audit-gate signal discipline — finding an existing halt file is a normal, determined gate verdict, not a missing/unreadable-input error. D17 nevertheless requires exit 2 and only a stderr diagnostic. Give this branch a stdout halt/refusal token and exit 0, retain the no-dispatch/no-AUDITCYCLE behavior, and change the branch's tests accordingly; emit the required [H-MAD] halt marker too.
  class: build
  quote: docs/02-design/features/grok-audit-surface.design.md › ``If the file exists, it launches nothing, prints no `AUDITCYCLE:` line, writes the stderr message of D8 and exits 2.``

- D18 does not specify how the planted sentinel value reaches the separate judge process — its only named copy is the mutable sentinel file, while the judge receives only run-dir and rc. Re-reading that file cannot distinguish its original value from a replacement, or search the log for the original after replacement/deletion. Name a retained expected-token channel outside the grok prompt/cwd, pass it through the real plant → exec → judge path, and test replacement/deletion through that path; otherwise read_escaped and sentinel_changed are under-specified.
  class: build
  quote: docs/02-design/features/grok-audit-surface.design.md › `canary-judge --run-dir <dir> --rc <exec's exit code>`; ``128 bits as 32 hex characters, written to `sentinel.txt`, flushed and read back.``; ```sentinel_changed` (the sentinel is absent or its bytes are not the token)``

- Canary stdout capture races creation of its parent directory — setup creates roots/work/stem and the reading directories, but not RUN/canary; the next pipeline tees into RUN/canary/stdout.txt while canary-plant is responsible for creating the canary layout. tee can open first, lose the capture, and make require refuse a successful canary. Create and verify the capture parent before starting the pipeline, or capture beside run.txt and pass that file to require; cover an initially empty run directory.
  class: build
  quote: docs/02-design/features/grok-audit-surface.design.md › `mkdir -p "$RUN/roots" "$RUN/work" "$RUN/stem" "$READING/resmoke" "$READING/s2"`; `$RUN/canary/stdout.txt`

- AC-1.9 is restated inconsistently after the reading-namespace migration — D11's exported-tree command still reads calibration/resmoke, whereas real records now live in calibration/runs/<run-id>/resmoke. D8's setup also directs the run-record copies into the old data/resmoke and data/s2 locations. Those instructions cannot reproduce the committed reading as required. Update every producer/consumer to the selected reading root and add a smoke re-derivation test against an exported namespaced reading.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `The design names the layout and how the smoke component is pointed at the re-smoke's records.`
  quote: docs/02-design/features/grok-audit-surface.design.md › `READING=$RUN/data/runs/<run-id>`; `--data <export>/docs/03-analysis/probes/grok-audit-surface/calibration/resmoke`; ``and its two copies into `data/resmoke/` and `data/s2/`.``

- AC-2.7's later-reading contract is narrowed by the fixed re-smoke parent — after any earlier run commits its re-smoke, the branch tip is no longer f7520e72, so the prescribed command hits commit-data's ref_moved guard. A new namespace alone does not make a later run appendable. Resolve and record the current confirmed branch tip as the new run's parent, retain the expected-old comparison, and test appending a second run after an earlier run's committed re-smoke.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `A later run adds a new namespace and never modifies an earlier one.`
  quote: docs/02-design/features/grok-audit-surface.design.md › `commit-data --parent f7520e72 --src "$RUN/data"`; `ref_moved:<oid>`; ``A later run writes its own `runs/<run-id>/` (D8).``

- D16 silently drops the plan's controlled codex tracer pair and makes an unsupported causal attribution — a single failed treatment can also reflect authentication, dispatch, or model failure. This violates Assumption verification as well as the audited plan. Specify the control and treatment commands/artifacts and attribute the failure to last-message placement only when the control passes and treatment fails; both-fail remains unverified while taking the codex-unavailable route.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.plan.md › ``Two otherwise identical `exec codex` dispatches run with a one-line prompt and `--cd` under `$RUN/roots`.``; `Only **control passes, treatment fails** is attributed to codex being unable to write its last message outside system temp.`
  quote: docs/02-design/features/grok-audit-surface.design.md › `So it is a Phase-5 tracer, run once before the re-smoke:`; `If it fails, the re-smoke and S2 run the codex-unavailable shape, and the spec is told that codex cannot write its last message outside system temp`

- AC-2.6's publication requirement is reduced to list identifiers — D15 requires the exclusion-list commit and blob but never requires the measurement document to publish the actual exclusion list. The runbook likewise supplies a list sha rather than its entries. Add the committed list contents to the measurement-doc contract and its doc pin, or obtain an explicit spec amendment permitting identifiers alone.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `The list is published in the measurement doc.`
  quote: docs/02-design/features/grok-audit-surface.design.md › `the exclusion-list commit and blob;`

- AC-6.2 is narrowed on INCONCLUSIVE — the spec requires measured fractions at both SKILL.md sites, with AC-6.3 additionally requiring the undecidable reason and fallback-only wording. D14 provides fractions only for PASS/MISS and replaces the INCONCLUSIVE branch with reason-only prose; its outcome test encodes the same omission. Include the observed fractions alongside the uncertainty clause and pin them, or amend the spec explicitly.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `It is replaced by the measured fractions and a pointer to the measurement doc.`; `This applies on PASS, MISS and INCONCLUSIVE alike.`
  quote: docs/02-design/features/grok-audit-surface.design.md › ``audit precision was not decidable on this seed set (`reason=<seeds_undetected|undecidable_flips>`), so grok stays fallback-only``

## Should-fix

- Remove the obsolete claim that the spec still owes the PROBE prefix — the supplied spec already defines that exact unknown-mode token. Leaving it recorded as outstanding debt obscures which upstream changes are actually required; correcting this changes no code or tests.
  class: measurement
  quote: docs/02-design/features/grok-audit-surface.design.md › `Spec AC-5.1/AC-5.4 owe the same prefix (report).`
  quote: docs/01-plan/features/grok-audit-surface.spec.md › ``It prints exactly one stdout line, `PROBE: UNREADABLE reason=unknown_mode`, and nothing else on stdout.``

## Nit

None

