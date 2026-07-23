# Implementation Plan: cycle-telemetry-fidelity

> Source: docs/02-design/features/cycle-telemetry-fidelity.design.md (post-audit v1.1, gate PASS)
> Branch target: feature/190-cycle-telemetry-fidelity

## Executive Summary

Five tasks: a new stdlib-only derivation module, its two telemetry call sites, a delegation
refactor that removes the duplicate `v<N>` implementation, the Phase 6/6b protocol change with a
doc-contract test, and a SKILL.md documentation update.

## Task 1: cycle-count derivation module

**Production file**: `h-mad/scripts/h_mad_cycle_counts.py`
**Test file**: `h-mad/tests/test_h_mad_cycle_counts.py`

**Description**: Single source for discovering `<stem>.v<N>.md` artifacts and deriving both cycle
counts. Pure functions over an explicit docs root — no state file, no printing, no writing.
Stdlib only (`pathlib`, `re`); importing `jsonschema` is a defect, because telemetry must keep
running under the bare `python3` that the state scripts cannot use.

**Code structure**:
```python
PHASE_SEGMENTS: dict[str, str] = {"plan": "plan", "design": "design", "impl_plan": "impl-plan"}

def audit_artifacts(docs_root: Path, feature: str, phase: str, *,
                    include_archive: bool = True) -> dict[int, Path]:
    """Map cycle number -> audit file for one phase. Empty when none exist."""
    ...

def analysis_artifacts(docs_root: Path, feature: str, *,
                       include_archive: bool = True) -> dict[int, Path]:
    """Map cycle number -> versioned gap-analysis file. Empty when none exist."""
    ...

def latest_audit_path(docs_root: Path, feature: str, phase: str, *,
                      include_archive: bool = True) -> Path | None:
    """Audit file with the highest cycle number, or None."""
    ...

def audit_cycles(docs_root: Path, feature: str) -> dict[str, int]:
    """{"plan": N, "design": N, "impl_plan": N} — max cycle reached, 0 when absent."""
    ...

def iterate_cycles(docs_root: Path, feature: str) -> int:
    """max(N) - 1 over analysis artifacts, floored at 0."""
    ...
```

Search roots — audit family: `docs/01-plan/features`, `docs/02-design/features`, plus
`docs/archive/*/<feature>` when `include_archive`. Analysis family: `docs/03-analysis`, plus the
same archive glob. `docs/templates` is never a search root.

Glob patterns, stated exactly: audit family `f"{feature}.{seg}.audit.v*.md"` where `seg` comes
from `PHASE_SEGMENTS`; analysis family `f"{feature}.analysis.v*.md"`.

Matching: glob on the literal stem, then re-filter every
candidate with `p.name.startswith(f"{feature}.")` — a case-sensitive check in Python, because the
default macOS filesystem is case-insensitive and would otherwise match `Feat`. Version parsing:
`re.compile(r"\.v(\d+)\.md$")` against `Path.name`; a non-matching name is skipped, never raised
on. An `OSError` from one root is caught and treated as "no artifacts here" so it cannot mask
counts found under the others.

**Acceptance Criteria**:
- [ ] AC-1.1: `f.plan.audit.v1.md` + `f.plan.audit.v2.md` → `audit_cycles(...)["plan"] == 2`
- [ ] AC-1.2: no audit files for a phase → that phase is `0`
- [ ] AC-1.3: `v1` and `v3` present, `v2` absent → `3`
- [ ] AC-1.4: `f.plan.audit.v2.md` + `f.impl-plan.audit.v1.md` → `{"plan": 2, "design": 0, "impl_plan": 1}`
- [ ] AC-1.5: `audit_cycles`, `iterate_cycles`, and `latest_audit_path` all delegate to the two
      `*_artifacts` functions — no second glob or version regex anywhere in the module or its callers
- [ ] AC-3.1: only `f.analysis.v1.md` → `iterate_cycles(...) == 0`
- [ ] AC-3.2: `f.analysis.v1.md`..`v4.md` → `3`
- [ ] AC-3.3: no versioned analysis files → `0`
- [ ] AC-3.4: unversioned `f.analysis.md` alone → `analysis_artifacts(...) == {}` and `iterate_cycles(...) == 0`
- [ ] AC-6.1: audit artifacts found under `docs/01-plan/features` and `docs/02-design/features`
- [ ] AC-6.2: audit and analysis artifacts found under `docs/archive/2026-07/<feature>/`
- [ ] AC-6.3: `v1` live + `v3` archived → `3`
- [ ] AC-6.4: analysis artifacts found under `docs/03-analysis`
- [ ] AC-7.1: deriving for `feat` ignores `feat-ab.plan.audit.v9.md` → `0`
- [ ] AC-7.2: `docs/templates/audit-example.audit.v1.md` contributes to no feature's count
- [ ] AC-7.3: a file named `f.plan.audit.vX.md` is ignored and does not raise
- [ ] AC-7.4: `Feat.plan.audit.v1.md` present, deriving for `feat` → `0` (fails a glob-only
      implementation on macOS, which is the point)
