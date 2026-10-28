# Implementation Plan: hmad-test-boundaries

> **Input**: `docs/02-design/features/hmad-test-boundaries.design.md` (`v1.2`), `docs/01-plan/features/hmad-test-boundaries.spec.md` (`v1.5`), `docs/01-plan/features/hmad-test-boundaries.plan.md` (`v1.3`), `h-mad/invariants.base.md`, `.h-mad/invariants.md`
> **Test runner**: `python3.11 -m pytest` (verified working interpreter `/opt/anaconda3/bin/python3.11 -m pytest`)
> **Language**: Python 3.11 (stdlib-only per `h-mad/invariants.base.md` §"No new external dependency")
> **Provenance**: Verified against working tree at commit `12fd1775f95952e136bf71d8d8889bdb2dcd0a1d` (`HEAD`) on `2026-10-28`

---

## Task Overview

| # | Task | Shape | Production File(s) | Test File(s) | Depends On | Est. Time |
|---|------|-------|--------------------|--------------|------------|-----------|
| 1 | `h_mad_test_boundaries_check` | `new-behaviour` | `h-mad/scripts/h_mad_test_boundaries_check.py` | `h-mad/tests/test_h_mad_test_boundaries_check.py` | — | 14 min |
| 2 | `design-template-test-boundaries` | `new-behaviour` | `h-mad/references/inline-protocols.md`, `h-mad/agents/design-author.md` | `h-mad/tests/test_h_mad_doc_templates.py`, `h-mad/tests/test_h_mad_test_boundaries_check.py` | 1 | 8 min |
| 3 | `h_mad_audit_gate_design_boundaries_wire` | `wiring` | `h-mad/scripts/h_mad_audit_gate.py` | `h-mad/tests/test_h_mad_test_boundaries_check.py` | 1 | 8 min |
| 4 | `audit_prompt_and_doc_auditor_test_boundaries` | `new-behaviour` | `h-mad/audit-prompt.template.md`, `h-mad/agents/doc-auditor.md` | `h-mad/tests/test_h_mad_test_boundaries_check.py` | 2 | 6 min |
| 5 | `calibration_broken_fixtures_and_mutation_spec` | `new-behaviour` | `h-mad/tests/mutation-specs/test_boundaries_gate.json` | `h-mad/tests/test_h_mad_test_boundaries_check.py` | 1, 2, 3, 4 | 6 min |

**Totals**: `5` tasks (`4` `new-behaviour`, `1` `wiring`), `6` existing files modified (`h-mad/references/inline-protocols.md`, `h-mad/agents/design-author.md`, `h-mad/scripts/h_mad_audit_gate.py`, `h-mad/audit-prompt.template.md`, `h-mad/agents/doc-auditor.md`, `h-mad/tests/test_h_mad_doc_templates.py`), `3` new files created (`h-mad/scripts/h_mad_test_boundaries_check.py`, `h-mad/tests/test_h_mad_test_boundaries_check.py`, `h-mad/tests/mutation-specs/test_boundaries_gate.json`), `8` mutation rows (`6` targeting `scripts/h_mad_test_boundaries_check.py` in Task 1 + `2` targeting `scripts/h_mad_audit_gate.py` in Task 3, codified in `h-mad/tests/mutation-specs/test_boundaries_gate.json` in Task 5), `35` new test methods in `h-mad/tests/test_h_mad_test_boundaries_check.py` across `7` test classes (`24` in Task 1 + `1` in Task 2 + `7` in Task 3 + `2` in Task 4 + `1` in Task 5, plus `1` new test function `test_design_template_contains_test_boundaries_five_column_table` and `PRIOR_HMAD_HEADINGS["design"]` expanded from `7` to `8` entries in `h-mad/tests/test_h_mad_doc_templates.py` bringing `test_h_mad_doc_templates.py` from `7` to `8` pytest nodes).

### Non-Interference with Active Mutation Specs (`h-mad/invariants.base.md` §"Mutation verification" & §"Behavioural premises carry their command")

Verified across all `178` tracked JSON files in `h-mad/tests/mutation-specs/*.json` at `HEAD` (`12fd1775f95952e136bf71d8d8889bdb2dcd0a1d`, identical to commit c8df5312bebfad93d95019db604686af3a5de068) via:

```bash
python3 -c '
import glob, json, os
targets = [
    "references/inline-protocols.md",
    "agents/design-author.md",
    "scripts/h_mad_audit_gate.py",
    "audit-prompt.template.md",
    "agents/doc-auditor.md",
    "tests/test_h_mad_doc_templates.py",
]
specs = sorted(glob.glob("h-mad/tests/mutation-specs/*.json"))
print("total_specs =", len(specs))
for t in targets:
    hits = []
    for s in specs:
        data = json.load(open(s))
        for m in data.get("mutations", []):
            f = m.get("file", "")
            if f == t or f.endswith("/" + t):
                hits.append((os.path.basename(s), m.get("name") or m.get("id"), m.get("find")))
    spec_files = sorted(set(h[0] for h in hits))
    print(f"TARGET: h-mad/{t} | specs={len(spec_files)} ({spec_files}) | mutations={len(hits)}")
'
```
Observed output:
```text
total_specs = 178
TARGET: h-mad/references/inline-protocols.md | specs=1 (['wire_registry_runner.json']) | mutations=1
TARGET: h-mad/agents/design-author.md | specs=3 (['author_done_line.json', 'author_report_path.json', 'probe_hygiene_and_h8_extensions.json']) | mutations=4
TARGET: h-mad/scripts/h_mad_audit_gate.py | specs=11 (['audit_gate_nested_bullets.json', 'audit_gate_stamp.json', 'audit_leg_set_gate.json', 'audit_round_cap.json', 'audit_suite_gate.json', 'audit_suite_summary_line.json', 'collect_report.json', 'grok_audit_surface.json', 'suite_lock.json', 'suite_tree_digest.json', 'tdd_judge_wiring.json']) | mutations=81
TARGET: h-mad/audit-prompt.template.md | specs=1 (['archreview_oversize_halt.json']) | mutations=1
TARGET: h-mad/agents/doc-auditor.md | specs=1 (['author_done_line.json']) | mutations=1
TARGET: h-mad/tests/test_h_mad_doc_templates.py | specs=0 ([]) | mutations=0
```

| Modified File | Referencing Mutation Spec(s) (`178` total scanned) | Protected Anchor Span(s) (`find`) | Planned Edit Site | Overlap |
|---|---|---|---|---|
| `h-mad/references/inline-protocols.md` | `1` spec (`1` mutation): `wire_registry_runner.json` (`M13: the template WIRE-RUNNER line carries a real value again`) | `` `<playwright — only when the pin is not a pytest test>` `` in `## Phase 5a — Implementation Plan` | Insert `## Test Boundaries` inside the `## Phase 4 — Design` template block immediately after `## Test Plan` and before `## Invariant Compliance` (`13 -> 14` headings) | None (`0` overlapping anchors) |
| `h-mad/agents/design-author.md` | `3` specs (`4` mutations): `author_done_line.json` (`1`), `author_report_path.json` (`2`), `probe_hygiene_and_h8_extensions.json` (`1`) | `'Hash the **document**, never your report file'` (`author_done_line.json`), `'- `REPORT`: path to write your report to.'` and `'puts the **owed list**, the declines with their reasons, and the verbatim text owed to sibling'` (`author_report_path.json`), and `'**Then delete the\n   probe.**'` in Rule `5.` (`probe_hygiene_and_h8_extensions.json`) | Insert Rule `7a.` after Rule `7.` under `## Rules — each closes a measured failure class` and append `TEST-BOUNDARIES: PASS` reporting sentence at the end of `## Output` without altering `Hash the **document**, never your report file` | None (`0` overlapping anchors) |
| `h-mad/scripts/h_mad_audit_gate.py` | `11` specs (`81` mutations): `audit_gate_nested_bullets.json` (`7`), `audit_gate_stamp.json` (`11`), `audit_leg_set_gate.json` (`13`), `audit_round_cap.json` (`5`), `audit_suite_gate.json` (`14`), `audit_suite_summary_line.json` (`14`), `collect_report.json` (`6`), `grok_audit_surface.json` (`5`), `suite_lock.json` (`2`), `suite_tree_digest.json` (`3`), `tdd_judge_wiring.json` (`1`) | In `main`: `'    if is_transport_path(args.audit_file):'`, `'    if args.suite_timeout is not None and args.project_tests is None:'`, `'    elif args.project_tests is not None:'`, `'        bound = DEFAULT_SUITE_TIMEOUT if args.suite_timeout is None else args.suite_timeout\n        outcome = run_suite(args.project_tests, command, bound)'`, `'    stamped = ""\n    if args.gated and verdict == "PASS":'`, `'    if args.gated and verdict == "PASS":'`, `'    stamped = ""'`, `'        for path in args.gated:'`, `'                files[os.path.relpath(path, args.audit_file.parent)] = _digest(path)'`, `'                print("GATE: UNSTAMPABLE must=0 should=0")'`, `'        legs = _leg_key(args.legs) or None'`, `'        stamp_path(args.audit_file).write_text('`, `'        stamped = f" gated={len(files)}"\n        # Deferred, not printed here'`, `'    print(f"GATE: {verdict} must={result[\'must_count\']} should={result[\'should_count\']}{stamped}")'`, and `'    if legs_line is not None:\n        print(f"GATE-LEGS: {legs_line}")'` | Define `_DESIGN_AUDIT_RE`, `_load_test_boundaries_checker`, `_candidate_design_paths`, and `_run_design_boundaries_checks` above `def main`, call `_run_design_boundaries_checks(args.audit_file, args.gated)` after `print(suite_line(suite, outcome))` and strictly above `# Declared ABOVE stamped deliberately` (`legs_line: str | None = None\n    stamped = ""\n    if args.gated and verdict == "PASS":`), and print `tb_lines` immediately after `if legs_line is not None:\n        print(f"GATE-LEGS: {legs_line}")` | None (`0` overlapping anchors) |
| `h-mad/audit-prompt.template.md` | `1` spec (`1` mutation): `archreview_oversize_halt.json` (`the-audit-template-stops-asking-for-the-done-marker`) | `'create the marker'` in the `## Output framing` section | Insert `{{ONLY:design}}` ... `{{END-ONLY}}` Test Boundaries block under `Axis A — Generic adversarial:` immediately after `- {{ONLY:design}} Cross-doc:` and before `Axis B — Invariant compliance` | None (`0` overlapping anchors) |
| `h-mad/agents/doc-auditor.md` | `1` spec (`1` mutation): `author_done_line.json` (`doc-auditor-hashes-the-document-it-audited`) | `'You hash the **report**, not the audited document'` under `## Output` | Insert Rule `7c.` between Rule `7b.` and Rule `8.` under `## Rules — each closes a measured failure class` | None (`0` overlapping anchors) |
| `h-mad/tests/test_h_mad_doc_templates.py` | `0` specs (`0` mutations) | N/A | Update `PRIOR_HMAD_HEADINGS["design"]` (`7 -> 8` entries) and add `test_design_template_contains_test_boundaries_five_column_table` | None (`0` overlapping anchors) |

---

## Task 1: `h_mad_test_boundaries_check`

**Task shape**: `new-behaviour`
**Production file**: `h-mad/scripts/h_mad_test_boundaries_check.py`
**Test file**: `h-mad/tests/test_h_mad_test_boundaries_check.py`

**Code structure**:
```python
#!/usr/bin/env python3
"""Standalone deterministic validator for the Phase 4 design `## Test Boundaries` section."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import NamedTuple

EXPECTED_COLUMNS: tuple[str, str, str, str, str] = (
    "Public interface",
    "Acceptance criteria",
    "Expected result source",
    "Mocked dependencies",
    "Exclusions",
)
REQUIRED_COLUMNS = EXPECTED_COLUMNS

PRE_EXISTING_FEATURES: frozenset[str] = frozenset({
    "claude-context-reduction",
    "exec-missing-report-recovery",
    "hemasuite-100-percent",
    "hpw-csa-macos-app",
    "hpw-csa-unified-ui",
    "hpw-csa-unified-ui-v2",
    "hpw-protocol-extraction",
    "orca-native-orchestration",
    "orca-native-transport",
    "tdd-dispatch-verification-discipline",
})

REASON_CODES: frozenset[str] = frozenset({
    "missing_section",
    "missing_table",
    "invalid_columns",
    "empty_cell",
    "placeholder_cell",
    "tautological_oracle",
    "invalid_non_test_row",
    "missing_spec",
    "uncovered_ac",
    "unknown_ac",
})

PLACEHOLDER_EXACT: frozenset[str] = frozenset({
    "-", "--", "---", "—", "–", "?", "???", "...", "…",
    "tbd", "todo", "fixme", "xxx", "n/a", "na", "none",
    "null", "nil", "placeholder", "pending", "later",
    "tba", "wip", "same", "ditto", "see above", "see below",
})

PLACEHOLDER_PREFIXES: tuple[str, ...] = (
    "tbd ",
    "todo ",
    "fixme ",
    "placeholder ",
)

PLACEHOLDER_RE = re.compile(
    r"^(?:tbd|todo|fixme|placeholder)\s+",
    re.IGNORECASE,
)

