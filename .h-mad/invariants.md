# H-MAD Project Invariants — Axis B Rubric (BrightGold70/skills repo)

> Inlined verbatim by `/h-mad` as the Axis B section of every plan/design/impl-plan audit.
> Scope: this repository is a collection of Claude Code **skills** (markdown `SKILL.md` +
> `references/*.md` + `scripts/*.py` + `hooks/*.sh`). Axis B rules below are the load-bearing
> architectural rules an auditor must enforce as hard gates for skill development here.
> Axis A (generic adversarial review) is covered by the audit-prompt template — not repeated here.

## Audit-gate signal discipline
- Any gate/check whose verdict is consumed by the orchestrator MUST communicate PASS/FAIL via an
  explicit **stdout token** and **exit 0** on a normal verdict (PASS or FAIL). Using a non-zero
  process exit to mean "FAIL" is a violation — a non-zero exit registers as a Claude Code tool
  failure (`PostToolUseFailure`) and leaks into coexisting plugins' error handling.
- A non-zero exit is permitted ONLY for genuine operational errors (missing/unreadable input).

## Single-source contract
- A rule applied by more than one surface (e.g. the audit blocking-item count, read by both the
  orchestrator gate step and `scripts/h_mad_do_preconditions.py`) MUST have exactly one
  authoritative implementation that all surfaces call, OR a test that asserts byte-equivalence of
  the rule across surfaces. Independent re-implementations that can silently diverge are a violation.
- A documented contract stated in a template (e.g. an empty-section sentinel) MUST match what the
  consuming gate logic treats as that case. Template guidance and gate behavior disagreeing is a violation.

## Standalone / no plugin dependency
- The skill MUST NOT acquire a **runtime dependency** on any other plugin (OMC, bkit, context-mode,
  caveman, etc.) or external skill (spec-kit, b-mad, pdca). Coexistence accommodations (sharing the
  `docs/.bkit-memory.json` state filename, conforming doc structure to an external validator's
  required sections) are allowed; *requiring another plugin to be installed at runtime* is a violation.

## No new external dependency
- Scripts MUST use only Python stdlib plus tooling already depended upon by the skill
  (the cmux/agy/codex dispatch substrate; `jq` only where the existing hook already uses it;
  `pytest`). Introducing a new third-party package or new CLI is a violation.

## Doc-template superset compliance
- Generated phase documents whose type is validated by the bkit PDCA validator
  (`plan` → `docs/01-plan/...`, `design` → `docs/02-design/...`, `report` → `docs/04-report/...`)
  MUST be supersets that (a) satisfy that type's bkit `REQUIRED_SECTIONS` by `##`-heading substring
  match AND (b) retain the existing h-mad sections. Dropping an h-mad section or failing the bkit
  validator is a violation. Boilerplate MUST NOT contain the `isPlanPlus` trigger literals
  ("Intent Discovery", "Plan-Plus", "Plan Plus", "Brainstorming-Enhanced") unless the extended
  variant is intended.

## Operator-override preservation
- The `## Acknowledged-not-fixed` sidecar override mechanism MUST remain functional. Any gate change
  that causes overridden items to still count as blocking (or that ignores the sidecar) is a violation.

## Backward compatibility
- A change to the audit gate MUST preserve the PASS verdict for audit docs that passed before the change.
  A change that flips a historically-passing audit to FAIL (absent a real new blocking item) is a violation.

## Marker discipline
- Orchestrator phase transitions and halts MUST emit `[H-MAD]` log markers so a run is diagnosable
  from logs alone. Silent state transitions are a violation.

---

## How agy uses this file
agy reads this verbatim as the Axis B section of the audit rubric. Any finding that violates an
Axis B rule is auto-classified `## Must-fix` regardless of how minor it looks — it cannot be
downgraded to Should-fix or Nit.
