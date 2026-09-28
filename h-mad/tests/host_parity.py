"""File-only checks for constructs declared across host runtime documents."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import h_mad_doc_block_exec as _dbe  # noqa: E402


@dataclass(frozen=True)
class ParityPaths:
    root: Path
    registry: Path
    skills: Mapping[str, Path]
    adapters: Mapping[Path, str]


@dataclass(frozen=True)
class Failure:
    kind: str
    file: str
    id: str = "-"
    reason: str | None = None
    token: str | None = None

    def line(self) -> str:
        line = f"PARITY {self.kind} file={self.file} id={self.id}"
        if self.reason is not None:
            line += f" reason={self.reason}"
        if self.token is not None:
            line += f" token={self.token}"
        return line


class UnsupportedPattern(ValueError):
    """A registry pattern cannot be expanded with the closed branch grammar."""


REQUIRED_KEYS = ("id", "pattern", "skills", "description")
_ID = re.compile(r"[a-z][a-z0-9-]*\Z")


def live_paths(root: Path) -> ParityPaths:
    skills = {name: root / name / "SKILL.md" for name in ("h-mad", "handoff")}
    adapters = {
        root / name / "references" / f"{host}-runtime.md": name
        for name in skills for host in ("codex", "agy", "grok")
    }
    return ParityPaths(root, root / "h-mad" / "references" / "host-constructs.json", skills, adapters)


A4_BRANCHES: Mapping[str, str] = {
    "tilde": r"~",  # M:B1
    "home": r"\$HOME",  # M:B2
    "home_braced": r"\$\{HOME\}",  # M:B3
}


def a4_pattern(branches: Iterable[str]) -> str:
    return "(?:" + "|".join(branches) + r")/\.claude\b(?:/[A-Za-z0-9_.-]+)*"


CATCH_ALL_AXES: Mapping[str, str] = {
    "A1": r"\b[A-Z][A-Za-z0-9]*\(",  # M:A1
    "A2": r"`[A-Z][a-z0-9]+(?:[A-Z][A-Za-z0-9]*)+`",  # M:A2
    "A3": r"\bCLAUDE[A-Z0-9_]*\b",  # M:A3
    "A4": a4_pattern(A4_BRANCHES.values()),  # M:A4
}
EXCLUSION_SUFFIXES = ("Error", "Exception", "Warning", "Expired", "Exit", "Interrupt")  # M:X


def expand_branches(pattern: str) -> list[str]:
    """Expand alternatives and optional groups while preserving regex atoms."""
    position = 0

    def sequence(closing: bool = False) -> list[str]:
        nonlocal position
        alternatives: list[str] = []
        current = [""]
        while position < len(pattern) and pattern[position] != ")":
            char = pattern[position]
            if char == "|":
                alternatives.extend(current)
                current = [""]
                position += 1
                continue
            if char == "(":
                start = position
                position += 1
                if pattern.startswith("?:", position):
                    position += 2
                elif pattern.startswith(("?=", "?!", "?<=", "?<!"), position):
                    # A lookaround is an indivisible atom, including its parentheses.
                    depth = 1
                    while position < len(pattern) and depth:
                        if pattern[position] == "\\":
                            position += 2
                            continue
                        if pattern[position] == "(":
                            depth += 1
                        elif pattern[position] == ")":
                            depth -= 1
                        position += 1
                    if depth:
                        raise UnsupportedPattern(pattern)
                    atom = pattern[start:position]
                    if position < len(pattern) and pattern[position] in "?*+{":
                        raise UnsupportedPattern(pattern)
                    current = [item + atom for item in current]
                    continue
                elif position < len(pattern) and pattern[position] == "?":
                    raise UnsupportedPattern(pattern)
                inner = sequence(True)
                if position >= len(pattern) or pattern[position] != ")":
                    raise UnsupportedPattern(pattern)
                position += 1
                if position < len(pattern) and pattern[position] in "*+{":
                    raise UnsupportedPattern(pattern)
                if position < len(pattern) and pattern[position] == "?":
                    position += 1
                    inner.append("")  # M:E1
                current = [left + right for left in current for right in inner]
                continue
            if char == "\\":
                if position + 1 >= len(pattern):
                    raise UnsupportedPattern(pattern)
                atom = pattern[position:position + 2]
                position += 2
            elif char == "[":
                start = position
                position += 1
                if position < len(pattern) and pattern[position] == "^":
                    position += 1
                if position < len(pattern) and pattern[position] == "]":
                    position += 1
                while position < len(pattern):
                    if pattern[position] == "\\":
                        position += 2
                    elif pattern[position] == "]":
                        position += 1
                        break
                    else:
                        position += 1
                else:
                    raise UnsupportedPattern(pattern)
                atom = pattern[start:position]
            else:
                atom = char
                position += 1
            if position < len(pattern) and pattern[position] in "?*+{":
                raise UnsupportedPattern(pattern)
            current = [item + atom for item in current]
        alternatives.extend(current)
        if not closing and position != len(pattern):
            raise UnsupportedPattern(pattern)
        return alternatives

    return sequence()


@dataclass(frozen=True)
class Row:
    id: str
    status: str
    mapping: str
    source: str


@dataclass(frozen=True)
class Table:
    rows: list[Row]
    problems: list[tuple[str, str, str]]


def _cells(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|") and not line.endswith(r"\|"):
        line = line[:-1]
    return [cell.replace(r"\|", "|").strip() for cell in re.split(r"(?<!\\)\|", line)]


def _cell_id(cell: str) -> str:
    if len(cell) >= 2 and cell[0] == cell[-1] == "`":
        return cell[1:-1]
    return cell


def adapter_table(text: str) -> Table:
    problems: list[tuple[str, str, str]] = []
    try:
        found = _dbe.find_heading(text, "## Construct mapping")
    except _dbe.AmbiguousHeading:
        problems.append(("TABLE_MISSING", "heading_twice", "-"))  # M:D23
        return Table([], problems)
    if found is None:
        problems.append(("TABLE_MISSING", "no_heading", "-"))  # M:D21
        return Table([], problems)
    start, level = found
    end = _dbe.fence_aware_end(text, start, level)
    lines: list[str] = []
    previous = -2
    for event in _dbe._fence_events(text):
        if event.kind == "prose" and start <= event.start < end and text[event.start:event.end].lstrip(" ")[:1] == "|":  # M:F1
            if lines and event.lineno != previous + 1:
                break
            lines.append(text[event.start:event.end].rstrip("\r\n"))
            previous = event.lineno
        elif lines:
            break
    if not lines:
        problems.append(("TABLE_MISSING", "no_table", "-"))  # M:D22
        return Table([], problems)
    parsed = [_cells(line) for line in lines]
    if len(parsed) < 2 or parsed[0] != ["construct", "status", "mapping", "source"]:
        problems.append(("TABLE_MALFORMED", "header", "-"))  # M:D24
        return Table([], problems)
    if len(parsed[1]) != 4 or any(re.fullmatch(r":?-+:?", cell) is None for cell in parsed[1]):
        problems.append(("TABLE_MALFORMED", "header", "-"))  # M:D42
        return Table([], problems)
    rows: list[Row] = []
    for cells in parsed[2:]:
        if len(cells) != 4:
            row_id = _cell_id(cells[0]) if cells else "-"  # M:K1
            if _ID.fullmatch(row_id) is None:
                row_id = "-"
            problems.append(("TABLE_MALFORMED", "cell_count", row_id))  # M:D25
            continue
        rows.append(Row(_cell_id(cells[0]), _cell_id(cells[1]), cells[2], cells[3]))
    return Table(rows, problems)


@dataclass(frozen=True)
class ParityResult:
    failures: list[Failure]
    stages: tuple[str, ...]


def _file(paths: ParityPaths, path: Path) -> str:
    try:
        return str(path.relative_to(paths.root))
    except ValueError:
        return str(path)


def check(paths: ParityPaths, *, axes: Mapping[str, str] = CATCH_ALL_AXES,
          exclusion_suffixes: Sequence[str] = EXCLUSION_SUFFIXES) -> ParityResult:
    failures: list[Failure] = []
    stages = ["registry"]
    registry_file = _file(paths, paths.registry)
    if not paths.registry.is_file():
        failures.append(Failure("REGISTRY_UNREADABLE", registry_file, reason="missing_file"))  # M:D01
        return ParityResult(failures, tuple(stages))
    try:
        data = json.loads(paths.registry.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError):
        failures.append(Failure("REGISTRY_UNREADABLE", registry_file, reason="invalid_json"))  # M:D02
        return ParityResult(failures, tuple(stages))
    if not isinstance(data, dict):
        failures.append(Failure("REGISTRY_UNREADABLE", registry_file, reason="not_object"))  # M:D03
        return ParityResult(failures, tuple(stages))
    if "constructs" not in data:
        failures.append(Failure("REGISTRY_UNREADABLE", registry_file, reason="no_constructs"))  # M:D04
        return ParityResult(failures, tuple(stages))
    elements = data["constructs"]
    if not isinstance(elements, list):
        failures.append(Failure("REGISTRY_UNREADABLE", registry_file, reason="constructs_not_array"))  # M:D05
        return ParityResult(failures, tuple(stages))
    for element in elements:
        if not isinstance(element, dict):
            failures.append(Failure("REGISTRY_UNREADABLE", registry_file, reason="element_not_object"))  # M:D06
            return ParityResult(failures, tuple(stages))

    field_checked = []
    valid_ids: dict[str, int] = {}
    for element in elements:
        missing = False
        for key in REQUIRED_KEYS:
            if key not in element:
                failures.append(Failure("REGISTRY_UNREADABLE", registry_file, reason=f"missing_key:{key}"))  # M:D07-D10
                missing = True
        for key in element:
            if key not in REQUIRED_KEYS:
                failures.append(Failure("REGISTRY_UNREADABLE", registry_file, reason=f"extra_key:{key}"))  # M:D11
        if missing:
            continue
        field_checked.append(element)
        identifier = element.get("id")
        if not isinstance(identifier, str):
            failures.append(Failure("REGISTRY_UNREADABLE", registry_file, reason="bad_id"))  # M:D38
        elif _ID.fullmatch(identifier) is None:
            failures.append(Failure("REGISTRY_UNREADABLE", registry_file, reason="bad_id"))  # M:D12
        else:
            valid_ids[identifier] = valid_ids.get(identifier, 0) + 1
        description = element.get("description")
        if not isinstance(description, str):
            failures.append(Failure("REGISTRY_UNREADABLE", registry_file, reason="empty_description"))  # M:D41
        elif not description.strip():
            failures.append(Failure("REGISTRY_UNREADABLE", registry_file, reason="empty_description"))  # M:D13
        skills = element.get("skills")
        if not isinstance(skills, list):
            failures.append(Failure("REGISTRY_UNREADABLE", registry_file, reason="bad_skill"))  # M:D39
        elif not skills:
            failures.append(Failure("REGISTRY_UNREADABLE", registry_file, reason="empty_skills"))  # M:D14
        elif any(not isinstance(skill, str) or skill not in paths.skills for skill in skills):
            failures.append(Failure("REGISTRY_UNREADABLE", registry_file, reason="bad_skill"))  # M:D15
        elif len(set(skills)) != len(skills):
            failures.append(Failure("REGISTRY_UNREADABLE", registry_file, reason="bad_skill"))  # M:D40
    duplicates = {identifier for identifier, count in valid_ids.items() if count > 1}
    for identifier in sorted(duplicates):
        failures.append(Failure("DUPLICATE_ID", registry_file, identifier))  # M:D16
    bad_patterns: set[str] = set()
    for element in field_checked:  # M:P1
        pattern = element.get("pattern")
        identifier = element.get("id")
        if not isinstance(pattern, str):
            failures.append(Failure("BAD_PATTERN", registry_file, identifier if isinstance(identifier, str) else "-"))  # M:D37
            bad_patterns.add(identifier)
            continue
        try:
            re.compile(pattern)
        except re.error:
            failures.append(Failure("BAD_PATTERN", registry_file, identifier if isinstance(identifier, str) else "-"))  # M:D17
            bad_patterns.add(identifier)
    if any(f.kind == "REGISTRY_UNREADABLE" for f in failures):  # M:Sa
        return ParityResult(failures, tuple(stages))

    stages.append("skill")
    for skill, path in paths.skills.items():
        skill_file = _file(paths, path)
        text = path.read_text(encoding="utf-8")
        spans: list[tuple[int, int]] = []
        for element in elements:
            identifier = element["id"]
            if identifier in bad_patterns:
                continue
            matches = list(re.finditer(element["pattern"], text))
            if skill in element["skills"]:
                spans.extend((match.start(), match.end()) for match in matches)
                if not matches:
                    failures.append(Failure("STALE_ENTRY", skill_file, identifier))  # M:D18
            elif matches:
                failures.append(Failure("UNDECLARED_SKILL", skill_file, identifier))  # M:D19
        if any(skill in element["skills"] for element in elements if element["id"] in bad_patterns):  # M:Sb
            continue
        hits = []
        for axis, expression in axes.items():
            for match in re.finditer(expression, text):
                token = match.group()
                if axis == "A2" and any(token.endswith(suffix + "`") for suffix in exclusion_suffixes):
                    continue
                hits.append((match.start(), match.end(), token))
        for start, end, token in sorted(hits):
            if not any(left < end and start < right for left, right in spans):
                failures.append(Failure("UNREGISTERED", skill_file, token=token))  # M:D20

    stages.append("adapter")
    registry = {element["id"]: element for element in elements}
    for path, skill in sorted(paths.adapters.items()):
        adapter_file = _file(paths, path)
        table = adapter_table(path.read_text(encoding="utf-8") if path.is_file() else "")
        for kind, reason, identifier in table.problems:
            failures.append(Failure(kind, adapter_file, identifier, reason))
        if any(kind == "TABLE_MISSING" for kind, _, _ in table.problems):  # M:Sd-missing
            continue
        if any(kind == "TABLE_MALFORMED" and reason == "header" for kind, reason, _ in table.problems):  # M:Sd-header
            continue
        present: set[str] = set()
        for kind, reason, identifier in table.problems:
            if kind == "TABLE_MALFORMED" and reason == "cell_count" and identifier != "-":
                present.add(identifier)  # M:Se
        for row in table.rows:
            if row.id in duplicates:  # M:Sc
                continue
            if row.id not in registry:
                failures.append(Failure("ROW_UNKNOWN_ID", adapter_file, row.id))  # M:D27
            elif skill not in registry[row.id]["skills"]:
                failures.append(Failure("ROW_WRONG_SKILL", adapter_file, row.id))  # M:D28
            if row.id in present:
                failures.append(Failure("ROW_DUPLICATE", adapter_file, row.id))  # M:D29
            present.add(row.id)
            if row.status not in ("mapped", "not-applicable"):
                failures.append(Failure("STATUS_INVALID", adapter_file, row.id))  # M:D30
            for cell_name, cell in (("mapping", row.mapping), ("source", row.source)):
                if not re.search(r"[A-Za-z0-9]", cell):
                    kind = "no_alnum"
                elif cell.lower() in ("tbd", "todo"):  # M:C1
                    kind = cell.lower()
                else:
                    continue
                failures.append(Failure("CELL_EMPTY", adapter_file, row.id, f"{cell_name}:{kind}"))  # M:D31-D36
        for element in elements:
            identifier = element["id"]
            if identifier in duplicates:
                continue
            if skill in element["skills"] and identifier not in present:
                failures.append(Failure("ROW_MISSING", adapter_file, identifier))  # M:D26
    return ParityResult(failures, tuple(stages))