MOCKED_NONE_PREFIXES: tuple[str, ...] = (
    "none ",
    "none —",
    "none –",
    "none -",
    "none (",
    "none;",
    "none:",
    "none,",
)

TAUTOLOGICAL_EXACT: frozenset[str] = frozenset({
    "implementation",
    "the implementation",
    "code",
    "the code",
    "source",
    "the source",
    "source code",
    "the source code",
    "function",
    "the function",
    "function output",
    "return value",
    "the return value",
    "computed",
    "computed value",
    "calculated",
    "calculated value",
    "self",
    "same function",
    "sut",
    "system under test",
    "unit under test",
    "actual output",
    "actual",
    "runtime output",
    "internal state",
    "mock",
    "the mock",
    "mock return value",
})

TAUTOLOGICAL_RE = re.compile(
    r"\b(?:"
    r"same\s+(?:function|method|code|logic|implementation|algorithm)"
    r"|(?:implementation|code|function|method|sut)\s+(?:under\s+test|itself|output|return\s+value)"
    r"|computed\s+by\s+(?:the\s+)?(?:implementation|code|function|method|sut)"
    r"|whatever\s+the\s+(?:code|function|implementation)\s+(?:returns|outputs|produces)"
    r"|call(?:ing)?\s+the\s+same\s+(?:function|method|helper)"
    r")\b",
    re.IGNORECASE,
)

VERIFIED_BY_KINDS: frozenset[str] = frozenset({
    "audit",
    "live-run",
    "operator",
    "doc-review",
})

VERIFIED_BY_PREFIX_RE = re.compile(r"^verified\s+by\s*:\s*(.*)$", re.IGNORECASE)
VERIFIED_BY_KIND_RE = re.compile(
    r"^(?P<kind>audit|live-run|operator|doc-review)(?:\s*$|[\s—–\-:(].*$)",
    re.IGNORECASE,
)

PROVING_PATH_RE = re.compile(
    r"(?:(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+\.[A-Za-z0-9]+"
    r"|\b[A-Za-z0-9_.-]+\.(?:md|py|sh|json|yaml|yml|toml|txt|js|ts)\b)"
)
TOKEN_RE = re.compile(r"\b[A-Z][A-Z0-9_-]{2,}:\s*[A-Z0-9_.-]*")
BACKTICK_SPAN_RE = re.compile(r"`[^`\n]{3,}`")
PROVENANCE_SUFFIX_RE = re.compile(
    r"\(\s*verified\s+by\s*:\s*[^)]+\)\s*$",
    re.IGNORECASE,
)

HEAD_AC_RE = re.compile(
    r"^\s*(?:-\s+(?:\[[ xX]\]\s+)?|#{1,6}\s+)(?:~~)?(?:\*\*|`)*(AC-(\d+)\.(\d+)([a-z]?))\b"
)
RETIRED_LINE_RE = re.compile(
    r"^\s*(?:-\s+(?:\[[ xX]\]\s+)?|#{1,6}\s+)"
    r"(?:"
    r"~~.*AC-\d+\.\d+[a-z]?.*~~"
    r"|(?:\*\*|`)*AC-\d+\.\d+[a-z]?(?:\*\*|`)*(?:\s*(?:\([^)]*\)|\[[^\]]*\]))*[:.,\s-]+"
    r"(?:(?:\(|\[)?(?:retired|superseded|removed|dropped)\b)"
    r")",
    re.IGNORECASE,
)
CELL_AC_RE = re.compile(r"\b(AC-(\d+)\.(\d+)([a-z]?))\b")

FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
TEST_BOUNDARIES_HEADING_RE = re.compile(r"^##\s+Test Boundaries\s*$")
LEVEL_1_OR_2_HEADING_RE = re.compile(r"^#{1,2}\s+\S")
VERSION_HISTORY_HEADING_RE = re.compile(r"^##\s+Version History\s*$", re.IGNORECASE)
UNESCAPED_PIPE_RE = re.compile(r"(?<!\\)\|")
SEPARATOR_CELL_RE = re.compile(r"^:?-{2,}:?$")


class Issue(NamedTuple):
    row: str        # "header", "-", or 1-based row number as string ("1", "2", ...)
    col: str        # "-" or exact column name from EXPECTED_COLUMNS
    code: str       # one of REASON_CODES
    detail: str     # human-readable diagnostic message


class CheckResult(NamedTuple):
    status: str             # "PASS", "EXEMPT", "FAIL", or "UNREADABLE"
    exit_code: int          # 0 for PASS/EXEMPT/FAIL; 2 for UNREADABLE
    path: str               # formatted path echoed in primary token
    rows: int = 0           # data row count on PASS
    acs_covered: int = 0    # active AC count covered on PASS
    acs_total: int = 0      # total active spec ACs on PASS
    exempt_reason: str = "" # "archived" or "pre_existing_feature" on EXEMPT
    error_type: str = ""    # exception/error class name on UNREADABLE
    issues: tuple[Issue, ...] = ()