- [ ] AC-NFR-1: `sys.modules` has no `jsonschema` after importing the module; the module's source
      contains no `import jsonschema`
- [ ] AC-LIVE-1: against the real repo `docs/` root — `orca-git-native-checkpoints-and-merge-gate`
      → `{"plan": 2, "design": 2, "impl_plan": 1}`; `worktree-parallel-multi-module-tdd` →
      `{"plan": 3, "design": 2, "impl_plan": 2}`; `dispatch-resolve-verb` →
      `{"plan": 2, "design": 1, "impl_plan": 1}`
- [ ] AC-EMPTY-1: for a feature with no analysis files `analysis_artifacts(...) == {}`; for one
      with `analysis.v1.md` it is `{1: <path>}` — both yield `iterate_cycles == 0`, and the
      mapping is what distinguishes them

**Dependencies on other tasks**: None

---

## Task 2: telemetry derives its counts

**Production file**: `h-mad/scripts/h_mad_telemetry.py`
**Test file**: `h-mad/tests/test_h_mad_telemetry.py`

**Description**: `cmd_record` and `cmd_summary` take their two counters from Task 1 instead of
from the state record. Both gain an optional `--docs-root`. `cmd_summary` additionally applies
the per-family fallback and computes its drift warnings from the displayed values.

**Code structure**:
```python
from pathlib import Path

from h_mad_cycle_counts import analysis_artifacts, audit_artifacts, audit_cycles, iterate_cycles

def resolve_docs_root(docs_root: str | None, state_path: Path) -> Path:
    """--docs-root when given; else the state file's parent when it is named 'docs'; else Path('docs')."""
    ...
```

In `cmd_record`, the two `feat_state.get(...)` reads for `audit_cycles` / `iterate_cycles` are
replaced by calls to Task 1. Everything else about the row is unchanged, including
`schema_version = 1`, and the existing exit paths (2 = feature absent, 3 = state missing or
malformed) are reached in the same order as today.

In `cmd_summary`, for each displayed row: derive both families; if
`audit_artifacts(...)` is empty for every phase use the row's stored `audit_cycles`, and
independently, if `analysis_artifacts(...)` is empty use the row's stored `iterate_cycles`.
Emptiness of the mapping is the trigger — never a count of zero. Derivation happens before the
warning loop so the warnings see displayed values.

**Acceptance Criteria**:
- [ ] AC-4.1: state record has `audit_cycles: {plan:0,design:0,impl_plan:0}` but artifacts exist
      on disk → the appended row carries the derived non-zero counts
- [ ] AC-4.2: invoked as `record --state <tmp>/docs/.bkit-memory.json` with no `--docs-root`, the
      docs root resolves to `<tmp>/docs`
- [ ] AC-4.3: feature absent from state → exit 2; state file missing → exit 3; state file
      malformed JSON → exit 3
- [ ] AC-4.4: no artifacts on disk → row records zeros, exit 0, no exception
- [ ] AC-5.1: a stored row with zero counts displays the derived counts when artifacts exist
- [ ] AC-5.2: a stored row with `audit_cycles.plan = 4` and **no** artifacts on disk displays `4`
- [ ] AC-5.3: `.h-mad/telemetry.jsonl` bytes are identical before and after `summary`
- [ ] AC-5.4: artifacts giving `plan = 4` produce the
      `WARN: ... audit_cycles > 3` line on stdout
- [ ] AC-5.5: `summary --docs-root <path>` uses that path
- [ ] AC-CLI-1: `record` and `summary` still accept every flag they accept today with unchanged
      defaults

**Dependencies on other tasks**: Task 1

---

## Task 3: remove the duplicate latest-audit implementation

**Production file**: `h-mad/scripts/h_mad_do_preconditions.py`
**Test file**: `h-mad/tests/test_h_mad_preconditions_shared.py` (existing — extend, do not rewrite)

**Description**: `_latest_audit` and `AUDIT_VERSION_RE` are a second implementation of Task 1's
rule. Delete both and delegate. Behaviour must not change: this checker gates `/h-mad do` on a
**live** audited plan and design, so it passes `include_archive=False`. If it began accepting
archived audits, a previously-shipped feature's artifacts could satisfy the precondition for new
work reusing that name.

**Code structure**:
```python
from h_mad_cycle_counts import latest_audit_path
# AUDIT_VERSION_RE deleted; _latest_audit deleted.
# call sites inside check() become:
plan_audit = latest_audit_path(repo_root / "docs", feature, "plan", include_archive=False)
design_audit = latest_audit_path(repo_root / "docs", feature, "design", include_archive=False)
```

