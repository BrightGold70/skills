AUDIT-tdd-gate-fail-opens-plan-v2-BEGIN
## Summary
The plan addresses FR-1–FR-7 as written, but its verification strategy has two blocking gaps: it does not compare every newly allowed path across old and new gates, and its differential domain excludes required unresolvable cells. The manual tool readings also lack complete reproducible invocations for the behaviors they are used to justify.

| FR | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |
| FR-7 | implemented-as-written |

Evidence: 14 repository files opened, 10 greps run; current gates, judge, test helper, plan, spec, and invariants inspected. 🌱 graft saved ~47,506 tokens this turn (1 call).

## Must-fix
- T0/T9 do not require an old-versus-new verdict diff, and their M-cell gate corpus omits the separately approved leaf-symlink-to-tests ALLOW — the base guard-narrowing invariant requires a corpus diff accounting for every softened verdict, so the three named relaxations are not proven exhaustive. Add that cell and an explicit comparison of the two readings that fails on any unnamed ALLOW.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.plan.md › `M-1…M-23: each cell's **gate** columns`
  quote: h-mad/invariants.base.md › `run a corpus of inputs through the old and new logic and diff the verdicts, then account for **every** input whose verdict softened`
- T6 inherits an impossible differential-domain predicate: M-12–M-14 and M-18 contain dangling links or loops, for which FR-3 deliberately produces no canonical target, yet the domain admits only targets whose canonical form is inside the root. Define membership for unresolvable paths in the spec and plan while retaining those required cells; otherwise an implementer can omit them or invent an inconsistent inside-root test.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.plan.md › `Cross-gate differential over the OD-5 domain`
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › `whose canonical target is inside the canonical root`
- R-4 supplies only a trailing-space Update fixture, then says every other M-15–M-23 result follows by substituting the header line; that substitution cannot reproduce multi-header Add/Update, Move, or Add-with-control cases, and the spec itself says some trim points were inferred rather than measured. Publish the actual fixture, patch, invocation, and observed output for each load-bearing manual case before T4 treats the whole code-point set as measured.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.plan.md › `same command with the header line substituted`
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › `The code points not run are inferred from the property, not measured.`
- R-5 records an English description of the Claude Edit action, without the exact tool invocation or a retrievable transcript — its refusal is a load-bearing premise for keeping the leaf-symlink rule, and the base invariant requires the command beside the output. Record the tool name and exact input fields with the build and observed response, or label the premise unverified.
  class: measurement
  quote: docs/01-plan/features/tdd-gate-fail-opens.plan.md › `then the Claude Code Edit tool on `pd5/src/link.py` replacing`
  quote: h-mad/invariants.base.md › `MUST carry the exact command that produced it`

## Should-fix
None

## Nit
None
AUDIT-tdd-gate-fail-opens-plan-v2-END