def has_test_boundaries_heading(design_text: str) -> bool: ...
def infer_project_root(design_path: Path, root: Path | None = None) -> Path | None: ...
def resolve_spec_path(design_path: Path, spec_path: Path | None = None, root: Path | None = None) -> Path: ...
def extract_spec_acs(spec_text: str) -> tuple[set[str], set[str]]: ...
def should_activate_design_check(design_path: Path, root: Path | None = None) -> bool: ...
def normalize_cell(raw_cell: str) -> str: ...
def is_placeholder_cell(norm_cell: str, col_name: str) -> bool: ...
def is_tautological_oracle(raw_cell: str) -> bool: ...
def has_proving_artifact(raw_cell: str) -> bool: ...
def validate_non_test_row(row_idx: int, pub_cell: str, oracle_cell: str, oracle_had_basic_error: bool) -> list[Issue]: ...
def check_design(
    design_path: Path,
    *,
    spec_path: Path | None = None,
    root: Path | None = None,
    no_exempt: bool = False,
) -> CheckResult: ...
def format_check_result(result: CheckResult) -> str: ...
def main(argv: list[str] | None = None) -> int: ...
```

**Implementation details** (inlined from `design.md` `v1.2` Component 2 & `spec.md` `v1.5` `FR-2`..`FR-4` so Phase 5d/5e task-scoped dispatches have the complete contract):
1. **Audit-gate signal discipline (`PASS` / `EXEMPT` / `FAIL` exit `0`; `UNREADABLE` exit `2`)**:
   - `TEST-BOUNDARIES: PASS path=<design_path> rows=<N> acs=<M>/<M>` (exit `0`)
   - `TEST-BOUNDARIES: EXEMPT path=<design_path> reason=<archived|pre_existing_feature>` (exit `0`)
   - `TEST-BOUNDARIES: FAIL path=<design_path> issues=<K> reasons=<comma-separated-sorted-unique-reason-codes>` (exit `0`), followed by `K` lines: `TEST-BOUNDARIES-ISSUE: row=<R|header|-> col=<column_name|-> code=<reason_code> detail=<message>`
   - `TEST-BOUNDARIES: UNREADABLE path=<target_path> err=<ErrorType>` (exit `2` when `design_path` or an explicitly passed `--spec <spec_path>` does not exist (`FileNotFoundError`), is a directory (`IsADirectoryError`), cannot be read (`OSError`), or cannot be decoded as UTF-8 (`UnicodeDecodeError`), or when a default-resolved `spec_path` exists on disk as a directory or non-UTF-8 file).
2. **`infer_project_root(design_path: Path, root: Path | None = None) -> Path | None` & two-branch `resolve_spec_path`**:
   - If `root is not None`: returns `Path(root).resolve()`.
   - Otherwise, let `abs_design = Path(design_path).resolve()`:
     - If `len(abs_design.parts) >= 4` and `abs_design.parts[-4:-1] == ("docs", "02-design", "features")`: returns `abs_design.parents[3]` (the ancestor immediately above `"docs"`, e.g. `/project` for `/project/docs/02-design/features/demo.design.md`).
     - If `"docs"` and `"archive"` appear as adjacent segments `("docs", "archive")` in `abs_design.parts[:-1]`: finds the index `i` where `abs_design.parts[i : i + 2] == ("docs", "archive")` and returns `Path(*abs_design.parts[:i])` (the ancestor immediately above `"docs"`, e.g. `/project` for `/project/docs/archive/2026-08/demo/demo.design.md`, regardless of archive nesting depth; when `abs_design.parts[-4:-2] == ("docs", "archive")`, this equals `abs_design.parents[3]`).
     - Otherwise (a design path outside `docs/02-design/features/` and `docs/archive/`, e.g. a synthetic file in `tmp_path`), returns `None` (and any caller needing a default root for a non-canonical path falls back to `Path.cwd().resolve()`, matching `spec.md` `v1.5` `FR-2.1`).
   - `resolve_spec_path(design_path: Path, spec_path: Path | None = None, root: Path | None = None) -> Path`:
     - If `spec_path is not None`: returns `Path(spec_path)`.
     - Let `abs_design = Path(design_path).resolve()`, `feature = _feature_stem(abs_design)` (stripping `.design.md` or `.md` from `abs_design.name`), `sib_cand = abs_design.parent / f"{feature}.spec.md"`, and `proj_root = infer_project_root(abs_design, root) or Path.cwd().resolve()`.
     - Branch 1 (`abs_design` is under `docs/02-design/features/` — either `len(abs_design.parts) >= 4 and abs_design.parts[-4:-1] == ("docs", "02-design", "features")` or `root is not None and abs_design.is_relative_to(Path(root).resolve() / "docs" / "02-design" / "features")`): let `plan_cand = proj_root / "docs" / "01-plan" / "features" / f"{feature}.spec.md"`. Returns `plan_cand` if `plan_cand.exists()` (including when `plan_cand` is a directory or non-UTF-8 file so `check_design` reports `UNREADABLE`), else `sib_cand` if `sib_cand.exists()`, else `plan_cand`.
     - Branch 2 (`abs_design` is NOT under `docs/02-design/features/`): returns `sib_cand` **only** (never falling back to `plan_cand` or `cwd`).
3. **3-arm `should_activate_design_check(design_path: Path, root: Path | None = None) -> bool`**:
   - Returns `False` if `not Path(design_path).exists()`; returns `True` if `Path(design_path).is_dir()`.
   - Arm 1: canonical `docs/02-design/features/` or `docs/archive/` path (or under `Path(root).resolve() / "docs" / ("02-design/features" | "archive")` when `root is not None`) -> `True`.
   - Arm 2: reading `design_path` raises `(OSError, UnicodeDecodeError)` -> `True` (fail-closed `UNREADABLE`), or `has_test_boundaries_heading(design_text)` is `True` -> `True`.
   - Arm 3: `spec_candidate = resolve_spec_path(abs_design, None, root)` exists and either `spec_candidate.is_dir()` / reading raises `(OSError, UnicodeDecodeError)` -> `True`, or `len(extract_spec_acs(spec_text)[0]) >= 1` -> `True`. Otherwise `False`.
4. **Exemptions (`check_design`)**:
   - Let `has_section = has_test_boundaries_heading(design_text)`.
   - Exact guard line (pinned by mutation `checker-no-exempt-flag-ignored`):
     `    if not has_section and not no_exempt:`
     check if `"archive" in Path(design_path).parts` (`exempt_reason="archived"`) or if `_feature_stem(design_path) in PRE_EXISTING_FEATURES` (`exempt_reason="pre_existing_feature"`), returning `CheckResult(status="EXEMPT", exit_code=0, path=str(design_path), exempt_reason=...)`.
5. **Exact helper algorithms (`normalize_cell`, `is_placeholder_cell`, `is_tautological_oracle`, `has_proving_artifact`, `validate_non_test_row`, `extract_spec_acs`)**:
   - `normalize_cell(raw_cell: str) -> str`:
     - Strips outer whitespace (`.strip()`), repeatedly strips surrounding backticks, asterisks, and underscores (`` `*_ ``) while stripping outer whitespace until stable, collapses internal whitespace runs (`re.sub(r"\s+", " ", s)`) to a single space, and applies `.casefold()`.
   - `is_placeholder_cell(norm_cell: str, col_name: str) -> bool`:
     - Assumes `norm_cell != ""` (empty strings are reported as `empty_cell`).
     - In column `"Mocked dependencies"`, if `norm_cell == "none"` or `norm_cell.startswith(MOCKED_NONE_PREFIXES)`, returns `False`.
     - Exact guard line (pinned by mutation `checker-placeholder-guard-disabled`):
       `    if norm_cell in PLACEHOLDER_EXACT:`
       `        return True`
     - Returns `True` if `norm_cell.startswith(PLACEHOLDER_PREFIXES)` (equivalently `bool(PLACEHOLDER_RE.match(norm_cell))`), else `False`.
     - Per `spec.md` `FR-2.4` Residual: any non-empty cell whose `norm_cell` is not in `PLACEHOLDER_EXACT` and does not start with `PLACEHOLDER_PREFIXES` (`"tbd "`, `"todo "`, `"fixme "`, `"placeholder "`) — including `"none — explanation"` or `"none (explanation)"` outside column 4 — returns `False` from `is_placeholder_cell` (passing the placeholder check, and is then evaluated by column-specific rules in `FR-2.5` and `FR-3`), whereas bare `"none"` is in `PLACEHOLDER_EXACT` and returns `True` in columns 1, 2, 3, 5.
   - `is_tautological_oracle(raw_cell: str) -> bool`:
     - First strips any trailing `(verified by: ...)` provenance suffix via `stripped = PROVENANCE_SUFFIX_RE.sub("", raw_cell)` inside `is_tautological_oracle` itself (so both direct unit calls to `is_tautological_oracle` and `check_design` strip it).
     - Normalizes `stripped` via `normalize_cell(stripped)` and strips leading/trailing punctuation characters (`".,;:!?'\"()[]{}-–—"` and `` `*_ ``) and outer whitespace to produce `cleaned`.
     - Exact guard line (pinned by mutation `checker-tautological-oracle-guard-disabled`):
       `    if cleaned in TAUTOLOGICAL_EXACT:`
       `        return True`
     - Returns `bool(TAUTOLOGICAL_RE.search(cleaned))`.
   - `has_proving_artifact(raw_cell: str) -> bool`:
     - Returns `bool(PROVING_PATH_RE.search(raw_cell) or TOKEN_RE.search(raw_cell) or BACKTICK_SPAN_RE.search(raw_cell))`.
   - `validate_non_test_row(row_idx: int, pub_cell: str, oracle_cell: str, oracle_had_basic_error: bool) -> list[Issue]`:
     - Strips outer whitespace and surrounding backticks from `pub_cell` to form `cleaned_pub`.
     - Matches `m = VERIFIED_BY_PREFIX_RE.match(cleaned_pub)`. If not matched, returns `[]` (standard test row).
     - Let `rest = m.group(1).strip()`. If `not VERIFIED_BY_KIND_RE.match(rest)`, returns `[Issue(str(row_idx), "Public interface", "invalid_non_test_row", f"unrecognized verified by kind in {pub_cell!r}; expected audit, live-run, operator, or doc-review")]`.
     - Exact guard line (pinned by mutation `checker-invalid-non-test-row-guard-disabled`):
       `    if not oracle_had_basic_error and not has_proving_artifact(oracle_cell):`
       returns `[Issue(str(row_idx), "Expected result source", "invalid_non_test_row", f"verified by row must name a concrete proving artifact in Expected result source: {oracle_cell!r}")]`.
     - Otherwise returns `[]`.
   - `extract_spec_acs(spec_text: str) -> tuple[set[str], set[str]]`:
     - Scans `spec_text.splitlines()` outside fenced code blocks (`FENCE_RE`), stopping as soon as a heading outside fenced code blocks matches `VERSION_HISTORY_HEADING_RE`.
     - For each line matching `m = HEAD_AC_RE.match(line)`, extracts `ac_id = m.group(1)`.
     - Exact guard line (pinned by mutation `checker-retired-ac-filter-disabled`):
       `        if RETIRED_LINE_RE.match(line):`
       adds `ac_id` to `retired_acs` (and discards from `active_acs`), else if `ac_id not in retired_acs`, adds `ac_id` to `active_acs`.
6. **Exact evaluation precedence, `Issue(row, col, code, detail)` coordinates, and deterministic ordering in `check_design`**:
   - **Step 6a — Design operational-input check (`UNREADABLE`, exit `2`)**:
     - Attempt `design_text = Path(design_path).read_text(encoding="utf-8")`. If `not Path(design_path).exists()`, `Path(design_path).is_dir()`, or reading/decoding raises `exc` (`OSError` or `UnicodeDecodeError`), return `CheckResult(status="UNREADABLE", exit_code=2, path=str(design_path), error_type=type(exc).__name__)` immediately.
   - **Step 6b — Exemption check (`EXEMPT`, exit `0`)**:
     - Let `has_section = has_test_boundaries_heading(design_text)`.
     - Exact guard line (pinned by mutation `checker-no-exempt-flag-ignored`):
       `    if not has_section and not no_exempt:`
       if `"archive" in Path(design_path).parts`, return `CheckResult(status="EXEMPT", exit_code=0, path=str(design_path), exempt_reason="archived")`; if `_feature_stem(design_path) in PRE_EXISTING_FEATURES`, return `CheckResult(status="EXEMPT", exit_code=0, path=str(design_path), exempt_reason="pre_existing_feature")`.
   - **Step 6c — Paired spec operational-input check on non-exempt designs (`UNREADABLE`, exit `2` — evaluated BEFORE structural early returns)**:
     - For any **non-exempt** design (including one missing `## Test Boundaries`), resolve and validate the paired `spec_path` for operational-input errors before returning structural `FAIL` (`missing_section`, `missing_table`, or header `invalid_columns`):
       - When `spec_path is not None` (explicit `--spec <spec_path>`): let `spec_candidate = Path(spec_path)`. Attempt `spec_text = spec_candidate.read_text(encoding="utf-8")`; if `not spec_candidate.exists()`, `spec_candidate.is_dir()`, or reading/decoding raises `exc` (`OSError` or `UnicodeDecodeError`), return `CheckResult(status="UNREADABLE", exit_code=2, path=str(spec_candidate), error_type=type(exc).__name__)` immediately. Otherwise set `spec_known = True` and `active_acs, retired_acs = extract_spec_acs(spec_text)`.
       - When `spec_path is None` (default-resolved `spec_candidate = resolve_spec_path(design_path, None, root)`):
         - If `spec_candidate.exists()` is `True`: attempt `spec_text = spec_candidate.read_text(encoding="utf-8")`; if `spec_candidate.is_dir()` or reading/decoding raises `exc` (`OSError` or `UnicodeDecodeError`), return `CheckResult(status="UNREADABLE", exit_code=2, path=str(spec_candidate), error_type=type(exc).__name__)` immediately. Otherwise set `spec_known = True` and `active_acs, retired_acs = extract_spec_acs(spec_text)`.
         - If `not spec_candidate.exists()`: set `spec_known = False`, `active_acs = set()`, `retired_acs = set()` (a missing default-resolved spec is a structural `FAIL` issue `missing_spec`, evaluated after section/table structural early returns).
   - **Step 6d — Section/table structural early returns on readable inputs (`FAIL`, exit `0`)**:
     - Missing `## Test Boundaries` on non-exempt design (`if not has_section:`): `Issue(row="-", col="-", code="missing_section", detail="missing ## Test Boundaries section")` (returns `FAIL` immediately).
     - Missing pipe table or `0` data rows under `## Test Boundaries`: `Issue(row="-", col="-", code="missing_table", detail=...)` (returns `FAIL` immediately).
     - Header cells `!= 5` or `[c.strip().casefold() for c in header_cells] != [c.casefold() for c in EXPECTED_COLUMNS]`: `Issue(row="header", col="-", code="invalid_columns", detail=...)` (returns `FAIL` immediately).
   - **Step 6e — Missing default-resolved spec issue (`missing_spec`)**:
     - Initialize `issues: list[Issue] = []`.
     - When `not spec_known` (`spec_path is None` and `not spec_candidate.exists()`): append `Issue(row="-", col="-", code="missing_spec", detail=f"missing paired spec: {spec_candidate}")` before per-row checks.
   - **Step 6f — Per-row checks (for 1-based `row_idx = 1..N`)**:
     - If `len(cells) != 5`: appends `Issue(row=str(row_idx), col="-", code="invalid_columns", detail=f"expected 5 columns, got {len(cells)}")` and continues to next row.
     - For each of the 5 columns `(col_name, raw_cell)` in `zip(EXPECTED_COLUMNS, cells)`:
       - Let `norm_cell = normalize_cell(raw_cell)`.
       - If `norm_cell == ""`: appends `Issue(row=str(row_idx), col=col_name, code="empty_cell", detail=f"empty cell in {col_name}")`.
       - Else if `is_placeholder_cell(norm_cell, col_name)`: appends `Issue(row=str(row_idx), col=col_name, code="placeholder_cell", detail=f"placeholder value {raw_cell!r} in {col_name}")`.
     - In column 2 (`"Acceptance criteria"`), if that cell did not fail `empty_cell` or `placeholder_cell`:
       - Extract all tokens `row_acs = [m.group(1) for m in CELL_AC_RE.finditer(cells[1])]`.
       - If `len(row_acs) == 0` and `spec_known` and `len(active_acs) >= 1`: appends `Issue(row=str(row_idx), col="Acceptance criteria", code="invalid_columns", detail="Acceptance criteria cell contains zero AC-X.Y tokens")`.
       - For each `ac_id` in `row_acs`: adds `ac_id` to `covered_acs`; if `spec_known` and `ac_id not in active_acs` and `ac_id not in retired_acs`: appends `Issue(row=str(row_idx), col="Acceptance criteria", code="unknown_ac", detail=f"unknown AC not in spec: {ac_id}")`.
     - In column 3 (`"Expected result source"`), let `oracle_had_basic_error` be `True` if column 3 failed `empty_cell` or `placeholder_cell`. If `not oracle_had_basic_error` and `is_tautological_oracle(cells[2])`: appends `Issue(row=str(row_idx), col="Expected result source", code="tautological_oracle", detail=f"tautological oracle in Expected result source: {cells[2]!r}")` and sets `oracle_had_basic_error = True`.
     - Calls `validate_non_test_row(row_idx, cells[0], cells[2], oracle_had_basic_error)` and extends `issues`.
   - **Step 6g — Post-row spec AC coverage check (when `spec_known`)**:
     - Let `missing_acs = sorted(active_acs - covered_acs, key=_ac_sort_key)` where `_ac_sort_key` sorts `AC-X.Y[a-z]` by `(int(X), int(Y), letter)`.
     - Exact guard line (pinned by mutation `checker-uncovered-ac-guard-disabled`):
       `        if missing_acs:`
       appends `Issue(row="-", col="Acceptance criteria", code="uncovered_ac", detail=f"missing active ACs: {', '.join(missing_acs)}")`.
   - `reasons=` on `TEST-BOUNDARIES: FAIL` is `",".join(sorted({i.code for i in issues}))`.

**Test specification** (`h-mad/tests/test_h_mad_test_boundaries_check.py` — all `24` test methods that directly exercise `h_mad_test_boundaries_check.py` are introduced in Task 1 across `6` test classes so all `24` fail at Task 1 RED and all `6` checker mutation rows reference existing test node IDs):
- `TestCliAndTableValidation::test_cli_tokens_and_unreadable_vs_missing_spec_disambiguation`:
  - Verifies CLI flags (`design_path`, `--spec`, `--root`, `--no-exempt`), the 4 primary tokens (`PASS`, `EXEMPT`, `FAIL` exit `0`; `UNREADABLE` exit `2`), `UNREADABLE` (exit `2`) vs `FAIL` `code=missing_spec` (exit `0`), and operational-input error precedence on the combined-invalid case where a non-exempt design omits `## Test Boundaries` and its paired `.spec.md` is unreadable (invalid UTF-8 bytes `b"\xff\xfe"` or a directory or a missing explicit `--spec`), asserting `TEST-BOUNDARIES: UNREADABLE` (exit `2`) rather than `missing_section` (`FAIL`, exit `0`).
- `TestCliAndTableValidation::test_infer_project_root_and_two_branch_resolve_spec_path_from_external_cwd`:
  - Directly asserts `infer_project_root(Path("/project/docs/02-design/features/demo.design.md")) == Path("/project").resolve()` (`parents[3]`), `infer_project_root(Path("/project/docs/archive/2026-08/demo/demo.design.md")) == Path("/project").resolve()` (ancestor immediately above `"docs"` via `("docs", "archive")` segment lookup), and `infer_project_root(tmp_path / "demo.design.md") is None`; invokes `h_mad_test_boundaries_check.py` from a different `cwd` (`tmp_path`) on an absolute `/.../docs/02-design/features/demo.design.md` without `--root`, tests explicit `--root` override, and verifies `resolve_spec_path`'s two-branch rule (`sib_cand` only outside `docs/02-design/features/`).
- `TestCliAndTableValidation::test_missing_section_and_missing_table_and_empty_rows`:
  - Verifies `missing_section` when `## Test Boundaries` is absent on a non-exempt design and `missing_table` when `## Test Boundaries` has no pipe table or `0` data rows.
- `TestCliAndTableValidation::test_invalid_columns_headers_cell_counts_and_zero_ac_tokens`:
  - Verifies `invalid_columns` on wrong column headers (`row=header col=-`), `!= 5` cells in a row (`row=<R> col=-`), and a 5-cell row whose non-empty, non-placeholder `Acceptance criteria` cell contains zero `AC-X.Y[a-z]` tokens when the paired spec has `>= 1` active ACs (`row=<R> col=Acceptance criteria`).
- `TestCliAndTableValidation::test_fenced_code_blocks_decoy_headings_and_tables_ignored`:
  - Verifies fenced code blocks (`` ``` `` and `~~~`) containing decoy `## Test Boundaries` headings and pipe tables are ignored.
- `TestCliAndTableValidation::test_empty_cell_and_placeholder_cell_across_all_five_columns`:
  - Verifies `empty_cell` and `placeholder_cell` (`PLACEHOLDER_EXACT` and `PLACEHOLDER_PREFIXES`) across all 5 columns.
- `TestCliAndTableValidation::test_mocked_dependencies_allows_none_and_none_explanations_only_in_col_4`:
  - Verifies bare `"none"` (in `PLACEHOLDER_EXACT`) is accepted in `Mocked dependencies` (column 4) and rejected as `placeholder_cell` in the other 4 columns (`Public interface`, `Acceptance criteria`, `Expected result source`, `Exclusions`), while `"none — ..."` / `"none (...)"` explanations are accepted in `Mocked dependencies` and also pass `is_placeholder_cell` (`False`) in the other 4 columns per `spec.md` `FR-2.4` Residual (where column-specific rules in `FR-2.5` and `FR-3` then evaluate them, e.g. rejecting `"none — explanation"` in `Acceptance criteria` as `invalid_columns` for having zero `AC-X.Y` tokens).
- `TestCliAndTableValidation::test_tautological_oracle_exact_tokens_and_phrase_regexes_rejected`:
  - Verifies `tautological_oracle` across `TAUTOLOGICAL_EXACT` (`"implementation"`, `"the code"`, `"computed"`, `"return value"`, `"same function"`, `"sut"`) and `TAUTOLOGICAL_RE` (`"computed by the implementation"`, `"calling the same helper"`).
- `TestCliAndTableValidation::test_provenance_suffix_in_expected_result_source_does_not_mask_tautology`:
  - Verifies `PROVENANCE_SUFFIX_RE` is stripped inside `is_tautological_oracle` so both `is_tautological_oracle("implementation (verified by: h-mad/tests/test_x.py)")` and `check_design` reject `"implementation (verified by: h-mad/tests/test_x.py)"` as `tautological_oracle`.
- `TestSpecAcCoverageAndNonTestRows::test_extract_spec_acs_reference_counts_and_retired_filtering`:
  - Verifies `extract_spec_acs` on all 5 reference specs (`hmad-test-boundaries` -> `17` active / `0` retired; `exec-path-hardening` -> `24` active / `0` retired; `audit-report-docs-copy` -> `40` active including `AC-2.6a`, `AC-2.6b`, `AC-3.5a`; `tdd-gate-fail-opens` -> `44` active including `- AC-3.6 (second arm, OQ-P1),`; `grok-audit-surface` -> `63` active / `1` retired `AC-3.7`).
- `TestSpecAcCoverageAndNonTestRows::test_mid_line_prose_and_version_history_and_fenced_ac_mentions_ignored`:
  - Verifies mid-line prose mentions of `AC-X.Y` and mentions inside `## Version History` or fenced blocks are ignored in `.spec.md`, while multi-token cells (`AC-1.1, AC-1.2`) are extracted in `.design.md`.
- `TestSpecAcCoverageAndNonTestRows::test_uncovered_ac_and_unknown_ac_and_optional_retired_ac_handling`:
  - Verifies `uncovered_ac`, `unknown_ac`, and optional inclusion/omission of retired ACs (`~~AC-1.2~~` and `AC-3.7: Retired in v1.10.`).
- `TestSpecAcCoverageAndNonTestRows::test_verified_by_rows_accept_valid_kinds_and_proving_artifacts_and_reject_invalid`:
  - Verifies `verified by: audit | live-run | operator | doc-review` acceptance with file paths, `TOKEN:` prefixes, or backticked commands, and `invalid_non_test_row` rejection on unrecognized kinds or bare prose in `Expected result source`.
- `TestExemptionsAndAuditGateIntegration::test_pre_existing_and_archived_designs_exempt_unless_no_exempt`:
  - Verifies `TEST-BOUNDARIES: EXEMPT` (`reason=pre_existing_feature` on the `10` `PRE_EXISTING_FEATURES` designs and `reason=archived` on unaugmented `docs/archive/**` designs) and `TEST-BOUNDARIES: FAIL` (`reasons=missing_section`) when `--no-exempt` is passed.
- `TestDesignAuthorAndSelfBootstrap::test_hmad_test_boundaries_design_passes_self_check`:
  - Runs `h_mad_test_boundaries_check.py` with `--no-exempt` on `docs/02-design/features/hmad-test-boundaries.design.md` paired with `docs/01-plan/features/hmad-test-boundaries.spec.md` and asserts `TEST-BOUNDARIES: PASS` with `acs=17/17` and exit code `0` (`AC-1.3`).
- `TestArchivedCalibrationAndPerformance::test_calibrated_exec_path_hardening_passes_under_200ms`:
  - Copies `docs/archive/2026-08/exec-path-hardening/exec-path-hardening.design.md` and `docs/archive/2026-08/exec-path-hardening/exec-path-hardening.spec.md` (`24` active ACs) into `tmp_path`, appends a realistic `## Test Boundaries` table covering all `24` active ACs, runs `check_design(..., no_exempt=True)` and CLI `--no-exempt`, asserts `TEST-BOUNDARIES: PASS` with `acs=24/24`, and asserts wall-clock runtime via `time.monotonic()` is `< 0.200`s (`< 200ms`) (`AC-6.1`).
- `TestArchivedCalibrationAndPerformance::test_calibrated_audit_report_docs_copy_passes_under_200ms`:
  - Copies `docs/archive/2026-09/audit-report-docs-copy/audit-report-docs-copy.design.md` and `docs/archive/2026-09/audit-report-docs-copy/audit-report-docs-copy.spec.md` (`40` active ACs) into `tmp_path`, appends a realistic `## Test Boundaries` table covering all `40` active ACs, runs `check_design(..., no_exempt=True)` and CLI `--no-exempt`, asserts `TEST-BOUNDARIES: PASS` with `acs=40/40`, and asserts wall-clock runtime `< 0.200`s (`AC-6.1`).
- `TestArchivedCalibrationAndPerformance::test_calibrated_tdd_gate_fail_opens_passes_under_200ms`:
  - Copies `docs/archive/2026-09/tdd-gate-fail-opens/tdd-gate-fail-opens.design.md` and `docs/archive/2026-09/tdd-gate-fail-opens/tdd-gate-fail-opens.spec.md` (`44` active ACs) into `tmp_path`, appends a realistic `## Test Boundaries` table covering all `44` active ACs, runs `check_design(..., no_exempt=True)` and CLI `--no-exempt`, asserts `TEST-BOUNDARIES: PASS` with `acs=44/44`, and asserts wall-clock runtime `< 0.200`s (`AC-6.1`).
- `TestArchivedCalibrationAndPerformance::test_archive_directory_remains_unmodified_and_stdlib_only`:
  - Asserts `git status --porcelain docs/archive/` is empty and inspects AST imports of `h-mad/scripts/h_mad_test_boundaries_check.py` against `sys.stdlib_module_names` (`AC-6.1`, `h-mad/invariants.base.md` §"No new external dependency").
- `TestSeededBrokenFixtures::test_seeded_broken_missing_section_and_missing_table_rejected`:
  - Starting from a passing calibrated design+spec pair in `tmp_path`, removes `## Test Boundaries` (`code=missing_section`) or removes its pipe table (`code=missing_table`) and asserts `TEST-BOUNDARIES: FAIL` (`AC-6.2`).
- `TestSeededBrokenFixtures::test_seeded_broken_placeholder_cell_rejected`:
  - Seeds `"tbd"` / `"n/a"` / `"none"` (in `Exclusions`) into a table cell on a calibrated design in `tmp_path` and asserts `TEST-BOUNDARIES: FAIL` with `code=placeholder_cell` (`AC-6.2`).
- `TestSeededBrokenFixtures::test_seeded_broken_uncovered_ac_rejected`:
  - Drops an active spec AC from the `## Test Boundaries` table on a calibrated design in `tmp_path` and asserts `TEST-BOUNDARIES: FAIL` with `code=uncovered_ac` (`AC-6.2`).
- `TestSeededBrokenFixtures::test_seeded_broken_implementation_oracle_rejected`:
  - Sets `Expected result source` to `"implementation"` on a calibrated design in `tmp_path` and asserts `TEST-BOUNDARIES: FAIL` with `code=tautological_oracle` (`AC-6.2`).
- `TestSeededBrokenFixtures::test_seeded_broken_non_test_row_without_artifact_rejected`:
  - Sets a `verified by: doc-review` / `verified by: operator` row's `Expected result source` to `"manual inspection by reviewer"` (no proving artifact) on a calibrated design in `tmp_path` and asserts `TEST-BOUNDARIES: FAIL` with `code=invalid_non_test_row` (`AC-6.2`).

**Expected RED result**:
```
FAILED h-mad/tests/test_h_mad_test_boundaries_check.py (24 failed, 0 passed — ModuleNotFoundError: No module named 'h_mad_test_boundaries_check')
```
RED split: `24 F, 0 P` (`24` test methods in `h-mad/tests/test_h_mad_test_boundaries_check.py`; `0` regression guards `--guard`).

**Expected GREEN result**:
```
PASSED h-mad/tests/test_h_mad_test_boundaries_check.py (0 failed, 24 passed)
```
GREEN split: `0 F, 24 P`.

**Mutation rows for `scripts/h_mad_test_boundaries_check.py`** (`6` rows, all referencing test methods created in Task 1, codified in `h-mad/tests/mutation-specs/test_boundaries_gate.json` in Task 5):
1. `checker-placeholder-guard-disabled`: `file="scripts/h_mad_test_boundaries_check.py"`, `symbol="is_placeholder_cell"`, `find="    if norm_cell in PLACEHOLDER_EXACT:"`, `replace="    if False:"`, `test="tests/test_h_mad_test_boundaries_check.py::TestSeededBrokenFixtures::test_seeded_broken_placeholder_cell_rejected"`.
2. `checker-tautological-oracle-guard-disabled`: `file="scripts/h_mad_test_boundaries_check.py"`, `symbol="is_tautological_oracle"`, `find="    if cleaned in TAUTOLOGICAL_EXACT:"`, `replace="    if False:"`, `test="tests/test_h_mad_test_boundaries_check.py::TestSeededBrokenFixtures::test_seeded_broken_implementation_oracle_rejected"`.
3. `checker-uncovered-ac-guard-disabled`: `file="scripts/h_mad_test_boundaries_check.py"`, `symbol="check_design"`, `find="        if missing_acs:"`, `replace="        if False:"`, `test="tests/test_h_mad_test_boundaries_check.py::TestSeededBrokenFixtures::test_seeded_broken_uncovered_ac_rejected"`.
4. `checker-invalid-non-test-row-guard-disabled`: `file="scripts/h_mad_test_boundaries_check.py"`, `symbol="validate_non_test_row"`, `find="    if not oracle_had_basic_error and not has_proving_artifact(oracle_cell):"`, `replace="    if False:"`, `test="tests/test_h_mad_test_boundaries_check.py::TestSeededBrokenFixtures::test_seeded_broken_non_test_row_without_artifact_rejected"`.
5. `checker-retired-ac-filter-disabled`: `file="scripts/h_mad_test_boundaries_check.py"`, `symbol="extract_spec_acs"`, `find="        if RETIRED_LINE_RE.match(line):"`, `replace="        if False:"`, `test="tests/test_h_mad_test_boundaries_check.py::TestSpecAcCoverageAndNonTestRows::test_extract_spec_acs_reference_counts_and_retired_filtering"`.
6. `checker-no-exempt-flag-ignored`: `file="scripts/h_mad_test_boundaries_check.py"`, `symbol="check_design"`, `find="    if not has_section and not no_exempt:"`, `replace="    if not has_section:"`, `test="tests/test_h_mad_test_boundaries_check.py::TestExemptionsAndAuditGateIntegration::test_pre_existing_and_archived_designs_exempt_unless_no_exempt"`.

**Acceptance criteria**:
- **AC-1.3** (self-bootstrap half): `docs/02-design/features/hmad-test-boundaries.design.md` passes `h_mad_test_boundaries_check.py --no-exempt` with `TEST-BOUNDARIES: PASS` (`acs=17/17`).
- **AC-2.1**: `python3 h-mad/scripts/h_mad_test_boundaries_check.py <design_path> [--spec <spec_path>] [--root <project_root>] [--no-exempt]` emits `TEST-BOUNDARIES: PASS | EXEMPT | FAIL` (exit `0`) or `TEST-BOUNDARIES: UNREADABLE` (exit `2`), infers `--root <project_root>` via `infer_project_root` (returning `abs_design.parents[3]` for canonical `docs/02-design/features/` paths and the ancestor immediately above `"docs"` for `docs/archive/...` paths, falling back to `Path.cwd().resolve()` when a caller needs a default root for a non-canonical path), and resolves default `.spec.md` via the two-branch `resolve_spec_path` rule.
- **AC-2.2**: Rejects `missing_section`, `missing_table`, and `invalid_columns` (headers other than the exact 5 columns, a data row with `!= 5` cells, or a 5-cell data row whose non-empty, non-placeholder `Acceptance criteria` cell contains zero `AC-X.Y[a-z]` tokens when the paired spec has `>= 1` active ACs), while ignoring `## Test Boundaries` headings and pipe tables inside CommonMark fenced code blocks (`` ``` `` or `~~~`).
- **AC-2.3**: Rejects `empty_cell` and `placeholder_cell` (`PLACEHOLDER_EXACT` and `PLACEHOLDER_PREFIXES`), except that `none` (and `none ...` explanations) in `Mocked dependencies` is accepted (while non-empty cells outside `PLACEHOLDER_EXACT` and `PLACEHOLDER_PREFIXES` pass the placeholder check per `FR-2.4` Residual).
- **AC-2.4**: Rejects `tautological_oracle` when `Expected result source` (after stripping any trailing `(verified by: ...)` provenance suffix) matches any entry in `TAUTOLOGICAL_EXACT` or regex in `TAUTOLOGICAL_RE`.
- **AC-3.1**: Extracts head-anchored active `AC-X.Y[a-z]` items from the paired `.spec.md` (stopping at `## Version History` and filtering retired/superseded/removed/dropped or struck-through ACs) and emits `uncovered_ac` for any active spec AC absent from column 2 and `unknown_ac` for any table AC absent from `active_acs | retired_acs`.
- **AC-3.2**: Validates `verified by: audit | live-run | operator | doc-review` rows and requires `Expected result source` to name a concrete proving artifact (`PROVING_PATH_RE`, `TOKEN_RE`, or `BACKTICK_SPAN_RE`), emitting `invalid_non_test_row` otherwise.
- **AC-4.1**: Emits `TEST-BOUNDARIES: EXEMPT` (`reason=pre_existing_feature` for the `10` stems in `PRE_EXISTING_FEATURES` and `reason=archived` for designs under `docs/archive/**`) when `## Test Boundaries` is absent and `--no-exempt` is not set, and emits `TEST-BOUNDARIES: FAIL` (`reasons=missing_section`) when `--no-exempt` is set.
- **AC-6.1**: Calibrates `h_mad_test_boundaries_check.py` against 3 archived design+spec pairs copied to `tmp_path` (`exec-path-hardening` `acs=24/24`, `audit-report-docs-copy` `acs=40/40`, `tdd-gate-fail-opens` `acs=44/44`) with `< 0.200`s (`< 200ms`) wall-clock execution per design (`time.monotonic()`) while leaving `docs/archive/` unmodified.
- **AC-6.2**: Rejects all `5` seeded broken fixture classes (`missing_section` / `missing_table`, `placeholder_cell`, `uncovered_ac`, `tautological_oracle`, `invalid_non_test_row`) with `TEST-BOUNDARIES: FAIL` and exact reason codes.

---

## Task 2: `design-template-test-boundaries`

**Task shape**: `new-behaviour`
**Production file**: `h-mad/references/inline-protocols.md`, `h-mad/agents/design-author.md`
**Test file**: `h-mad/tests/test_h_mad_doc_templates.py`, `h-mad/tests/test_h_mad_test_boundaries_check.py`

**Code structure**:
1. In `h-mad/references/inline-protocols.md`, under `## Phase 4 — Design`, inside numbered step `3. Draft the design:`'s `markdown` fenced code block (where each `## ` heading is indented by 3 spaces), immediately after the `## Test Plan` block and immediately before `## Invariant Compliance`, insert (`13 -> 14` headings):
```markdown
   ## Test Boundaries
   | Public interface | Acceptance criteria | Expected result source | Mocked dependencies | Exclusions |
   |---|---|---|---|---|
   | `<module.func or CLI command or verified by: audit\|live-run\|operator\|doc-review>` | `AC-1.1` | `<independent spec table / fixture / analytical formula / proving artifact path>` | `none` | `<what this boundary intentionally does not test>` |

   <!--
   Rules for ## Test Boundaries (enforced by h_mad_test_boundaries_check.py):
   - Every active AC-X.Y (including lettered AC-X.Y[a-z]) in docs/01-plan/features/<feature>.spec.md must appear in Acceptance criteria in at least one row.
   - Public interface names the module, class, function, CLI entrypoint, or script under test — or verified by: audit, verified by: live-run, verified by: operator, or verified by: doc-review for non-test rows.
   - Expected result source states the independent source of truth for expected outputs (spec table, RFC/protocol fixture, golden corpus, analytical formula, or for a verified by: row, the concrete proving artifact path or command token) — never the implementation under test.
   - Mocked dependencies lists only external boundaries (clocks, network, filesystem, subprocesses, external services) or none when no dependencies are mocked.
   - Exclusions states what this boundary intentionally does not test (or which sibling row/layer covers it).
   -->
```
2. In `h-mad/agents/design-author.md`, under `## Rules — each closes a measured failure class`, immediately after Rule `7.` (`h_mad_precheck_doc.py`), insert Rule `7a.`:
```markdown
7a. **Populate `## Test Boundaries` for every active spec `AC-X.Y[a-z]` and run the deterministic boundary checker before reporting `DONE`.**
    Every `docs/02-design/features/<feature>.design.md` you author or revise must carry a `## Test Boundaries` section containing the 5-column Markdown pipe table (`| Public interface | Acceptance criteria | Expected result source | Mocked dependencies | Exclusions |`) covering every active `AC-X.Y` (including lettered `AC-X.Y[a-z]`) in `docs/01-plan/features/<feature>.spec.md`. Before emitting `DESIGN-AUTHOR: DONE`, run:
    `python3 <skill_dir>/scripts/h_mad_test_boundaries_check.py docs/02-design/features/<feature>.design.md --spec docs/01-plan/features/<feature>.spec.md`
    (where <skill_dir> is the active H-MAD skill directory for the current host, e.g. h-mad in this checkout, `~/.claude/skills/h-mad`, `~/.agents/skills/h-mad`, or `~/.gemini/config/skills/h-mad`).
    Read the `TEST-BOUNDARIES:` token, never `$?`. Fix any `TEST-BOUNDARIES: FAIL` (`TEST-BOUNDARIES-ISSUE:`) or `UNREADABLE` output until the checker prints `TEST-BOUNDARIES: PASS`.
```
And under `## Output` in `h-mad/agents/design-author.md`, in the paragraph following the `DESIGN-AUTHOR: DONE` fenced block (preserving `Hash the **document**, never your report file` untouched), require reporting the `TEST-BOUNDARIES: PASS` verification output alongside the premise verification commands.

**Test specification**:
1. In `h-mad/tests/test_h_mad_doc_templates.py`:
   - Update `PRIOR_HMAD_HEADINGS["design"]` from `7` entries to `8` entries by inserting `"Test Boundaries"` immediately after `"Test Strategy"` and before `"Invariant Compliance"`.
   - Add `test_design_template_contains_test_boundaries_five_column_table() -> None` (`1` new test function, bringing `h-mad/tests/test_h_mad_doc_templates.py` from `7` to `8` pytest nodes) verifying that in `_template_blocks()["design"]`:
     1. `_headings(block)` has `14` headings with `"Test Boundaries"` positioned immediately after `"Test Plan"` and immediately before `"Invariant Compliance"`, and
     2. the `## Test Boundaries` section slice (between `## Test Boundaries` and `## Invariant Compliance`) contains the exact 5-column Markdown pipe table header `| Public interface | Acceptance criteria | Expected result source | Mocked dependencies | Exclusions |` and separator row `|---|---|---|---|---|` (so removing the table while retaining `## Test Boundaries` fails the test):
   ```python
   # h-mad/tests/test_h_mad_doc_templates.py
   def test_design_template_contains_test_boundaries_five_column_table() -> None:
       block = _template_blocks()["design"]
       headings = _headings(block)
       assert len(headings) == 14
       tb_idx = headings.index("Test Boundaries")
       assert headings[tb_idx - 1] == "Test Plan"
       assert headings[tb_idx + 1] == "Invariant Compliance"
       sec_match = re.search(
           r"^\s*## Test Boundaries\s*\n(?P<body>.*?)(?=^\s*## Invariant Compliance\b)",
           block,
           flags=re.MULTILINE | re.DOTALL,
       )
       assert sec_match is not None, "missing ## Test Boundaries section body before ## Invariant Compliance"
       sec_body = sec_match.group("body")
       expected_header = (
           "| Public interface | Acceptance criteria | Expected result source | Mocked dependencies | Exclusions |"
       )
       assert expected_header in sec_body
       assert "|---|---|---|---|---|" in sec_body
   ```
2. In `h-mad/tests/test_h_mad_test_boundaries_check.py`, add `TestDesignAuthorAndSelfBootstrap::test_design_author_requires_test_boundaries_and_pre_done_check` (`1` new method, bringing `TestDesignAuthorAndSelfBootstrap` to `2` methods and `h-mad/tests/test_h_mad_test_boundaries_check.py` to `25` methods):
   - `TestDesignAuthorAndSelfBootstrap::test_design_author_requires_test_boundaries_and_pre_done_check`:
     - Verifies `h-mad/agents/design-author.md` requires `## Test Boundaries` for every active `AC-X.Y[a-z]` and contains the exact host-independent self-check command substring `python3 <skill_dir>/scripts/h_mad_test_boundaries_check.py docs/02-design/features/<feature>.design.md --spec docs/01-plan/features/<feature>.spec.md` and `(where <skill_dir> is the active H-MAD skill directory for the current host, e.g. h-mad in this checkout`, requiring `TEST-BOUNDARIES: PASS` before `DESIGN-AUTHOR: DONE` (`AC-1.3`).

**Expected RED result**:
```
FAILED h-mad/tests/test_h_mad_doc_templates.py::test_bkit_validated_templates_have_required_superset_headings[design]
FAILED h-mad/tests/test_h_mad_doc_templates.py::test_design_template_contains_test_boundaries_five_column_table
FAILED h-mad/tests/test_h_mad_test_boundaries_check.py::TestDesignAuthorAndSelfBootstrap::test_design_author_requires_test_boundaries_and_pre_done_check
```
RED split across both test files (`--expect-fail 3 --expect-pass 30`): `h-mad/tests/test_h_mad_doc_templates.py` has `8` pytest nodes (`2 F, 6 P`, where the `6` existing nodes `test_bkit_validated_templates_have_required_superset_headings[plan]`, `test_bkit_validated_templates_have_required_superset_headings[report]`, `test_template_blocks_do_not_contain_plan_plus_trigger_literals`, and `test_bkit_validator_accepts_plan_design_report_templates[...]` (`3` nodes) are regression guards `--guard`); `h-mad/tests/test_h_mad_test_boundaries_check.py` has `25` pytest nodes (`1 F, 24 P`, where all `24` Task 1 methods are regression guards `--guard`); combined: `3 F, 30 P`.

**Expected GREEN result**:
```
PASSED h-mad/tests/test_h_mad_doc_templates.py (0 failed, 8 passed)
PASSED h-mad/tests/test_h_mad_test_boundaries_check.py (0 failed, 25 passed)
```
GREEN split: `0 F, 33 P` combined (`8 P` in `test_h_mad_doc_templates.py` + `25 P` in `test_h_mad_test_boundaries_check.py`). Also verify `h-mad/tests/test_h_mad_doc_shape_check.py` remains untouched and passes (`REQUIRED_SECTIONS["design"]` in `h_mad_doc_shape_check.py` retains its `7` bkit-mirrored headings, verified by `TestMirrorFidelity::test_required_sections_match_the_live_validator`).

**Acceptance criteria**:
- **AC-1.1**: The Phase 4 design template in `h-mad/references/inline-protocols.md` includes `## Test Boundaries` (`13 -> 14` headings, positioned between `## Test Plan` and `## Invariant Compliance`) with the 5-column Markdown pipe table (`| Public interface | Acceptance criteria | Expected result source | Mocked dependencies | Exclusions |`) and separator row `|---|---|---|---|---|`, and `h-mad/tests/test_h_mad_doc_templates.py` verifies both `"Test Boundaries"` in `PRIOR_HMAD_HEADINGS["design"]` (`7 -> 8` entries) and the 5-column table inside the `## Test Boundaries` template section (`test_design_template_contains_test_boundaries_five_column_table`).
- **AC-1.2**: `REQUIRED_SECTIONS["design"]` in `h-mad/scripts/h_mad_doc_shape_check.py` remains untouched (`7` bkit-mirrored headings), preserving `TestMirrorFidelity::test_required_sections_match_the_live_validator` in `h-mad/tests/test_h_mad_doc_shape_check.py`.
- **AC-1.3** (authoring-contract half): `h-mad/agents/design-author.md` includes Rule `7a.` requiring `## Test Boundaries` and the `<skill_dir>/scripts/h_mad_test_boundaries_check.py` self-check before `DESIGN-AUTHOR: DONE`.

---

## Task 3: `h_mad_audit_gate_design_boundaries_wire`

**Task shape**: `wiring`
**Production file**: `h-mad/scripts/h_mad_audit_gate.py`
**Test file**: `h-mad/tests/test_h_mad_test_boundaries_check.py`
**WIRE**: `h-mad/scripts/h_mad_audit_gate.py:main` → `_run_design_boundaries_checks`
**WIRE-PIN**: `h-mad/tests/test_h_mad_test_boundaries_check.py::TestExemptionsAndAuditGateIntegration::test_gate_fails_and_suppresses_stamp_when_design_boundaries_fail`

**Code structure**:
1. In `h-mad/scripts/h_mad_audit_gate.py`, keep top-level imports (`11` stdlib import lines) untouched and insert `_DESIGN_AUDIT_RE`, `_load_test_boundaries_checker()`, `_candidate_design_paths()`, and `_run_design_boundaries_checks()` immediately before `def main(argv: list[str] | None = None) -> int:`:
```python
_DESIGN_AUDIT_RE = re.compile(
    r"^(?P<feature>.+)\.design\.audit\.v\d+(?:\.[a-z0-9_-]+)?\.md$"
)


def _load_test_boundaries_checker():
    """Load sibling h_mad_test_boundaries_check.py via spec_from_file_location.

    Never a top-level import: tree_lock_plugin.py loads h_mad_audit_gate.py by
    file path without h-mad/scripts on sys.path.
    """
    import importlib.util

    checker_path = Path(__file__).with_name("h_mad_test_boundaries_check.py")
    spec = importlib.util.spec_from_file_location(
        "_h_mad_test_boundaries_check", checker_path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {checker_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, checker_path


def _candidate_design_paths(audit_file: Path, gated: list[Path]) -> list[Path]:
    """Resolve deduplicated existing candidate .design.md paths in CLI order."""
    out: list[Path] = []
    seen: set[Path] = set()
    for path in gated:
        if path.name.endswith(".design.md") and path.exists():
            resolved = path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                out.append(path)
    if out:
        return out

    m = _DESIGN_AUDIT_RE.match(audit_file.name)
    if m is not None:
        feature = m.group("feature")
        abs_report = audit_file.resolve()
        co_located = audit_file.parent / f"{feature}.design.md"
        if co_located.exists():
            candidate = co_located
        elif (
            len(abs_report.parts) >= 4
            and abs_report.parts[-4:-1] == ("docs", "02-design", "features")
        ):
            canonical = (
                abs_report.parents[3]
                / "docs"
                / "02-design"
                / "features"
                / f"{feature}.design.md"
            )
            candidate = (
                canonical
                if canonical.exists()
                else Path("docs/02-design/features") / f"{feature}.design.md"
            )
        elif "docs" in abs_report.parts[:-1]:
            docs_idx = len(abs_report.parts) - 2 - abs_report.parts[:-1][::-1].index("docs")
            report_project_root = Path(*abs_report.parts[:docs_idx])
            canonical = (
                report_project_root
                / "docs"
                / "02-design"
                / "features"
                / f"{feature}.design.md"
            )
            candidate = (
                canonical
                if canonical.exists()
                else Path("docs/02-design/features") / f"{feature}.design.md"
            )
        else:
            candidate = Path("docs/02-design/features") / f"{feature}.design.md"
        if candidate.exists():
            resolved = candidate.resolve()
            if resolved not in seen:
                seen.add(resolved)
                out.append(candidate)
    return out


def _run_design_boundaries_checks(
    audit_file: Path, gated: list[Path]
) -> tuple[bool, list[str]]:
    """Evaluate activated candidate .design.md paths before .gated.json stamping."""
    candidates = [p for p in _candidate_design_paths(audit_file, gated) if p.exists()]
    if not candidates:
        return True, []

    checker, checker_path = _load_test_boundaries_checker()
    all_ok = True
    lines: list[str] = []
    for design_path in candidates:
        proj_root = checker.infer_project_root(design_path)
        if not checker.should_activate_design_check(design_path, proj_root):
            continue
        cmd = [sys.executable, str(checker_path), str(design_path)]
        if proj_root is not None:
            cmd.extend(["--root", str(proj_root)])
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        out_lines = [ln for ln in (proc.stdout or "").splitlines() if ln.strip()]
        lines.extend(out_lines)
        primary = out_lines[0] if out_lines else ""
        if proc.returncode != 0 or not (
            primary.startswith("TEST-BOUNDARIES: PASS ")
            or primary.startswith("TEST-BOUNDARIES: EXEMPT ")
        ):
            all_ok = False
    return all_ok, lines
```
2. Inside `h-mad/scripts/h_mad_audit_gate.py:main`, immediately after the `elif args.project_tests is not None:` suite evaluation block and strictly ABOVE `# Declared ABOVE stamped deliberately`:
```python
    tb_ok, tb_lines = _run_design_boundaries_checks(args.audit_file, args.gated)
    if not tb_ok:
        verdict = "FAIL"
```
3. Inside `h-mad/scripts/h_mad_audit_gate.py:main`, immediately after `if legs_line is not None:\n        print(f"GATE-LEGS: {legs_line}")` and before `print(f"[H-MAD] {feature} gate {verdict}")`:
```python
    for tb_line in tb_lines:
        print(tb_line)
```

**Test specification** (add `7` methods to `TestExemptionsAndAuditGateIntegration` in `h-mad/tests/test_h_mad_test_boundaries_check.py`, bringing `TestExemptionsAndAuditGateIntegration` from `1` to `8` methods and the file total from `25` to `32` methods):
- `TestExemptionsAndAuditGateIntegration::test_isolated_spec_from_file_location_activation_parity`:
  - Loads `h_mad_audit_gate.py` in a context where `h-mad/scripts` is absent from `sys.path` via `importlib.util.spec_from_file_location`, and asserts exact parity between direct `h_mad_test_boundaries_check.should_activate_design_check` and `h_mad_audit_gate._load_test_boundaries_checker()[0].should_activate_design_check` across fenced `## Test Boundaries` headings, active lettered ACs vs retired-only specs, and both spec resolution branches (`AC-4.2`, `AC-4.3`).
- `TestExemptionsAndAuditGateIntegration::test_external_project_root_activation_fails_missing_section`:
  - Runs `h_mad_audit_gate.py` against a separate project tree under `tmp_path / "external_project" / "docs" / "02-design" / "features" / "demo.design.md"` (missing `## Test Boundaries`, no paired spec); asserts Arm 1 activates and `GATE: FAIL` + `TEST-BOUNDARIES: FAIL ... reasons=missing_section` is emitted (`AC-4.2`, `AC-4.3`).
- `TestExemptionsAndAuditGateIntegration::test_unreadable_paired_spec_fails_gate_closed`:
  - Runs `h_mad_audit_gate.py` on an external `.design.md` (no `## Test Boundaries` heading) paired with a sibling `.spec.md` containing invalid UTF-8 bytes (`b"\xff\xfe"`); asserts `should_activate_design_check` returns `True`, `h_mad_audit_gate.py` emits `GATE: FAIL` and `TEST-BOUNDARIES: UNREADABLE`, and does not crash (`AC-2.1`, `AC-4.2`).
- `TestExemptionsAndAuditGateIntegration::test_directory_valued_design_candidate_fails_gate_closed`:
  - Runs `h_mad_audit_gate.py` with a positional `<feature>.design.audit.v1.p1.md` report whose co-located canonical `docs/02-design/features/<feature>.design.md` is a directory (`mkdir()`); asserts `should_activate_design_check` returns `True`, `h_mad_audit_gate.py` emits `GATE: FAIL` and `TEST-BOUNDARIES: UNREADABLE ... err=IsADirectoryError` (`AC-2.1`, `AC-4.2`).
- `TestExemptionsAndAuditGateIntegration::test_gate_fails_and_suppresses_stamp_when_design_boundaries_fail` (**WIRE-PIN**):
  - Runs `h_mad_audit_gate.py` on a clean `must=0 should=0` audit report paired (via repeatable `--gated`, via positional `<feature>.design.audit.v1.md`, and with a nonexistent `--gated missing.design.md` falling back to positional `<feature>.design.audit.v1.md`'s existing co-located `<feature>.design.md`) with an activated `.design.md` whose `## Test Boundaries` fails; asserts `GATE: FAIL must=0 should=0`, `TEST-BOUNDARIES: FAIL` printed immediately after `GATE:` / `GATE-CLASS:`, and no `.gated.json` sidecar file written (`AC-4.2`, `AC-4.4`, `AC-6.3`).
  - **Why this WIRE-PIN fails on a caller assertion (never `ImportError`)**: `h_mad_audit_gate.py` is already present and executable before Task 3; without the `main` → `_run_design_boundaries_checks` wire in `h_mad_audit_gate.py:main`, `h_mad_audit_gate.py` evaluates only the clean `must=0 should=0` audit report, prints `GATE: PASS must=0 should=0 gated=1`, and writes the `.gated.json` stamp, failing the test's `assert "GATE: FAIL" in proc.stdout` and `assert not gated_stamp.exists()` assertions.
- `TestExemptionsAndAuditGateIntegration::test_gate_passes_and_writes_stamp_when_activated_design_passes_or_is_exempt`:
  - Runs `h_mad_audit_gate.py` on a clean `must=0 should=0` audit report with `--gated` pointing to (a) an activated `.design.md` whose `## Test Boundaries` table passes (`TEST-BOUNDARIES: PASS ...`) and (b) an activated `.design.md` that is exempt (`TEST-BOUNDARIES: EXEMPT ...`, e.g. under `docs/archive/` or a `PRE_EXISTING_FEATURES` stem without `## Test Boundaries`); asserts in both cases that `h_mad_audit_gate.py` emits `GATE: PASS must=0 should=0 gated=1`, prints the captured `TEST-BOUNDARIES: PASS ...` or `TEST-BOUNDARIES: EXEMPT ...` line immediately after `GATE:` / `GATE-CLASS:` / `GATE-LEGS:`, writes a `.gated.json` sidecar that verifies cleanly via `--verify-stamp` (`STAMP: CURRENT`), and fails in Task 3 RED because unwired `h_mad_audit_gate.py` emits no `TEST-BOUNDARIES:` line (`AC-4.3`).
- `TestExemptionsAndAuditGateIntegration::test_gate_does_not_activate_on_bare_synthetic_design_in_tmp_path` (**regression guard `--guard`**):
  - Runs `h_mad_audit_gate.py` on a clean `must=0 should=0` audit report `--gated` to a bare synthetic `.design.md` in `tmp_path` outside `docs/02-design/features/` and `docs/archive/` with no `## Test Boundaries` heading and no paired `.spec.md` with active `AC-X.Y[a-z]`; asserts `GATE: PASS must=0 should=0 gated=1`, `.gated.json` written, and `"TEST-BOUNDARIES:" not in proc.stdout` (`AC-4.3`, `AC-4.4`, `AC-6.3`). Because this negative fall-through test asserts that unwired/unactivated runs do not emit `TEST-BOUNDARIES:`, it passes in Task 3 RED and is declared as a regression guard (`--guard`) for `h_mad_assemble_tdd.py --phase red`.

**Expected RED result**:
```
FAILED h-mad/tests/test_h_mad_test_boundaries_check.py::TestExemptionsAndAuditGateIntegration::test_isolated_spec_from_file_location_activation_parity
FAILED h-mad/tests/test_h_mad_test_boundaries_check.py::TestExemptionsAndAuditGateIntegration::test_external_project_root_activation_fails_missing_section
FAILED h-mad/tests/test_h_mad_test_boundaries_check.py::TestExemptionsAndAuditGateIntegration::test_unreadable_paired_spec_fails_gate_closed
FAILED h-mad/tests/test_h_mad_test_boundaries_check.py::TestExemptionsAndAuditGateIntegration::test_directory_valued_design_candidate_fails_gate_closed
FAILED h-mad/tests/test_h_mad_test_boundaries_check.py::TestExemptionsAndAuditGateIntegration::test_gate_fails_and_suppresses_stamp_when_design_boundaries_fail
FAILED h-mad/tests/test_h_mad_test_boundaries_check.py::TestExemptionsAndAuditGateIntegration::test_gate_passes_and_writes_stamp_when_activated_design_passes_or_is_exempt
```
RED split (`--expect-fail 6 --expect-pass 26`): `6 F, 26 P` (`32` test methods in `h-mad/tests/test_h_mad_test_boundaries_check.py`: the `6` positive activation/wiring/activated-pass/activated-exempt tests fail before `h_mad_audit_gate.py` is wired, while `TestExemptionsAndAuditGateIntegration::test_gate_does_not_activate_on_bare_synthetic_design_in_tmp_path` and the `25` tests from Tasks 1–2 pass and must be passed as regression guards `--guard` to `h_mad_assemble_tdd.py --phase red`).

**Expected GREEN result**:
```
PASSED h-mad/tests/test_h_mad_test_boundaries_check.py (0 failed, 32 passed)
```
GREEN split: `0 F, 32 P`.

**Mutation rows for `scripts/h_mad_audit_gate.py`** (`2` rows, codified in `h-mad/tests/mutation-specs/test_boundaries_gate.json` in Task 5):
1. `audit-gate-connection-removed-bypasses-test-boundaries`: `file="scripts/h_mad_audit_gate.py"`, `symbol="main"`, `find='    tb_ok, tb_lines = _run_design_boundaries_checks(args.audit_file, args.gated)\n    if not tb_ok:\n        verdict = "FAIL"'`, `replace='    tb_ok, tb_lines = _run_design_boundaries_checks(args.audit_file, args.gated)\n    if False:\n        verdict = "FAIL"'`, `test="tests/test_h_mad_test_boundaries_check.py::TestExemptionsAndAuditGateIntegration::test_gate_fails_and_suppresses_stamp_when_design_boundaries_fail"`.
2. `audit-gate-connection-forced-unconditional-activation`: `file="scripts/h_mad_audit_gate.py"`, `symbol="_run_design_boundaries_checks"`, `find="        if not checker.should_activate_design_check(design_path, proj_root):\n            continue"`, `replace="        if False:\n            continue"`, `test="tests/test_h_mad_test_boundaries_check.py::TestExemptionsAndAuditGateIntegration::test_gate_does_not_activate_on_bare_synthetic_design_in_tmp_path"`.

**Acceptance criteria**:
- **AC-4.2**: `h_mad_audit_gate.py` loads `h_mad_test_boundaries_check.py` via `importlib.util.spec_from_file_location`, resolves existing candidate `.design.md` paths from repeatable `--gated` (filtering via `path.exists()` before deciding whether to fall back) or positional `<feature>.design.audit.v<N>[.<leg>].md` reports, delegates root inference and 3-arm activation to `infer_project_root` and `should_activate_design_check`, flips `verdict = "FAIL"` before `.gated.json` stamping on any non-`PASS`/non-`EXEMPT` result, and prints `TEST-BOUNDARIES:` lines immediately after `GATE:` / `GATE-CLASS:` / `GATE-LEGS:`.
- **AC-4.3**: `h_mad_audit_gate.py` activates `h_mad_test_boundaries_check.py` if and only if at least one of the 3 arms of `should_activate_design_check` holds, emits `GATE: PASS` + `TEST-BOUNDARIES: PASS` / `TEST-BOUNDARIES: EXEMPT` and writes `.gated.json` when every activated candidate design passes or is exempt on a `must=0` report, and suppresses `.gated.json` creation whenever `tb_ok` is `False` (`h-mad/invariants.base.md` §"Audit-gate signal discipline" & §"Single-source contract").
- **AC-4.4**: Non-design audit reports and bare synthetic `.design.md` test fixtures in `tmp_path` outside `docs/02-design/features/` and `docs/archive/` without `## Test Boundaries` or active spec ACs do not activate the checker, preserving all existing `test_h_mad_audit_gate.py`, `test_h_mad_audit_leg_set_gate.py`, and `test_h_mad_audit_cycle.py` tests and existing mutation specs (`audit_suite_gate.json`, `audit_gate_stamp.json`).

---

## Task 4: `audit_prompt_and_doc_auditor_test_boundaries`

**Task shape**: `new-behaviour`
**Production file**: `h-mad/audit-prompt.template.md`, `h-mad/agents/doc-auditor.md`
**Test file**: `h-mad/tests/test_h_mad_test_boundaries_check.py`

**Code structure**:
1. In `h-mad/audit-prompt.template.md`, under `Axis A — Generic adversarial:`, immediately after the existing inline `- {{ONLY:design}} Cross-doc: does the design implement what the plan promised?` bullet (and its two continuation lines) and before `Axis B — Invariant compliance`, insert:
```markdown
{{ONLY:design}}
- Test Boundaries (`## Test Boundaries` 5-column table): raise a `## Must-fix` (`class: build`) finding whenever:
  1. `## Test Boundaries` is missing **on a non-exempt design**, leaves any active spec `AC-X.Y[a-z]` uncovered, or contains placeholder cells;
  2. Any row's `Expected result source` is semantically tautological (derives expected values from the implementation, helper, or formula under test rather than an independent specification, fixture, protocol rule, or analytical invariant);
  3. Any row tests a private/internal helper instead of the public interface, or mocks the unit under test / an internal collaborator that should be exercised for real; or
  4. Any `verified by:` row (`verified by: audit | live-run | operator | doc-review`) claims non-test verification for behavior that can and should be unit/integration tested, or names a proving artifact that does not actually verify the listed AC.
{{END-ONLY}}
```
2. In `h-mad/agents/doc-auditor.md`, under `## Rules — each closes a measured failure class`, immediately after Rule `7b.` (`Classify every finding, on a continuation line.`) and before Rule `8.` (`You never fix anything.`), insert Rule `7c.`:
```markdown
7c. **Phase 4 design audits: challenge `## Test Boundaries` on coverage, oracle independence, boundary placement, and `verified by:` escape hatches.**
    On a Phase 4 design audit, raise a `## Must-fix` (`class: build`) finding whenever:
    - `## Test Boundaries` is missing **on a non-exempt design**, leaves any active spec `AC-X.Y[a-z]` uncovered, or contains placeholder cells;
    - Any row's `Expected result source` is semantically tautological (re-states the implementation's internal logic or helper output rather than an independent spec table, fixture, protocol contract, or analytical invariant);
    - Any row targets a private/internal helper instead of the public interface, or mocks the unit under test / an internal collaborator that should run for real; or
    - Any `verified by:` row (`verified by: audit | live-run | operator | doc-review`) claims non-test verification for behavior that can and should be unit/integration tested, or names a proving artifact that does not verify the listed AC.
```

**Test specification** (add class `TestAuditPromptAndDocAuditorContract` with `2` methods in `h-mad/tests/test_h_mad_test_boundaries_check.py`, bringing file total from `32` to `34` methods):
- `TestAuditPromptAndDocAuditorContract::test_audit_prompt_and_doc_auditor_contain_test_boundaries_rubric`:
  - Verifies `h-mad/audit-prompt.template.md` (`{{ONLY:design}}` block) and `h-mad/agents/doc-auditor.md` (Rule `7c.` under `## Rules — each closes a measured failure class`) both require `## Must-fix` (`class: build`) when `## Test Boundaries` is missing on a non-exempt design or leaves any active spec `AC-X.Y[a-z]` uncovered, and challenge semantic oracle independence, public-interface boundary placement, internal-collaborator mocking, and `verified by:` justification (`AC-5.1`).
- `TestAuditPromptAndDocAuditorContract::test_assemble_audit_resolves_test_boundaries_for_design_only`:
  - Verifies `h_mad_assemble_audit.resolve` includes the `## Test Boundaries` rubric for `design` and strips it for `plan` and `impl-plan` with zero `unresolved_conditional` leaks (`AC-5.1`).

**Expected RED result**:
```
FAILED h-mad/tests/test_h_mad_test_boundaries_check.py::TestAuditPromptAndDocAuditorContract::test_audit_prompt_and_doc_auditor_contain_test_boundaries_rubric
FAILED h-mad/tests/test_h_mad_test_boundaries_check.py::TestAuditPromptAndDocAuditorContract::test_assemble_audit_resolves_test_boundaries_for_design_only
```
RED split (`--expect-fail 2 --expect-pass 32`): `2 F, 32 P` (`34` test methods in `h-mad/tests/test_h_mad_test_boundaries_check.py`: the `2` new tests in `TestAuditPromptAndDocAuditorContract` fail, while the `32` tests from Tasks 1–3 pass as regression guards `--guard`).

**Expected GREEN result**:
```
PASSED h-mad/tests/test_h_mad_test_boundaries_check.py (0 failed, 34 passed)
```
GREEN split: `0 F, 34 P`. Also verify `h-mad/tests/test_h_mad_audit_spec_axis.py` (`16` existing tests) continues to pass (`0 F, 16 P`).

**Acceptance criteria**:
- **AC-5.1**: `h-mad/audit-prompt.template.md` (`{{ONLY:design}}` ... `{{END-ONLY}}`) and `h-mad/agents/doc-auditor.md` (Rule `7c.`) instruct `doc-auditor` on Phase 4 design audits to raise a `## Must-fix` (`class: build`) finding on missing non-exempt `## Test Boundaries`, uncovered active spec ACs, semantic oracle tautologies, private-helper / over-mocked boundaries, or unjustified `verified by:` rows, and `h_mad_assemble_audit.resolve` resolves the block cleanly for `design` only.

---

## Task 5: `calibration_broken_fixtures_and_mutation_spec`

**Task shape**: `new-behaviour`
**Production file**: `h-mad/tests/mutation-specs/test_boundaries_gate.json`
**Test file**: `h-mad/tests/test_h_mad_test_boundaries_check.py`

**Code structure** (`h-mad/tests/mutation-specs/test_boundaries_gate.json` — `8` mutations total: `2` on `scripts/h_mad_audit_gate.py` + `6` on `scripts/h_mad_test_boundaries_check.py`, conforming to `h_mad_mutation_harness.py:_load_spec`; `"command"` excludes `test_mutation_spec_schema_and_check_anchors_pass` via `-k "not test_mutation_spec_schema_and_check_anchors_pass"` so active mutations on disk do not cause `--check-anchors` inside that test to fail with `ANCHORS_DRIFTED` during mutation probes):
```json
{
  "_why": "hmad-test-boundaries: Phase 4 design test-boundaries checker and two-direction audit-gate connection enforcement.",
  "root": "../..",
  "command": [
    "python3.11",
    "-m",
    "pytest",
    "tests/test_h_mad_test_boundaries_check.py",
    "-k",
    "not test_mutation_spec_schema_and_check_anchors_pass",
    "-q"
  ],
  "target_command": [
    "python3.11",
    "-m",
    "pytest",
    "-q"
  ],
  "mutations": [
    {
      "name": "audit-gate-connection-removed-bypasses-test-boundaries",
      "_mechanism": "Direction 1 connection removal: h_mad_audit_gate.py ignores a failing TEST-BOUNDARIES verdict and stamps PASS while h_mad_test_boundaries_check.py remains intact.",
      "file": "scripts/h_mad_audit_gate.py",
      "symbol": "main",
      "find": "    tb_ok, tb_lines = _run_design_boundaries_checks(args.audit_file, args.gated)\n    if not tb_ok:\n        verdict = \"FAIL\"",
      "replace": "    tb_ok, tb_lines = _run_design_boundaries_checks(args.audit_file, args.gated)\n    if False:\n        verdict = \"FAIL\"",
      "test": "tests/test_h_mad_test_boundaries_check.py::TestExemptionsAndAuditGateIntegration::test_gate_fails_and_suppresses_stamp_when_design_boundaries_fail"
    },
    {
      "name": "audit-gate-connection-forced-unconditional-activation",
      "_mechanism": "Direction 2 forced unconditional activation: h_mad_audit_gate.py runs h_mad_test_boundaries_check.py even when should_activate_design_check returns False, breaking synthetic tmp_path design fixtures.",
      "file": "scripts/h_mad_audit_gate.py",
      "symbol": "_run_design_boundaries_checks",
      "find": "        if not checker.should_activate_design_check(design_path, proj_root):\n            continue",
      "replace": "        if False:\n            continue",
      "test": "tests/test_h_mad_test_boundaries_check.py::TestExemptionsAndAuditGateIntegration::test_gate_does_not_activate_on_bare_synthetic_design_in_tmp_path"
    },
    {
      "name": "checker-placeholder-guard-disabled",
      "_mechanism": "Disables placeholder blocklist matching so placeholder cells like 'tbd' or 'n/a' pass.",
      "file": "scripts/h_mad_test_boundaries_check.py",
      "symbol": "is_placeholder_cell",
      "find": "    if norm_cell in PLACEHOLDER_EXACT:",
      "replace": "    if False:",
      "test": "tests/test_h_mad_test_boundaries_check.py::TestSeededBrokenFixtures::test_seeded_broken_placeholder_cell_rejected"
    },
    {
      "name": "checker-tautological-oracle-guard-disabled",
      "_mechanism": "Disables exact tautological-oracle detection so Expected result source = 'implementation' passes.",
      "file": "scripts/h_mad_test_boundaries_check.py",
      "symbol": "is_tautological_oracle",
      "find": "    if cleaned in TAUTOLOGICAL_EXACT:",
      "replace": "    if False:",
      "test": "tests/test_h_mad_test_boundaries_check.py::TestSeededBrokenFixtures::test_seeded_broken_implementation_oracle_rejected"
    },
    {
      "name": "checker-uncovered-ac-guard-disabled",
      "_mechanism": "Skips uncovered_ac emission when active spec ACs are missing from the table.",
      "file": "scripts/h_mad_test_boundaries_check.py",
      "symbol": "check_design",
      "find": "        if missing_acs:",
      "replace": "        if False:",
      "test": "tests/test_h_mad_test_boundaries_check.py::TestSeededBrokenFixtures::test_seeded_broken_uncovered_ac_rejected"
    },
    {
      "name": "checker-invalid-non-test-row-guard-disabled",
      "_mechanism": "Skips concrete proving artifact check on verified by: rows so 'manual inspection by reviewer' passes.",
      "file": "scripts/h_mad_test_boundaries_check.py",
      "symbol": "validate_non_test_row",
      "find": "    if not oracle_had_basic_error and not has_proving_artifact(oracle_cell):",
      "replace": "    if False:",
      "test": "tests/test_h_mad_test_boundaries_check.py::TestSeededBrokenFixtures::test_seeded_broken_non_test_row_without_artifact_rejected"
    },
    {
      "name": "checker-retired-ac-filter-disabled",
      "_mechanism": "Treats retired ACs in spec.md as active ACs, causing false uncovered_ac failures on grok-audit-surface AC-3.7.",
      "file": "scripts/h_mad_test_boundaries_check.py",
      "symbol": "extract_spec_acs",
      "find": "        if RETIRED_LINE_RE.match(line):",
      "replace": "        if False:",
      "test": "tests/test_h_mad_test_boundaries_check.py::TestSpecAcCoverageAndNonTestRows::test_extract_spec_acs_reference_counts_and_retired_filtering"
    },
    {
      "name": "checker-no-exempt-flag-ignored",
      "_mechanism": "Ignores --no-exempt so pre-existing or archived designs without ## Test Boundaries still return EXEMPT instead of FAIL.",
      "file": "scripts/h_mad_test_boundaries_check.py",
      "symbol": "check_design",
      "find": "    if not has_section and not no_exempt:",
      "replace": "    if not has_section:",
      "test": "tests/test_h_mad_test_boundaries_check.py::TestExemptionsAndAuditGateIntegration::test_pre_existing_and_archived_designs_exempt_unless_no_exempt"
    }
  ]
}
```

**Test specification** (add `TestSeededBrokenFixtures::test_mutation_spec_schema_and_check_anchors_pass` (`1` method) in `h-mad/tests/test_h_mad_test_boundaries_check.py`, bringing `TestSeededBrokenFixtures` from `5` to `6` methods and the file total from `34` to `35` methods across `7` classes):
- `TestSeededBrokenFixtures::test_mutation_spec_schema_and_check_anchors_pass`:
  - Loads `h-mad/tests/mutation-specs/test_boundaries_gate.json`, asserts top-level keys `"root": "../.."`, `"command"`, `"target_command"`, and `"mutations"` with `len(spec["mutations"]) == 8` (`2` targeting `scripts/h_mad_audit_gate.py` and `6` targeting `scripts/h_mad_test_boundaries_check.py`), asserts `"-k"` and `"not test_mutation_spec_schema_and_check_anchors_pass"` are in `spec["command"]` (preventing recursive `--check-anchors` execution while a mutant is active on disk), and runs `python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/test_boundaries_gate.json h-mad/tests/mutation-specs/audit_suite_gate.json h-mad/tests/mutation-specs/audit_gate_stamp.json`, asserting `ANCHORS: ANCHORS_OK` (`AC-6.3`).

**Expected RED result**:
```
FAILED h-mad/tests/test_h_mad_test_boundaries_check.py::TestSeededBrokenFixtures::test_mutation_spec_schema_and_check_anchors_pass
```
RED split (`--expect-fail 1 --expect-pass 34`): `1 F, 34 P` (`35` test methods in `h-mad/tests/test_h_mad_test_boundaries_check.py`: `test_mutation_spec_schema_and_check_anchors_pass` fails with `FileNotFoundError` before `h-mad/tests/mutation-specs/test_boundaries_gate.json` is created, while the `34` tests from Tasks 1–4 pass as regression guards `--guard`, and reverting `h-mad/tests/mutation-specs/test_boundaries_gate.json` in 5e flips `test_mutation_spec_schema_and_check_anchors_pass` back to RED).

**Expected GREEN result**:
```
PASSED h-mad/tests/test_h_mad_test_boundaries_check.py (0 failed, 35 passed)
```
GREEN split: `0 F, 35 P`, plus `python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/test_boundaries_gate.json` prints `MUTATION: ALL_CAUGHT` (`survived=0 refused=0`).

**Acceptance criteria**:
- **AC-6.3**: `h-mad/tests/mutation-specs/test_boundaries_gate.json` declares `8` mutations (`2` two-direction connection mutations on `scripts/h_mad_audit_gate.py` + `6` guard mutations on `scripts/h_mad_test_boundaries_check.py`), passes `h_mad_mutation_harness.py --check-anchors` (`ANCHORS: ANCHORS_OK`), and achieves `MUTATION: ALL_CAUGHT` (`survived=0 refused=0`).

---

## Verification Matrix (Spec AC → Task → Test Method)

| AC ID | Task | Verifying Test Method(s) |
|---|---|---|
| `AC-1.1` | Task 2 | `h-mad/tests/test_h_mad_doc_templates.py::test_bkit_validated_templates_have_required_superset_headings`, `h-mad/tests/test_h_mad_doc_templates.py::test_design_template_contains_test_boundaries_five_column_table` |
| `AC-1.2` | Task 2 | `h-mad/tests/test_h_mad_doc_shape_check.py::TestMirrorFidelity::test_required_sections_match_the_live_validator` |
| `AC-1.3` | Task 1, Task 2 | `h-mad/tests/test_h_mad_test_boundaries_check.py::TestDesignAuthorAndSelfBootstrap::test_hmad_test_boundaries_design_passes_self_check` (Task 1), `h-mad/tests/test_h_mad_test_boundaries_check.py::TestDesignAuthorAndSelfBootstrap::test_design_author_requires_test_boundaries_and_pre_done_check` (Task 2) |
| `AC-2.1` | Task 1 | `h-mad/tests/test_h_mad_test_boundaries_check.py::TestCliAndTableValidation::test_cli_tokens_and_unreadable_vs_missing_spec_disambiguation`, `h-mad/tests/test_h_mad_test_boundaries_check.py::TestCliAndTableValidation::test_infer_project_root_and_two_branch_resolve_spec_path_from_external_cwd` |
| `AC-2.2` | Task 1 | `h-mad/tests/test_h_mad_test_boundaries_check.py::TestCliAndTableValidation::test_missing_section_and_missing_table_and_empty_rows`, `h-mad/tests/test_h_mad_test_boundaries_check.py::TestCliAndTableValidation::test_invalid_columns_headers_cell_counts_and_zero_ac_tokens`, `h-mad/tests/test_h_mad_test_boundaries_check.py::TestCliAndTableValidation::test_fenced_code_blocks_decoy_headings_and_tables_ignored` |
| `AC-2.3` | Task 1 | `h-mad/tests/test_h_mad_test_boundaries_check.py::TestCliAndTableValidation::test_empty_cell_and_placeholder_cell_across_all_five_columns`, `h-mad/tests/test_h_mad_test_boundaries_check.py::TestCliAndTableValidation::test_mocked_dependencies_allows_none_and_none_explanations_only_in_col_4` |
| `AC-2.4` | Task 1 | `h-mad/tests/test_h_mad_test_boundaries_check.py::TestCliAndTableValidation::test_tautological_oracle_exact_tokens_and_phrase_regexes_rejected`, `h-mad/tests/test_h_mad_test_boundaries_check.py::TestCliAndTableValidation::test_provenance_suffix_in_expected_result_source_does_not_mask_tautology` |
| `AC-3.1` | Task 1 | `h-mad/tests/test_h_mad_test_boundaries_check.py::TestSpecAcCoverageAndNonTestRows::test_extract_spec_acs_reference_counts_and_retired_filtering`, `h-mad/tests/test_h_mad_test_boundaries_check.py::TestSpecAcCoverageAndNonTestRows::test_mid_line_prose_and_version_history_and_fenced_ac_mentions_ignored`, `h-mad/tests/test_h_mad_test_boundaries_check.py::TestSpecAcCoverageAndNonTestRows::test_uncovered_ac_and_unknown_ac_and_optional_retired_ac_handling` |
| `AC-3.2` | Task 1 | `h-mad/tests/test_h_mad_test_boundaries_check.py::TestSpecAcCoverageAndNonTestRows::test_verified_by_rows_accept_valid_kinds_and_proving_artifacts_and_reject_invalid` |
| `AC-4.1` | Task 1 | `h-mad/tests/test_h_mad_test_boundaries_check.py::TestExemptionsAndAuditGateIntegration::test_pre_existing_and_archived_designs_exempt_unless_no_exempt` |
| `AC-4.2` | Task 3 | `h-mad/tests/test_h_mad_test_boundaries_check.py::TestExemptionsAndAuditGateIntegration::test_isolated_spec_from_file_location_activation_parity`, `h-mad/tests/test_h_mad_test_boundaries_check.py::TestExemptionsAndAuditGateIntegration::test_external_project_root_activation_fails_missing_section`, `h-mad/tests/test_h_mad_test_boundaries_check.py::TestExemptionsAndAuditGateIntegration::test_unreadable_paired_spec_fails_gate_closed`, `h-mad/tests/test_h_mad_test_boundaries_check.py::TestExemptionsAndAuditGateIntegration::test_directory_valued_design_candidate_fails_gate_closed`, `h-mad/tests/test_h_mad_test_boundaries_check.py::TestExemptionsAndAuditGateIntegration::test_gate_fails_and_suppresses_stamp_when_design_boundaries_fail` |
| `AC-4.3` | Task 3 | `h-mad/tests/test_h_mad_test_boundaries_check.py::TestExemptionsAndAuditGateIntegration::test_isolated_spec_from_file_location_activation_parity`, `h-mad/tests/test_h_mad_test_boundaries_check.py::TestExemptionsAndAuditGateIntegration::test_external_project_root_activation_fails_missing_section`, `h-mad/tests/test_h_mad_test_boundaries_check.py::TestExemptionsAndAuditGateIntegration::test_gate_passes_and_writes_stamp_when_activated_design_passes_or_is_exempt`, `h-mad/tests/test_h_mad_test_boundaries_check.py::TestExemptionsAndAuditGateIntegration::test_gate_does_not_activate_on_bare_synthetic_design_in_tmp_path` |
| `AC-4.4` | Task 3 | `h-mad/tests/test_h_mad_test_boundaries_check.py::TestExemptionsAndAuditGateIntegration::test_gate_fails_and_suppresses_stamp_when_design_boundaries_fail`, `h-mad/tests/test_h_mad_test_boundaries_check.py::TestExemptionsAndAuditGateIntegration::test_gate_does_not_activate_on_bare_synthetic_design_in_tmp_path` |
| `AC-5.1` | Task 4 | `h-mad/tests/test_h_mad_test_boundaries_check.py::TestAuditPromptAndDocAuditorContract::test_audit_prompt_and_doc_auditor_contain_test_boundaries_rubric`, `h-mad/tests/test_h_mad_test_boundaries_check.py::TestAuditPromptAndDocAuditorContract::test_assemble_audit_resolves_test_boundaries_for_design_only` |
| `AC-6.1` | Task 1 | `h-mad/tests/test_h_mad_test_boundaries_check.py::TestArchivedCalibrationAndPerformance::test_calibrated_exec_path_hardening_passes_under_200ms`, `h-mad/tests/test_h_mad_test_boundaries_check.py::TestArchivedCalibrationAndPerformance::test_calibrated_audit_report_docs_copy_passes_under_200ms`, `h-mad/tests/test_h_mad_test_boundaries_check.py::TestArchivedCalibrationAndPerformance::test_calibrated_tdd_gate_fail_opens_passes_under_200ms`, `h-mad/tests/test_h_mad_test_boundaries_check.py::TestArchivedCalibrationAndPerformance::test_archive_directory_remains_unmodified_and_stdlib_only` |
| `AC-6.2` | Task 1 | `h-mad/tests/test_h_mad_test_boundaries_check.py::TestSeededBrokenFixtures::test_seeded_broken_missing_section_and_missing_table_rejected`, `h-mad/tests/test_h_mad_test_boundaries_check.py::TestSeededBrokenFixtures::test_seeded_broken_placeholder_cell_rejected`, `h-mad/tests/test_h_mad_test_boundaries_check.py::TestSeededBrokenFixtures::test_seeded_broken_uncovered_ac_rejected`, `h-mad/tests/test_h_mad_test_boundaries_check.py::TestSeededBrokenFixtures::test_seeded_broken_implementation_oracle_rejected`, `h-mad/tests/test_h_mad_test_boundaries_check.py::TestSeededBrokenFixtures::test_seeded_broken_non_test_row_without_artifact_rejected` |
| `AC-6.3` | Task 5 | `h-mad/tests/test_h_mad_test_boundaries_check.py::TestSeededBrokenFixtures::test_mutation_spec_schema_and_check_anchors_pass` |

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-10-28 | Initial implementation plan | H-MAD (implplan-author) |
| 1.1 | 2026-10-28 | Resolve Phase 5b Audit Cycle 1 findings (`v1.p1` & `v1.p2`): move all `24` checker tests into Task 1 so every new test fails at RED and all `6` Task 1 mutation rows reference existing test node IDs; inline `normalize_cell`, `is_tautological_oracle`, and `Issue` coordinate contracts into Task 1; fix `infer_project_root` archive-root segment lookup and `FR-2.4` residual placeholder description; add `test_design_template_contains_test_boundaries_five_column_table` in Task 2; add `test_gate_passes_and_writes_stamp_when_activated_design_passes_or_is_exempt` and `_candidate_design_paths` existence filtering in Task 3; remove fabricated `I1`/`I4`/`I5`/`I7` IDs and `<= 6` `## ` section assertions; exclude `test_mutation_spec_schema_and_check_anchors_pass` from `test_boundaries_gate.json` `"command"`; label regression guards (`--guard`); and re-derive the Non-Interference table over all `178` mutation specs with runnable command and exact anchors. | H-MAD (implplan-author) |
| 1.2 | 2026-10-28 | Resolve Phase 5b Audit Cycle 2 findings (`v2.p1` & `v2.p2`): in Task 1 (`check_design`), establish operational-input error precedence (`UNREADABLE`, exit `2`) on `spec_path` for non-exempt designs before section/table structural early returns (`missing_section`, `missing_table`, header `invalid_columns`) so `test_unreadable_paired_spec_fails_gate_closed` and `check_design` agree on the combined-invalid case, and cover the combined-invalid case explicitly in `test_cli_tokens_and_unreadable_vs_missing_spec_disambiguation`; in Task 2, align the `(where <skill_dir> is the active H-MAD skill directory for the current host, e.g. h-mad in this checkout` substring in Rule `7a.` and `test_design_author_requires_test_boundaries_and_pre_done_check` so literal substring matching passes without backtick mismatch; and in Task 4, update the `test_h_mad_audit_spec_axis.py` existing test count from `14` to `16` (`0 F, 16 P`). | H-MAD (implplan-author) |
