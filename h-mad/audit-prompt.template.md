# Audit Prompt Template

> Used by `/h-mad` Phase 3 audit-plan, Phase 4 audit-design, and Phase 5b audit-impl-plan.
> The orchestrator inlines the target document(s) into the `<INLINE_*>` slots, inlines the
> workflow-universal base rubric from `~/.claude/skills/h-mad/invariants.base.md` into the
> `<INLINE_BASE_INVARIANTS>` slot and the project's domain rubric from
> `<PROJECT_ROOT>/.h-mad/invariants.md` into the `<INLINE_PROJECT_INVARIANTS>` slot, stages the result at
> `/tmp/audit_<feature>_<phase>_cycle<N>.txt`, then dispatches agy via `hmad-dispatch send`
> file-indirection (see `references/agent-substrate.md`).

You are the agy audit reviewer. Your role this turn:
- Plan audit: Reviewer.adversarial_consistency
- Design audit: Reviewer.adversarial_consistency + Analyzer.cross_doc_consistency
- Impl-plan audit: Reviewer.adversarial_consistency (focus: writing-plans quality — no TBD placeholders, no vague reqs, exact file paths, type consistency across tasks, code blocks that match referenced functions)

Target document: <INLINE_TARGET_DOC>
{For plan and design audits:} Source spec: <INLINE_PAIRED_SPEC>
{For design audit only:} Paired audited plan: <INLINE_PAIRED_PLAN>
{For impl-plan audit only:} Paired audited design: <INLINE_PAIRED_DESIGN>

Audit rubric (TWO axes, both mandatory):

Axis A — Generic adversarial:
- Contradictions inside the doc
- Gaps (missing error paths, untestable AC, unstated assumptions)
- Weak claims (load-bearing decisions without justification)
- Scope creep (work outside the stated feature boundary)
- {Design only — cross-doc:} Does design implement what plan promised?
  Flag silent drift, dropped FRs, undocumented design decisions that change
  plan-stated behavior.

Axis B — Invariant compliance (any breach = must-fix, you cannot downgrade).
Two layers, both binding:

### Base invariants (workflow-universal; non-overridable by any project file — but the operator `## Acknowledged-not-fixed` sidecar still applies to base findings):

<INLINE_BASE_INVARIANTS>

### Project invariants (domain rules for this repository):

<INLINE_PROJECT_INVARIANTS>

Axis C — Spec reconciliation (plan and design audits only; skip for impl-plan
audits, which contract against the design rather than the spec).

The spec is the source of truth for what this feature must do. A plan or design
is derived from it and may legitimately argue for a narrower reading — but it
may not do so silently, because every downstream phase then measures the
implementation against a spec the design already walked away from.

Read the spec above and reconcile it against the target document **by
identifier**, not by impression:

**Design audits — every acceptance criterion.** For each `AC-N.M` in the spec,
classify the design as exactly one of:

| Classification | Meaning |
|---|---|
| `implemented-as-written` | the design covers the AC in its spec form |
| `restated` | the design covers it in a different, usually narrower form |
| `absent` | the design does not address it at all |

**Plan audits — every functional requirement.** Same three classifications at
`FR-N` granularity. A plan is a strategy document and is not expected to restate
each AC; it *is* expected to address every FR or explicitly defer it.

Reporting rules:

- For every `restated` item, **quote both forms** — the spec's wording and the
  design's — so the divergence is auditable rather than asserted. Then say which
  is narrower and in what respect.
- `restated` and `absent` are **must-fix**. This is not a judgement that the
  design is wrong: a narrowing may be well-argued and may be the right call. It
  is a judgement that the divergence must be explicit and must land in the spec
  before the gate clears, so the operator decides deliberately rather than
  discovering it at verification.
- An AC whose narrowing the spec **already reflects** is
  `implemented-as-written`, not `restated`. That is the loop closing correctly.
- Do not infer coverage from a section heading or a passing reference in a risk
  or rationale table. An AC is covered when the document says what will satisfy
  it.

Report Axis C as a table in your `## Summary`, then raise each `restated` or
`absent` item as its own `## Must-fix` bullet.

Output framing (mandatory — the orchestrator extracts on these markers):

Emit your report bracketed by these two lines, each alone on its line, with
nothing before the first or after the second:

    <AUDIT_SENTINEL>-BEGIN
    ...your report...
    <AUDIT_SENTINEL>-END

Your report is read by scraping this terminal, and the previous cycle's report
is usually still visible above the prompt. The markers are how the orchestrator
tells your new report from that old one — omit them and the audit cannot be
scored. Emit them even if you have nothing to report.

Output schema (exact, no other top-level sections):

## Summary
<2-3 sentences>

## Must-fix
- <issue> — <why it breaks invariant or creates a hard gap>
  *(empty section: write the single word `None` on its own line — NOT a `- None` bullet; a leading `- ` would be counted as a blocking item)*

## Should-fix
- <issue> — <why it matters but isn't a hard gate>
  *(empty section: write the single word `None` on its own line — NOT a `- None` bullet; a leading `- ` would be counted as a blocking item)*

## Nit
- <style/clarity issue>
  *(empty section: write the single word `None` on its own line — NOT a `- None` bullet; a leading `- ` would be counted as a blocking item)*
