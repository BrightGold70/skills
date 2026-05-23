# H-MAD Project Invariants — Axis B Rubric (Template)

> Copy this file to `<PROJECT_ROOT>/.h-mad/invariants.md` and replace the
> generic categories + HemaSuite worked example with your own project's rules.
> The `/h-mad` orchestrator inlines this file verbatim as the Axis B rubric
> for all plan, design, and impl-plan audits.

## What goes in this file

Each invariant is a **project-specific rule** that the audit must enforce as a hard
gate. The audit-prompt template already covers **Axis A** (generic adversarial
review: contradictions, gaps, weak claims, scope creep, untestable acceptance
criteria) — you don't need to repeat those here. Axis B is exclusively about your
project's load-bearing architectural rules.

Format: one short bullet per invariant. Be specific about which module/facade/rule
is mandatory, and what the violation looks like.

## Generic categories (rename to fit your project)

### Unified-facade routing
- All external calls to subsystem X MUST go through `<FacadeClass>`. Direct
  instantiation of `<ConcreteImpl>` outside `<FacadeClass>` is a violation.

### Data-source priority
- Data source A is authoritative. Data source B is fallback only — never called
  when source A has data.

### Hard rules from the project's CLAUDE.md (or equivalent)
- [Copy your project's hard rules from CLAUDE.md here — e.g. path safety, stats
  from R only, NLM subprocess gateway, etc.]

### Pipeline guarantees
- [List invariants about output guarantees, idempotency, atomicity, etc.]

### Logger markers
- All async/background operations MUST emit `[<MODULE>]` log markers so
  failures are diagnosable from logs alone.

---

## HemaSuite worked example (delete this section in your project)

> The following is a filled-out Axis B rubric for the HemaSuite project.
> It exists to show what a completed invariants.md looks like. Delete it
> and replace with your own project's rules.

### Unified-facade routing
- All evidence-retrieval calls (PubMed search, NLM query, guideline lookup)
  MUST go through `KnowledgeOrchestrator`. Direct instantiation of
  `PubMedClient`, `NLMClient`, or `GuidelineDB` outside `KnowledgeOrchestrator`
  is a violation.
- All reference operations (add, retrieve, format citation, verify) MUST go
  through `UnifiedReferenceEngine`. Direct calls to `EndNoteAdapter` or
  `CitationFormatter` outside `URE` are violations.

### Data-source priority
- NotebookLM is authoritative for clinical evidence. PubMed is fallback only.
  Any design that calls PubMed when NLM has relevant data violates data-source
  priority.

### NLM-Hard-Dependency
- All NotebookLM CLI interactions MUST go through `tools/nlm_cli.py`. Direct
  invocation of the `nlm` binary from any other module is a violation.

### KO ownership of NLM lifecycle
- `KnowledgeOrchestrator` owns NLM session lifecycle (init, query, teardown).
  No other module may call `nlm_cli.py` independently.

### Hard Rule 5 (stats)
- All p-values and confidence intervals MUST originate from R computation via
  `clinical-statistics-analyzer`. Generating statistical values textually is a
  violation.

### Pipeline-guarantee citations
- All manuscript sections with factual claims MUST cite a PMID present in
  the project's `data/references.enl` library. Uncited factual claims are
  a violation.

---

## How agy uses this file

agy reads this file verbatim as the Axis B section of the audit rubric. Any
finding that violates an Axis B rule is auto-classified as `## Must-fix`
regardless of how minor it looks — you cannot downgrade an Axis B violation
to Should-fix or Nit.

## Tips

- Keep invariants short (1-2 sentences each).
- Use negative phrasing ("MUST NOT", "is a violation") rather than positive
  ("should", "ideally") — auditors pattern-match on violations, not ideals.
- If a rule has exceptions, state them inline ("except during unit tests that
  mock the facade").
- Don't list invariants that are obvious from the code structure — only rules
  that an auditor might not know without domain context.
