<!-- ORCHESTRATOR-NOTE:START — assembly strips everything down to ORCHESTRATOR-NOTE:END; it never reaches the reviewer. -->
# Audit Prompt Template

> Used by `/h-mad` Phase 3 audit-plan, Phase 4 audit-design, and Phase 5b audit-impl-plan.
> The orchestrator inlines the target document(s) into the `INLINE_*` slots, inlines the
> workflow-universal base rubric from `~/.claude/skills/h-mad/invariants.base.md` into the
> `INLINE_BASE_INVARIANTS` slot and the project's domain rubric from
> `<PROJECT_ROOT>/.h-mad/invariants.md` into the `INLINE_PROJECT_INVARIANTS` slot, stages the result at
> `/tmp/audit_<feature>_<phase>_cycle<N>.txt`, then dispatches agy via `hmad-dispatch send`
> file-indirection (see `references/agent-substrate.md`).
>
> **Slot names are written here WITHOUT their angle brackets on purpose.** Assembly is a
> literal string replace over the whole file, so a bracketed `<INLINE_…>` mention in this
> note would be substituted too — splicing a second copy of the rubric into the middle of
> a blockquote. Prose in this repo refers to slots bare; only a real slot is bracketed.
>
> ## Applicability markers
>
> `{{ONLY:…}}` is an **assembly directive, never reviewer content**. The audience list is
> one or more of `plan`, `design`, `impl-plan`, comma-separated. For the audit you are
> assembling:
>
> - **applies** → delete the marker, keep the content;
> - **does not apply** → delete the marker *and* the content it governs.
>
> Never leave the marker in, and never blank a slot while keeping its label — a reviewer
> shown `Paired audited plan:` with nothing after it reads a missing document, not an
> inapplicable one.
>
> Two forms, distinguished by whether the marker shares its line with content:
>
> | Form | Written as | Governs |
> |---|---|---|
> | Inline | `{{ONLY:design}} <content>` (may follow a `- ` bullet) | the rest of that line, plus any following lines indented deeper than it |
> | Block | `{{ONLY:design}}` alone on its line | every line down to the matching `{{END-ONLY}}`, both marker lines included |
>
> After substitution, **no `{{` may survive** — step 7.2's preflight greps for it and halts
> `<phase>:unresolved_conditional`. This is a live failure: the old markers were spelled
> three different ways (`{For design audit only:}`, `{Design only — cross-doc:}`), and
> `{Design only — cross-doc:}` reached the reviewer in **69 of 69** dispatched prompts,
> telling every plan and impl-plan audit to perform a design-only check.
<!-- ORCHESTRATOR-NOTE:END -->

You are the agy audit reviewer. Your role this turn:
- Plan audit: Reviewer.adversarial_consistency
- Design audit: Reviewer.adversarial_consistency + Analyzer.cross_doc_consistency
- Impl-plan audit: Reviewer.adversarial_consistency (focus: writing-plans quality — no TBD placeholders, no vague reqs, exact file paths, type consistency across tasks, code blocks that match referenced functions)

Target document: <INLINE_TARGET_DOC>
{{ONLY:plan,design}} Source spec: <INLINE_PAIRED_SPEC>
{{ONLY:design}} Paired audited plan: <INLINE_PAIRED_PLAN>
{{ONLY:impl-plan}} Paired audited design: <INLINE_PAIRED_DESIGN>

Audit rubric (TWO axes, both mandatory):

Axis A — Generic adversarial:
- Contradictions inside the doc
- Gaps (missing error paths, untestable AC, unstated assumptions)
- Weak claims (load-bearing decisions without justification)
- Scope creep (work outside the stated feature boundary)
- {{ONLY:design}} Cross-doc: does the design implement what the plan promised?
  Flag silent drift, dropped FRs, undocumented design decisions that change
  plan-stated behavior.

Axis B — Invariant compliance (any breach = must-fix, you cannot downgrade).
Two layers, both binding:

### Base invariants (workflow-universal; non-overridable by any project file — but the operator `## Acknowledged-not-fixed` sidecar still applies to base findings):

<INLINE_BASE_INVARIANTS>

### Project invariants (domain rules for this repository):

<INLINE_PROJECT_INVARIANTS>

{{ONLY:plan,design}}
Axis C — Spec reconciliation.

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
{{END-ONLY}}

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

Report file (preferred delivery under Orca — the orchestrator fills the path below, or leaves it empty):

<REPORT_FILE_PATH>

If a path appears above, your **final two actions** are: (1) write your report — the exact `## Summary` / `## Must-fix` / `## Should-fix` / `## Nit` schema above; the `<AUDIT_SENTINEL>` brackets are optional inside the file — to that exact path (for a hard atomicity guarantee, write to `<path>.tmp` and `mv` it into place); then (2) create the marker `<that-path>.done` (e.g. `: > "<path>.done"`). The coordinator reads the file, not your terminal, so the file must be complete before the marker exists. If the path is empty, ignore this section and deliver via the terminal sentinels above.
