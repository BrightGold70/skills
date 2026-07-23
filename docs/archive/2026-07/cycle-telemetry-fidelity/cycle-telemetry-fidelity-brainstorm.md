# Brainstorm: cycle-telemetry-fidelity

## Executive Summary

Both H-MAD cycle counters (`audit_cycles`, `iterate_cycles`) are seeded to zero and never
incremented, so every quality signal derived from them is unreachable; derive the audit counts
from the `.audit.v<N>.md` files already on disk, and make Phase 6b emit the same kind of
versioned artifact so iterate counts become derivable by one rule rather than two.

## Problem Statement

`h_mad_state_write.py:53-54` seeds `audit_cycles: {plan:0, design:0, impl_plan:0}` and
`iterate_cycles: 0`. Nothing anywhere in `h-mad/` — no script, no SKILL.md step, no reference
protocol — ever increments either. `h_mad_telemetry.py:46-60` reports the zeros faithfully, so
every recorded run claims it consumed no audit and no iterate cycles.

Measured on HemaSuite `clinical-abbreviation-hygiene`: recorded `0/0/0`, actual `1/2/2`.

The consequence is not a cosmetic wrong number. Both drift warnings are dead code:

| Warning | Location | Fires when | Actual |
|---|---|---|---|
| "possible plan/design quality drift" | `h_mad_telemetry.py:122-128` | any `audit_cycles > 3` | never |
| "possible implementation drift" | `h_mad_telemetry.py:124-130` | `iterate_cycles > 3` | never |

`references/state-schema.md:18-19` documents non-zero example values the code cannot produce,
so the schema doc reads as a working feature.

## Proposed Approach

**Derive counts from versioned artifacts at telemetry-record time; no counter, no write path.**

A counter is state that must be maintained in lockstep with reality by an orchestrator step
somebody has to remember. That is precisely the failure being fixed — the counter is dead
because no step was ever written to advance it, and a re-introduced step is a step a future run
can skip just as silently. A derived count cannot drift out of sync with the thing it counts,
needs no orchestrator discipline, and backfills every historical feature for free.

**Audit cycles — derivable today.** The filenames are machine-generated and strictly formed:

```
docs/01-plan/features/<feature>.plan.audit.v<N>.md
docs/01-plan/features/<feature>.impl-plan.audit.v<N>.md
docs/02-design/features/<feature>.design.audit.v<N>.md
docs/archive/<YYYY-MM>/<feature>/<feature>.<phase>.audit.v<N>.md
```

`audit_cycles[phase] = max(N)` over that set, 0 when none exist. Verified against both repos.

**Iterate cycles — not derivable, and that is the real defect.** Phase 6b re-runs the full gap
analysis and **overwrites** `docs/03-analysis/<feature>.analysis.md` in place. Each cycle
destroys the prior measurement. `review-pipeline-correctness.analysis.md` happens to carry prose
`## v1.2 Re-measure` entries; `clinical-abbreviation-hygiene.analysis.md` carries no Version
History at all — the convention is not enforced and cannot be relied on.

So rather than special-casing iterate with a counter, **make Phase 6b write
`docs/03-analysis/<feature>.analysis.v<N>.md` per cycle** (latest also copied to the unversioned
path for existing readers). Then `iterate_cycles = max(N) - 1` by the same glob rule, one
mechanism covers both, and each iterate cycle leaves a readable record of what it measured
instead of erasing it. The counting fix and the auditability fix are the same change.

**Backfill on read, not by rewrite.** `.h-mad/telemetry.jsonl` is append-only. `summary`
recomputes from disk at display time, so historical rows report real numbers without mutating
the log.

## Alternatives Considered

- **Explicit `--increment audit_cycles.<phase>` on `h_mad_state_write.py`** — rejected as the
  primary mechanism. It reintroduces exactly the dependency that failed: a prose step in
  SKILL.md that an orchestrator must execute at each of ~6 call sites, silently wrong if
  skipped, and unable to backfill. Kept in mind as a fallback if derivation proves ambiguous
  for a phase.
- **Increment inside `h_mad_audit_gate.py` when it emits a verdict** — rejected. The gate is a
  pure verdict unit with no knowledge of the feature or the state file; the base invariant on
  single-source verdict units argues against giving it a side effect. It is also called by
  `h_mad_do_preconditions.py`, which would then increment a counter as a side effect of a
  precondition check.
- **Parse `## Version History` prose in the analysis doc for iterate counts** — rejected. The
  convention is unenforced (one of two sampled analyses has no such section) and heading-prose
  matching is the exact failure class that has bitten this codebase repeatedly (B4
  `isolate_bibliography` heading matcher; the audit gate's bullet-only classifier).
- **Rewrite historical rows in `telemetry.jsonl`** — rejected. Mutating an append-only audit log
  to correct it is a worse precedent than computing the correction at read time.

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| A glob picks up template/example files (`docs/templates/audit-example.audit.v1.md` exists in HemaSuite, and has no phase segment) | H | Require the full `<feature>.<phase>.audit.v<N>.md` shape anchored on the feature name; exclude `docs/templates/`. Pin with a test using that real filename. |
| Archived features live under `docs/archive/<YYYY-MM>/<feature>/`, so a live-dir-only glob under-counts every shipped feature | H | Search live dirs **and** the archive; a test fixture covering both. |
| Changing Phase 6b's output path breaks readers of the unversioned `<feature>.analysis.md` — including `h_mad_phase7_preconditions.py`, which reads it for the match rate | M | Keep writing the unversioned path as the latest-cycle copy; versioned files are additive. Regression test that Phase 7 preconditions still parse. |
| Derived count disagrees with an operator's memory of a run, with no stored number to appeal to | L | The artifacts *are* the evidence; a disagreement means a file is missing, which is worth knowing. |
| Feature names that are prefixes of one another (`feat` vs `feat-ab`) cross-match in a glob | M | Anchor on the exact `<feature>.` prefix, not a substring — the same defect fixed in `handoff_paths.py` by the `__` separator. |

## Dependencies

None. Self-contained within `h-mad/scripts/` + `references/inline-protocols.md` §Phase 6b.
No HemaSuite change; HemaSuite benefits automatically as a consumer.

## Open Questions

- **Does Phase 6b's per-cycle artifact belong in this feature, or is it a second feature?** It is
  the only way to satisfy "derive from disk" for `iterate_cycles`, and it changes a phase's
  documented output contract — a larger blast radius than a telemetry fix. Recommended: keep it
  here, because splitting leaves `iterate_cycles` derivable-in-principle and dead-in-practice
  until the second feature lands.
- **Should `max(N)` or `count(files)` define a cycle count?** They differ if a cycle number is
  skipped or a file is deleted. `max(N)` matches "how many cycles did this run reach";
  `count()` matches "how many audit artifacts survive". Leaning `max(N)`, with a test pinning
  the behaviour on a gap.
- **Should the drift warnings' threshold (`> 3`) be revisited** now that they can fire for the
  first time? Out of scope to change, but worth measuring once real numbers exist.

## Version History
- v1.0: Initial brainstorm draft.
