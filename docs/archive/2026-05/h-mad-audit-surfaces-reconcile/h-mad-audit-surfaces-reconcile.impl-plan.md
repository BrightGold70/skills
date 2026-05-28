# Implementation Plan: h-mad-audit-surfaces-reconcile

> Source: docs/02-design/features/h-mad-audit-surfaces-reconcile.design.md (v1.1, post-audit)
> Branch target: feature/001-h-mad-audit-surfaces-reconcile
> All paths relative to repo root `~/Coding/skills/` (skill dir = `h-mad/`).
> Tasks ordered as a DAG: Task 1 → 2 (code); 3 → 4 (assembly); 5/6/7 (docs); 8 (closure).

## Task 1: audit-gate verdict unit

**Production file**: `h-mad/scripts/h_mad_audit_gate.py`
**Test file**: `h-mad/tests/test_h_mad_audit_gate.py`

**Description**: The single source of truth for the empty-section + blocking-count contract. A pure `classify` function counts blocking bullets in `## Must-fix` and `## Should-fix`, excluding the empty sentinel and operator-acknowledged items. A CLI wrapper prints the verdict token plus a `[H-MAD]` marker and always exits 0 on a verdict (exit 2 only on operational error). Replaces the `SKILL.md` awk one-liner.

**Code structure**:
```python
def classify(text: str, acknowledged: set[str] | None = None) -> dict:
    """Count blocking bullets in Must-fix/Should-fix. Returns {verdict, must_count, should_count}."""
    ...

def _is_blocking_bullet(line: str, acknowledged: set[str]) -> bool:
    """True iff line matches '^- ' and stripped-remainder.lower() not in {'none'} and remainder not in acknowledged."""
    ...

def main(argv: list[str] | None = None) -> int:
    """CLI: <audit-file> [--ack-file F] [--must-only]; prints 'GATE: PASS|FAIL must=N should=M' + '[H-MAD] <feature> gate <verdict>'; exit 0 on verdict, 2 on operational error."""
    ...
```

**Acceptance Criteria**:
- [ ] AC-1.1: `classify("## Must-fix\nNone\n## Should-fix\nNone\n")` → `{"verdict":"PASS","must_count":0,"should_count":0}` (bare None; FR-1).
- [ ] AC-1.2: `classify("## Must-fix\n- None\n## Should-fix\nNone\n")` → `must_count==0` (stray `- None` excluded; FR-1 defense-in-depth).
- [ ] AC-1.3: `classify("## Must-fix\n- real issue — why\n")` → `must_count==1, verdict=="FAIL"` (FR-1).
- [ ] AC-1.4: header-only section (no body line) → count 0.
- [ ] AC-1.5: items under `## Acknowledged-not-fixed` passed via `acknowledged` are excluded from counts (FR-7/operator override, incl. base-layer items).
- [ ] AC-1.6: CLI on a clean file prints `GATE: PASS must=0 should=0` + a line containing `[H-MAD]` and `gate PASS`, exit 0 (FR-3 AC-3.1).
- [ ] AC-1.7: CLI on a dirty file prints `GATE: FAIL` with counts + `[H-MAD]` marker, exit 0 (FR-3 AC-3.2).
- [ ] AC-1.8: CLI on a missing file → stderr message, exit 2 (FR-3 AC-3.3).
- [ ] AC-1.9: `--must-only` flag bases the verdict on `must_count` alone (D-b; for the `/h-mad do` precondition path).
- [ ] AC-1.10: no third-party import — `python3 -c "import ast; ..."` confirms only stdlib (FR-6 AC-6.1).

**Dependencies on other tasks**: None.

## Task 2: preconditions consumes the shared unit

**Production file**: `h-mad/scripts/h_mad_do_preconditions.py`
**Test file**: `h-mad/tests/test_h_mad_preconditions_shared.py`

**Description**: Replace the local `_count_must_fix` body with a call to `h_mad_audit_gate.classify(...)['must_count']` (Must-fix only, per D-b). Public CLI flags + exit semantics of preconditions remain unchanged.

**Code structure**:
```python
from h_mad_audit_gate import classify  # same scripts/ dir

def _count_must_fix(path: Path) -> int:
    return classify(path.read_text())["must_count"]
```

**Acceptance Criteria**:
- [ ] AC-2.1: For a shared fixture set, `_count_must_fix(f)` equals `classify(f.read_text())['must_count']` (FR-2 AC-2.1, FR-4 AC-4.1).
- [ ] AC-2.2: `- None` in a fixture's Must-fix no longer inflates the precondition DIRTY count (regression of the original bug).
- [ ] AC-2.3: existing preconditions CLI behavior (MISSING/DIRTY/OK + exit codes) unchanged for non-empty-sentinel fixtures.

**Dependencies on other tasks**: Task 1.

## Task 3: audit template — empty marker + two-slot

**Production file**: `h-mad/audit-prompt.template.md`
**Test file**: `h-mad/tests/test_h_mad_invariants_layering.py` (assembly assertions)

**Description**: State the canonical bare-`None` empty marker in the output schema. Add a labeled base-invariants block above the project-invariants block (two named slots), with a header stating base rules are non-overridable by project files while the operator `## Acknowledged-not-fixed` sidecar still applies.

**Acceptance Criteria**:
- [ ] AC-3.1: template instructs bare `None` (no leading `- `) for empty sections; a test asserts the exact marker string the verdict unit treats as empty (FR-1 AC-1.4).
- [ ] AC-3.2: template contains a base-invariants slot and a project-invariants slot, base above project, base block labeled non-overridable (FR-9/D-f).

