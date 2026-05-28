# Spec: h-mad-audit-surfaces-reconcile

## Executive Summary

Three reconciliations in the `/h-mad` skill. **Thrust A (audit gate)**: single-source the empty-section + blocking-count contract across the authoring template and the two counting readers (the orchestrator gate-step and `h_mad_do_preconditions.py`); switch the verdict from a non-zero process exit to an explicit stdout token so a legitimate gate-FAIL stops registering as a Claude Code tool failure (the root of the OMC `[TOOL ERROR - RETRY REQUIRED]` noise). **Thrust B (doc templates)**: extend h-mad's phase-document templates to a *superset* that includes the bkit PDCA validator's `REQUIRED_SECTIONS`, so h-mad plan/design/report docs pass the bkit template-compliance hook instead of triggering "Missing required sections" warnings. **Thrust C (two-layer Axis B invariants)**: split the audit's Axis B rubric into a workflow-universal **base layer** that ships with the skill (always inlined for every project) plus the existing per-project domain layer (`<PROJECT_ROOT>/.h-mad/invariants.md`), so universal rules (gate-signal, marker, doc-superset, no-plugin-dependency) are enforced everywhere without each repo re-copying them. All dependency-free (no new external dep; zero runtime OMC dependency).

## Goal

Make the `/h-mad` audit-gate empty-section contract correct and single-sourced across its three reader surfaces, internalize the gate's PASS/FAIL signal so a legitimate gate-FAIL no longer registers as a tool error (the source of OMC retry-guidance noise), bring h-mad's phase-document templates into superset compliance with the bkit PDCA template validator, and document the OMC coexistence behavior — without adding any new external dependency.

## Functional Requirements

### FR-1: Empty-section sentinel never counts as a blocking item (Axis 1)

- **Description**: An audit doc section (`## Must-fix`, `## Should-fix`) that is empty must score **zero** blocking items regardless of which permitted empty-marker form the author used. The current defect: a `- None` bullet is counted as one blocking item → false gate-FAIL.
- **Acceptance Criteria**:
  - AC-1.1: An audit doc whose `## Must-fix` and `## Should-fix` bodies contain only an empty-marker (the canonical form chosen in design — e.g. bare `None`) scores 0 and the gate verdict is PASS.
  - AC-1.2: An audit doc that writes the empty-marker as a bullet (`- None`) scores 0 for that section (not 1) and does not by itself cause a FAIL.
  - AC-1.3: An audit doc with one real bullet (`- <issue> — <why>`) in `## Must-fix` scores ≥1 and the gate verdict is FAIL.
  - AC-1.4: The permitted empty-marker form is stated identically in `audit-prompt.template.md` and in the gate logic; a test asserts the template's empty-marker string matches what the gate treats as "empty".

### FR-2: Both gate readers agree on the blocking-item count contract (Axis 2)

- **Description**: The orchestrator gate (`SKILL.md`) and `h_mad_do_preconditions.py` must apply the **same** rule for what counts as a blocking bullet. The section *scope* each enforces (the orchestrator gate counts Must-fix + Should-fix; preconditions.py counts Must-fix only) must be an explicit, documented decision — either aligned or deliberately divergent with a stated reason — not an accidental inconsistency.
- **Acceptance Criteria**:
  - AC-2.1: Given the same audit doc, both readers return the **same blocking-item count for `## Must-fix`** (i.e. the per-section counting logic is identical, including FR-1 empty-marker handling).
  - AC-2.2: The section-scope difference (Should-fix blocks the orchestrator gate but not the `/h-mad do` precondition) is either removed (made consistent) or documented in `SKILL.md` and `references/state-schema.md`/`phase-table.md` with the rationale. A test or doc-lint asserts the chosen behavior matches the documentation.
  - AC-2.3: No audit doc exists for which one reader reports the Must-fix section clean and the other reports it dirty.

### FR-3: Gate verdict is signalled by output token, not process exit code (Axis 3)

