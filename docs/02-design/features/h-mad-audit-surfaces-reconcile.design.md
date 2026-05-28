# Design: h-mad-audit-surfaces-reconcile

> Source: docs/01-plan/features/h-mad-audit-surfaces-reconcile.plan.md (v1.3, post-audit gate-clean)

## Executive Summary

Concrete design for the three thrusts. **Thrust A**: a new python-stdlib verdict unit `scripts/h_mad_audit_gate.py` becomes the single source of truth for the empty-section + blocking-count contract; it prints a `GATE: PASS|FAIL` token plus a `[H-MAD]` marker and exits 0, and is imported by `h_mad_do_preconditions.py`. **Thrust B**: the seven phase-document templates in `references/inline-protocols.md` gain bkit `REQUIRED_SECTIONS` as a superset. **Thrust C**: a skill-shipped `invariants.base.md` plus a two-slot audit-prompt template assemble Axis B as base-then-project. This document resolves D-b…D-f and specifies file-level changes, interfaces, error handling, the test plan, build order, and invariant compliance.

## Overview

The audit gate's verdict logic is extracted from a `SKILL.md` awk one-liner into a tested python module with two consumption modes (CLI for the orchestrator gate-step, import for the precondition checker). The empty-marker contract is fixed to bare `None` and hardened so a stray `- None` bullet never counts. Document templates become supersets; the Axis B rubric becomes two-layer. All changes live inside the skill directory; no new runtime dependency is introduced.

## Architecture

```
audit-prompt.template.md ──(base slot + project slot)──┐
  invariants.base.md ───────────────────────────────────┤ Axis B (base then project)
  <PROJECT_ROOT>/.h-mad/invariants.md ───────────────────┘

agy audit doc (.audit.vN.md)
        │
        ▼
scripts/h_mad_audit_gate.py   ← SINGLE SOURCE OF TRUTH (counting + verdict)
   ├── classify(text, ack=...) -> {verdict, must_count, should_count}
   ├── CLI: prints "GATE: PASS|FAIL must=N should=M" + "[H-MAD] gate <verdict>", exit 0
   └── imported by ─────────► scripts/h_mad_do_preconditions.py  (uses must_count only)
                              SKILL.md gate-step ──(parses token)──► orchestrator
```

Two counting readers consume one rule; the template authors the empty-marker the rule recognizes. The verdict travels as stdout text, never as the process exit code.

## Components Changed / Added

| Component | File path | Change | Purpose |
|---|---|---|---|
| Verdict unit | `scripts/h_mad_audit_gate.py` | new | Single-source counting + PASS/FAIL token + `[H-MAD]` marker (FR-1/2/3/4) |
| Preconditions | `scripts/h_mad_do_preconditions.py` | modify | Import `classify`; drop the local `_count_must_fix` body in favor of the shared unit (FR-2/4) |
| Audit template | `audit-prompt.template.md` | modify | Canonical bare-`None` empty-marker; add base-invariants slot beside the project slot (FR-1, FR-9/D-f) |
| Orchestrator doc | `SKILL.md` | modify | Gate-step parses token + mandates `[H-MAD]` marker; audit-assembly inlines base then project; "Known interactions" (OMC) subsection (FR-3/5/9) |
| Base invariants | `invariants.base.md` | new | Workflow-universal Axis B rules, shipped with skill (FR-9) |
| Invariants example | `invariants.example.md` | modify | Trim to a domain-only example (workflow rules now live in base) |
| Phase templates | `references/inline-protocols.md` | modify | 7 doc templates → bkit-compliant superset (FR-8) |
| Tests | `tests/test_h_mad_audit_gate.py`, `tests/test_h_mad_doc_templates.py`, `tests/test_h_mad_invariants_layering.py` | new | FR-7/8/9 coverage |
| Skills-repo project invariants | `.h-mad/invariants.md` | modify | Reduce to domain-only (workflow rules migrated to base) (FR-9/AC-9.6) |
| OMC upstream-note sidecar | `docs/04-report/features/h-mad-audit-surfaces-reconcile.omc-upstream-note.md` | new (Phase 7) | Informational OMC interaction note (FR-5) |
| Dependency-inventory note | `## Dependency Inventory` section in `docs/04-report/features/h-mad-audit-surfaces-reconcile.report.md` | new (Phase 7) | Verified dep inventory; zero plugin deps (FR-6) |

