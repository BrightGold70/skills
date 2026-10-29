# Design: hmad-test-boundaries

## Executive Summary

| Perspective | Summary |
|---|---|
| **Problem** | H-MAD's Phase 6 TDD gate (`h-mad/scripts/h_mad_tdd_judge.py` and `h-mad/hooks/h-mad-tdd-gate.sh`) and mutation harness (`h-mad/scripts/h_mad_mutation_harness.py`) verify that tests precede production edits and catch declared code mutations, but Phase 4 (Design) does not require a machine-checked declaration of the public interface under test, the independent source of expected outputs (the oracle), mocked external dependencies, or boundary exclusions. This gap allows tautological tests (asserting against outputs computed by the implementation under test) and boundary drift (testing private helpers or mocking internal collaborators) to pass Phase 4 unchallenged. |
| **Solution** | Add a mandatory `## Test Boundaries` section with a 5-column Markdown table (`Public interface`, `Acceptance criteria`, `Expected result source`, `Mocked dependencies`, `Exclusions`) to the Phase 4 design template (`h-mad/references/inline-protocols.md`) and `h-mad/agents/design-author.md`; ship a standalone stdlib-only deterministic checker (`h-mad/scripts/h_mad_test_boundaries_check.py`) that is the single authoritative owner of fenced-heading detection, project-root inference (`infer_project_root`), two-branch paired `.spec.md` resolution (`resolve_spec_path`), head-anchored active/retired `AC-X.Y[a-z]` extraction, and 3-arm gate activation (`should_activate_design_check`); integrate the checker into `h-mad/scripts/h_mad_audit_gate.py` via `importlib.util.spec_from_file_location` without modifying `REQUIRED_SECTIONS` in `h-mad/scripts/h_mad_doc_shape_check.py`; extend the Phase 4 design audit rubric (`h-mad/audit-prompt.template.md` and `h-mad/agents/doc-auditor.md`); and calibrate the checker against 3 archived design+spec pairs (`< 200ms` per design), 5 seeded broken fixture classes, and a two-direction connection-enforced mutation spec (`h-mad/tests/mutation-specs/test_boundaries_gate.json`). |
| **Function / UX Effect** | Every new Phase 4 design document (`docs/02-design/features/<feature>.design.md`) must include a valid `## Test Boundaries` table covering 100% of active `AC-X.Y[a-z]` identifiers in `docs/01-plan/features/<feature>.spec.md` (either as unit/integration test rows or as `verified by: audit \| live-run \| operator \| doc-review` rows naming a concrete proving artifact) before `h-mad/scripts/h_mad_audit_gate.py` can emit `GATE: PASS` or write a `.gated.json` stamp. Pre-existing tracked designs (`10` feature stems in `PRE_EXISTING_FEATURES`) and archived designs (`docs/archive/**`) lacking `## Test Boundaries` emit `TEST-BOUNDARIES: EXEMPT` unless `--no-exempt` is passed. |
| **Core Value** | Forces test-boundary and oracle-independence decisions upstream into Phase 4 Design where deterministic tooling (`h-mad/scripts/h_mad_test_boundaries_check.py`) rejects structural, coverage, placeholder, and lexical-tautology defects in `< 200ms` and Phase 4 LLM auditors (`h-mad/agents/doc-auditor.md`) challenge semantic oracle tautologies and over-mocked internal boundaries before Phase 5 (`impl-plan`) and Phase 6 (`implement`). |

## Overview