**Dependencies on other tasks**: None (text), but co-validated with Task 4.

## Task 4: base invariants + assembly wiring

**Production files**: `h-mad/invariants.base.md` (new), `h-mad/SKILL.md` (audit-assembly section)
**Test file**: `h-mad/tests/test_h_mad_invariants_layering.py`

**Description**: Add `invariants.base.md` holding the workflow-universal Axis B rules. Update `SKILL.md` §"Audit prompt assembly" so the orchestrator inlines base-then-project into the Axis B slots; base always present even if the project file is absent/empty.

**Acceptance Criteria**:
- [ ] AC-4.1: `h-mad/invariants.base.md` exists with the workflow-universal rules (FR-9 AC-9.1).
- [ ] AC-4.2: a simulated assembly (base file + project file) yields Axis B with base before project (FR-9 AC-9.2).
- [ ] AC-4.3: with an empty/absent project file, base rules still present (FR-9 AC-9.3/9.5).
- [ ] AC-4.4: base block labeled non-overridable; a base item under a sidecar `## Acknowledged-not-fixed` is still excluded by `classify` (FR-9 AC-9.4 + Task 1 AC-1.5).

**Dependencies on other tasks**: Task 3 (template slots), Task 1 (classify for AC-4.4).

## Task 5: SKILL.md gate-step rewrite + Known interactions

**Production file**: `h-mad/SKILL.md`
**Test file**: `h-mad/tests/test_h_mad_doc_templates.py` (doc-lint: token-step present, no `exit (c>0)` verdict)

**Description**: Rewrite the §"Audit prompt assembly" gate step (step 10) to call `h_mad_audit_gate.py` and parse the `GATE:` token (not `$?`/`exit (c>0)`), and to require a `[H-MAD]` marker on FAIL/halt. Add a "Known interactions" subsection documenting the OMC Stop-hook nag + tool-error retry-guidance, the shared `persistent-mode.mjs` root, the `DISABLE_OMC=1`/`OMC_SKIP_HOOKS=persistent-mode` workaround (demoted post-FR-3 to "only for the Stop-hook nag"), and that h-mad has zero runtime OMC dependency.

**Acceptance Criteria**:
- [ ] AC-5.1: gate-step parses the `GATE:` token; the doc no longer instructs `exit (c>0)`/`$?` for the verdict (FR-3 AC-3.4).
- [ ] AC-5.2: gate-step mandates a `[H-MAD]` marker on FAIL/halt (FR-3 marker discipline).
- [ ] AC-5.3: "Known interactions" names both OMC noise sources, the root file, the workaround env vars, and states zero OMC runtime dependency (FR-5 AC-5.1/5.3).

**Dependencies on other tasks**: Task 1 (the CLI it calls).

## Task 6: 7 doc-template superset

**Production file**: `h-mad/references/inline-protocols.md`
**Test file**: `h-mad/tests/test_h_mad_doc_templates.py`

**Description**: Extend each of the 7 phase-doc templates to the superset section sets in the design's D-e table (h-mad sections retained + bkit `REQUIRED_SECTIONS` added). Avoid the extended-variant detector literals.

**Acceptance Criteria**:
- [ ] AC-6.1: a doc generated from each of the plan/design/report templates passes bkit `validateDocument` (FR-8 AC-8.1/8.2/8.3) — test `pytest.skip`s if node/validator absent (portability).
- [ ] AC-6.2: each template retains its prior h-mad section names (FR-8 AC-8.4) — pure text assertion, always runs.
- [ ] AC-6.3: no template boilerplate contains an extended-variant detector literal (FR-8 AC-8.5) — pure text assertion.

**Dependencies on other tasks**: None.

## Task 7: trim project invariants to domain-only

**Production files**: `h-mad/invariants.example.md`, repo `.h-mad/invariants.md` (skills-repo project layer)
**Test file**: `h-mad/tests/test_h_mad_invariants_layering.py` (no workflow-rule duplication between base and example)

**Description**: Move the workflow-universal rules out of `invariants.example.md` (leave a domain-only worked example) and trim the skills-repo `.h-mad/invariants.md` to domain-only, since the workflow rules now live in `invariants.base.md` (FR-9 AC-9.6).

**Acceptance Criteria**:
- [ ] AC-7.1: `invariants.example.md` no longer duplicates the base workflow rules; a test asserts no base-rule heading appears verbatim in both base and example (FR-9 AC-9.6).
- [ ] AC-7.2: skills-repo `.h-mad/invariants.md` reduced to domain-only (or a thin placeholder) — base rules absent.

**Dependencies on other tasks**: Task 4 (base file must exist first).

## Task 8: dependency-inventory note + full suite

**Production file**: (doc) dependency-inventory section staged for the Phase-7 report; verify-all
**Test file**: full `h-mad/tests/` run

**Description**: Record the verified dependency inventory (for the Phase-7 report's `## Dependency Inventory`). Run the full test suite; all green (bkit-validator tests skip if node absent).

**Acceptance Criteria**:
- [ ] AC-8.1: dependency-inventory content drafted (intrinsic cmux/agy/codex; tooling jq/jsonschema/pytest; zero plugin deps) for Phase-7 (FR-6 AC-6.3).
- [ ] AC-8.2: `pytest h-mad/tests/ -q` → 100% pass (skips allowed for validator-absent).
- [ ] AC-8.3: backward-compat — existing committed `.audit.v*.md` that passed under the awk gate still classify PASS (NFR).

**Dependencies on other tasks**: Tasks 1–7.