## Data Model / Schema Changes

None. No persisted schema change. The verdict unit returns an in-memory dict `{"verdict": "PASS"|"FAIL", "must_count": int, "should_count": int}`. The `orchestrator_state` schema is unchanged.

## API / Interface Changes

- **`h_mad_audit_gate.classify(text: str, acknowledged: set[str] | None = None) -> dict`** — counts blocking bullets in `## Must-fix` and `## Should-fix`. A line counts iff it matches `^- ` AND its stripped remainder lowercased ∉ {`none`} AND its remainder is not in `acknowledged`. Returns `{verdict, must_count, should_count}`; `verdict == "PASS"` iff `must_count == 0 and should_count == 0`.
- **CLI** `python3 scripts/h_mad_audit_gate.py <audit-file> [--ack-file <sidecar>] [--must-only]` — prints `GATE: PASS|FAIL must=N should=M`, then `[H-MAD] <feature> gate <verdict>` (feature derived from filename), exits **0** for any verdict; exits **2** only on operational error (missing/unreadable file, to stderr). `--must-only` reports/PASS-FAILs on `must_count` alone (used by the `/h-mad do` precondition path, D-b).
- **`h_mad_do_preconditions.py`** — replaces local counting with `classify(text, ack)["must_count"]` (Must-fix only; D-b). Public CLI/exit semantics of preconditions unchanged.
- **`audit-prompt.template.md`** — gains a labeled base-invariants block above the project-invariants block (two named slots; D-f). No raw substitution tokens appear in any plan/design prose.

## Detailed Design

### D-c — canonical empty-marker (resolved)
Empty `## Must-fix`/`## Should-fix`/`## Nit` sections are written as bare `None` (no leading `- `). The template instructs the reviewer accordingly. Defense-in-depth: `classify` also excludes any `- None` bullet (stripped, case-insensitive), so a non-conforming reviewer cannot produce a false FAIL. This closes Axis 1 at both the authoring surface (template) and the counting surface (unit).

### D-b — Must/Should parity (resolved)
The per-section *counting rule* is identical across both readers (same `classify`). The *section scope* differs by design: the orchestrator gate (Phase 3/4/5b) requires `must_count == 0 AND should_count == 0`; the `/h-mad do` precondition uses `--must-only` (`must_count == 0`). Rationale: `/h-mad do` force-starts Phase 5 — it must hard-block only on breakage-level Must-fix, not on improvement-level Should-fix. This intentional divergence is documented in `SKILL.md` and `references/phase-table.md`. FR-2/AC-2.1 (identical counting) holds; AC-2.2 (scope documented) satisfied.

### D-d — workaround framing (resolved)
After FR-3, a gate-FAIL no longer emits a non-zero exit, so it no longer triggers `PostToolUseFailure` → the OMC retry-guidance chain is severed at the root. `SKILL.md` "Known interactions" therefore documents: (1) retry-guidance noise is fixed at root by the token verdict — no workaround needed; (2) `DISABLE_OMC=1` / `OMC_SKIP_HOOKS=persistent-mode` remains relevant ONLY for the separate autopilot Stop-hook nag (friction item 6, not addressed here).

### D-e — superset section sets per doc type (resolved)
Each template keeps its h-mad sections and adds the bkit `REQUIRED_SECTIONS` for its type (substring match against `##` headings; avoid extended-variant detector literals). Overlap mapping: h-mad "Risks" → "Risks and Mitigation"; "Out-of-Scope" already satisfies bkit "Scope" but a distinct `## Scope` is added; "Test Strategy" retained alongside a new `## Test Plan`. Only `plan`/`design`/`report` are bkit-validated; brainstorm/spec/impl-plan/analysis get Executive Summary + Version History for consistency.