- **Description**: The audit gate must communicate PASS/FAIL via an explicit stdout token and **always exit 0** under normal operation (PASS or FAIL). It must not use `exit (c>0)` / non-zero exit as the verdict, because a non-zero exit makes a legitimate gate-FAIL register as a Claude Code `PostToolUseFailure` (which OMC's `post-tool-use-failure.mjs` records and `persistent-mode.mjs` then surfaces as `[TOOL ERROR - RETRY REQUIRED]`).
- **Acceptance Criteria**:
  - AC-3.1: Running the gate on a clean audit prints a deterministic PASS token (e.g. `GATE: PASS`) and exits 0.
  - AC-3.2: Running the gate on a dirty audit prints a deterministic FAIL token (e.g. `GATE: FAIL`, with the blocking count) and exits 0.
  - AC-3.3: A non-zero exit from the gate is reserved exclusively for *operational* errors (missing/unreadable audit file), never for a FAIL verdict.
  - AC-3.4: `SKILL.md` Phase-3/4/5b gate-step instructions parse the token, not the exit code; the documented gate command no longer relies on `$?`/`exit (c>0)` for the verdict.

### FR-4: One shared contract across all three surfaces (no silent drift)

- **Description**: The empty-section + blocking-count contract must live in a single authoritative place that the template references and that both gate readers use, so the three surfaces cannot diverge again.
- **Acceptance Criteria**:
  - AC-4.1: The blocking-item counting logic exists in exactly one implementation that both the orchestrator gate path and `h_mad_do_preconditions.py` invoke (or, if the awk one-liner is retained, a test asserts byte-for-byte equivalence of the counting rule between the two surfaces).
  - AC-4.2: A test fails if the template's documented empty-marker, the gate's counting rule, and the preconditions parser's counting rule disagree.

### FR-5: OMC coexistence documented (informational, not a code patch to OMC)

- **Description**: `SKILL.md` gains a "Known interactions" subsection documenting (a) the OMC autopilot Stop-hook false-positive nag and (b) the tool-error retry-guidance noise, their shared root in `persistent-mode.mjs`, the `DISABLE_OMC=1` / `OMC_SKIP_HOOKS=persistent-mode` workaround, and the note that after FR-3 the gate no longer triggers the retry-guidance path. A separate informational upstream note (Phase-7 report sidecar) describes the interaction to OMC, framed as "non-zero exit correctly flagged; durable fix is h-mad-side", not a bug report.
- **Acceptance Criteria**:
  - AC-5.1: `SKILL.md` contains a "Known interactions" (or equivalently named) subsection naming both OMC noise sources, the root file, the workaround env vars, and the post-FR-3 reduction in retry-guidance.
  - AC-5.2: A Phase-7 report sidecar file contains the informational upstream-note text; it does not assert an OMC bug and does not modify any file under the OMC plugin tree.
  - AC-5.3: The doc states explicitly that h-mad has **zero** runtime dependency on OMC.

### FR-6: No new external dependency; gate self-contained

- **Description**: The feature's deliverables must add no new external CLI/library dependency. The gate verdict logic must be self-contained and runnable without network or plugin presence.
- **Acceptance Criteria**:
  - AC-6.1: Any new gate implementation uses only tools already depended upon (POSIX shell/awk and/or python3 stdlib) — no new third-party package, no new CLI.
  - AC-6.2: The gate produces identical PASS/FAIL verdicts whether or not OMC/bkit/context-mode plugins are present (verdict independent of external hooks).
  - AC-6.3: A dependency-inventory note in the feature docs records the verified deps (cmux/agy/codex intrinsic; jq/jsonschema/pytest tooling; zero plugin deps) so future audits can confirm no regression.

### FR-7: Test coverage for the contract across surfaces

- **Description**: Tests cover the empty-section matrix, the blocking-count rule, the token-not-exit-code behavior, the cross-surface agreement, and the `## Acknowledged-not-fixed` override.
- **Acceptance Criteria**:
  - AC-7.1: Empty-section matrix test: canonical empty-marker, `- None` bullet, header-only, and real bullets each produce the expected count/verdict (covers FR-1).
  - AC-7.2: Token/exit-code test: PASS and FAIL both exit 0 and print the correct token; operational error exits non-zero (covers FR-3).
  - AC-7.3: Cross-surface agreement test: the orchestrator gate rule and `h_mad_do_preconditions.py` counting agree on Must-fix for a shared fixture set (covers FR-2/FR-4).
  - AC-7.4: Acknowledged-not-fixed override test: items under `## Acknowledged-not-fixed` in a sidecar are excluded from the blocking count exactly as before (no regression to the override semantics).
  - AC-7.5: `preconditions.py` parser test covers the same empty-marker + real-bullet cases.

### FR-8: h-mad phase-document templates are a superset compliant with the bkit PDCA validator (Thrust B)

- **Description**: The h-mad doc templates in `references/inline-protocols.md` for all seven phase document types (brainstorm, spec, plan, design, impl-plan, analysis, report) are extended so each is a **superset** that keeps the existing h-mad sections AND adds every section the bkit PDCA `REQUIRED_SECTIONS` table requires for that type. The bkit validator (`lib/pdca/template-validator.js`) only validates `plan`/`design`/`report` (detected by path `docs/01-plan|02-design|04-report/...`); those three MUST validate clean. The other four are extended for organizational consistency (minimum: Executive Summary + Version History). Section-matching is by case-insensitive substring of a `##`-level heading; headings must contain the full required phrase, and templates must avoid the `isPlanPlus` trigger strings ("Intent Discovery", "Plan-Plus", "Plan Plus", "Brainstorming-Enhanced") unless plan-plus is intended.
- **Acceptance Criteria**:
  - AC-8.1: For a plan doc generated from the updated template, `validateDocument` returns `valid: true` (zero missing) for type `plan` — i.e. `##` headings cover Executive Summary, Overview, Scope, Requirements, Success Criteria, Risks and Mitigation, Architecture Considerations, Convention Prerequisites, Next Steps, Version History.
  - AC-8.2: For a design doc, `validateDocument` returns clean for type `design` (Executive Summary, Overview, Architecture, Detailed Design, Implementation Order, Test Plan, Version History).
  - AC-8.3: For a report doc, `validateDocument` returns clean for type `report` (Executive Summary, Version History).
  - AC-8.4: The existing h-mad sections for each type are retained (superset, not replacement) — a test/lint asserts the prior h-mad section names still appear in each template.
  - AC-8.5: Generated plan/design/report docs do not accidentally trigger `isPlanPlus` (no banned literal in boilerplate), so they validate against the base type, not `plan-plus`.
  - AC-8.6: This feature's own `plan.md`, `design.md`, and `report.md` validate clean against the bkit hook (dogfood) — no "Missing required sections" warning on write.

### FR-9: Two-layer Axis B invariants — base (skill-shipped) + project (Thrust C)

- **Description**: The audit's Axis B rubric is assembled from two layers: a workflow-universal **base** file shipped with the skill (`~/.claude/skills/h-mad/invariants.base.md`) that is inlined for every project, plus the per-project **domain** file (`<PROJECT_ROOT>/.h-mad/invariants.md`). The audit-prompt assembly inlines base first, then project, into the Axis B section. Base invariants are non-overridable (a project file cannot downgrade a base rule). The base layer holds the workflow-universal rules this feature establishes (audit-gate signal discipline, marker discipline, no-plugin-dependency, doc-template superset compliance, operator-override preservation, backward-compatibility, single-source contract); project files hold only domain rules (e.g. HemaSuite's facade/NLM/Hard-Rule invariants).
- **Acceptance Criteria**:
  - AC-9.1: `~/.claude/skills/h-mad/invariants.base.md` exists, ships with the skill, and contains the workflow-universal Axis B rules.
  - AC-9.2: The audit-prompt assembly (documented in `SKILL.md` §"Audit prompt assembly") inlines base invariants then project invariants into the Axis B slot; a generated audit prompt contains both, base before project.
  - AC-9.3: A project whose `.h-mad/invariants.md` contains only domain rules still has the base rules enforced in its audits (base added by the orchestrator regardless of project-file contents).
  - AC-9.4: Base rules are documented as non-overridable; the assembly labels the base block so a project file cannot silently downgrade a base must-fix. Non-overridability blocks *project-file* downgrade only — it does NOT disable the operator `## Acknowledged-not-fixed` sidecar, which remains a valid conscious deferral path for base-layer findings (Operator-override-preservation invariant). A test/lint asserts a base-layer item listed under a sidecar `## Acknowledged-not-fixed` is excluded from the gate count exactly as a project/Axis-A item.
  - AC-9.5: Backward-compatible: an existing project with only `.h-mad/invariants.md` (no awareness of the base file) gains the base layer automatically — no project-side migration required.
  - AC-9.6: `SKILL.md` bootstrap + audit-assembly sections reference both files; the skills-repo and HemaSuite project invariants files are reduced to domain-only (workflow rules migrated to base).

