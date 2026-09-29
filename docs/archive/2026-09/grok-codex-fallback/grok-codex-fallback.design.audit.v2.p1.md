AUDIT-grok-codex-fallback-design-v2-BEGIN
## Summary
The design specifies all 58 current ACs, but its known format-detector disagreement and the new CLI conflict with binding base invariants. The fixture placement also needs a concrete in-skill source, and the paired plan still carries two superseded contracts.
Evidence: 9 files opened, 11 greps run; I read the saved spec, design, plan, both invariant layers, prior audit reports, and the relevant dispatch and combiner code, and executed jq/Python parser controls. 🌱 graft saved ~183,245 tokens (one call reported ~$0.03), 3 calls.

| FR | implemented-as-written | restated | absent |
|---|---|---|---|
| 1 | AC-1.1, AC-1.2, AC-1.3, AC-1.4 | — | — |
| 2 | AC-2.1, AC-2.1b, AC-2.2, AC-2.3, AC-2.4, AC-2.5, AC-2.6, AC-2.7 | — | — |
| 3 | AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5, AC-3.6, AC-3.7 | — | — |
| 4 | AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5, AC-4.6, AC-4.7, AC-4.8, AC-4.9, AC-4.10 | — | — |
| 5 | AC-5.1, AC-5.2, AC-5.2b, AC-5.3 | — | — |
| 6 | AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5, AC-6.6 | — | — |
| 7 | AC-7.1, AC-7.2, AC-7.3, AC-7.4, AC-7.5 | — | — |
| 8 | AC-8.1, AC-8.2, AC-8.3, AC-8.4, AC-8.5 | — | — |
| 9 | AC-9.1, AC-9.2, AC-9.3, AC-9.4 | — | — |
| 10 | AC-10.1, AC-10.2 | — | — |
| 11 | AC-11.1, AC-11.2, AC-11.3 | — | — |

## Must-fix
- FR-5's shell and Python detector equivalence is knowingly false beyond the two AC-5.2b examples — a valid object with a top-level `type` and 5,000 nested array levels is accepted by jq but skipped after Python 3.11 raises `RecursionError`; I reproduced both outcomes. The jq-absent grep route has further documented disagreements. A limited agreement test cannot satisfy the universal spec rule or the base single-source contract; use one parser or specify and test an identical input domain on both surfaces.
  class: build
  quote: docs/01-plan/features/grok-codex-fallback.spec.md › `must return the same answer on every line,`
  quote: docs/02-design/features/grok-codex-fallback.design.md › `21 agreed. The 6 that disagreed fall into one class:`
- The new `grok` executable is an external CLI dependency, although the design declares compliance by calling it an optional runtime verb. The base invariant forbids introducing a new CLI without qualification; this needs a redesign or an explicit operator `Acknowledged-not-fixed` sidecar decision before the gate can clear.
  class: build
  quote: docs/02-design/features/grok-codex-fallback.design.md › `grok --cwd <cd_dir> --always-approve --output-format streaming-json --prompt-file <bounded-prompt-file>`
  quote: h-mad/invariants.base.md › `Introducing a new third-party package or new CLI is a violation.`
- The fixture helper's source is not pinned inside `h-mad/` — the design promises an F0 path and hash check while claiming tests never read outside the skill, but the specified F0 lives under repository `docs/`. Require an in-skill copy at an exact path, checked against F0's committed hash, so the suite remains runnable with the skill alone.
  class: build
  quote: docs/02-design/features/grok-codex-fallback.design.md › `No code or test reads outside `h-mad/`, apart from the`
  quote: docs/01-plan/features/grok-codex-fallback.spec.md › `A test may copy F0 under`
  quote: .h-mad/invariants.md › `A skill MUST remain runnable from a bare clone: no import of another skill's`

## Should-fix
- The paired plan still prescribes agy → grok → codex precedence, while the current spec and design require the codex banner before grok. Mark the plan's older rule superseded or update it; otherwise 5d has two incompatible classifier contracts and can reintroduce the codex-log regression.
  class: build
  quote: docs/01-plan/features/grok-codex-fallback.plan.md › `same precedence (agy first, then grok, then codex).`
  quote: docs/02-design/features/grok-codex-fallback.design.md › `agy, then the codex banner in the head window, then grok, then codex-text`
  quote: docs/01-plan/features/grok-codex-fallback.spec.md › `**Precedence:** `agy-ndjson` first, then the **codex banner**, then `grok-ndjson`, then`
- The paired plan's success criterion still says 55 ACs; the current spec and design contain 58 distinct IDs (re-derived with the plan's suffix-aware grammar). Update the measurement so the implementation gate does not certify an obsolete coverage total.
  class: measurement
  quote: docs/01-plan/features/grok-codex-fallback.plan.md › `All 55 spec ACs across FR-1–FR-11 pass automated tests.`
  quote: docs/01-plan/features/grok-codex-fallback.spec.md › `AC census 55 to 58 distinct IDs.`

## Nit
None
AUDIT-grok-codex-fallback-design-v2-END
