#!/usr/bin/env python3
"""Standalone deterministic validator for the Phase 4 design Test Boundaries section."""
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
    "missing_section", "missing_table", "invalid_columns", "empty_cell",
    "placeholder_cell", "tautological_oracle", "invalid_non_test_row",
    "missing_spec", "uncovered_ac", "unknown_ac",
})

PLACEHOLDER_EXACT: frozenset[str] = frozenset({
    "-", "--", "---", "—", "–", "?", "???", "...", "…",
    "tbd", "todo", "fixme", "xxx", "n/a", "na", "none",
    "null", "nil", "placeholder", "pending", "later",
    "tba", "wip", "same", "ditto", "see above", "see below",
})
PLACEHOLDER_PREFIXES: tuple[str, ...] = (
    "tbd ", "todo ", "fixme ", "placeholder ",
)
PLACEHOLDER_RE = re.compile(r"^(?:tbd|todo|fixme|placeholder)\s+", re.IGNORECASE)
MOCKED_NONE_PREFIXES: tuple[str, ...] = (
    "none ", "none —", "none –", "none -", "none (", "none;", "none:", "none,",
)

TAUTOLOGICAL_EXACT: frozenset[str] = frozenset({
    "implementation", "the implementation", "code", "the code",
    "source", "the source", "source code", "the source code",
    "function", "the function", "function output", "return value",
    "the return value", "computed", "computed value", "calculated",
    "calculated value", "self", "same function", "sut", "system under test",
    "unit under test", "actual output", "actual", "runtime output",
    "internal state", "mock", "the mock", "mock return value",
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
    "audit", "live-run", "operator", "doc-review",
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
    r"\(\s*verified\s+by\s*:\s*[^)]+\)\s*$", re.IGNORECASE,
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
    row: str
    col: str
    code: str
    detail: str


class CheckResult(NamedTuple):
    status: str
    exit_code: int
    path: str
    rows: int = 0
    acs_covered: int = 0
    acs_total: int = 0
    exempt_reason: str = ""
    error_type: str = ""
    issues: tuple[Issue, ...] = ()


def _unfenced_lines(text: str):
    """Yield Markdown lines outside CommonMark backtick and tilde fences."""
    fence = ""
    for line in text.splitlines():
        match = FENCE_RE.match(line)
        if fence:
            if (match and match.group(1)[0] == fence[0]
                    and len(match.group(1)) >= len(fence)
                    and not match.group(2).strip()):
                fence = ""
            continue
        if match:
            marker, info = match.groups()
            if marker[0] != "`" or "`" not in info:
                fence = marker
                continue
        yield line


def has_test_boundaries_heading(design_text: str) -> bool:
    return any(TEST_BOUNDARIES_HEADING_RE.match(line)
               for line in _unfenced_lines(design_text))


def _feature_stem(design_path: Path) -> str:
    name = Path(design_path).name
    for suffix in (".design.md", ".md"):
        if name.endswith(suffix):
            return name[:-len(suffix)]
    return name


def _is_canonical_design(abs_design: Path, root: Path | None) -> bool:
    return (
        abs_design.parts[-4:-1] == ("docs", "02-design", "features")
        or (root is not None and abs_design.is_relative_to(
            Path(root).resolve() / "docs" / "02-design" / "features"))
    )


def infer_project_root(design_path: Path, root: Path | None = None) -> Path | None:
    if root is not None:
        return Path(root).resolve()
    abs_design = Path(design_path).resolve()
    if abs_design.parts[-4:-1] == ("docs", "02-design", "features"):
        return abs_design.parents[3]
    for i in range(len(abs_design.parts) - 2):
        if abs_design.parts[i:i + 2] == ("docs", "archive"):
            return Path(*abs_design.parts[:i])
    return None


def resolve_spec_path(
    design_path: Path, spec_path: Path | None = None, root: Path | None = None,
) -> Path:
    if spec_path is not None:
        return Path(spec_path)
    abs_design = Path(design_path).resolve()
    feature = _feature_stem(abs_design)
    sib_cand = abs_design.parent / f"{feature}.spec.md"
    if _is_canonical_design(abs_design, root):
        proj_root = infer_project_root(abs_design, root) or Path.cwd().resolve()
        plan_cand = proj_root / "docs" / "01-plan" / "features" / f"{feature}.spec.md"
        if plan_cand.exists():
            return plan_cand
        if sib_cand.exists():
            return sib_cand
        return plan_cand
    return sib_cand


def extract_spec_acs(spec_text: str) -> tuple[set[str], set[str]]:
    active_acs: set[str] = set()
    retired_acs: set[str] = set()
    for line in _unfenced_lines(spec_text):
        if VERSION_HISTORY_HEADING_RE.match(line):
            break
        match = HEAD_AC_RE.match(line)
        if not match:
            continue
        ac_id = match.group(1)
        if RETIRED_LINE_RE.match(line):
            retired_acs.add(ac_id)
            active_acs.discard(ac_id)
        elif ac_id not in retired_acs:
            active_acs.add(ac_id)
    return active_acs, retired_acs


def should_activate_design_check(design_path: Path, root: Path | None = None) -> bool:
    design_path = Path(design_path)
    if not design_path.exists():
        return False
    if design_path.is_dir():
        return True
    abs_design = design_path.resolve()
    archived = any(abs_design.parts[i:i + 2] == ("docs", "archive")
                   for i in range(len(abs_design.parts) - 2))
    if (_is_canonical_design(abs_design, root) or archived
            or (root is not None and abs_design.is_relative_to(
                Path(root).resolve() / "docs" / "archive"))):
        return True
    try:
        design_text = design_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return True
    if has_test_boundaries_heading(design_text):
        return True
    spec_candidate = resolve_spec_path(abs_design, None, root)
    if spec_candidate.exists():
        try:
            spec_text = spec_candidate.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return True
        return bool(extract_spec_acs(spec_text)[0])
    return False


def normalize_cell(raw_cell: str) -> str:
    value = raw_cell.strip()
    while True:
        stripped = value.strip("`*_").strip()
        if stripped == value:
            return re.sub(r"\s+", " ", value).casefold()
        value = stripped


def is_placeholder_cell(norm_cell: str, col_name: str) -> bool:
    if col_name == "Mocked dependencies" and (
        norm_cell == "none" or norm_cell.startswith(MOCKED_NONE_PREFIXES)
    ):
        return False
    if norm_cell in PLACEHOLDER_EXACT:
        return True
    return norm_cell.startswith(PLACEHOLDER_PREFIXES)


def is_tautological_oracle(raw_cell: str) -> bool:
    stripped = PROVENANCE_SUFFIX_RE.sub("", raw_cell)
    cleaned = normalize_cell(stripped).strip(".,;:!?'\"()[]{}-–—`*_ ")
    if cleaned in TAUTOLOGICAL_EXACT:
        return True
    return bool(TAUTOLOGICAL_RE.search(cleaned))


def has_proving_artifact(raw_cell: str) -> bool:
    return bool(PROVING_PATH_RE.search(raw_cell) or TOKEN_RE.search(raw_cell)
                or BACKTICK_SPAN_RE.search(raw_cell))


def validate_non_test_row(
    row_idx: int, pub_cell: str, oracle_cell: str, oracle_had_basic_error: bool,
) -> list[Issue]:
    cleaned_pub = pub_cell.strip().strip("`").strip()
    match = VERIFIED_BY_PREFIX_RE.match(cleaned_pub)
    if not match:
        return []
    rest = match.group(1).strip()
    if not VERIFIED_BY_KIND_RE.match(rest):
        return [Issue(str(row_idx), "Public interface", "invalid_non_test_row",
                      f"unrecognized verified by kind in {pub_cell!r}; expected audit, live-run, operator, or doc-review")]
    if not oracle_had_basic_error and not has_proving_artifact(oracle_cell):
        return [Issue(str(row_idx), "Expected result source", "invalid_non_test_row",
                      f"verified by row must name a concrete proving artifact in Expected result source: {oracle_cell!r}")]
    return []


def _table_cells(line: str) -> list[str]:
    cells = UNESCAPED_PIPE_RE.split(line.strip())
    if cells and not cells[0]:
        cells.pop(0)
    if cells and not cells[-1]:
        cells.pop()
    return [cell.strip() for cell in cells]


def _boundary_table(design_text: str) -> tuple[list[str], list[list[str]]]:
    section: list[str] = []
    in_section = False
    for line in _unfenced_lines(design_text):
        if not in_section:
            if TEST_BOUNDARIES_HEADING_RE.match(line):
                in_section = True
            continue
        if LEVEL_1_OR_2_HEADING_RE.match(line):
            break
        section.append(line)
    for index in range(len(section) - 1):
        if not UNESCAPED_PIPE_RE.search(section[index]):
            continue
        separator = _table_cells(section[index + 1])
        if not separator or not all(SEPARATOR_CELL_RE.fullmatch(c) for c in separator):
            continue
        rows: list[list[str]] = []
        for line in section[index + 2:]:
            if not UNESCAPED_PIPE_RE.search(line):
                break
            rows.append(_table_cells(line))
        return _table_cells(section[index]), rows
    return [], []


def _ac_sort_key(ac_id: str) -> tuple[int, int, str]:
    match = CELL_AC_RE.fullmatch(ac_id)
    assert match is not None
    return int(match.group(2)), int(match.group(3)), match.group(4)


def check_design(
    design_path: Path,
    *,
    spec_path: Path | None = None,
    root: Path | None = None,
    no_exempt: bool = False,
) -> CheckResult:
    design_path = Path(design_path)
    path = str(design_path)
    try:
        design_text = design_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return CheckResult("UNREADABLE", 2, path, error_type=type(exc).__name__)

    has_section = has_test_boundaries_heading(design_text)
    if not has_section and not no_exempt:
        if "archive" in Path(design_path).parts:
            return CheckResult("EXEMPT", 0, path, exempt_reason="archived")
        if _feature_stem(design_path) in PRE_EXISTING_FEATURES:
            return CheckResult("EXEMPT", 0, path, exempt_reason="pre_existing_feature")

    spec_candidate = resolve_spec_path(design_path, spec_path, root)
    spec_known = spec_path is not None or spec_candidate.exists()
    active_acs: set[str] = set()
    retired_acs: set[str] = set()
    if spec_known:
        try:
            spec_text = spec_candidate.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            return CheckResult("UNREADABLE", 2, str(spec_candidate), error_type=type(exc).__name__)
        active_acs, retired_acs = extract_spec_acs(spec_text)

    if not has_section:
        return CheckResult("FAIL", 0, path, issues=(
            Issue("-", "-", "missing_section", "missing ## Test Boundaries section"),
        ))
    header_cells, rows = _boundary_table(design_text)
    if not rows:
        return CheckResult("FAIL", 0, path, issues=(
            Issue("-", "-", "missing_table", "missing pipe table or data rows in ## Test Boundaries"),
        ))
    if (len(header_cells) != 5 or [c.strip().casefold() for c in header_cells]
            != [c.casefold() for c in EXPECTED_COLUMNS]):
        return CheckResult("FAIL", 0, path, issues=(
            Issue("header", "-", "invalid_columns",
                  f"expected columns: {', '.join(EXPECTED_COLUMNS)}"),
        ))

    issues: list[Issue] = []
    if not spec_known:
        issues.append(Issue("-", "-", "missing_spec", f"missing paired spec: {spec_candidate}"))
    covered_acs: set[str] = set()
    for row_idx, cells in enumerate(rows, 1):
        if len(cells) != 5:
            issues.append(Issue(str(row_idx), "-", "invalid_columns",
                                f"expected 5 columns, got {len(cells)}"))
            continue
        basic_errors: set[str] = set()
        for col_name, raw_cell in zip(EXPECTED_COLUMNS, cells):
            norm_cell = normalize_cell(raw_cell)
            if norm_cell == "":
                issues.append(Issue(str(row_idx), col_name, "empty_cell", f"empty cell in {col_name}"))
                basic_errors.add(col_name)
            elif is_placeholder_cell(norm_cell, col_name):
                issues.append(Issue(str(row_idx), col_name, "placeholder_cell",
                                    f"placeholder value {raw_cell!r} in {col_name}"))
                basic_errors.add(col_name)

        if "Acceptance criteria" not in basic_errors:
            row_acs = [m.group(1) for m in CELL_AC_RE.finditer(cells[1])]
            if not row_acs and spec_known and active_acs:
                issues.append(Issue(str(row_idx), "Acceptance criteria", "invalid_columns",
                                    "Acceptance criteria cell contains zero AC-X.Y tokens"))
            for ac_id in row_acs:
                covered_acs.add(ac_id)
                if spec_known and ac_id not in active_acs and ac_id not in retired_acs:
                    issues.append(Issue(str(row_idx), "Acceptance criteria", "unknown_ac",
                                        f"unknown AC not in spec: {ac_id}"))

        oracle_had_basic_error = "Expected result source" in basic_errors
        if not oracle_had_basic_error and is_tautological_oracle(cells[2]):
            issues.append(Issue(str(row_idx), "Expected result source", "tautological_oracle",
                                f"tautological oracle in Expected result source: {cells[2]!r}"))
            oracle_had_basic_error = True
        issues.extend(validate_non_test_row(row_idx, cells[0], cells[2], oracle_had_basic_error))

    if spec_known:
        missing_acs = sorted(active_acs - covered_acs, key=_ac_sort_key)
        if missing_acs:
            issues.append(Issue("-", "Acceptance criteria", "uncovered_ac",
                                f"missing active ACs: {', '.join(missing_acs)}"))
    if issues:
        return CheckResult("FAIL", 0, path, issues=tuple(issues))
    return CheckResult("PASS", 0, path, rows=len(rows),
                       acs_covered=len(active_acs & covered_acs), acs_total=len(active_acs))


def format_check_result(result: CheckResult) -> str:
    token = f"TEST-BOUNDARIES: {result.status} path={result.path}"
    if result.status == "PASS":
        return f"{token} rows={result.rows} acs={result.acs_covered}/{result.acs_total}"
    if result.status == "EXEMPT":
        return f"{token} reason={result.exempt_reason}"
    if result.status == "UNREADABLE":
        return f"{token} err={result.error_type}"
    reasons = ",".join(sorted({issue.code for issue in result.issues}))
    lines = [f"{token} issues={len(result.issues)} reasons={reasons}"]
    lines.extend(
        f"TEST-BOUNDARIES-ISSUE: row={issue.row} col={issue.col} "
        f"code={issue.code} detail={issue.detail}"
        for issue in result.issues
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("design_path", type=Path)
    parser.add_argument("--spec", type=Path)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--no-exempt", action="store_true")
    args = parser.parse_args(argv)
    result = check_design(args.design_path, spec_path=args.spec, root=args.root,
                          no_exempt=args.no_exempt)
    print(format_check_result(result))
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