## Non-Functional Requirements

- **Performance**: N/A (gate runs on small text files; sub-second).
- **Security**: N/A (no new input surface; gate reads local audit files only).
- **Compatibility**:
  - Backward-compatible with existing committed audit docs in the repo: any historical `.audit.v*.md` that previously passed must still pass under the new gate (regression-checked against existing fixtures/files).
  - If awk is retained, the rule must work under both BSD awk (macOS default) and GNU awk.
- **Self-containment**: no new external dependency (FR-6); verdict independent of plugin ecosystem.
- **Hook-clean**: after Thrust B, the bkit PDCA template-compliance hook emits no "Missing required sections" warning for h-mad-generated plan/design/report docs (FR-8).

## Out-of-Scope

- Friction items 2 (Phase-7 merge step), 3 (agy/Codex dispatch helper), 4 (state-init/jsonschema friction), 5 (rotting infra tests) — separate features.
- Renaming `docs/.bkit-memory.json` to drop the bkit filename coupling.
- Internalizing/replacing the intrinsic cmux/agy/codex dispatch CLIs or jq/jsonschema/pytest tooling.
- Patching any file under the OMC plugin tree.
- Redesigning the audit severity taxonomy (what counts as Must vs Should vs Nit).

## Assumptions

- The agy audit reviewer follows the template's empty-marker instruction; the gate is hardened so that even a non-conforming `- None` is handled correctly (defense-in-depth), but the template is the primary guidance.
- The `## Acknowledged-not-fixed` operator-override mechanism (sidecar `.audit.v<N+1>.md`) remains the supported escape and must be preserved unchanged.
- No `/h-mad` feature is mid-flight in the skills repo, so a section-scope change to preconditions.py cannot break an in-progress gate (verified: only this feature is active).
- The exact canonical empty-marker form and the Axis-2 alignment decision are settled in Phase 4 design; this spec fixes the *requirements*, not the chosen marker string.
- The bkit PDCA `REQUIRED_SECTIONS` table is treated as a fixed external contract to conform to; if bkit changes it, the superset templates may need a follow-up (acceptable — it's a versioned external validator).
- The superset section *content/order* per doc type is a Phase-4 design decision; this spec fixes that the required sections must be present and the h-mad sections retained.

## Version History

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-05-28 | Initial spec — Thrust A (audit-gate reconcile, FR-1…FR-7). |
| 1.1 | 2026-05-28 | Added Thrust B (FR-8: superset doc templates compliant with bkit PDCA validator, all 7 phase docs); Executive Summary + Version History; hook-clean NFR. |
| 1.2 | 2026-05-28 | Added Thrust C (FR-9: two-layer Axis B invariants — skill-shipped base + per-project domain); reworded "three reader surfaces" → authoring template + two counting readers. |
