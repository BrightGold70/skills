# Plan: h-mad-audit-surfaces-reconcile

## Executive Summary

Three reconciliations in the `/h-mad` skill, delivered together. **Thrust A** fixes the audit gate: the empty-section + blocking-count contract is defined in disagreeing places (the authoring template, the orchestrator gate-step, and `h_mad_do_preconditions.py`) causing false gate-FAILs, and the gate signals its verdict via a non-zero process exit that the Claude Code harness reports as a tool failure — which OMC amplifies into recurring `[TOOL ERROR - RETRY REQUIRED]` noise. **Thrust B** extends h-mad's phase-document templates to a superset that includes the bkit PDCA validator's required sections, so generated plan/design/report docs pass the bkit template-compliance hook. **Thrust C** splits the audit's Axis B rubric into a skill-shipped, workflow-universal base layer plus the existing per-project domain layer, so universal rules are enforced for every project without re-copying. All three are dependency-free and leave the multi-agent dispatch substrate untouched.

## Overview

Single-source the audit-gate contract and switch its verdict to an explicit stdout token (A); extend the seven phase-document templates to a bkit-compliant superset (B); assemble Axis B from a base + project two-layer (C). Net effect: audit cycles stop mis-failing, stop generating OMC retry noise, produce hook-clean docs, and enforce workflow-universal invariants everywhere — a cleaner, self-contained skill.

## Scope

In scope, all within `~/.claude/skills/h-mad/` → `github.com/BrightGold70/skills/h-mad/`: the audit-gate verdict logic and the **three surfaces** that share its contract — one **authoring template** (`audit-prompt.template.md`, which states the empty-marker for the reviewer) plus two **counting readers** (the orchestrator gate-step in `SKILL.md`, and `h_mad_do_preconditions.py`). Only the two counting readers parse the verdict token; the template authors guidance. Also in scope: the seven doc templates in `references/inline-protocols.md`; a new skill-shipped `invariants.base.md` and the audit-assembly wiring; tests under `~/.claude/skills/h-mad/tests/`; and this feature's own docs (dogfood). Excluded items are under Out-of-Scope.

## Goals

- Empty audit sections never count as blocking, in any permitted empty-marker form — FR-1.
- The two counting readers apply an identical per-section blocking-count rule; section-scope handling aligned or documented — FR-2.
- Gate verdict is an stdout token (`GATE: PASS|FAIL`) with `exit 0`; non-zero reserved for operational errors; the rewritten gate-step emits `[H-MAD]` markers on FAIL/halt — FR-3.
- Contract lives in one authoritative implementation both readers use — FR-4.
- OMC coexistence documented in `SKILL.md`; informational upstream note as a report sidecar — FR-5.
- No new external dependency; verdict plugin-independent and self-contained — FR-6.
- Tests for the empty-matrix, token/exit, cross-surface agreement, override — FR-7.
- h-mad phase-document templates extended to a bkit-compliant superset across all 7 doc types; plan/design/report validate clean — FR-8.
- Two-layer Axis B invariants: skill-shipped base + per-project domain, base inlined for every project and non-overridable — FR-9.

## Requirements

Full functional + non-functional requirements are specified in `h-mad-audit-surfaces-reconcile.spec.md` (FR-1…FR-9 + NFRs). This plan maps each FR to a deliverable in the Deliverables table; success is "all ACs pass automated tests" plus the hook-clean, dependency, and base-layer-enforced NFRs. Load-bearing requirements: FR-3 (token-not-exit verdict + `[H-MAD]` markers), FR-4 (single source), FR-8 (superset templates pass the bkit validator), FR-9 (base invariants inlined everywhere).

## Implementation Strategy

**Thrust A** — extract the blocking-item counting + PASS/FAIL decision into one self-contained, tested **python stdlib unit** that is the single source of truth, consumed by both counting readers: the orchestrator gate-step calls it as a CLI (prints `GATE: PASS|FAIL` + counts + a `[H-MAD]` marker line, exits 0) and `h_mad_do_preconditions.py` imports it. This satisfies FR-1 (empty-marker handling defined once), FR-2/FR-4 (one rule, no drift), and FR-3 (token verdict + marker, no exit-code overloading). The template states the canonical empty-marker so reviewer output and the unit's "empty" definition coincide.

