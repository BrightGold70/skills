AUDIT-audit-report-docs-copy-plan-v1-BEGIN
## Summary
Axis C finds all six functional requirements implemented-as-written at plan granularity; none is restated or absent. The plan nevertheless has four invariant-level gaps: it can gate stale content after `CONFLICT`, does not mutation-pin its new connections bidirectionally, does not replay the motivating incident path, and relies on a corpus claim contradicted by the repository.

| Spec item | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |

## Must-fix
- The recipe never requires the `COLLECT:` token to be consumed before gating — the plan says `MISSING` and `CONFLICT` exit 0, then documents `collect-report` followed by gating the printed docs path. On `CONFLICT` that path already exists with different, preserved bytes, so the next step can gate and PASS the stale report; require an explicit `COLLECT: OK` branch, halt with an `[H-MAD]` marker on both other verdicts, and test that the gate is not invoked.
- FR-6's four named mutations do not satisfy bidirectional connection enforcement — they cover empty-copy, overwrite, validation removal, and refusal removal, but omit drop/force pairs for `collect()` surface propagation, CLI-to-`collect()` delegation, and the `hmad-dispatch collect-report` route; the gate also has only the drop mutation, not a force-refusal mutation caught by the non-`.report.md` case. The base invariant requires each new connection to be mutated in both directions with the callee left intact.
- AC-2.9 exercises only the existing-identical no-write branch, not the incident that motivated the feature — cycle 8 already has its recovered docs copy, so that tracer cannot show that a real transport-only report becomes persisted or that it cannot gate beforehand. The Incident replay invariant requires a reachable real survivor (for example the cycle-8 transport bytes in an isolated project root, or the pre-restoration tree) to traverse absent docs → collected byte-identical docs → gateable docs.
- The basename safety evidence is false as written — the risk table says the corpus contains no docs artifact named `*.report.md`, but this repository contains many, including `docs/04-report/features/gate-blindness-hardening.report.md` and `docs/archive/2026-08/audit-cycle-verb/audit-cycle-verb.report.md`. Because the proposed guard identifies transport solely by that suffix and AC-3.5 deliberately applies it inside `docs/`, the plan must correct the corpus claim and reconcile the gate's audit-input domain with these real artifacts; an incorrect load-bearing corpus assertion violates Assumption verification.

## Should-fix
- Define the collector's internal result contract before the impl-plan — current `collect()` returns only `(delivered, collected_path)` while the CLI must distinguish `CONFLICT`, and current `PassSpec.out_path` is mandatory while `--out` must be optional. State the exact compatible type/signature changes so the CLI does not independently re-check content or invent a dummy output path.
- Add explicit tests for FR-2's operational-error surface — unreadable/non-directory project roots, an unwritable or blocked docs directory, and missing required flags are promised to exit 2 without a `COLLECT:` line, but “tests for every AC” does not cover these description-level requirements.

## Nit
None
AUDIT-audit-report-docs-copy-plan-v1-END
