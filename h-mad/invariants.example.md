# H-MAD Project Invariants — Axis B Rubric (Template)

> Copy this file to `<PROJECT_ROOT>/.h-mad/invariants.md` and customize for your project.
> The /h-mad orchestrator inlines this file's content as **Axis B** of the audit rubric
> when dispatching agy for plan/design/impl-plan audits (Phases 3, 4, 5b) and the
> architectural review (Phase 6a-prime). Any violation of an invariant listed here is
> auto-classified `must-fix` — agy cannot downgrade.

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

Operations that must go through a single canonical entry point rather than direct calls.

- Every `<concern A>` operation MUST route through `<UnifiedXxxModule>`. Direct calls to legacy `<old_module>` are forbidden.
- Every `<concern B>` operation MUST route through `<UnifiedYyyFacade>`.

### Data-source priority

Order-of-fallback rules for external data sources.

- `<primary source>` first; fall back to `<secondary source>` only when `<primary>` returns no result.
- No path that uses `<secondary>` while claiming `<primary>` is the source.

### Hard rules from the project's CLAUDE.md (or equivalent)

If your project documents numbered hard rules, list them here verbatim or by reference.

- Hard Rule N: `<exact wording>` — violation = must-fix.

### Pipeline guarantees

Architectural invariants enforced by specific helper modules that future code must respect.

- Any change touching `<pipeline-X>` MUST cite the helper module + logger marker (e.g., `[X-GUARD] <feature> <op> <decision>`).

### Logger markers

Greppability conventions for runtime tracing.

- Per-feature log lines use the marker `[<PROJECT>] <feature> phase<N> <decision>` and are written via `<emit-marker-script>`.

---

## HemaSuite worked example (delete this section in your project)

For reference — this is what HemaSuite's `.h-mad/invariants.md` would look like
(currently inlined into the audit-prompt.template.md):

### Unified-facade routing
- Every citation op → `UnifiedReferenceEngine`
- Every parallel I/O → `UnifiedParallelEngine`
- Every evidence/NLM op → `KnowledgeOrchestrator`
- Every agent call → `UnifiedAgentDaemon`
- Every NLM subprocess → `tools/nlm_cli.py`
- Every figure → `UnifiedFigureEngine`
- Every table → `UnifiedTableEngine`
- Every entry-point → `UnifiedLauncher`

### Data-source priority
- NLM first, PubMed fallback only when NLM has no relevant data

### NLM-Hard-Dependency
- NLM-touching paths MUST produce NLM-grounded output OR halt clean
- "Skip NLM if down" is a violation

### KO ownership of NLM lifecycle
- `notebook_id` must NOT be passed outside `KnowledgeOrchestrator`

### Hard Rule 5 (stats)
- No p-values, CIs, or test statistics generated textually — must come from R/CSA computation

### Pipeline-guarantee citations
- Any change touching `scaffold-echo-guard`, `nlm-hard-dependency`, `lightrag-*` (model-config / filter-enforcement), or `review-round Hard-Rule-8` pipelines must cite the helper module and logger marker

---

## How agy uses this file

When dispatched for an audit, the orchestrator inlines this file's body (Generic
Categories section + your custom additions, MINUS the worked example) as the
"Axis B" rubric in the audit-prompt template. agy then:

1. Reads the plan/design/impl-plan target document.
2. Flags any line/section that violates an Axis B invariant as **must-fix**.
3. Cannot downgrade Axis B violations to should-fix or nit.
4. Returns audit output with `axis: B` + `invariant: <tag>` per finding.

The pass-gate (`## Must-fix` count = 0) blocks phase advancement until all Axis B
violations are resolved or operator-overridden.

## Tips

- **Be specific.** "Use the unified module" is too vague. "Citation operations MUST route through `UnifiedReferenceEngine.process()`; direct calls to `endnote_writer.write_refs()` are forbidden" is the right shape.
- **Cite the source.** If an invariant comes from a numbered Hard Rule in your CLAUDE.md, reference it by number so reviewers can verify the wording.
- **Keep it tight.** Aim for 5–15 invariants. More than that suggests you've conflated Axis A (generic quality) with Axis B (project-specific architecture). Move the Axis A items out.
- **Update over time.** As your project's architecture evolves, edit this file. The skill picks up the latest version at dispatch time.