`hmad-test-boundaries` closes the Phase 4 design verification gap across all 6 functional requirements (`FR-1`..`FR-6`) and All 17 ACs (`AC-1.1`..`AC-6.3`) defined in `docs/01-plan/features/hmad-test-boundaries.spec.md` (`v1.5`) and `docs/01-plan/features/hmad-test-boundaries.plan.md` (`v1.3`). Rather than modifying `REQUIRED_SECTIONS["design"]` in `h-mad/scripts/h_mad_doc_shape_check.py` (which mirrors bkit's live `template-validator.js` and is locked by `TestMirrorFidelity` in `h-mad/tests/test_h_mad_doc_shape_check.py`), this design adds `## Test Boundaries` as an H-MAD superset heading in `h-mad/references/inline-protocols.md` (`13 -> 14` Phase 4 template headings) and `PRIOR_HMAD_HEADINGS["design"]` in `h-mad/tests/test_h_mad_doc_templates.py` (`7 -> 8` headings), and enforces table completeness, placeholder hygiene, tautological-oracle rejection, and head-anchored active spec AC coverage through a standalone stdlib-only script (`h-mad/scripts/h_mad_test_boundaries_check.py`) wired into `h-mad/scripts/h_mad_audit_gate.py`.

All premises and counts in this design were verified against the working tree at repository `HEAD` (`git rev-parse HEAD` = `9f330f71d65b5e667bd42a92065e77b9bd030d82`):

1. **`h_mad_doc_shape_check.py` bkit mirror constraint (`FR-1.3`, `AC-1.2`):**
   - Command: `python3 -c 'import sys; sys.path.insert(0, "h-mad/scripts"); import h_mad_doc_shape_check as m; print(len(m.REQUIRED_SECTIONS["design"]), m.REQUIRED_SECTIONS["design"])'`
   - Observed output: `7 ['Executive Summary', 'Overview', 'Architecture', 'Detailed Design', 'Implementation Order', 'Test Plan', 'Version History']` (`7` headings).
2. **Phase 4 design template heading count in `h-mad/references/inline-protocols.md` and `PRIOR_HMAD_HEADINGS["design"]` in `h-mad/tests/test_h_mad_doc_templates.py` (`FR-1.1`, `FR-1.3`, `AC-1.1`):**
   - Command: `python3 -c 'import re, ast, pathlib; seg = re.search(r"^## Phase 4\b.*?(?=^## Phase |\Z)", pathlib.Path("h-mad/references/inline-protocols.md").read_text(), re.M | re.S).group(0); body = re.search(r"^\s*`{3,4}markdown\s*\n(.*?)(?m:^\s*`{3,4}\s*$)", seg, re.M | re.S).group(1); h = [l.strip().removeprefix("##").strip() for l in body.splitlines() if l.strip().startswith("## ")]; print(len(h), h); tree = ast.parse(pathlib.Path("h-mad/tests/test_h_mad_doc_templates.py").read_text()); [print(len(v.elts), [e.value for e in v.elts]) for node in tree.body if isinstance(node.targets[0] if isinstance(node, ast.Assign) else None, ast.Name) and node.targets[0].id == "PRIOR_HMAD_HEADINGS" for k, v in zip(node.value.keys, node.value.values) if getattr(k, "value", "") == "design"]'`
   - Observed output: `13 ['Executive Summary', 'Overview', 'Architecture Overview', 'Detailed Design', 'Components Changed / Added', 'Implementation Order', 'Data Model / Schema Changes', 'API / Interface Changes', 'Error Handling Strategy', 'Test Strategy', 'Test Plan', 'Invariant Compliance', 'Version History']` (`13` headings before; `14` after inserting `## Test Boundaries`) and `7 ['Architecture Overview', 'Components Changed / Added', 'Data Model / Schema Changes', 'API / Interface Changes', 'Error Handling Strategy', 'Test Strategy', 'Invariant Compliance']` (`7` entries before; `8` after adding `"Test Boundaries"`).
3. **Tracked design corpus & pre-existing exemption baseline (`FR-4.1`, `AC-4.1`):**
   - Command: `git ls-files 'docs/**/*.design.md' | wc -l && git ls-files 'docs/02-design/features/*.design.md' | wc -l && git ls-files 'docs/archive/**/*.design.md' | wc -l && git ls-files 'docs/01-plan/features/*.spec.md'`
   - Observed output: `39` total tracked `.design.md` files (`10` in `docs/02-design/features/` and `29` in `docs/archive/`), `0` matches for `git grep -n "Test Boundaries" -- 'docs/02-design/**' 'docs/archive/**'` (exit code `1`), and `4` tracked paired `docs/01-plan/features/<feature>.spec.md` files (`exec-missing-report-recovery.spec.md`, `orca-native-orchestration.spec.md`, `orca-native-transport.spec.md`, `tdd-dispatch-verification-discipline.spec.md`; `6` of the `10` pre-existing feature designs have no paired `.spec.md`).
4. **Head-anchored active vs. retired AC counts across the 5 reference specs (`FR-3.1`, `AC-3.1`, `FR-6.1`, `AC-6.1`):**
   - Command: `python3 -c 'import re, pathlib; HEAD_AC = re.compile(r"^\s*(?:-\s+(?:\[[ xX]\]\s+)?|#{1,6}\s+)(?:~~)?(?:\*\*|`)*(AC-(\d+)\.(\d+)([a-z]?))\b"); RETIRED = re.compile(r"^\s*(?:-\s+(?:\[[ xX]\]\s+)?|#{1,6}\s+)(?:~~.*AC-\d+\.\d+[a-z]?.*~~|(?:\*\*|`)*AC-\d+\.\d+[a-z]?(?:\*\*|`)*(?:\s*(?:\([^)]*\)|\[[^\]]*\]))*[:.,\s-]+(?:(?:\(|\[)?(?:retired|superseded|removed|dropped)\b))", re.I); [print(p, len({m.group(1) for line in re.split(r"^##\s+Version History\b", pathlib.Path(p).read_text(), flags=re.M)[0].splitlines() if (m := HEAD_AC.match(line)) and not RETIRED.match(line)})) for p in ["docs/01-plan/features/hmad-test-boundaries.spec.md", "docs/archive/2026-08/exec-path-hardening/exec-path-hardening.spec.md", "docs/archive/2026-09/audit-report-docs-copy/audit-report-docs-copy.spec.md", "docs/archive/2026-09/tdd-gate-fail-opens/tdd-gate-fail-opens.spec.md", "docs/archive/2026-10/grok-audit-surface/grok-audit-surface.spec.md"]]'`
   - Observed output: `17` active ACs in `hmad-test-boundaries.spec.md`, `24` in `exec-path-hardening.spec.md`, `40` in `audit-report-docs-copy.spec.md`, `44` in `tdd-gate-fail-opens.spec.md`, and `63` active ACs (`1` retired: `AC-3.7`) in `grok-audit-surface.spec.md`.

## Architecture Overview

```
+-----------------------------------------------------------------------------------+
| Phase 4 Design Authoring (h-mad/references/inline-protocols.md & design-author.md)|
|   docs/02-design/features/<feature>.design.md                                     |
|   └── ## Test Boundaries (5-column Markdown pipe table)                           |
|       | Public interface | Acceptance criteria | Expected result source |         |
|       | Mocked dependencies | Exclusions |                                        |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| Phase 4 Design Audit Rubric (h-mad/audit-prompt.template.md & doc-auditor.md)     |
|   - {{ONLY:design}} block challenges semantic oracle independence, private-helper |
|     boundaries, internal-collaborator mocking, and verified-by justification      |
|   - Raises Must-fix (class: build) if ## Test Boundaries is missing on a          |
|     non-exempt design, leaves any active spec AC uncovered, or has placeholders   |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| Phase 4 Audit Gate (h-mad/scripts/h_mad_audit_gate.py)                            |
|   1. Collect existing candidate .design.md paths from repeatable --gated <path>   |
|      args (or positional <feature>.design.audit.v<N>[.<leg>].md reports)          |
|   2. Load h_mad_test_boundaries_check.py via importlib.util.spec_from_file_location|
|      inside helper _load_test_boundaries_checker() (no top-level sibling import)  |
|   3. Derive proj_root = checker.infer_project_root(design_path) and call          |
|      checker.should_activate_design_check(design_path, proj_root) (3-arm rule)    |
|   4. For each activated design, run h_mad_test_boundaries_check.py (passing       |
|      --root <proj_root> when non-None) BEFORE `stamped = ""\n    if args.gated...`|
|   5. Flip verdict = "FAIL" (suppressing .gated.json) if any token not in          |
|      {"PASS", "EXEMPT"}, while preserving report must/should counts on GATE: line |
|   6. Print captured TEST-BOUNDARIES: / TEST-BOUNDARIES-ISSUE: lines immediately   |
|      after GATE: -> GATE-CLASS: -> GATE-LEGS:                                     |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| Standalone Deterministic Checker (h-mad/scripts/h_mad_test_boundaries_check.py)   |
|   Single authoritative owner of:                                                  |
|   - Fenced-code-block-aware (` ``` ` / `~~~`) ## Test Boundaries heading & table  |
|   - Project root derivation infer_project_root(design_path, root) (parents[3]     |
|     for <root>/docs/02-design/features/<f>.design.md) & two-branch paired         |
|     .spec.md resolution resolve_spec_path(design_path, spec_path, root)           |
|   - Head-anchored active vs. retired AC-X.Y[a-z] extraction from .spec.md         |
|   - 3-arm activation predicate should_activate_design_check(design_path, root)    |
|   - 4-token stdout contract: PASS / EXEMPT / FAIL (exit 0), UNREADABLE (exit 2)   |
|   - 10-code failure vocabulary & < 200ms per-design execution budget              |
+-----------------------------------------------------------------------------------+
```

### Component Boundary Interactions

- **Template & Shape-Check Boundary (`inline-protocols.md` <-> `test_h_mad_doc_templates.py` <-> `h_mad_doc_shape_check.py`):**
  `h-mad/scripts/h_mad_doc_shape_check.py` remains untouched (`REQUIRED_SECTIONS["design"]` keeps its `7` bkit-mirrored headings). `h-mad/references/inline-protocols.md` gains `## Test Boundaries` immediately after `## Test Plan` and immediately before `## Invariant Compliance` (`13 -> 14` headings), and `PRIOR_HMAD_HEADINGS["design"]` in `h-mad/tests/test_h_mad_doc_templates.py` gains `"Test Boundaries"` (`7 -> 8` headings).
- **Gate & Checker Boundary (`h_mad_audit_gate.py` <-> `h_mad_test_boundaries_check.py`):**
  `h-mad/tests/tree_lock_plugin.py` loads `h-mad/scripts/h_mad_audit_gate.py` via `importlib.util.spec_from_file_location("h_mad_audit_gate", ...)` without `h-mad/scripts` on `sys.path`. To satisfy both `tree_lock_plugin.py` isolation and Axis B single-source ownership (`h-mad/invariants.base.md`), `h_mad_audit_gate.py` keeps its `11` standard-library top-level imports unchanged and loads `h_mad_test_boundaries_check.py` inside a helper function via `importlib.util.spec_from_file_location` from `Path(__file__).with_name("h_mad_test_boundaries_check.py")`, delegating project-root derivation and 3-arm activation to `infer_project_root(design_path)` and `should_activate_design_check(design_path, proj_root)`.

## Detailed Design

### Component 1: Phase 4 Design Template & Authoring Contract (`FR-1`, `AC-1.1`..`AC-1.3`)

#### 1.1 `h-mad/references/inline-protocols.md`
- **Structural locator:** Under `## Phase 4 — Design`, inside numbered step `3. Draft the design:`, within the `markdown` fenced code block (where each `## ` heading is indented by 3 spaces), immediately after the `## Test Plan` block and immediately before `## Invariant Compliance`.
- **Residual:** All other phase sections (`## Phase 1`, `## Phase 2`, `## Phase 3`, `## Phase 5a`, `## Phase 6`, `## Phase 7`) and steps `1`, `2`, `4`, `5`, `6` of `## Phase 4 — Design` remain untouched.
- **Exact Markdown block to insert into the Phase 4 template (increasing Phase 4 template `## ` headings from `13` to `14`):**

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

#### 1.2 `h-mad/tests/test_h_mad_doc_templates.py`
- **Structural locator:** Module-level dictionary `PRIOR_HMAD_HEADINGS`, key `"design"`, immediately after `"Test Strategy"` and before `"Invariant Compliance"`.
- **Residual:** `PRIOR_HMAD_HEADINGS["plan"]`, `PRIOR_HMAD_HEADINGS["report"]`, all test functions in `h-mad/tests/test_h_mad_doc_templates.py`, and `REQUIRED_SECTIONS["design"]` in `h-mad/scripts/h_mad_doc_shape_check.py` (`7` headings) remain untouched.
- **Exact update (`7 -> 8` entries in `PRIOR_HMAD_HEADINGS["design"]`):**

```python
    "design": [
        "Architecture Overview",
        "Components Changed / Added",
        "Data Model / Schema Changes",
        "API / Interface Changes",
        "Error Handling Strategy",
        "Test Strategy",
        "Test Boundaries",
        "Invariant Compliance",
    ],
```

#### 1.3 `h-mad/agents/design-author.md` and Self-Bootstrapping Sequence
- **Structural locator:**
  1. Under `## Rules — each closes a measured failure class`, immediately after Rule `7.` (`h_mad_precheck_doc.py`), add Rule `7a.` requiring the design author to populate `## Test Boundaries` and run `h_mad_test_boundaries_check.py`.
  2. Under `## Output`, in the paragraph following the `DESIGN-AUTHOR: DONE` fenced block, require reporting the `TEST-BOUNDARIES: PASS` verification output alongside the premise verification commands.
- **Residual:** `## Why you exist` and `## Where your report goes` in `h-mad/agents/design-author.md` remain untouched.
- **Exact rule addition under `## Rules — each closes a measured failure class`:**

```markdown
7a. **Populate `## Test Boundaries` for every active spec `AC-X.Y[a-z]` and run the deterministic boundary checker before reporting `DONE`.**
    Every `docs/02-design/features/<feature>.design.md` you author or revise must carry a `## Test Boundaries` section containing the 5-column Markdown pipe table (`| Public interface | Acceptance criteria | Expected result source | Mocked dependencies | Exclusions |`) covering every active `AC-X.Y` (including lettered `AC-X.Y[a-z]`) in `docs/01-plan/features/<feature>.spec.md`. Before emitting `DESIGN-AUTHOR: DONE`, run:
    `python3 <skill_dir>/scripts/h_mad_test_boundaries_check.py docs/02-design/features/<feature>.design.md --spec docs/01-plan/features/<feature>.spec.md`
    (where `<skill_dir>` is the active H-MAD skill directory for the current host, e.g. `h-mad` in this checkout, `~/.claude/skills/h-mad`, `~/.agents/skills/h-mad`, or `~/.gemini/config/skills/h-mad`).
    Read the `TEST-BOUNDARIES:` token, never `$?`. Fix any `TEST-BOUNDARIES: FAIL` (`TEST-BOUNDARIES-ISSUE:`) or `UNREADABLE` output until the checker prints `TEST-BOUNDARIES: PASS`.
```

- **Self-bootstrapping sequence (`FR-1.2`, `AC-1.3`):**
  During `hmad-test-boundaries`'s own Phase 4 (which executes before Phase 6 creates `h-mad/scripts/h_mad_test_boundaries_check.py` or edits `h-mad/agents/design-author.md`), `docs/02-design/features/hmad-test-boundaries.design.md` is authored with a compliant `## Test Boundaries` section covering All 17 ACs (`AC-1.1`..`AC-6.3`). Once Phase 6 implementation creates `h-mad/scripts/h_mad_test_boundaries_check.py` and updates `h-mad/agents/design-author.md`, `h-mad/tests/test_h_mad_test_boundaries_check.py` runs `h_mad_test_boundaries_check.py` against `docs/02-design/features/hmad-test-boundaries.design.md` and asserts `TEST-BOUNDARIES: PASS` with `acs=17/17`.

---

### Component 2: Standalone Test Boundaries Checker (`h-mad/scripts/h_mad_test_boundaries_check.py` — `FR-2`, `FR-3`, `FR-4.1`, `FR-4.2`, `AC-2.1`..`AC-4.3`)

#### 2.1 Module Architecture & Standard-Library Imports
`h-mad/scripts/h_mad_test_boundaries_check.py` is a standalone Python 3 module and CLI script using only standard-library imports (`from __future__ import annotations`, `argparse`, `re`, `sys`, `from pathlib import Path`, `from typing import NamedTuple`). It makes zero network, LLM, or subprocess/git calls and completes in `< 200ms` (`< 0.200` seconds) per design document. When `--root <project_root>` is omitted, `infer_project_root` infers `<design_path>`'s ancestor project root (`abs_design.parents[3]`) when `<design_path>` resides under `docs/02-design/features/` or `docs/archive/`, and falls back to `Path.cwd().resolve()` when a caller needs a default root for a non-canonical path (`FR-2.1`, `AC-2.1`).

#### 2.2 Module-Level Constants & Data Structures

```python
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

# Concrete proving artifact indicators for `verified by:` rows (FR-3.3 / AC-3.2):
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

# Head-anchored spec AC definition & retired-line patterns (FR-3.1 / AC-3.1):
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

# Multi-token AC extraction inside design table column 2 (`Acceptance criteria`):
CELL_AC_RE = re.compile(r"\b(AC-(\d+)\.(\d+)([a-z]?))\b")

# CommonMark fence & ATX heading patterns:
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
```

#### 2.3 Public & Helper Functions

1. **`has_test_boundaries_heading(design_text: str) -> bool`**
   - Iterates `design_text.splitlines()` tracking CommonMark fenced code blocks (` ``` ` or `~~~` with 0–3 leading spaces; a fence closes only on a line with at least as many characters of the same marker and no trailing text).
   - Returns `True` iff a line outside fenced code blocks matches `TEST_BOUNDARIES_HEADING_RE` (`^##\s+Test Boundaries\s*$`).

2. **`infer_project_root(design_path: Path, root: Path | None = None) -> Path | None`**
   - Single shared helper for deriving the target project root from `<design_path>` or `--root`:
   - If `root is not None`: returns `Path(root).resolve()`.
   - Otherwise, let `abs_design = Path(design_path).resolve()`:
     - For a canonical design path `<project_root>/docs/02-design/features/<feature>.design.md`, **`abs_design.parents[3]`** is `<project_root>` (three parent levels above `features/`):
       if `len(abs_design.parts) >= 4` and `abs_design.parts[-4:-1] == ("docs", "02-design", "features")`, returns `abs_design.parents[3]` (the actual project root containing `docs/02-design/features/<feature>.design.md`, even when `h_mad_test_boundaries_check.py` or `h_mad_audit_gate.py` is installed in an external skill directory or invoked from another working directory).
     - If `len(abs_design.parts) >= 4` and `abs_design.parts[-4:-2] == ("docs", "archive")`: returns `abs_design.parents[3]` (and more generally, when `"docs"` and `"archive"` appear as adjacent segments `("docs", "archive")` in `abs_design.parts[:-1]`, returns the ancestor immediately above `"docs"`).
     - Otherwise (a design path outside `docs/02-design/features/` and `docs/archive/`, e.g. a synthetic file in `tmp_path`), returns `None` (and any caller needing a default root for a non-canonical path falls back to `Path.cwd().resolve()`, matching `spec.md` `v1.5` `FR-2.1`).

3. **`resolve_spec_path(design_path: Path, spec_path: Path | None = None, root: Path | None = None) -> Path`**
   - If `spec_path is not None`: returns `Path(spec_path)`.
   - Let `abs_design = Path(design_path).resolve()`, `feature = _feature_stem(abs_design)` (stripping `.design.md` or `.md` from `abs_design.name`), `sib_cand = abs_design.parent / f"{feature}.spec.md"`, and `proj_root = infer_project_root(abs_design, root)`.
   - Determines whether `abs_design` is under `docs/02-design/features/`:
     either (`len(abs_design.parts) >= 4 and abs_design.parts[-4:-1] == ("docs", "02-design", "features")`) or (`root is not None and abs_design.is_relative_to(Path(root).resolve() / "docs" / "02-design" / "features")`).
   - **Two-branch rule matching `spec.md` `FR-2.1` and `FR-4.2` Arm 3:**
     - **Branch 1 (`abs_design` is under `docs/02-design/features/`):** Let `plan_cand = proj_root / "docs" / "01-plan" / "features" / f"{feature}.spec.md"`. Returns `plan_cand` if `plan_cand.exists()` (including when `plan_cand` is a directory or non-UTF-8 file so `check_design` reports `UNREADABLE`), else `sib_cand` if `sib_cand.exists()`, else `plan_cand`.
     - **Branch 2 (`abs_design` is NOT under `docs/02-design/features/`):** Returns `sib_cand` **only** (never falling back to `plan_cand` or `cwd_cand`, which would falsely match a repository's live `docs/01-plan/features/<feature>.spec.md` when testing a bare synthetic `.design.md` in `tmp_path`).

4. **`extract_spec_acs(spec_text: str) -> tuple[set[str], set[str]]`**
   - Scans `spec_text.splitlines()` outside fenced code blocks (` ``` ` / `~~~`), stopping as soon as a heading outside fenced code blocks matches `VERSION_HISTORY_HEADING_RE` (`^##\s+Version History\s*$`).
   - For each line, tests `m = HEAD_AC_RE.match(line)`. If matched, extracts only the single head-defined identifier `ac_id = m.group(1)` (ignoring any mid-line prose mentions of `AC-...` later on the same line).
   - Tests `RETIRED_LINE_RE.match(line)`:
     - If matched (either struck-through `~~...AC-X.Y...~~` or followed after optional parenthesized/bracketed tags and `[:.,\s-]+` — with `-` at the end of the character class — by `(?:retired|superseded|removed|dropped)\b`), adds `ac_id` to `retired_acs` (and removes from `active_acs` if previously seen).
     - Otherwise, if `ac_id not in retired_acs`, adds `ac_id` to `active_acs`.
   - Returns `(active_acs, retired_acs)`.

5. **`should_activate_design_check(design_path: Path, root: Path | None = None) -> bool`**
   - The single authoritative 3-arm activation predicate (`FR-4.2`, `AC-4.2`, `AC-4.3`).
   - If `not Path(design_path).exists()`, returns `False`.
   - If `Path(design_path).is_dir()`, returns `True` (routing the directory candidate to `check_design` / CLI so it emits `TEST-BOUNDARIES: UNREADABLE path=<design_path> err=IsADirectoryError` and exits `2`).
   - Let `abs_design = Path(design_path).resolve()`.
   - **Arm 1 (`is_canonical_design_or_archive` — canonical design or archive directory without defaulting to the skill checkout root):**
     Never defaults `effective_root` to the skill checkout root. Instead, returns `True` if:
     - `len(abs_design.parts) >= 4 and abs_design.parts[-4:-1] == ("docs", "02-design", "features")`, OR
     - adjacent segments `("docs", "archive")` appear in `abs_design.parts[:-1]` (including `abs_design.parts[-4:-2] == ("docs", "archive")`), OR
     - `root is not None` and (`abs_design.is_relative_to(Path(root).resolve() / "docs" / "02-design" / "features")` or `abs_design.is_relative_to(Path(root).resolve() / "docs" / "archive")`).
   - **Arm 2 (`## Test Boundaries` heading present outside fenced code blocks, or unreadable `<design_path>`):**
     Tries reading `abs_design.read_text(encoding="utf-8")`. If reading or decoding `design_path` raises `(OSError, UnicodeDecodeError)` (for example, invalid UTF-8 bytes or permission error on an existing file), returns `True` so `h_mad_audit_gate.py` invokes `h_mad_test_boundaries_check.py`, which emits `TEST-BOUNDARIES: UNREADABLE` (exit `2`) and fails the gate closed (`GATE: FAIL`). If `has_test_boundaries_heading(design_text)` is `True`, returns `True`.
   - **Arm 3 (resolvable paired `<feature>.spec.md` on disk containing `>= 1` active head-anchored `AC-X.Y[a-z]` item under `FR-3.1`, or unreadable existing `<spec_candidate>`):**
     Computes `spec_candidate = resolve_spec_path(abs_design, None, root)`. If `spec_candidate.exists()` is `True`:
     - Tries reading `spec_candidate.read_text(encoding="utf-8")`.
     - If `spec_candidate` is a directory or reading/decoding raises `(OSError, UnicodeDecodeError)`, returns `True` (routing the candidate to `h_mad_test_boundaries_check.py`, which emits `TEST-BOUNDARIES: UNREADABLE path=<spec_candidate> err=<ErrorType>` and exits `2`, causing `h_mad_audit_gate.py` to fail closed with `GATE: FAIL` instead of crashing with an uncaught exception).
     - Otherwise, computes `active_acs, _ = extract_spec_acs(spec_text)` and returns `len(active_acs) >= 1`.
   - Otherwise returns `False`.

6. **`normalize_cell(raw_cell: str) -> str`**
   - Strips leading/trailing whitespace, strips surrounding `` `*_ `` characters repeatedly while outer whitespace is stripped, collapses internal whitespace runs (`\s+`) to a single space, and applies `.casefold()`.

7. **`is_placeholder_cell(norm_cell: str, col_name: str) -> bool`**
   - Assumes `norm_cell != ""` (empty strings are reported as `empty_cell`).
   - In column `"Mocked dependencies"`, if `norm_cell == "none"` or `norm_cell.startswith(MOCKED_NONE_PREFIXES)`, returns `False`.
   - Returns `True` if `norm_cell in PLACEHOLDER_EXACT` or `norm_cell.startswith(PLACEHOLDER_PREFIXES)` (equivalently `bool(PLACEHOLDER_RE.match(norm_cell))`).

8. **`is_tautological_oracle(raw_cell: str) -> bool`**
   - Normalizes `raw_cell` via `normalize_cell(raw_cell)` and strips leading/trailing punctuation (`".,;:!?'\"()[]{}-–—"` and `` `*_ ``).
   - Returns `True` if the resulting string is in `TAUTOLOGICAL_EXACT` or matches `TAUTOLOGICAL_RE`.

9. **`has_proving_artifact(raw_cell: str) -> bool`**
   - Returns `True` iff `raw_cell` matches `PROVING_PATH_RE`, `TOKEN_RE`, or `BACKTICK_SPAN_RE`.

10. **`validate_non_test_row(row_idx: int, pub_cell: str, oracle_cell: str, oracle_had_basic_error: bool) -> list[Issue]`**
    - Strips outer whitespace and surrounding backticks from `pub_cell`.
    - Matches `m = VERIFIED_BY_PREFIX_RE.match(cleaned_pub)`. If not matched, returns `[]` (standard test row).
    - Remainder `rest = m.group(1).strip()`. If `not VERIFIED_BY_KIND_RE.match(rest)`, returns `[Issue(str(row_idx), "Public interface", "invalid_non_test_row", f"unrecognized verified by kind in {pub_cell!r}; expected audit, live-run, operator, or doc-review")]`.
    - If `not oracle_had_basic_error` and `not has_proving_artifact(oracle_cell)`, returns `[Issue(str(row_idx), "Expected result source", "invalid_non_test_row", f"verified by row must name a concrete proving artifact in Expected result source: {oracle_cell!r}")]`.
    - Otherwise returns `[]`.

11. **`check_design(design_path: Path, *, spec_path: Path | None = None, root: Path | None = None, no_exempt: bool = False) -> CheckResult`**
    - Implements the full validation pipeline and returns a `CheckResult`.
    - `format_check_result(result: CheckResult) -> str` formats the primary `TEST-BOUNDARIES:` line and any `TEST-BOUNDARIES-ISSUE:` lines.
    - `main(argv: list[str] | None = None) -> int` parses `<design_path>`, `--spec`, `--root`, `--no-exempt`, invokes `check_design`, prints `format_check_result(result)`, and returns `result.exit_code` (`0` for `PASS`/`EXEMPT`/`FAIL`, `2` for `UNREADABLE`).

---

### Component 3: Phase 4 Design Audit Gate Integration (`h-mad/scripts/h_mad_audit_gate.py` — `FR-4.2`, `AC-4.2`..`AC-4.4`)

#### 3.1 Structural Locators in `h-mad/scripts/h_mad_audit_gate.py`
1. **Helper functions locator:** Insert `_DESIGN_AUDIT_RE`, `_load_test_boundaries_checker()`, `_candidate_design_paths()`, and `_run_design_boundaries_checks()` immediately before `def main(argv: list[str] | None = None) -> int:`.
2. **Pre-stamp evaluation locator inside `main()`:** Immediately after the suite evaluation block (`elif args.project_tests is not None: ... print(suite_line(suite, outcome))`) and **immediately before** the comment `# Declared ABOVE stamped deliberately: audit_suite_gate.json anchors the` and the 3-line block:
   ```python
   legs_line: str | None = None
   stamped = ""
   if args.gated and verdict == "PASS":
   ```
   This preserves the exact two-line mutation anchor `    stamped = ""\n    if args.gated and verdict == "PASS":` required by `h-mad/tests/mutation-specs/audit_suite_gate.json` (`the-red-suite-hostages-the-cycle-verdict`) and `h-mad/tests/mutation-specs/audit_gate_stamp.json` (`a-failing-gate-writes-a-stamp`).
3. **Post-`GATE:` stdout emission locator inside `main()`:** Immediately after `if legs_line is not None:\n        print(f"GATE-LEGS: {legs_line}")` and immediately before `print(f"[H-MAD] {feature} gate {verdict}")`.
4. **Residual:** Top-level imports in `h-mad/scripts/h_mad_audit_gate.py` (`11` stdlib import lines), `classify()`, `classify_detail()`, `exit_check()`, `round_check()`, `verify_stamp()`, and `GATE:` / `GATE-CLASS:` / `GATE-LEGS:` line formatting remain untouched.

#### 3.2 Exact Helper & `main()` Wiring in `h-mad/scripts/h_mad_audit_gate.py`

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
    """Resolve deduplicated candidate .design.md paths in CLI order."""
    out: list[Path] = []
    seen: set[Path] = set()
    for path in gated:
        if path.name.endswith(".design.md"):
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

Inside `main()`:
```python
    tb_ok, tb_lines = _run_design_boundaries_checks(args.audit_file, args.gated)
    if not tb_ok:
        verdict = "FAIL"

    # Declared ABOVE `stamped` deliberately: `audit_suite_gate.json` anchors the
    # red-suite-hostage row on `stamped = ""` immediately followed by the `if`,
    # and splitting that pair drifts a neighbouring feature's mutation spec.
    legs_line: str | None = None
    stamped = ""
    if args.gated and verdict == "PASS":
        ...
```
And after `GATE-LEGS:`:
```python
    if legs_line is not None:
        print(f"GATE-LEGS: {legs_line}")
    for tb_line in tb_lines:
        print(tb_line)
    print(f"[H-MAD] {feature} gate {verdict}")
    return 0
```

---

### Component 4: Phase 4 Design Audit Prompt & Doc-Auditor Instructions (`h-mad/audit-prompt.template.md`, `h-mad/agents/doc-auditor.md` — `FR-5`, `AC-5.1`)

#### 4.1 `h-mad/audit-prompt.template.md`
- **Structural locator:** Under `Axis A — Generic adversarial:`, immediately after the existing inline `- {{ONLY:design}} Cross-doc: does the design implement what the plan promised?` bullet (and its two continuation lines), before `Axis B — Invariant compliance`.
- **Residual:** `{{ONLY:plan,design}}` header slots, `{{ONLY:impl-plan}}` header slot, `Axis B`, `Axis C — Spec reconciliation.`, `Effort contract`, and `Output framing` remain untouched.
- **Exact addition in `h-mad/audit-prompt.template.md` (using the template's block conditional directive `{{ONLY:design}}` ... `{{END-ONLY}}`):**

```markdown
{{ONLY:design}}
- Test Boundaries (`## Test Boundaries` 5-column table): raise a `## Must-fix` (`class: build`) finding whenever:
  1. `## Test Boundaries` is missing **on a non-exempt design**, leaves any active spec `AC-X.Y[a-z]` uncovered, or contains placeholder cells;
  2. Any row's `Expected result source` is semantically tautological (derives expected values from the implementation, helper, or formula under test rather than an independent specification, fixture, protocol rule, or analytical invariant);
  3. Any row tests a private/internal helper instead of the public interface, or mocks the unit under test / an internal collaborator that should be exercised for real; or
  4. Any `verified by:` row (`verified by: audit | live-run | operator | doc-review`) claims non-test verification for behavior that can and should be unit/integration tested, or names a proving artifact that does not actually verify the listed AC.
{{END-ONLY}}
```

#### 4.2 `h-mad/agents/doc-auditor.md`
- **Structural locator:** Under `## Rules — each closes a measured failure class`, immediately after Rule `7b.` (`Classify every finding, on a continuation line.`) and before Rule `8.` (`You never fix anything.`).
- **Residual:** All other sections of `h-mad/agents/doc-auditor.md` (`## Why you exist`, `## What you are given`, `## Output`, `## Standing caveat — you may be gating, and you are told which`) and `h-mad/agents/change-reviewer.md` remain untouched.
- **Exact addition in `h-mad/agents/doc-auditor.md`:**

```markdown
7c. **Phase 4 design audits: challenge `## Test Boundaries` on coverage, oracle independence, boundary placement, and `verified by:` escape hatches.**
    On a Phase 4 design audit, raise a `## Must-fix` (`class: build`) finding whenever:
    - `## Test Boundaries` is missing **on a non-exempt design**, leaves any active spec `AC-X.Y[a-z]` uncovered, or contains placeholder cells;
    - Any row's `Expected result source` is semantically tautological (re-states the implementation's internal logic or helper output rather than an independent spec table, fixture, protocol contract, or analytical invariant);
    - Any row targets a private/internal helper instead of the public interface, or mocks the unit under test / an internal collaborator that should run for real; or
    - Any `verified by:` row (`verified by: audit | live-run | operator | doc-review`) claims non-test verification for behavior that can and should be unit/integration tested, or names a proving artifact that does not verify the listed AC.
```

---

### Component 5: Calibration Corpus, Test Suite, and Mutation Specification (`h-mad/tests/test_h_mad_test_boundaries_check.py`, `h-mad/tests/mutation-specs/test_boundaries_gate.json` — `FR-6`, `AC-6.1`..`AC-6.3`)

#### 5.1 Test Suite Architecture (`h-mad/tests/test_h_mad_test_boundaries_check.py`)
The dedicated test suite `h-mad/tests/test_h_mad_test_boundaries_check.py` is organized into 7 test classes:

1. **`TestDesignAuthorAndSelfBootstrap` (`AC-1.3`):**
   - Verifies `h-mad/agents/design-author.md` requires `## Test Boundaries` for every active `AC-X.Y[a-z]` and contains the exact host-independent self-check command substring `python3 <skill_dir>/scripts/h_mad_test_boundaries_check.py docs/02-design/features/<feature>.design.md --spec docs/01-plan/features/<feature>.spec.md`, requiring `TEST-BOUNDARIES: PASS` before `DESIGN-AUTHOR: DONE`.
   - Runs `h_mad_test_boundaries_check.py` with `--no-exempt` on `docs/02-design/features/hmad-test-boundaries.design.md` paired with `docs/01-plan/features/hmad-test-boundaries.spec.md` and asserts `TEST-BOUNDARIES: PASS` with `acs=17/17` and exit code `0`.
2. **`TestCliAndTableValidation` (`AC-2.1`..`AC-2.4`):**
   - Tests CLI flags (`<design_path>`, `--spec`, `--root`, `--no-exempt`), the 4 primary tokens (`PASS`, `EXEMPT`, `FAIL` exit `0`; `UNREADABLE` exit `2`), and disambiguation of `UNREADABLE` (exit `2` on missing/directory/non-UTF-8 `<design_path>` or explicit `--spec`, or directory/non-UTF-8 default-resolved `<spec_path>`) vs `FAIL` `code=missing_spec` (exit `0` when `--spec` was omitted on a non-exempt design and no default spec exists).
   - Tests invoking `h_mad_test_boundaries_check.py` from a different `cwd` (`tmp_path`) on an absolute `/.../docs/02-design/features/demo.design.md` without `--root` (verifying `infer_project_root` uses `parents[3]` to resolve `/.../docs/01-plan/features/demo.spec.md`), tests distinguishing canonical ancestor inference (without `--root` from another `cwd`) from an explicit `--root` override, and verifies `resolve_spec_path`'s two-branch rule (returning `sib_cand` only when `<design_path>` is not under `docs/02-design/features/`, never falling back to `plan_cand` or `cwd_cand`).
   - Tests `missing_section`, `missing_table` (heading with no pipe table or no data rows), and `invalid_columns` for both (a) wrong column headers or `!= 5` cells and (b) a 5-cell row whose non-empty, non-placeholder `Acceptance criteria` cell contains zero `AC-X.Y[a-z]` tokens when the paired spec has `>= 1` active ACs.
   - Tests fenced code blocks (` ``` ` and `~~~`) containing decoy `## Test Boundaries` headings and pipe tables.
   - Tests `empty_cell` and `placeholder_cell` across all 5 columns, verifying that `"none"` and `"none — ..."` / `"none (...)"` are accepted in `Mocked dependencies` and rejected as `placeholder_cell` in the other 4 columns.
   - Tests `tautological_oracle` across exact tokens (`"implementation"`, `"the code"`, `"computed"`, `"return value"`, `"same function"`, `"sut"`) and phrase regexes (`"computed by the implementation"`, `"calling the same helper"`).
3. **`TestSpecAcCoverageAndNonTestRows` (`AC-3.1`, `AC-3.2`):**
   - Tests `extract_spec_acs` on all 5 reference specs (`hmad-test-boundaries` -> `17` active / `0` retired; `exec-path-hardening` -> `24` active / `0` retired; `audit-report-docs-copy` -> `40` active including `AC-2.6a`, `AC-2.6b`, `AC-3.5a`; `tdd-gate-fail-opens` -> `44` active including `- AC-3.6 (second arm, OQ-P1),`; `grok-audit-surface` -> `63` active / `1` retired `AC-3.7`).
   - Verifies mid-line prose mentions of `AC-X.Y` and mentions inside `## Version History` or fenced blocks are ignored in `.spec.md`, while multi-token cells (`AC-1.1, AC-1.2`) are extracted in `.design.md`.
   - Verifies `uncovered_ac`, `unknown_ac`, and optional inclusion/omission of retired ACs (`~~AC-1.2~~` and `AC-3.7: Retired in v1.10.`).
   - Verifies `verified by: audit | live-run | operator | doc-review` acceptance with file paths, `TOKEN:` prefixes, or backticked commands, and `invalid_non_test_row` rejection on unrecognized kinds or bare prose in `Expected result source`.
4. **`TestExemptionsAndAuditGateIntegration` (`AC-4.1`..`AC-4.4`):**
   - Verifies `TEST-BOUNDARIES: EXEMPT` (`reason=pre_existing_feature` on the `10` `PRE_EXISTING_FEATURES` designs and `reason=archived` on unaugmented `docs/archive/**` designs) and `TEST-BOUNDARIES: FAIL` (`reasons=missing_section`) when `--no-exempt` is passed.
   - **Isolated-loading parity test (`AC-4.2`, `AC-4.3`):** Loads `h_mad_audit_gate.py` in a subprocess/context where `h-mad/scripts` is absent from `sys.path` via `importlib.util.spec_from_file_location`, and asserts exact parity between direct `h_mad_test_boundaries_check.should_activate_design_check` and `h_mad_audit_gate`'s `_load_test_boundaries_checker()[0].should_activate_design_check` across:
     1. fenced `## Test Boundaries` headings (` ``` ` and `~~~` ignored; outside fence activated),
     2. active lettered ACs (`AC-2.6a` activates arm 3) vs retired-only specs (`- AC-1.1: Retired in v1.2.` does not activate arm 3), and
     3. both spec resolution paths (`<root>/docs/01-plan/features/<feature>.spec.md` and co-located `<design_dir>/<feature>.spec.md`).
   - **External project root activation test (`AC-4.2`, `AC-4.3`):** Runs `h_mad_audit_gate.py` against a separate project tree under `tmp_path / "external_project" / "docs" / "02-design" / "features" / "demo.design.md"` (with a missing `## Test Boundaries` section and no paired spec), verifying Arm 1 activates and `GATE: FAIL` + `TEST-BOUNDARIES: FAIL ... reasons=missing_section` is emitted even though `external_project` is outside the skill checkout root.
   - **Unreadable paired spec fail-closed gate test (`AC-2.1`, `AC-4.2`):** Runs `h_mad_audit_gate.py` on an external `.design.md` (with no `## Test Boundaries` heading) paired with a sibling `.spec.md` containing invalid UTF-8 bytes (`b"\xff\xfe"`), asserting `should_activate_design_check` returns `True`, `h_mad_audit_gate.py` does not crash, `GATE: FAIL` is emitted, and `TEST-BOUNDARIES: UNREADABLE` is printed.
   - **Directory-valued design candidate fail-closed gate test (`AC-2.1`, `AC-4.2`):** Runs `h_mad_audit_gate.py` with a positional `<feature>.design.audit.v1.p1.md` report (and no `--gated`) whose co-located canonical `docs/02-design/features/<feature>.design.md` is a **directory** (`mkdir()`), asserting `should_activate_design_check` returns `True`, `h_mad_audit_gate.py` emits `GATE: FAIL` and `TEST-BOUNDARIES: UNREADABLE ... err=IsADirectoryError`, and does not pass silently.
   - **Direction 1 connection-enforcement test (`AC-4.2`, `AC-4.4`, `AC-6.3`):** Runs `h_mad_audit_gate.py` on a clean `must=0 should=0` audit report paired (via repeatable `--gated` and via positional `<feature>.design.audit.v1.md`) with an activated `.design.md` whose `## Test Boundaries` fails; asserts `GATE: FAIL must=0 should=0`, `TEST-BOUNDARIES: FAIL` printed immediately after `GATE:` / `GATE-CLASS:`, and no `.gated.json` file written.
   - **Direction 2 connection-enforcement negative fixture test (`AC-4.3`, `AC-4.4`, `AC-6.3`):** Runs `h_mad_audit_gate.py` on a clean `must=0 should=0` audit report `--gated` to a bare synthetic `.design.md` in `tmp_path` outside `docs/02-design/features/` and `docs/archive/` with no `## Test Boundaries` heading and no paired `.spec.md` with active `AC-X.Y[a-z]`; asserts `GATE: PASS must=0 should=0 gated=1`, `.gated.json` written, and `"TEST-BOUNDARIES:" not in proc.stdout`.
5. **`TestAuditPromptAndDocAuditorContract` (`AC-5.1`):**
   - Verifies `h-mad/audit-prompt.template.md` (`{{ONLY:design}}` block) and `h-mad/agents/doc-auditor.md` (`## Rules — each closes a measured failure class`) both require `Must-fix` (`build` class) when `## Test Boundaries` is missing **on a non-exempt design** or leaves any active spec `AC-X.Y[a-z]` uncovered, and challenge semantic oracle independence, public-interface boundary placement, internal-collaborator mocking, and `verified by:` justification.
   - Verifies `h_mad_assemble_audit.resolve` includes the `## Test Boundaries` rubric for `design` and strips it for `plan` and `impl-plan` with zero `unresolved_conditional` leaks.
6. **`TestArchivedCalibrationAndPerformance` (`AC-6.1`):**
   - Copies the 3 archived design+spec pairs (`exec-path-hardening` with `24` active ACs, `audit-report-docs-copy` with `40` active ACs, `tdd-gate-fail-opens` with `44` active ACs) into `tmp_path`, appends realistic `## Test Boundaries` tables covering all active ACs (including `verified by:` and `Mocked dependencies = none` rows), runs `check_design(..., no_exempt=True)` and CLI `--no-exempt`, asserts `TEST-BOUNDARIES: PASS` with `acs=24/24`, `acs=40/40`, and `acs=44/44`, measures wall-clock runtime via `time.monotonic()` asserting `< 0.200` seconds (`< 200ms`) per design, and asserts `git status --porcelain docs/archive/` is empty.
7. **`TestSeededBrokenFixtures` (`AC-6.2`):**
   - Starting from a passing calibrated design+spec pair in `tmp_path`, constructs the 5 seeded broken fixture classes (`missing_section` / `missing_table`, `placeholder_cell`, `uncovered_ac`, `tautological_oracle`, `invalid_non_test_row`) and asserts `TEST-BOUNDARIES: FAIL` with the exact expected `code=<reason_code>`.

#### 5.2 Mutation Specification (`h-mad/tests/mutation-specs/test_boundaries_gate.json` — `FR-6.3`, `AC-6.3`)
`h-mad/tests/mutation-specs/test_boundaries_gate.json` conforms to `h_mad_mutation_harness.py:_load_spec` (`"root": "../.."`, `"command"`, `"target_command"`, `"mutations"` with `"symbol"` pins on every mutation):

```json
{
  "_why": "hmad-test-boundaries: Phase 4 design test-boundaries checker and two-direction audit-gate connection enforcement.",
  "root": "../..",
  "command": [
    "python3.11",
    "-m",
    "pytest",
    "tests/test_h_mad_test_boundaries_check.py",
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

## Components Changed / Added

| Component | File path | Change type | Purpose |
|---|---|---|---|
| Phase 4 Design template | `h-mad/references/inline-protocols.md` | modify | Add `## Test Boundaries` section (`13 -> 14` headings) with the 5-column table and column contract comments (`FR-1.1`, `AC-1.1`). |
| Design-author agent instructions | `h-mad/agents/design-author.md` | modify | Add Rule `7a` and output requirement to populate `## Test Boundaries` and run `python3 <skill_dir>/scripts/h_mad_test_boundaries_check.py` before `DESIGN-AUTHOR: DONE` (`FR-1.2`, `AC-1.3`). |
| Template superset test | `h-mad/tests/test_h_mad_doc_templates.py` | modify | Add `"Test Boundaries"` to `PRIOR_HMAD_HEADINGS["design"]` (`7 -> 8` headings) while keeping `h_mad_doc_shape_check.py` untouched (`FR-1.3`, `AC-1.1`, `AC-1.2`). |
| Standalone test-boundaries checker | `h-mad/scripts/h_mad_test_boundaries_check.py` | new | Implement deterministic 5-column table validation, placeholder/tautology rejection, project-root inference (`infer_project_root`), two-branch spec resolution (`resolve_spec_path`), head-anchored active spec AC coverage, exemptions, and `should_activate_design_check` (`FR-2`, `FR-3`, `FR-4`, `AC-2.1`..`AC-4.3`). |
| Phase 4 audit gate | `h-mad/scripts/h_mad_audit_gate.py` | modify | Load `h_mad_test_boundaries_check.py` via `importlib.util.spec_from_file_location`, propagate `infer_project_root`, evaluate existing activated `.design.md` candidates before `.gated.json` stamping, and emit `TEST-BOUNDARIES:` lines after `GATE:` / `GATE-CLASS:` / `GATE-LEGS:` (`FR-4.2`, `AC-4.2`..`AC-4.4`). |
| Audit prompt template | `h-mad/audit-prompt.template.md` | modify | Add `{{ONLY:design}}` `## Test Boundaries` audit rubric under `Axis A — Generic adversarial:` (`FR-5.1`, `AC-5.1`). |
| Doc-auditor agent instructions | `h-mad/agents/doc-auditor.md` | modify | Add Rule `7c` challenging `## Test Boundaries` on non-exempt missing sections, AC coverage, semantic oracle tautologies, boundary placement, and `verified by:` rows (`FR-5.2`, `AC-5.1`). |
| Test boundaries test suite | `h-mad/tests/test_h_mad_test_boundaries_check.py` | new | Unit, CLI, repeatable `--gated` integration, external project/cwd, unreadable-spec and directory-candidate fail-closed, isolated-loading parity, two-direction connection enforcement, self-test (`acs=17/17`), 3-design calibration (`< 200ms`), and 5-broken-fixture suite (`FR-1`..`FR-6`, `AC-1.3`..`AC-6.3`). |
| Mutation specification | `h-mad/tests/mutation-specs/test_boundaries_gate.json` | new | Declare checker guard mutations and both connection-enforcement mutation directions on `h_mad_audit_gate.py` for `h_mad_mutation_harness.py` (`FR-6.3`, `AC-6.3`). |

## Implementation Order

1. **Step 1 — Standalone Checker & Authoritative Activation Helper (`h-mad/scripts/h_mad_test_boundaries_check.py` + unit tests in `h-mad/tests/test_h_mad_test_boundaries_check.py`):**
   Write failing RED unit tests for `h_mad_test_boundaries_check.py` (`AC-2.1`..`AC-2.4`, `AC-3.1`..`AC-3.2`, `AC-4.1`), then implement `h-mad/scripts/h_mad_test_boundaries_check.py` (including `infer_project_root`, `resolve_spec_path`, `should_activate_design_check`, `extract_spec_acs`, `check_design`, and `main`) to reach GREEN.
2. **Step 2 — Phase 4 Design Template & Authoring Contract (`h-mad/references/inline-protocols.md`, `h-mad/tests/test_h_mad_doc_templates.py`, `h-mad/agents/design-author.md`):**
   Update `PRIOR_HMAD_HEADINGS["design"]` in `h-mad/tests/test_h_mad_doc_templates.py` (`7 -> 8` entries) and add the `design-author.md` / self-bootstrap test in `h-mad/tests/test_h_mad_test_boundaries_check.py` (`AC-1.1`..`AC-1.3`), then update `h-mad/references/inline-protocols.md` (`13 -> 14` Phase 4 headings) and `h-mad/agents/design-author.md` to reach GREEN while keeping `h-mad/scripts/h_mad_doc_shape_check.py` untouched.
3. **Step 3 — Phase 4 Audit Gate Wiring (`h-mad/scripts/h_mad_audit_gate.py` + integration/parity/connection tests in `h-mad/tests/test_h_mad_test_boundaries_check.py`):**
   Write failing RED tests in `h-mad/tests/test_h_mad_test_boundaries_check.py` for repeatable `--gated` and positional `<report>` candidate resolution, external project root activation, unreadable paired spec and directory-valued design candidate fail-closed handling, isolated `spec_from_file_location` activation parity (`AC-4.2`, `AC-4.3`), Direction 1 connection removal/bypass, and Direction 2 forced unconditional activation (`AC-4.4`), then wire `_load_test_boundaries_checker`, `_candidate_design_paths`, and `_run_design_boundaries_checks` into `h-mad/scripts/h_mad_audit_gate.py` to reach GREEN.
4. **Step 4 — Phase 4 Audit Prompt & Doc-Auditor Rubric (`h-mad/audit-prompt.template.md`, `h-mad/agents/doc-auditor.md`):**
   Write failing RED tests in `h-mad/tests/test_h_mad_test_boundaries_check.py` (`AC-5.1`), then add the `{{ONLY:design}}` block in `h-mad/audit-prompt.template.md` and Rule `7c` in `h-mad/agents/doc-auditor.md` and verify `h-mad/tests/test_h_mad_audit_spec_axis.py` stays GREEN.
5. **Step 5 — Archived Calibration (`< 200ms`), Seeded Broken Fixtures, and Mutation Spec (`h-mad/tests/test_h_mad_test_boundaries_check.py`, `h-mad/tests/mutation-specs/test_boundaries_gate.json`):**
   Add the 3 archived calibration tests (`exec-path-hardening` `acs=24/24`, `audit-report-docs-copy` `acs=40/40`, `tdd-gate-fail-opens` `acs=44/44` with `time.monotonic() < 0.200`s assertions) and the 5 seeded broken fixture tests (`AC-6.1`, `AC-6.2`), create `h-mad/tests/mutation-specs/test_boundaries_gate.json`, and verify `h_mad_mutation_harness.py --check-anchors` (`ANCHORS: ANCHORS_OK`) and full mutation execution (`MUTATION: ALL_CAUGHT`, `AC-6.3`).

## Data Model / Schema Changes

1. **Phase 4 `## Test Boundaries` 5-Column Markdown Table Schema:**
   - Exact ordered column headers (matched case-insensitively after stripping outer whitespace):
     `| Public interface | Acceptance criteria | Expected result source | Mocked dependencies | Exclusions |`
   - Column semantics:
     - `Public interface` (column 1): Public function/method/class/CLI entrypoint under test, or `verified by: audit | live-run | operator | doc-review` for non-test rows.
     - `Acceptance criteria` (column 2): One or more `AC-X.Y[a-z]` identifiers from the paired `.spec.md` (extracted via `\bAC-(\d+)\.(\d+)([a-z]?)\b`).
     - `Expected result source` (column 3): Independent oracle (spec table, protocol fixture, golden corpus, analytical formula, or concrete proving artifact path / `TOKEN:` / backticked command for `verified by:` rows).
     - `Mocked dependencies` (column 4): External system boundaries mocked in the test, or `none` (and `none ...` explanations).
     - `Exclusions` (column 5): Behavior intentionally excluded from this boundary row (or covered by a sibling row).
2. **`CheckResult` and `Issue` NamedTuples (`h-mad/scripts/h_mad_test_boundaries_check.py`):**
   - `Issue(row: str, col: str, code: str, detail: str)`
   - `CheckResult(status: str, exit_code: int, path: str, rows: int, acs_covered: int, acs_total: int, exempt_reason: str, error_type: str, issues: tuple[Issue, ...])`
3. **Mutation Spec Schema (`h-mad/tests/mutation-specs/test_boundaries_gate.json`):**
   - Top-level keys required by `h_mad_mutation_harness.py:_load_spec`: `"root": "../.."`, `"command"`, `"target_command"`, and `"mutations"`, with each mutation object carrying `"name"`, `"_mechanism"`, `"file"`, `"symbol"`, `"find"`, `"replace"`, and `"test"`.
4. **`.gated.json` Sidecar Schema (`h-mad/scripts/h_mad_audit_gate.py`):**
   - Unchanged (`{"verdict": "PASS", "files": {...}, "suite": ..., "legs": ...}`). A `TEST-BOUNDARIES: FAIL` or `UNREADABLE` result flips `verdict` to `"FAIL"` before the stamp block, preventing `.gated.json` creation.

## API / Interface Changes

### 1. CLI Interface: `h-mad/scripts/h_mad_test_boundaries_check.py`

```bash
python3 h-mad/scripts/h_mad_test_boundaries_check.py <design_path> [--spec <spec_path>] [--root <project_root>] [--no-exempt]
```

| Argument / Flag | Type | Default | Description |
|---|---|---|---|
| `design_path` | `Path` (positional) | required | Path to the `.design.md` document to validate. |
| `--spec <spec_path>` | `Path | None` | `None` | Explicit path to the paired `.spec.md` file. When omitted, resolved via `resolve_spec_path`. |
| `--root <project_root>` | `Path | None` | `None` | Repository root directory; when omitted, `infer_project_root` infers `<design_path>`'s ancestor project root (`parents[3]`) for canonical `docs/02-design/features/` or `docs/archive/` paths (falling back to `Path.cwd().resolve()` if a caller needs a default root for a non-canonical path). |
| `--no-exempt` | `bool` (`store_true`) | `False` | Disables archive and `PRE_EXISTING_FEATURES` exemptions when `## Test Boundaries` is absent. |

### 2. Python Module API: `h-mad/scripts/h_mad_test_boundaries_check.py`

```python
def infer_project_root(design_path: Path, root: Path | None = None) -> Path | None: ...
def resolve_spec_path(design_path: Path, spec_path: Path | None = None, root: Path | None = None) -> Path: ...
def should_activate_design_check(design_path: Path, root: Path | None = None) -> bool: ...
def extract_spec_acs(spec_text: str) -> tuple[set[str], set[str]]: ...
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

### 3. Stdout Output Grammar (`h-mad/scripts/h_mad_test_boundaries_check.py` and `h-mad/scripts/h_mad_audit_gate.py`)

- `TEST-BOUNDARIES: PASS path=<design_path> rows=<N> acs=<M>/<M>` (exit `0`)
- `TEST-BOUNDARIES: EXEMPT path=<design_path> reason=<archived|pre_existing_feature>` (exit `0`)
- `TEST-BOUNDARIES: FAIL path=<design_path> issues=<K> reasons=<comma-separated-sorted-unique-reason-codes>` (exit `0`), followed by `K` lines:
  `TEST-BOUNDARIES-ISSUE: row=<R|header|-> col=<column_name|-> code=<reason_code> detail=<message>`
- `TEST-BOUNDARIES: UNREADABLE path=<target_path> err=<ErrorType>` (exit `2`)

## Error Handling Strategy

1. **Audit-Gate Signal Discipline ("Read the token, never `$?`"):**
   - Every normal evaluation verdict (`PASS`, `EXEMPT`, `FAIL` — including `code=missing_spec` when `--spec` was not supplied and neither default spec candidate exists on disk) prints its `TEST-BOUNDARIES:` primary token to stdout and exits `0`.
   - Exit code `2` (`TEST-BOUNDARIES: UNREADABLE path=<target_path> err=<ErrorType>`) is reserved strictly for operational input errors:
     1. `<design_path>` does not exist (`FileNotFoundError`), is a directory (`IsADirectoryError`), cannot be read (`OSError`), or cannot be decoded as UTF-8 (`UnicodeDecodeError`).
     2. An **explicitly passed** `--spec <spec_path>` does not exist, is a directory, cannot be read, or cannot be decoded as UTF-8.
     3. A **default-resolved** `<spec_path>` (when `--spec` was omitted on a non-exempt design) **exists on disk** as a directory (`IsADirectoryError`) or cannot be decoded as UTF-8 (`UnicodeDecodeError`).
2. **Closed 10-Code Failure Vocabulary (`TEST-BOUNDARIES: FAIL`, exit `0`):**
   - `missing_section`, `missing_table`, `invalid_columns`, `empty_cell`, `placeholder_cell`, `tautological_oracle`, `invalid_non_test_row`, `missing_spec`, `uncovered_ac`, `unknown_ac`.
   - Deterministic ordering: `reasons=` lists sorted unique `code` values (`",".join(sorted({i.code for i in issues}))`), and `TEST-BOUNDARIES-ISSUE:` lines are emitted in deterministic traversal order (`missing_section` / `missing_table` / header `invalid_columns`, then `missing_spec`, then row `1..N` issues in column order `1..5` plus row-level `invalid_columns` / `unknown_ac` / `tautological_oracle` / `invalid_non_test_row`, then `uncovered_ac` sorted by `(int(X), int(Y), letter)`).
3. **Fail-Closed Propagation in `h_mad_audit_gate.py`:**
   - Any activated candidate `.design.md` whose `h_mad_test_boundaries_check.py` subprocess returns non-zero or a primary line not starting with `TEST-BOUNDARIES: PASS ` or `TEST-BOUNDARIES: EXEMPT ` forces `verdict = "FAIL"` before the `.gated.json` stamp block while keeping `h_mad_audit_gate.py`'s own exit code `0` and preserving the audit report's `must=` and `should=` counts on the `GATE:` line.

## Test Strategy

- **Unit & CLI Boundary (`h-mad/tests/test_h_mad_test_boundaries_check.py`):**
  Exercise `check_design`, `extract_spec_acs`, `infer_project_root`, `resolve_spec_path`, `should_activate_design_check`, and the `h_mad_test_boundaries_check.py` CLI directly against temporary design/spec fixtures in `tmp_path` and real read-only repository specs (`hmad-test-boundaries`, `exec-path-hardening`, `audit-report-docs-copy`, `tdd-gate-fail-opens`, `grok-audit-surface`). Mock zero internal parser/validator functions; use `tmp_path` only for isolated filesystem fixtures.
- **Gate Integration, Isolated-Loading Parity, and Two-Direction Connection Enforcement (`h-mad/tests/test_h_mad_test_boundaries_check.py`):**
  Exercise `h-mad/scripts/h_mad_audit_gate.py` both via `subprocess.run` and via isolated `importlib.util.spec_from_file_location` loading with `h-mad/scripts` removed from `sys.path`. Test both connection directions (Direction 1: failing activated design flips a clean audit report from `GATE: PASS` to `GATE: FAIL` and suppresses `.gated.json`; Direction 2: bare synthetic `.design.md` in `tmp_path` without `## Test Boundaries` or active spec ACs does not activate and emits `GATE: PASS` with no `TEST-BOUNDARIES:` line), plus external project tree activation, unreadable paired `.spec.md` fail-closed handling, and directory-valued `.design.md` candidate fail-closed handling.
- **Template & Audit-Prompt Contract Tests (`h-mad/tests/test_h_mad_doc_templates.py`, `h-mad/tests/test_h_mad_doc_shape_check.py`, `h-mad/tests/test_h_mad_audit_spec_axis.py`, `h-mad/tests/test_h_mad_test_boundaries_check.py`):**
  Verify template superset headings (`14` in `inline-protocols.md`, `8` in `PRIOR_HMAD_HEADINGS["design"]`, `7` untouched in `h_mad_doc_shape_check.REQUIRED_SECTIONS["design"]`) and `{{ONLY:design}}` conditional resolution via `h_mad_assemble_audit.py`.
- **Archived Calibration (`< 200ms`) & Mutation Harness Verification (`h-mad/tests/mutation-specs/test_boundaries_gate.json`):**
  Calibrate against 3 real archived design+spec pairs copied to `tmp_path` (`acs=24/24`, `acs=40/40`, `acs=44/44`), assert `< 0.200`s (`< 200ms`) wall-clock execution per design via `time.monotonic()`, reject all 5 seeded broken fixture classes, and run `h-mad/scripts/h_mad_mutation_harness.py` to confirm `ANCHORS: ANCHORS_OK` and `MUTATION: ALL_CAUGHT`.

## Test Plan

1. **Template & Doc-Shape Verification (`AC-1.1`, `AC-1.2`):**
   - Command: `python3.11 -m pytest h-mad/tests/test_h_mad_doc_templates.py h-mad/tests/test_h_mad_doc_shape_check.py -q`
   - Expected: `0` failures; `PRIOR_HMAD_HEADINGS["design"]` contains `"Test Boundaries"` (`8` entries) and `REQUIRED_SECTIONS["design"]` in `h_mad_doc_shape_check.py` retains `7` entries.
2. **Standalone Checker, Gate Integration, Parity, Self-Test, Calibration (`< 200ms`), and Broken Fixtures (`AC-1.3`, `AC-2.1`..`AC-6.2`):**
   - Command: `python3.11 -m pytest h-mad/tests/test_h_mad_test_boundaries_check.py h-mad/tests/test_h_mad_audit_spec_axis.py -q`
   - Expected: `0` failures; `hmad-test-boundaries.design.md` self-test passes with `TEST-BOUNDARIES: PASS` (`acs=17/17`); 3 archived calibration pairs pass with `acs=24/24`, `acs=40/40`, `acs=44/44` in `< 200ms` each; 5 broken fixtures fail with exact reason codes; `git status --porcelain docs/archive/` is empty.
3. **Existing Audit Gate & Cycle Regression Suites (`AC-4.4`):**
   - Command: `python3.11 -m pytest h-mad/tests/test_h_mad_audit_gate.py h-mad/tests/test_h_mad_audit_leg_set_gate.py h-mad/tests/test_h_mad_audit_cycle.py -q`
   - Expected: `0` failures.
4. **Mutation Anchor & Kill Verification (`AC-4.4`, `AC-6.3`):**
   - Command:
     ```bash
     python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors \
       h-mad/tests/mutation-specs/test_boundaries_gate.json \
       h-mad/tests/mutation-specs/audit_suite_gate.json \
       h-mad/tests/mutation-specs/audit_gate_stamp.json
     python3 h-mad/scripts/h_mad_mutation_harness.py \
       h-mad/tests/mutation-specs/test_boundaries_gate.json
     ```
   - Expected: `ANCHORS: ANCHORS_OK` and `MUTATION: ALL_CAUGHT` (`survived=0 refused=0`).

## Test Boundaries

| Public interface | Acceptance criteria | Expected result source | Mocked dependencies | Exclusions |
|---|---|---|---|---|
| `h-mad/references/inline-protocols.md` (Phase 4 — Design template) & `h-mad/scripts/h_mad_doc_shape_check.py::check_document` | `AC-1.1, AC-1.2` | Independent specification & bkit superset contract in `docs/01-plan/features/hmad-test-boundaries.spec.md` (`FR-1.1`, `AC-1.1`, `AC-1.2`: `14` ordered `## ` headings in the Phase 4 template and the `7` required bkit design headings) (verified by: `h-mad/tests/test_h_mad_doc_templates.py`, `h-mad/tests/test_h_mad_doc_shape_check.py`) | `none` | Runtime semantic validation of table cells and AC coverage (covered by `check_design` rows below). |
| `h-mad/agents/design-author.md` and `h_mad_test_boundaries_check.py::check_design` on `docs/02-design/features/hmad-test-boundaries.design.md` | `AC-1.3` | `FR-1.2` contract in `docs/01-plan/features/hmad-test-boundaries.spec.md` and the `17` head-anchored active ACs (`AC-1.1`..`AC-6.3`) yielding `TEST-BOUNDARIES: PASS` with `acs=17/17` (verified by: `h-mad/tests/test_h_mad_test_boundaries_check.py`) | `none` | Phase 4 audit gate CLI orchestration (covered by `h_mad_audit_gate.py::main` row). |
| `h-mad/scripts/h_mad_test_boundaries_check.py::main` and `check_design` | `AC-2.1, AC-2.2, AC-2.3, AC-2.4` | Closed 4-token stdout table (`PASS`, `EXEMPT`, `FAIL` exit `0`; `UNREADABLE` exit `2`), 10-code failure vocabulary, `PLACEHOLDER_EXACT` / `PLACEHOLDER_PREFIXES`, and `TAUTOLOGICAL_EXACT` / `TAUTOLOGICAL_RE` in `docs/01-plan/features/hmad-test-boundaries.spec.md` `FR-2.1`..`FR-2.5` (verified by: `h-mad/tests/test_h_mad_test_boundaries_check.py`) | Temporary `.design.md` and `.spec.md` files in pytest `tmp_path` to isolate filesystem inputs | Semantic domain tautologies not matching the closed lexical set (covered by `doc-auditor` prompt in `AC-5.1`). |
| `h-mad/scripts/h_mad_test_boundaries_check.py::extract_spec_acs` and `validate_non_test_row` | `AC-3.1, AC-3.2` | Reference spec census counts (`17`, `24`, `40`, `44`, `63` active ACs and `AC-3.7` retired in `grok-audit-surface.spec.md`) and closed 4-kind `verified by:` / proving-artifact rules in `docs/01-plan/features/hmad-test-boundaries.spec.md` `FR-3.1`..`FR-3.3` (verified by: `h-mad/tests/test_h_mad_test_boundaries_check.py`) | Temporary `.design.md` and `.spec.md` files in pytest `tmp_path` for synthetic retired/unknown AC and `verified by:` cases | Exemption and audit-gate CLI wiring (covered by `FR-4` rows below). |
| `h-mad/scripts/h_mad_test_boundaries_check.py::should_activate_design_check` and `h-mad/scripts/h_mad_audit_gate.py::main` | `AC-4.1, AC-4.2, AC-4.3, AC-4.4` | `PRE_EXISTING_FEATURES` (`10` stems), `29` archived designs, 3-arm activation parity across isolated `importlib.util.spec_from_file_location` loading, pre-stamp `verdict` flipping, and post-`GATE:` stdout emission order in `docs/01-plan/features/hmad-test-boundaries.spec.md` `FR-4.1`..`FR-4.2` (verified by: `h-mad/tests/test_h_mad_test_boundaries_check.py`) | Temporary audit reports and `.design.md` / `.spec.md` fixtures in pytest `tmp_path` for gate subprocess runs | LLM auditor evaluation of prose quality (covered by `AC-5.1`). |
| `h-mad/audit-prompt.template.md`, `h-mad/agents/doc-auditor.md`, and `h-mad/scripts/h_mad_assemble_audit.py::resolve` | `AC-5.1` | `FR-5.1` and `FR-5.2` rubric requirements in `docs/01-plan/features/hmad-test-boundaries.spec.md` (non-exempt missing section, uncovered AC, semantic oracle tautology, boundary placement, `verified by:` justification) and `test_h_mad_audit_spec_axis.py` (verified by: `h-mad/tests/test_h_mad_test_boundaries_check.py`) | `none` | Live LLM dispatch execution during pytest runs. |
| `h-mad/tests/test_h_mad_test_boundaries_check.py` (calibration + broken fixtures) and `h-mad/scripts/h_mad_mutation_harness.py` on `h-mad/tests/mutation-specs/test_boundaries_gate.json` | `AC-6.1, AC-6.2, AC-6.3` | `FR-6.1`..`FR-6.3` in `docs/01-plan/features/hmad-test-boundaries.spec.md`: `PASS` with `acs=24/24`, `acs=40/40`, `acs=44/44` in `< 0.200`s (`time.monotonic()`), `FAIL` with exact codes on 5 broken fixture classes, and `ANCHORS: ANCHORS_OK` / `MUTATION: ALL_CAUGHT` (`survived=0 refused=0`) (verified by: `h-mad/tests/test_h_mad_test_boundaries_check.py`) | Copies of the 3 archived `.design.md` + `.spec.md` pairs in pytest `tmp_path` so `docs/archive/` remains untouched | Unrelated mutation specs outside `test_boundaries_gate.json`, `audit_suite_gate.json`, and `audit_gate_stamp.json`. |

## Invariant Compliance

- **Audit-gate signal discipline (`h-mad/invariants.base.md`):** Complies because `h-mad/scripts/h_mad_test_boundaries_check.py` communicates all normal verdicts (`TEST-BOUNDARIES: PASS`, `TEST-BOUNDARIES: EXEMPT`, `TEST-BOUNDARIES: FAIL`, including `code=missing_spec`) via explicit stdout tokens with exit code `0`, reserving exit code `2` (`TEST-BOUNDARIES: UNREADABLE`) for unreadable or missing input files, and `h-mad/scripts/h_mad_audit_gate.py` continues to emit `GATE: PASS` / `GATE: FAIL` with exit code `0`.
- **Single-source contract (`h-mad/invariants.base.md`):** Complies because `h-mad/scripts/h_mad_test_boundaries_check.py` is the single authoritative owner of fenced `## Test Boundaries` heading detection, project-root inference (`infer_project_root`), two-branch paired `.spec.md` resolution (`resolve_spec_path`), head-anchored active/retired `AC-X.Y[a-z]` extraction, and `should_activate_design_check(design_path, root)`. `h-mad/scripts/h_mad_audit_gate.py` loads `h_mad_test_boundaries_check.py` via `importlib.util.spec_from_file_location` and delegates project-root inference and activation to `infer_project_root` and `should_activate_design_check`, backed by an isolated-loading parity test in `h-mad/tests/test_h_mad_test_boundaries_check.py`.
- **Standalone / no plugin dependency & No new external dependency (`h-mad/invariants.base.md`):** Complies because `h-mad/scripts/h_mad_test_boundaries_check.py` uses only Python 3 standard-library modules (`argparse`, `pathlib`, `re`, `sys`, `typing`) and zero external packages or plugins.
- **Doc-template superset compliance (`h-mad/invariants.base.md`):** Complies because `REQUIRED_SECTIONS["design"]` in `h-mad/scripts/h_mad_doc_shape_check.py` remains untouched (`7` headings matching bkit's validator), while the Phase 4 design template in `h-mad/references/inline-protocols.md` (`14` headings) and `PRIOR_HMAD_HEADINGS["design"]` in `h-mad/tests/test_h_mad_doc_templates.py` (`8` headings) remain a strict superset.
- **Operator-override preservation & Backward compatibility (`h-mad/invariants.base.md`):** Complies because `## Acknowledged-not-fixed` handling in `h-mad/scripts/h_mad_audit_gate.py` is untouched, the `10` pre-existing feature stems in `PRE_EXISTING_FEATURES` and `29` archived designs in `docs/archive/**` emit `TEST-BOUNDARIES: EXEMPT`, and bare synthetic `.design.md` test fixtures in `tmp_path` without `## Test Boundaries` or active spec ACs do not activate the check.
- **Connection enforcement & Mutation verification (`h-mad/invariants.base.md`):** Complies because `h-mad/tests/mutation-specs/test_boundaries_gate.json` declares and kills mutations in both connection directions on `h-mad/scripts/h_mad_audit_gate.py` (Direction 1: connection removal/bypass on an activated failing design; Direction 2: forced unconditional activation on a bare synthetic `.design.md` in `tmp_path`) as well as guard mutations on `h-mad/scripts/h_mad_test_boundaries_check.py`.
- **Skill self-containment & Skill manifest integrity (`.h-mad/invariants.md`):** Complies because all scripts and tests resolve sibling scripts relative to `h-mad/` (`Path(__file__).with_name(...)`) and derive target project roots via `infer_project_root(design_path, root)` with zero cross-skill imports, and `h-mad/SKILL.md` frontmatter (`name` and `description`) is unchanged.

## Version History

- v1.0: 2026-10-28 — Initial Phase 4 technical design for `hmad-test-boundaries` covering all 6 FRs (`FR-1`..`FR-6`) and All 17 ACs (`AC-1.1`..`AC-6.3`), including the Phase 4 template and `design-author.md` updates, standalone `h_mad_test_boundaries_check.py` architecture, `h_mad_audit_gate.py` `spec_from_file_location` integration, Phase 4 auditor prompt updates, 3-design calibration (`< 200ms`), 5 broken fixture classes, two-direction connection mutation spec, and self-validating `## Test Boundaries` table.
- v1.1: 2026-10-28 — Address Phase 4 Design Audit Cycle 1 findings (v1.p1 & v1.p2): add infer_project_root(design_path, root) using parents[3] for canonical design/archive paths and propagate --root from h_mad_audit_gate.py; enforce the two-branch resolve_spec_path contract (sib_cand only outside docs/02-design/features/); route unreadable design/spec candidates in should_activate_design_check to the checker so the gate fails closed; use the host-independent <skill_dir> command in design-author.md (AC-1.3); update Row 1 of ## Test Boundaries to name public contract surfaces and the independent spec/bkit superset contract; and update the Overview spec version citation to v1.4.
- v1.2: 2026-10-28 — Address Phase 4 Design Audit Cycle 2 findings (v2.p1): replace .is_file() candidate filtering in should_activate_design_check and h_mad_audit_gate.py (_candidate_design_paths and _run_design_boundaries_checks) with .exists() + .is_dir() routing so directory-valued design candidates emit TEST-BOUNDARIES: UNREADABLE (exit 2) and fail the gate closed (AC-4.2); make default --root project-root inference vs Path.cwd().resolve() fallback explicit across Section 2.1, infer_project_root, API table, and TestCliAndTableValidation matching spec.md v1.5 (AC-2.1); and update the Overview spec version citation to v1.5.