**Thrust B** — for each of the seven doc templates in `references/inline-protocols.md`, add the bkit `REQUIRED_SECTIONS` for that type while retaining the existing h-mad sections (superset). Matching is case-insensitive substring against `##`-level headings, so headings must contain the full required phrase (e.g. "Risks and Mitigation", not "Risks"); boilerplate must avoid the extended-variant detector trigger literals. This feature's own plan/design/report are authored to the superset to dogfood the result.

**Thrust C** — add `invariants.base.md` shipped with the skill holding the workflow-universal Axis B rules; update the audit-prompt assembly to inline base-then-project into the Axis B slot, with the base block labeled non-overridable. Migrate the workflow-universal rules out of project invariants files (the skills-repo project file becomes domain-thin; HemaSuite's file is already domain-only and is unaffected except that its audits now also receive the base rules).

**Patterns followed**: single-source-of-truth helper; token-based control signal instead of exit-code overloading; defense-in-depth (template guidance + hardened parser); superset-not-replacement for templates; layered-rubric (base + project) for invariants.

## Architecture Considerations

- **Verdict unit boundary**: a python stdlib module exposing a function that takes an audit-doc path/text and returns `{verdict, must_count, should_count}`; a thin CLI wrapper prints `GATE: PASS|FAIL`, the counts, and a `[H-MAD] <feature> gate <verdict>` marker line, then exits 0. `h_mad_do_preconditions.py` imports the same function for its Must-fix check. Resolved: python for both surfaces (no awk retained), removing BSD/GNU-awk divergence and enforcing the single-source contract.
- **Marker discipline**: the gate-step and any halt path emit `[H-MAD]` markers (FAIL verdict and operational-error halt both marked) so runs are diagnosable from logs alone (Axis B Marker discipline).
- **Signal isolation**: by moving the verdict off the exit code, the gate no longer crosses the harness `PostToolUseFailure` boundary on a FAIL — severing the OMC retry-noise chain at its h-mad-side root.
- **Template layering**: doc templates remain plain markdown skeletons in `inline-protocols.md`; the superset only adds headings + guidance text. The bkit validator is treated as a fixed external contract (versioned).
- **Two-layer Axis B assembly**: the orchestrator inlines `invariants.base.md` first (labeled as non-overridable base), then `<PROJECT_ROOT>/.h-mad/invariants.md`, into the Axis B section of the audit prompt. Base is always present regardless of project-file contents, so existing single-file projects gain the base layer with no migration.
- **Non-overridability scope (operator escape preserved)**: "non-overridable" means a *project invariants file* cannot downgrade or delete a base rule. It does NOT disable the operator `## Acknowledged-not-fixed` sidecar escape hatch — an operator may still defer a base-layer finding via the sidecar exactly as for project-layer or Axis-A findings. Disabling the sidecar for base findings would itself violate the Operator-override-preservation invariant, so the base layer changes *who can downgrade silently* (no project file), not *whether the operator can consciously defer* (still yes, via the audited sidecar).
- **No new coupling**: nothing added depends on OMC/bkit at runtime; bkit is only a *target contract* for doc structure, validated by bkit's own separate hook.

## Convention Prerequisites

- Tooling already present: `python3` stdlib only (no third-party import) for the verdict unit; POSIX shell where the existing hook already uses it; `pytest` for tests; `jq` only where the existing tdd-gate already uses it. No new dependency may be introduced (FR-6 / AC-6.1).
- Tests live in the skill's own hierarchy: `~/.claude/skills/h-mad/tests/` (→ `github.com/BrightGold70/skills/h-mad/tests/`), keeping the skill portable and standalone.
- Doc paths must follow the bkit-detected layout (`docs/01-plan/features/*.plan.md`, `docs/02-design/features/*.design.md`, `docs/04-report/features/*.report.md`) for the validator to type them — h-mad already uses these paths.
- `##`-level headings only are seen by the bkit validator; superset headings must use `##`, contain the required phrase, and avoid the extended-variant detector literals.
- The gate-step and halt paths MUST emit `[H-MAD]` log markers (Axis B Marker discipline).
- The `## Acknowledged-not-fixed` operator-override sidecar mechanism MUST be preserved unchanged.
- `invariants.base.md` ships inside the skill directory and is always inlined; the base block is labeled non-overridable in the assembled prompt.

## Deliverables

| Deliverable | Type | Satisfies |
|---|---|---|
| Single blocking-count + verdict unit — python stdlib, prints token + `[H-MAD]` marker, exit 0 | module / shared logic | FR-1, FR-2, FR-3, FR-4 |
| `h_mad_do_preconditions.py` imports the shared verdict unit | module | FR-2, FR-4 |
| `audit-prompt.template.md` canonical empty-marker | template/doc | FR-1, FR-4 |
| `SKILL.md` gate-step rewrite — token parsing + `[H-MAD]` marker mandate | doc | FR-3 |
| `SKILL.md` "Known interactions" (OMC) subsection | doc | FR-5 |
| Phase-7 informational upstream-note sidecar | doc artifact | FR-5 |
| Dependency-inventory note in feature docs | doc | FR-6 |
| `references/inline-protocols.md` — 7 doc templates extended to bkit-compliant superset | template/doc | FR-8 |
| This feature's plan/design/report authored to the superset (dogfood) | doc | FR-8 (AC-8.6) |
| `invariants.base.md` (skill-shipped, workflow-universal Axis B) | doc | FR-9 |
| `SKILL.md` audit-assembly update — inline base then project | doc | FR-9 |
| Project invariants trimmed to domain-only (skills-repo; HemaSuite already domain-only) | doc | FR-9 (AC-9.6) |
| Test file(s) under `h-mad/tests/`: empty-matrix, token/exit, cross-surface, override, preconditions, bkit-validator pass, base+project assembly order | tests | FR-7, FR-8, FR-9 |

## Design-deferred decisions (resolved in Phase 4, not here)

- **D-a — verdict unit shape**: RESOLVED in this revision — a single python stdlib unit for both counting readers (awk one-liner retired). Recorded here for traceability; no longer open.
- **D-b — Must/Should parity**: align `h_mad_do_preconditions.py` to Must-fix+Should-fix parity with the orchestrator gate, or keep Must-fix-only for the `/h-mad do` precondition (a deliberately looser bar to *enter* autonomous mode) and document the intent.
- **D-c — canonical empty-marker string**: bare `None` vs other; must be stated in the template and recognized by the verdict unit.
- **D-d — workaround framing post-FR-3**: whether `SKILL.md` leads with `DISABLE_OMC=1` or demotes it to "only for the separate Stop-hook nag".
- **D-e — superset section order/content per doc type**: exact merged heading set + ordering + boilerplate for each of the 7 templates, and the overlap mapping (h-mad "Overview"≡bkit "Overview"; h-mad "Risks"→"Risks and Mitigation"; h-mad "Out-of-Scope" already satisfies bkit "Scope" but a distinct "## Scope" is added for clarity).
- **D-f — base/project inline mechanism**: a two-slot template (one base-invariants slot plus one project-invariants slot) vs orchestrator-side concatenation into the existing single invariants slot; and the exact non-overridable labeling. (Slot placeholders are referred to by name in the design doc, never embedded as raw substitutable tokens in plan/design prose, to avoid corruption when these docs are themselves inlined into an audit prompt.)

## Risks and Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| Changing the verdict from exit-code to token breaks a caller that reads `$?` | Gate silently mis-reads as always-pass | Inventory all callers (orchestrator gate step in `SKILL.md`; `preconditions.py` uses the imported function, not exit code); update `SKILL.md` in lockstep; AC-3.4 + cross-surface test guard it |
| Gate-step rewrite omits `[H-MAD]` markers | Failures/halts not diagnosable from logs (Axis B violation) | FR-3 mandates markers; Convention Prerequisites + Deliverables require them; test asserts marker emitted on FAIL |
| New gate logic diverges from historical audit-doc formatting | Previously-passing audits start failing | NFR backward-compat: regression-test against existing committed `.audit.v*.md` |
| Acknowledged-not-fixed override regressed during refactor | Operator escape hatch breaks | AC-7.4 explicit override test; preserve semantics |
| Must/Should parity change alters `/h-mad do` gating | A feature gains/loses ability to enter autonomous mode | Explicit D-b decision; document delta; no in-flight features |
| Superset templates accidentally trigger the extended-variant detector | plan validated against the stricter extended variant → false "missing" | AC-8.5: ban the detector trigger literals in boilerplate; test validates against base type |
| bkit `REQUIRED_SECTIONS` changes in a future bkit version | Superset drifts out of compliance | Treat as versioned external contract; follow-up if bkit changes |
| Base invariants could be silently overridden by a project file | Universal rule downgraded per-project | Inline base first + label non-overridable (AC-9.4); document precedence. The operator `## Acknowledged-not-fixed` sidecar remains valid for base findings (conscious, audited deferral) — only silent project-file downgrade is blocked |
| Existing single-file projects unaware of the base file | Base rules not applied where expected | Orchestrator always inlines base regardless of project-file contents (AC-9.3/9.5); no project migration required |

## Success Criteria

- All ACs (FR-1 … FR-9) pass automated tests.
- Verdict unit returns identical PASS/FAIL with and without OMC/bkit/context-mode present (AC-6.2).
- Running the gate on a failing audit prints `GATE: FAIL`, emits a `[H-MAD]` marker, and exits 0 — no `PostToolUseFailure`/`last-tool-error.json` for that run.
- Existing committed audit docs that previously passed still pass (NFR backward-compat).
- `validateDocument` returns clean for h-mad-generated plan/design/report (FR-8); this feature's own docs emit no bkit "Missing required sections" warning.
- A generated audit prompt for any project contains the base invariants (base before project) in its Axis B section (FR-9); HemaSuite audits now enforce the workflow-universal base rules.
- `SKILL.md` states zero runtime OMC dependency and documents the workaround.

## Next Steps

1. Re-run the Phase 3 audit cycle on this revised plan; iterate until must-fix=0 AND should-fix=0.
2. Phase 4 design: resolve D-b…D-f; produce the design doc (authored to the bkit `design` superset).
3. Phase 5: impl-plan → TDD implementation of the verdict unit, preconditions import, template superset edits, `SKILL.md` edits, `invariants.base.md` + assembly, tests under `h-mad/tests/`.
4. Phase 6: gap analysis ≥90% + 100% test pass.
5. Phase 7: report (bkit `report` superset) + upstream-note sidecar + archive + commit/push.

## Out-of-Scope (confirmed from spec)

- Friction items 2 (Phase-7 merge step), 3 (dispatch helper), 4 (state-init/jsonschema), 5 (rotting infra tests).
- Renaming `docs/.bkit-memory.json`.
- Internalizing cmux/agy/codex or jq/jsonschema/pytest.
- Patching any OMC plugin file.
- Redesigning the audit severity taxonomy.
- The bkit extended-plan and `prd` doc variants (only base plan/design/report targeted).
- A per-feature (third) invariants layer — base + project only.

## Version History

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-05-28 | Initial plan — Thrust A (audit-gate reconcile). |
| 1.1 | 2026-05-28 | Restructured to bkit-PDCA superset layout; added Thrust B (FR-8 doc-template superset). |
| 1.2 | 2026-05-28 | Applied plan-audit v1 fixes (mandate `[H-MAD]` markers in gate-step; clarified three surfaces = 1 template + 2 readers; resolved D-a to python-only; specified test path `h-mad/tests/`; terminology → Must/Should parity). Added Thrust C (FR-9 two-layer base+project invariants) + D-f. |
| 1.3 | 2026-05-28 | Applied plan-audit v2 must-fix: clarified base non-overridability blocks only silent project-file downgrade, NOT the operator `## Acknowledged-not-fixed` sidecar (preserved for base findings). Reworded D-f to drop raw slot tokens (nit — prevents audit-prompt corruption). |