Note the signature shift: the old helper took a `features_dir`, the new one takes a **docs root**
and a phase. No new parameter is needed — `check(repo_root: Path, feature: str)` already receives
`repo_root` (`h_mad_do_preconditions.py:43`), so `repo_root / "docs"` is directly available at
both call sites. The existing `plan_features` / `design_features` locals stay as they are, because
they are still used to build the `MISSING:` message strings.

**Acceptance Criteria**:
- [ ] AC-3T-1: every existing test in `test_h_mad_preconditions_shared.py` and
      `test_h_mad_do_preconditions*` passes unmodified
- [ ] AC-3T-2: `AUDIT_VERSION_RE` and `_latest_audit` no longer appear in
      `h_mad_do_preconditions.py`
- [ ] AC-3T-3: a feature whose only audits live under `docs/archive/` does **not** satisfy the
      precondition — `check()` reports `MISSING:` for it
- [ ] AC-3T-4: with a live `f.plan.audit.v1.md` and `f.plan.audit.v2.md`, the file whose must-fix
      count is read is `v2`

**Dependencies on other tasks**: Task 1

---

## Task 4: Phase 6/6b protocol emits versioned analyses

**Production file**: `h-mad/references/inline-protocols.md`
**Test file**: `h-mad/tests/test_h_mad_analysis_versioning_docs.py`

**Description**: Apply the two prose replacements and the closing note specified verbatim in the
design's §"Phase 6 / 6b protocol change (FR-2)". Edits are confined to prose steps; the fenced
`# Analysis: <feature>` template block and its headings are not touched, which is what keeps
`test_h_mad_doc_templates.py` green.

**Code structure**: not applicable — documentation change. The doc-contract test reads
`h-mad/references/inline-protocols.md` and asserts on its §Phase 6 / §Phase 6b sections, the same
pattern `test_h_mad_substrate_docs.py` uses.

**Acceptance Criteria**:
- [ ] AC-2.1: §Phase 6 step 6 instructs saving to both `<feature>.analysis.v1.md` and the
      unversioned `<feature>.analysis.md`
- [ ] AC-2.2: §Phase 6b step 3 instructs writing the next unused `v<N>`, forbids overwriting a
      previous cycle, and requires refreshing the unversioned path
- [ ] AC-2.3: the protocol states the unversioned path holds the latest cycle and names
      `h_mad_phase7_preconditions.py` as the reason
- [ ] AC-2.4: the protocol names `h_mad_cycle_counts.py` and `max(N) - 1` as what depends on the
      per-cycle files
- [ ] AC-4T-1: `test_h_mad_doc_templates.py` passes unchanged after the edit

**Dependencies on other tasks**: None

---

## Task 5: document the derived counts

**Production file**: `h-mad/SKILL.md`
**Test file**: `h-mad/tests/test_h_mad_skill_telemetry_docs.py` (new — deliberately NOT Task 4's
file, which is scoped to the analysis-versioning protocol contract; a file named for analysis
versioning must not assert on SKILL.md's telemetry section)

**Description**: §Telemetry currently shows the `record` invocation with no indication that the
counts are derived. State it, and document `--docs-root` on both subcommands. Required by the
project invariant on skill manifest integrity: `record`'s observable behaviour changes, so its
documented contract must change with it.

**Acceptance Criteria**:
- [ ] AC-5T-1: §Telemetry states that `audit_cycles` and `iterate_cycles` are derived from
      artifacts on disk, not read from state
- [ ] AC-5T-2: §Telemetry documents `--docs-root` and its default
- [ ] AC-5T-3: `h-mad/SKILL.md` frontmatter `name` and `description` are unchanged

**Dependencies on other tasks**: Task 2 (the flag must exist before it is documented)

---

## Task dependency graph

```
Task 1 ──┬── Task 2 ── Task 5
         └── Task 3
Task 4 (independent)
```

Independent tasks (`Dependencies on other tasks: None`): **Task 1, Task 4**. Tasks 2, 3, 5 are
dependent and remain serial in topological order.

## Version History
- v1.0: Initial implementation plan draft.
- v1.1: Addressed `.impl-plan.audit.v1.md`. Must-fix: Task 5's SKILL.md assertions were bundled
  into Task 4's `test_h_mad_analysis_versioning_docs.py`, a file named for a different contract —
  split into a dedicated `test_h_mad_skill_telemetry_docs.py`. Should-fix: stated the analysis
  glob (`f"{feature}.analysis.v*.md"`) explicitly alongside the audit one in Task 1; clarified in
  Task 3 that no new parameter is needed because `check(repo_root, feature)` already receives
  `repo_root` (`h_mad_do_preconditions.py:43`) — the audit inferred a missing variable from my
  ambiguous wording, not from the code. Nit: added the `from pathlib import Path` line to Task 2's
  imports block.