| Doc type | Superset `##` sections (h-mad retained + bkit added) |
|---|---|
| brainstorm | Executive Summary*, Problem Statement, Proposed Approach, Alternatives Considered, Risks & Mitigations, Dependencies, Open Questions, Version History* |
| spec | Executive Summary, Goal, Scope*, Functional Requirements, Non-Functional Requirements, Out-of-Scope, Assumptions, Version History |
| plan | Executive Summary, Overview, Scope, Goals, Requirements, Implementation Strategy, Architecture Considerations, Convention Prerequisites, Deliverables, Risks and Mitigation, Success Criteria, Next Steps, Out-of-Scope, Version History |
| design | Executive Summary, Overview, Architecture, Components Changed/Added, Data Model/Schema Changes, API/Interface Changes, Detailed Design, Error Handling Strategy, Test Plan, Test Strategy, Implementation Order, Invariant Compliance, Version History |
| impl-plan | Executive Summary*, Overview*, Task N…, Implementation Order*, Test Plan*, Version History* |
| analysis | Executive Summary*, (match-rate analysis body), Version History* |
| report | Executive Summary, (outcome body), Version History |

(*) added for organizational consistency; not bkit-validated for that type.

### D-f — base/project inline mechanism (resolved)
Two-slot template. `audit-prompt.template.md` carries a base-invariants block (header: "BASE INVARIANTS — workflow-universal, non-overridable by project files; operator `## Acknowledged-not-fixed` sidecar still applies") above the project-invariants block. The orchestrator inlines `invariants.base.md` into the base slot and `<PROJECT_ROOT>/.h-mad/invariants.md` into the project slot. Base is always present even if the project file is absent/empty (AC-9.3/9.5). Slot names are referenced descriptively in this design — never embedded as raw substitutable tokens — so this doc can itself be inlined into an audit prompt without corruption.

### Verdict unit counting algorithm
Iterate lines; set `section` on `^## Must-fix`/`^## Should-fix`/`^## Acknowledged-not-fixed`/other `^## `. Collect Acknowledged-not-fixed item texts into `ack`. A Must/Should line counts iff `^- ` and stripped-remainder lower ∉ {`none`} and remainder ∉ `ack`. This preserves the operator sidecar for all layers including base findings.

### Phase-7 artifacts (FR-5 sidecar, FR-6 dependency note) — paths + format + generation
- **OMC upstream-note sidecar (FR-5)** — path `docs/04-report/features/h-mad-audit-surfaces-reconcile.omc-upstream-note.md`. Plain markdown, informational. Sections: (1) Observed interaction — `persistent-mode.mjs` reads `last-tool-error.json` written by `post-tool-use-failure.mjs` on `PostToolUseFailure`, surfacing `[TOOL ERROR - RETRY REQUIRED]`; (2) Root cause — h-mad's prior gate used a non-zero exit as the verdict; (3) Resolution — fixed h-mad-side by the token verdict (FR-3); OMC behavior is correct given a real non-zero exit, so this is informational, not a bug report. Generated in Phase 7 closure by authoring the file; MUST NOT modify any file under the OMC plugin tree.
- **Dependency-inventory note (FR-6)** — a `## Dependency Inventory` section appended to the Phase-7 report (`docs/04-report/features/h-mad-audit-surfaces-reconcile.report.md`). Records the verified inventory: intrinsic CLIs (cmux/agy/codex), tooling (jq/jsonschema/pytest), and **zero plugin dependencies** (OMC = 0 refs; bkit = filename + doc-structure-target only). Generated in Phase 7 from the inventory established this feature; a test (`test_h_mad_invariants_layering.py` or a dedicated check) is not required, but the note's presence is part of the Phase-7 report checklist.

## Error Handling Strategy

