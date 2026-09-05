AUDIT-doc-block-exec-plan-v87-BEGIN

## Summary

The plan concretely addresses all six functional requirements, but its supporting evidence still contains unreproducible commands and an unsupported causal attribution. I checked repository sources and probe artifacts without modifying files; OneContext history was unavailable.

Evidence: 16 files opened, 12 greps run.

| Requirement | Classification | Coverage |
|---|---|---|
| FR-1 | implemented-as-written | Tagged extraction, heading selection, ordinals, shared scanner |
| FR-2 | implemented-as-written | Literal simultaneous substitution and explicit refusals |
| FR-3 | implemented-as-written | Disposable cwd, shell modes, preamble, separate streams, cleanup |
| FR-4 | implemented-as-written | Verdict grammar, exit partition, registry checks |
| FR-5 | implemented-as-written | Validated timeout, process-group termination, bounded drain |
| FR-6 | implemented-as-written | Atomic tagging/migration and caller wiring tests |

## Must-fix

- The heading differential, Setext census, and grammar corpus lack reproducible probe definitions — their commands reference files absent from the repository root and the historical tracked tree. Temporary scripts exist in session scratch directories, including different versions of the heading differential, but the document provides neither their source nor a stable locator. This violates **Behavioural premises carry their command**: readers cannot reproduce the evidence supporting the scanner and guard-narrowing decisions without reconstructing the measurement. Include the complete probes or address preserved artifacts precisely.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `on the new side (throwaway `heading_differential.py`, one `re.match` per line per selector),`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `script is a throwaway (`grammar_corpus.py`, one `md.render(src)` per case, a needle asserted on`

- The explanation for the historical `49 across 2 files` result attributes it to changing cwd without a supporting controlled pair — rerunning the census logic against the current root produced `73 / 10`; against `h-mad/` and `handoff/`, it produced `0 / 0` for each. The filter cannot retain both sibling top-level skill files from either subdirectory. This violates **Assumption verification**’s causal-pair requirement. Preserve the historical observation, but remove the asserted cause unless the actual invocation reproducing it is recovered.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `that is the count the script returns when run from a **subdirectory**, where`

## Should-fix

- The register’s exclusions contradict its revision-specific membership rule — the awk probe remains excluded because v1.96 executed it, and the fifteenth renderer case remains excluded because it once ran. Neither explanation establishes execution in v1.103. Apply the same re-entry rule already used for the six screen-two legs, or explicitly change the register’s policy.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `- The **`awk` boundary probe** row is **out** of this register: v1.96 re-ran all five of its legs,`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `- The **scanner grammar corpus** row is **in** this register for its fourteen and out for its`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `probe leaves the register **only for the revision that executes it** and re-enters at the next`

- The shared screen residual incorrectly assigns SHA filtering to screen two — the extracted spec pattern matched both `three files measured` and `three files measured abc1234`. The plan’s earlier explanation correctly says screen two has no SHA stage. Restrict this residual to screen one so reviewers do not mistake screen-two hits for missing provenance.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `*shape* filter and never a verdict, and each tests for a sha on the **same line**, so a claim whose`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `` `awk`-numbered body and has no sha stage anywhere in it. ``

## Nit

None

AUDIT-doc-block-exec-plan-v87-END