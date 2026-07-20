# H-MAD Base Invariants — Axis B (workflow-universal)

> Shipped with the `/h-mad` skill. The orchestrator inlines this file verbatim into the
> `<INLINE_BASE_INVARIANTS>` slot of every plan / design / impl-plan audit, **before** the
> per-project `<PROJECT_ROOT>/.h-mad/invariants.md` domain layer. These rules apply to every
> project that uses `/h-mad` and are **non-overridable by any project file**: a project's
> invariants file may add domain rules but may not downgrade or delete a base rule. The
> operator `## Acknowledged-not-fixed` sidecar escape hatch still applies to base findings
> (a base item listed under that section in a sidecar `.audit.v<N+1>.md` is a conscious,
> audited deferral — it is excluded from the gate count exactly like any other layer's item).
>
> Axis A (generic adversarial review) is covered by the audit-prompt template — not repeated here.

## Audit-gate signal discipline
- Any gate/check whose verdict the orchestrator consumes MUST communicate PASS/FAIL via an
  explicit **stdout token** and **exit 0** on a normal verdict (PASS or FAIL). Using a non-zero
  process exit to mean "FAIL" is a violation — a non-zero exit registers as a Claude Code tool
  failure (`PostToolUseFailure`) and leaks into coexisting plugins' error handling. A non-zero
  exit is permitted ONLY for genuine operational errors (missing/unreadable input).

## Single-source contract
- A rule applied by more than one surface (e.g. an audit blocking-item count read by both the
  orchestrator gate step and a precondition checker) MUST have exactly one authoritative
  implementation that all surfaces call, OR a test asserting byte-equivalence across surfaces.
  Independent re-implementations that can silently diverge are a violation.
- A contract stated in a template (e.g. an empty-section sentinel) MUST match what the consuming
  gate logic treats as that case. Template guidance and gate behavior disagreeing is a violation.

## Standalone / no plugin dependency
- The skill MUST NOT acquire a **runtime dependency** on any other plugin (OMC, bkit,
  context-mode, etc.) or external skill (spec-kit, b-mad, pdca). Coexistence accommodations
  (sharing a state filename, conforming doc structure to an external validator's required
  sections) are allowed; *requiring another plugin installed at runtime* is a violation.

## No new external dependency
- Scripts MUST use only Python stdlib plus tooling already depended upon by the skill (the
  agent dispatch substrate (cmux or orca, via `hmad-dispatch`); `jq` where the existing hook
  already uses it; `pytest`).
  Introducing a new third-party package or new CLI is a violation.

## Doc-template superset compliance
- Generated phase documents whose type is validated by an external doc-structure validator
  (e.g. bkit PDCA: `plan` → `docs/01-plan/...`, `design` → `docs/02-design/...`,
  `report` → `docs/04-report/...`) MUST be supersets that satisfy that validator's required
  sections AND retain the existing h-mad sections. Dropping an h-mad section or failing the
  validator is a violation.

## Operator-override preservation
- The `## Acknowledged-not-fixed` sidecar override mechanism MUST remain functional for all
  layers (base + project). Any gate change that causes overridden items to still count as
  blocking, or that ignores the sidecar, is a violation.

## Backward compatibility
- A change to the audit gate MUST preserve the PASS verdict for audit docs that passed before
  the change. Flipping a historically-passing audit to FAIL (absent a real new blocking item)
  is a violation.

## Marker discipline
- Orchestrator phase transitions and halts MUST emit `[H-MAD]` log markers so a run is
  diagnosable from logs alone. Silent state transitions are a violation.

---

## How agy uses this file
agy reads this verbatim as the **base** portion of the Axis B rubric, before the project layer.
Any finding that violates a base rule is auto-classified `## Must-fix` and cannot be downgraded.