- Verdict unit: operational errors (file missing/unreadable) → message to stderr + exit 2 (distinct from the verdict's exit 0). Never raises on a normal FAIL.
- `classify` is pure (no I/O) and total over any string input — malformed markdown yields counts, never an exception.
- Orchestrator gate-step: parses the `GATE:` token from stdout; if the token is absent (unexpected), treat as operational error and halt `step3|4|5b:gate_token_missing` with a `[H-MAD]` marker (fail-closed, not silent-pass).
- Assembly: if `invariants.base.md` is missing, halt `audit:base_invariants_missing` (base layer is mandatory) rather than silently auditing without it.

## Test Plan

Tests live under `~/.claude/skills/h-mad/tests/` (skills-repo `h-mad/tests/`), pytest. Mapping:

- `test_h_mad_audit_gate.py` — FR-1 empty-matrix (bare `None`, `- None`, header-only, real bullet); FR-3 token+exit0 for PASS/FAIL, exit2 on missing file, `[H-MAD]` marker present on FAIL; FR-7 Acknowledged-not-fixed exclusion (incl. a base-layer item); `--must-only` mode.
- `test_h_mad_doc_templates.py` — FR-8: render/lint each of the 7 templates; assert bkit `validateDocument` clean for plan/design/report; assert h-mad section names retained (AC-8.4); assert no extended-variant trigger literal (AC-8.5). The bkit-validator assertions `pytest.skip` when node/the validator is absent (portability); the literal/section-name assertions run unconditionally (pure text checks).
- `test_h_mad_invariants_layering.py` — FR-9: assembled audit prompt contains base then project (AC-9.2); base present when project file empty/absent (AC-9.3/9.5); base block labeled non-overridable (AC-9.4); base-layer item under sidecar is excluded by `classify` (AC-9.4 operator-override).
- Cross-surface: assert `h_mad_do_preconditions` Must-fix count == `classify(...)['must_count']` over a shared fixture set (FR-2/AC-2.1, FR-4/AC-4.1).
- Backward-compat: existing committed `.audit.v*.md` that passed under the awk gate still PASS under `classify` (NFR).

## Test Strategy

Unit-level for `classify` (pure function, exhaustive matrix). Subprocess-level for the CLI (token/exit/marker). Doc-lint via the bkit validator invoked from a node subprocess. No mocking of the filesystem boundary beyond tmp fixtures. The bkit validator is treated as an external oracle, not re-implemented.

**Portability — graceful skip**: the bkit-validator-dependent tests (`test_h_mad_doc_templates.py`) MUST detect absence of the validator (`shutil.which("node")` is None, or the bkit `template-validator.js` path does not exist) and `pytest.skip(...)` with a clear reason rather than fail. This keeps the skill's own test suite green on a bare clone where neither node nor the bkit plugin is installed, satisfying the Standalone invariant. The `classify`/CLI tests (the core FR-1/3/7 coverage) have no such dependency and always run.

## Implementation Order

1. `h_mad_audit_gate.py` (`classify` + CLI) + `test_h_mad_audit_gate.py` — Thrust A core.
2. `h_mad_do_preconditions.py` imports `classify` + cross-surface test — Thrust A finish.
3. `audit-prompt.template.md` bare-`None` marker + two-slot — D-c/D-f.
4. `invariants.base.md` + `SKILL.md` audit-assembly (base then project) + `test_h_mad_invariants_layering.py` — Thrust C.
5. `SKILL.md` gate-step token rewrite + `[H-MAD]` marker + "Known interactions" — Thrust A docs + FR-5/D-d.
6. `references/inline-protocols.md` 7-template superset + `test_h_mad_doc_templates.py` — Thrust B (D-e).
7. Trim skills-repo `.h-mad/invariants.md` + `invariants.example.md` to domain-only — FR-9/AC-9.6.
8. Dependency-inventory note + full suite + bkit-validator pass — FR-6.

## Invariant Compliance

Axis B (base layer this feature establishes):
- **Audit-gate signal discipline** — complies: verdict is stdout token + exit 0 (FR-3).
- **Single-source contract** — complies: one `classify` consumed by both readers (FR-4).
- **Standalone / no plugin dependency** — complies: no runtime OMC/bkit dependency; bkit only a doc-structure target.
- **No new external dependency** — complies: python stdlib + existing tooling only.
- **Doc-template superset compliance** — complies: FR-8 + dogfood; this design validates as bkit `design`.
- **Operator-override preservation** — complies: `classify` excludes Acknowledged-not-fixed items for all layers incl. base.
- **Backward compatibility** — complies: NFR regression test on historical audits.
- **Marker discipline** — complies: gate-step + halts emit `[H-MAD]`.

Project layer: the skills-repo domain invariants (post-trim) are non-domain-heavy; no HemaSuite domain rule applies to this repo. This design requires no invariant update.

## Version History

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-05-28 | Initial design — resolves D-b…D-f; specifies verdict unit, two-slot Axis B, 7-template superset, test plan, build order, invariant compliance. Authored to bkit `design` superset. |
| 1.1 | 2026-05-28 | Applied design-audit v1 should-fixes: specified Phase-7 upstream-note sidecar + dependency-inventory note paths/format/generation (FR-5/FR-6); mandated bkit-validator template tests `pytest.skip` when node/validator absent (portability). |
