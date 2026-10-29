#!/usr/bin/env python3
"""h_mad_wire_registry.py — Phase-5d registry schema and JSONL loader."""
from __future__ import annotations

import json
import ast
import fnmatch
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from h_mad_audit_gate import _acknowledged_from_text, suite_busy_line

VALID_KINDS: frozenset[str] = frozenset({"wire"})
VALID_PROVENANCE: frozenset[str] = frozenset({"superseded", "pinned-a-defect", "renamed"})
# A record names the runner its pin belongs to; absent means pytest, so every
# record written before the field existed reads back unchanged. Only a runner in
# RESOLVED_RUNNERS can be judged here: the rest are counted `unverifiable` at
# 5f -- cannot-judge, never `missing` (decision 2026-10-25, runner field).
DEFAULT_RUNNER = "pytest"
VALID_RUNNERS: frozenset[str] = frozenset({"pytest", "playwright"})
RESOLVED_RUNNERS: frozenset[str] = frozenset({"pytest"})
DEFAULT_REGISTRY = ".h-mad/wires.jsonl"


class RegistryError(Exception):
    """Malformed registry content — a cannot-judge, never a verdict."""


def _record_key(record: dict) -> tuple[str, str]:
    """The registry's identity: `(owning_feature, id)`, never `id` alone.

    `id` is the impl-plan task number (`"Task 4"`), and every impl-plan numbers
    its tasks from 1 — so two features that both register a Task N collide by
    construction. Keyed on the bare id, `register` upserted one feature's wire
    over another's and `compare` (keyed the same way) saw the successor and
    reported nothing, which is precisely the silent removal the `status`
    /`removal_provenance`/`removed_by_feature` tombstone fields exist to force
    an author to declare. Measured before the fix: 1 of 7 records ever
    registered in this repo had already been lost that way (J43).

    `owning_feature` is a required field, so this key is always available.
    """
    return (record["owning_feature"], record["id"])


def _record_label(record: dict) -> str:
    """`<feature>::<id>` for halt reasons — a bare id now names no single wire."""
    return f"{record['owning_feature']}::{record['id']}"


def pins(record: dict, field: str = "pin") -> list[str]:
    """`pin` as a list, whether it was stored as a string or a list.

    One wiring task can wire N call sites, and one pin per record could only
    ever prove site 1 — the rest were left to ACs and the wire-scoped revert,
    which the registry cannot see. A string stays a string on disk: every
    record written before the list form is still read unchanged, and `register`
    keeps writing a bare string when it is given exactly one pin.
    """
    value = record[field]
    return [value] if isinstance(value, str) else list(value)


def pin_labels(record: dict, offending: list[str]) -> list[str]:
    """One halt-reason label per offending pin.

    `<feature>::<id>` for a single-pin record, so every string emitted before
    multi-pin is byte-identical; `<feature>::<id>#<pin>` once a record carries
    more than one, because two broken sites on one record would otherwise emit
    the same line twice and name neither — the J43 defect one level down.
    """
    label = _record_label(record)
    if len(pins(record)) == 1:
        return [label]
    return [f"{label}#{pin}" for pin in offending]


def _base_node_id(node_id: str) -> str:
    """Strip a trailing `[...]` parameter suffix from the final `::` test segment."""
    prefix, sep, tail = node_id.rpartition("::")
    if sep and "[" in tail and tail.endswith("]"):
        base_tail = tail.split("[", 1)[0]
        if base_tail:
            return f"{prefix}::{base_tail}"
    return node_id


def _resolve_pin(pin: str, collected: set[str]) -> tuple[list[str], str]:
    """Resolve one pin against `collected` -> `(matched_node_ids, bucket)`.

    An unparametrized pin resolves to all collected parameter cases that share a
    single `_base_node_id` test identity; matching more than one distinct base
    test identity is `"ambiguous"`, and matching none is `"missing"`.
    """
    if "[" in pin:
        if "::" in pin and pin in collected:
            return [pin], ""
        matches = sorted(node_id for node_id in collected if node_id.endswith("::" + pin))
        if len(matches) == 1:
            return matches, ""
        return ([], "ambiguous") if matches else ([], "missing")

    if "::" in pin:
        if pin in collected:
            return [pin], ""
        exact = sorted(node_id for node_id in collected if _base_node_id(node_id) == pin)
        if exact:  # M:PARAM-EXACT
            return exact, ""

    groups: dict[str, list[str]] = {}
    suffix = "::" + pin
    for node_id in collected:
        base = _base_node_id(node_id)
        if base.endswith(suffix):
            groups.setdefault(base, []).append(node_id)
    if len(groups) == 1:  # M:PARAM-SUFFIX
        return sorted(next(iter(groups.values()))), ""
    return ([], "ambiguous") if groups else ([], "missing")


def unresolved_pins(record: dict, collected: set[str], field: str = "pin") -> list[str]:
    """The pins of `record` that do not resolve to a single collected test identity."""
    return [
        pin for pin in pins(record, field)
        if _resolve_pin(pin, collected)[1] != ""
    ]


def _validate_pin_field(record: dict, field: str) -> None:
    """A pin is a non-empty string, or a list of distinct non-empty strings."""
    value = record[field]
    if isinstance(value, str):
        return
    if not isinstance(value, list):
        raise RegistryError(f"{field} must be a string or a list of strings")
    if not value:
        raise RegistryError(f"{field} list must not be empty")
    for element in value:
        if not isinstance(element, str) or not element:
            raise RegistryError(f"{field} list must hold non-empty strings: {element!r}")
    if len(set(value)) != len(value):
        raise RegistryError(f"{field} list must not repeat a pin")


def record_runner(record: dict) -> str:
    return record.get("runner", DEFAULT_RUNNER)


def _names_a_non_py_file(pin: object) -> bool:
    """A non-pytest pin must be `<file>::<test>`, and the file must not be Python.

    A bare name (`test_x`, `TestRun::test_x`) resolves against the pytest
    collection by suffix, so it is a pytest pin whatever runner it claims.
    """
    if not isinstance(pin, str) or "::" not in pin:
        return False
    file = pin.split("::", 1)[0]
    name = file.rsplit("/", 1)[-1]
    return file == file.strip() and "." in name and not name.lower().endswith(".py")


def runner_problem(record: dict) -> str | None:
    """Why the record's runner is unacceptable, or None. Never raises.

    A pytest pin may not claim another runner: `unverifiable` stands down at 5f,
    so a pytest pin carrying it would park a real FAIL where nothing judges it.
    The gate calls this to skip a bad record loudly, `validate_record` to refuse
    one at write time, and `verify` to refuse a hand-edited one at read time.
    """
    runner = record_runner(record)
    if not isinstance(runner, str) or runner not in VALID_RUNNERS:  # M:RUNNER-VALID
        return f"invalid runner: {runner!r} (one of {', '.join(sorted(VALID_RUNNERS))})"
    if runner == DEFAULT_RUNNER:
        return None
    for field in ("pin", "successor_pin"):
        if not isinstance(record.get(field), (str, list)):
            continue
        bad = [pin for pin in pins(record, field) if not _names_a_non_py_file(pin)]
        if bad:  # M:RUNNER-FILE
            return (f"runner {runner!r} needs every {field} to name a non-.py file "
                    f"(`<file>::<test>`): {', '.join(map(str, bad))}")
    return None


def validate_record(record: dict) -> dict:
    """Return the record, or raise RegistryError naming the offending field."""
    if not isinstance(record, dict):
        raise RegistryError("record must be an object")
    required = ("kind", "id", "caller", "callee", "pin", "owning_feature", "registered_ts")
    for field in required:
        if field not in record or record[field] in (None, "") or record[field] == []:
            raise RegistryError(f"missing required field: {field}")
    _validate_pin_field(record, "pin")
    if record["kind"] not in VALID_KINDS:
        raise RegistryError(f"invalid kind: {record['kind']!r}")
    if record.get("status", "active") == "removed":
        provenance = record.get("removal_provenance")
        if provenance not in VALID_PROVENANCE:
            raise RegistryError("missing or invalid removal_provenance")
        if not record.get("removed_by_feature"):
            raise RegistryError("missing removed_by_feature")
        if provenance == "superseded" and not record.get("superseding_feature"):
            raise RegistryError("missing superseding_feature")
        if provenance == "renamed":
            if not record.get("successor_pin"):
                raise RegistryError("missing successor_pin")
            _validate_pin_field(record, "successor_pin")
    problem = runner_problem(record)
    if problem:
        raise RegistryError(problem)
    return record


def load(path: Path) -> list[dict]:
    """Parse JSONL. Raises RegistryError naming the 1-based line number on a bad line."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    records: list[dict] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise RegistryError(f"invalid registry line {line_number}: {exc}") from exc
    return records


def register(entries: list[dict], path: Path) -> list[dict]:
    """Write a batch, then re-read and compare the stored records."""
    records = load(path)
    for entry in entries:
        if not isinstance(entry, dict):
            raise RegistryError("record must be an object")
        record = dict(entry)
        record["registered_ts"] = datetime.now(timezone.utc).isoformat()
        record.setdefault("status", "active")
        validate_record(record)
        for index, existing in enumerate(records):
            if _record_key(existing) == _record_key(record):
                records[index] = record
                break
        else:
            records.append(record)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, sort_keys=True) + "\n" for record in records), encoding="utf-8")
    try:
        stored = load(path)
    except (OSError, RegistryError) as exc:
        raise RegistryError(f"registry read-back failed: {exc}") from exc
    if stored != records:
        raise RegistryError("registry read-back mismatch")
    return stored


def git_show(sha: str, path: str, repo: Path) -> str | None:
    """Validate the SHA, then read the path at it; None means path absent."""
    validated = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if validated.returncode != 0:
        raise RegistryError(f"invalid commit SHA: {sha}")
    shown = subprocess.run(
        ["git", "show", f"{sha}:{path}"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if shown.returncode == 0:
        return shown.stdout
    if shown.returncode == 128:
        return None
    raise RegistryError(f"unable to read {path} at commit {sha}")


def changed_files(base: str, repo: Path) -> list[tuple[str | None, str]]:
    result = subprocess.run(
        ["git", "diff", "--name-status", "--diff-filter=d", base, "HEAD", "--", "*.py"],
        cwd=repo, capture_output=True, text=True, check=False,
    )
    if result.returncode:
        raise RegistryError(result.stderr.strip() or "unable to inspect changed files")
    changed: list[tuple[str | None, str]] = []
    for line in result.stdout.splitlines():
        fields = line.split("\t")
        if not fields:
            continue
        status = fields[0]
        if status.startswith("R") and len(fields) >= 3:
            changed.append((fields[1], fields[2]))
        elif len(fields) >= 2:
            changed.append((None if status.startswith("A") else fields[1], fields[1]))
    return changed


def build_module_index(repo: Path) -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = {}
    for path in repo.rglob("*.py"):
        if ".git" in path.parts:
            continue
        rel = path.relative_to(repo)
        parts = list(rel.with_suffix("").parts)
        if parts[-1] == "__init__":
            parts.pop()
        names = [rel.stem]
        if parts:
            names.append(".".join(parts))
        for name in names:
            index.setdefault(name, []).append(path)
    return index


def ast_targets(source: str) -> set[str]:
    tree = ast.parse(source)
    targets: set[str] = set()

    def dotted(node: ast.AST) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            parent = dotted(node.value)
            return f"{parent}.{node.attr}" if parent else node.attr
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            targets.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            targets.add(node.module)
        elif isinstance(node, ast.Call):
            target = dotted(node.func)
            if target:
                targets.add(target)
    return targets


def challenge(base: str, impl_plan: Path, boundaries: Path, ack: Path, repo: Path) -> dict:
    changed = [pair for pair in changed_files(base, repo) if not _is_test_path(pair[1])]
    if not changed:
        return _challenge_result("WIRECHALLENGE: NOT_COMPARED reason=no_production_diff", [], [], [], [], [])
    if not boundaries.exists():
        return _challenge_result("WIRECHALLENGE: NOT_COMPARED reason=no_boundaries", [], [], [], [], [])

    try:
        boundary_map = json.loads(boundaries.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError(f"invalid boundaries: {exc}") from exc
    if not boundary_map:
        return _challenge_result("WIRECHALLENGE: NOT_COMPARED reason=no_boundaries", [], [], [], [], [])

    from h_mad_wire_pin_gate import _parse_tasks
    tasks = _parse_tasks(impl_plan.read_text(encoding="utf-8"))
    claims = _production_claims(impl_plan, tasks)
    normalized_claims = {_normal_path(value, repo): task for value, task in claims.items()}
    changed_heads = {_normal_path(head, repo) for _, head in changed}
    matched_claims = {
        head: _claim_for(head, normalized_claims)
        for head in changed_heads
    }
    dangling = [
        f"{task['id']}: {path}"
        for path, task in normalized_claims.items()
        if not any(claim_path == path for claim_path in matched_claims.values())
    ]
    unattributed = [head for _, head in changed if matched_claims.get(_normal_path(head, repo)) is None]
    wiring_heads = {
        head for head in changed_heads
        if matched_claims.get(head) is not None
        and normalized_claims[matched_claims[head]].get("shape") == "wiring"
    }
    index = build_module_index(repo)
    details: list[str] = []
    ambiguous: list[str] = []
    raised: list[str] = []
    for base_path, head_path in changed:
        rel_head = _normal_path(head_path, repo)
        claim_path = matched_claims.get(rel_head)
        task = normalized_claims.get(claim_path) if claim_path else None
        if not task or rel_head in wiring_heads:
            continue
        head_source = head_path_obj = repo / head_path
        head_text = head_source.read_text(encoding="utf-8")
        base_text = "" if base_path is None else (git_show(base, base_path, repo) or "")
        added_targets = ast_targets(head_text) - ast_targets(base_text)
        caller_boundary = _boundary_for(rel_head, boundary_map)
        if caller_boundary is None:
            continue
        for target in sorted(added_targets):
            candidates = _resolve_target(target, index)
            if len(candidates) > 1:
                item = f"{rel_head}: {target} -> {', '.join(sorted(_rel(p, repo) for p in candidates))}"
                ambiguous.append(item)
                details.append(f"AMBIGUOUS {item}")
                continue
            if not candidates:
                continue
            target_rel = _rel(candidates[0], repo)
            target_boundary = _boundary_for(target_rel, boundary_map)
            if target_boundary and target_boundary != caller_boundary:
                item = f"{task['id']} {rel_head}: {target} ({caller_boundary} -> {target_boundary})"
                raised.append(item)
                details.append(f"CHALLENGE {item}")
    acknowledged = _acknowledged_from_text(ack.read_text(encoding="utf-8")) if ack.exists() else set()
    acknowledged_items = [item for item in raised if item in acknowledged]
    stale = sorted(acknowledged - set(raised))
    token = (
        f"WIRECHALLENGE: challenges={len(raised)} acknowledged={len(acknowledged_items)} "
        f"unattributed={len(unattributed)} dangling={len(dangling)} stale={len(stale)} ambiguous={len(ambiguous)}"
    )
    details.extend(f"UNATTRIBUTED {item}" for item in unattributed)
    details.extend(f"DANGLING {item}" for item in dangling)
    details.extend(f"STALE {item}" for item in stale)
    return _challenge_result(token, raised, acknowledged_items, unattributed, dangling, ambiguous, details)


def _challenge_result(token: str, challenges: list[str], acknowledged: list[str], unattributed: list[str], dangling: list[str], ambiguous: list[str], details: list[str] | None = None) -> dict:
    return {
        "token": token, "challenges": len(challenges), "acknowledged": len(acknowledged),
        "unattributed": len(unattributed), "dangling": len(dangling), "stale": 0,
        "ambiguous": len(ambiguous), "details": details or [],
    }


def _is_test_path(path: str) -> bool:
    parts = Path(path).parts
    return "tests" in parts or Path(path).name.startswith("test_")


def _rel(path: Path, repo: Path) -> str:
    return path.relative_to(repo).as_posix()


def _normal_path(value: str, repo: Path) -> str:
    path = Path(value.replace("\\", "/"))
    if path.is_absolute():
        try:
            path = path.relative_to(repo)
        except ValueError:
            pass
    return path.as_posix().removeprefix("./")


def _claim_for(head: str, claims: dict[str, dict]) -> str | None:
    if head in claims:
        return head
    matches = [claim for claim in claims if head.endswith("/" + claim) or claim.endswith("/" + head)]
    return matches[0] if len(matches) == 1 else None


def _production_claims(plan: Path, tasks: list[dict]) -> dict[str, dict]:
    lines = plan.read_text(encoding="utf-8").splitlines()
    result: dict[str, dict] = {}
    task_index = -1
    for line in lines:
        if line.lstrip().startswith("## Task ") or re.match(r"^\s*#{2,3}\s+[MT]\d+", line):
            task_index += 1
        match = re.match(r"^\s*(?:[-*•]\s+)?\*{0,2}Production file\*{0,2}\s*:\s*(.*)$", line, re.I)
        if match and 0 <= task_index < len(tasks):
            result[match.group(1).strip().strip('`')] = tasks[task_index]
    return result


def _boundary_for(path: str, mapping: dict) -> str | None:
    for pattern, name in mapping.items():
        if fnmatch.fnmatch(path, pattern):
            return str(name)
    return None


def _resolve_target(target: str, index: dict[str, list[Path]]) -> list[Path]:
    candidates: list[Path] = []
    for key in (target, target.split(".")[0]):
        if key in index:
            candidates.extend(index[key])
    return list(dict.fromkeys(candidates))


def load_base(sha: str, path: str, repo: Path) -> list[dict]:
    """Parse JSONL from a committed registry; an absent file is empty."""
    text = git_show(sha, path, repo)
    if text is None:
        return []
    records: list[dict] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise RegistryError(f"invalid registry line {line_number}: {exc}") from exc
    return records


def compare(base_records: list[dict], head_records: list[dict]) -> list[dict]:
    """Return BASE records whose `(owning_feature, id)` is absent at HEAD."""
    head_keys = {_record_key(record) for record in head_records}
    return [record for record in base_records if _record_key(record) not in head_keys]


def partition(
    records: list[dict], collected: set[str]
) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """-> (resolving, missing, ambiguous, unverified_renames). Pure; no subprocess, no git."""
    resolving: list[dict] = []
    missing: list[dict] = []
    ambiguous: list[dict] = []
    unverified_renames: list[dict] = []

    def resolve_all(record: dict, field: str) -> tuple[list[str] | None, str]:
        """-> (node_ids, "") when EVERY pin resolves once, else (None, bucket).

        A record is only as verified as its weakest pin: one unresolved site
        makes the whole record unjudgeable, because a partial pass would report
        a wire as proven while a site it names went unchecked. Ambiguity
        outranks absence — a pin naming more than one test must be qualified
        before the record can be judged at all, and qualifying it often fixes
        the sibling too.
        """
        node_ids: list[str] = []
        bucket = ""
        for pin in pins(record, field):
            matches, pin_bucket = _resolve_pin(pin, collected)
            if not pin_bucket:
                node_ids.extend(matches)
            elif pin_bucket == "ambiguous":
                bucket = "ambiguous"
            elif bucket != "ambiguous":
                bucket = "missing"
        return (None, bucket) if bucket else (node_ids, "")

    for record in records:
        if record.get("status", "active") == "active":
            node_ids, bucket = resolve_all(record, "pin")
            if node_ids is not None:
                resolved = dict(record)
                resolved["node_ids"] = node_ids
                resolved["node_id"] = node_ids[0]
                resolving.append(resolved)
            elif bucket == "missing":
                missing.append(record)
            else:
                ambiguous.append(record)
            continue
        if record.get("removal_provenance") != "renamed":
            continue
        node_ids, bucket = resolve_all(record, "successor_pin")
        if node_ids is not None:
            resolved = dict(record)
            resolved["pin"] = record["successor_pin"]
            resolved["node_ids"] = node_ids
            resolved["node_id"] = node_ids[0]
            resolving.append(resolved)
        elif bucket == "missing":
            unverified_renames.append(record)
        else:
            ambiguous.append(record)
    return resolving, missing, ambiguous, unverified_renames


DEFAULT_TESTPATHS = (Path("h-mad/tests"),)


def _refuse_a_busy_tree(result: subprocess.CompletedProcess) -> None:
    """A pytest session refused by the working-tree lock measured nothing.

    Read as an unreadable registry, never as every pin broken: the lock refuses
    the whole session before one test runs, so an empty outcome table here is
    "not measured", and scoring it would report every wire as a regression.
    """
    output = (getattr(result, "stdout", "") or "") + (getattr(result, "stderr", "") or "")
    busy = suite_busy_line(getattr(result, "returncode", None), output)
    if busy:
        raise RegistryError(f"pytest refused, another run holds this tree: {busy}")


def collect(repo: Path, testpaths: tuple[Path, ...] | list[Path], python: str = sys.executable) -> set[str]:
    """Collect repo-relative pytest node ids from the requested test paths."""
    result = subprocess.run(
        [
            python, "-m", "pytest", *[str(path) for path in testpaths],
            "--collect-only", "-q",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    _refuse_a_busy_tree(result)
    if result.returncode not in (0, 5):
        stdout_lines = (getattr(result, "stdout", "") or "").splitlines()
        stderr_lines = (getattr(result, "stderr", "") or "").splitlines()
        stdout_tail = "\n".join(stdout_lines[-20:]).strip() or "<empty>"
        stderr_tail = "\n".join(stderr_lines[-20:]).strip() or "<empty>"
        raise RegistryError(
            f"pytest collection failed with {python} exit code {result.returncode}; "
            f"stdout (last 20 lines): {stdout_tail}; "
            f"stderr (last 20 lines): {stderr_tail}"
        )
    node_ids: set[str] = set()
    for line in result.stdout.splitlines():
        line = line.strip()
        if "::" in line and not line.endswith(" tests collected"):
            node_ids.add(line)
    return node_ids


def _cli_pin(pin: str, repo: Path) -> str:
    """Resolve a subproject-rooted node id to a `repo`-relative path for pytest."""
    file_part, sep, rest = pin.partition("::")
    if not sep or (repo / file_part).exists():
        return pin
    matches = sorted(
        child / file_part
        for child in repo.iterdir()
        if child.is_dir() and not child.name.startswith(".") and (child / file_part).exists()
    ) if repo.is_dir() else []
    if len(matches) == 1:  # M:SUBPROJ-PIN
        return f"{matches[0].relative_to(repo).as_posix()}::{rest}"
    return pin


def run_pins(resolving: list[dict], repo: Path, python: str = sys.executable) -> tuple[list[dict], list[dict]]:
    """Run resolving pytest pins and return (verified, broken)."""
    if not resolving:
        return [], []
    def _group(record: dict) -> list[str]:
        if record.get("node_ids"):
            return record["node_ids"]
        return [record["node_id"]] if record.get("node_id") else pins(record)

    per_record = [_group(record) for record in resolving]
    all_pins = list(dict.fromkeys(pin for group in per_record for pin in group))
    cli_pins = [_cli_pin(pin, repo) for pin in all_pins]
    result = subprocess.run(
        [python, "-m", "pytest", "-q", "-rA", "-vv", *cli_pins],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    _refuse_a_busy_tree(result)
    outcomes: dict[str, str] = {}
    statuses = ("PASSED", "FAILED", "ERROR", "SKIPPED", "XFAIL", "XPASS")
    for line in result.stdout.splitlines():
        status = next((value for value in statuses if re.search(rf"\b{value}\b", line)), None)
        if status:
            for pin in all_pins:
                if pin in line:
                    outcomes[pin] = status

    verified: list[dict] = []
    broken: list[dict] = []
    for record, group in zip(resolving, per_record):
        failed = [pin for pin in group if outcomes.get(pin) != "PASSED"]
        if not failed:
            verified.append(record)
            continue
        # Every failing site is named: a record reported broken on one pin while
        # another also failed would send the author to fix half the wire.
        record["broken_pins"] = failed
        broken.append(record)
        for pin in failed:
            reason = outcomes.get(pin, "ABSENT FROM PYTEST OUTPUT")
            print(f"BROKEN {record['owning_feature']}: {pin} ({reason})")
    return verified, broken


def _git_root(repo: Path) -> Path | None:
    """The work tree root — the only directory `git show <sha>:<path>` reads from.

    `None` when `repo` is not in a work tree. That is not this function's error
    to raise: the base read that follows calls `git rev-parse` itself and refuses
    a non-repo loudly, so failing here would only move the same refusal earlier
    and duplicate its message.
    """
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=repo, capture_output=True, text=True, check=False,
    )
    root = result.stdout.strip()
    if result.returncode != 0 or not root:
        return None
    return Path(root)


def _registry_base_path(registry: Path, repo: Path) -> str:
    """Return the registry's path relative to the GIT ROOT, as `git show` reads it.

    Relative to the git root, NOT to `--repo`. `git show <sha>:<path>` resolves
    `<path>` from the work tree root regardless of the cwd it is run in, so a
    `--repo`-relative path is only correct when `--repo` happens to BE the root.
    That holds in a single-project repo, which is why this was invisible: there
    the two coincide. In a nested project they do not, and the old path named a
    real file at the root that is a DIFFERENT registry — so `compare()` measured
    one project's registry against another's and reported every record of the
    root's registry as an undeclared removal. Measured (J49, HemaSuite
    2026-08-29): a sub-project verify returned `FAIL undeclared_removals=5`,
    naming five records of a feature with zero records in the file being
    compared, where the truth was `PASS registered=23 verified=23`.

    A registry outside the work tree is refused rather than silently falling back
    to `DEFAULT_REGISTRY`, which was the same defect by a shorter route: an
    unrelated file compared with a straight face.

    With no work tree at all there is no root to be relative to, so the
    `--repo`-relative path stands. Nothing reads it: `load_base` runs
    `git rev-parse` first and refuses a non-repo there.
    """
    root = _git_root(repo)
    base = root if root is not None else repo
    try:
        return registry.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        if root is None:
            return DEFAULT_REGISTRY
        raise RegistryError(
            f"registry {registry} is outside the git work tree {root}; "
            "refusing to guess a base path for it"
        ) from None


def registry_notice(registry: Path, repo: Path) -> tuple[str, str | None]:
    """`(absolute path actually used, ambiguity warning or None)` — #33.

    `DEFAULT_REGISTRY` is RELATIVE and nothing resolves it, so two byte-identical
    invocations from two directories in one repo write two different files and
    echo the same token: `registry=.h-mad/wires.jsonl` either way. Measured on
    HemaSuite, which currently carries two live registries that differ —
    `/…/HemaSuite/.h-mad/wires.jsonl` and
    `/…/HemaSuite/hematology-paper-writer/.h-mad/wires.jsonl`.

    NOT fixed by resolving the default against the git root, which is the obvious
    move and re-creates J49. `_registry_base_path`'s docstring records what that
    cost: a sub-project `verify` compared its registry against a DIFFERENT one at
    the root and returned `FAIL undeclared_removals=5` where the truth was
    `PASS registered=23 verified=23`. A nested project's own registry is a
    SUPPORTED configuration, so forcing every default onto the root would
    consolidate two deliberately separate registries.

    The defect is not that the default points at the wrong file. It is that WHICH
    file was used is invisible. So: name the resolved path, and warn — never
    refuse — when the relative default was used while a different registry also
    exists at the git root. That is exactly the HemaSuite situation, and a refusal
    would break the supported nested case.
    """
    used = registry.resolve()
    if registry.is_absolute():
        return str(used), None
    root = _git_root(repo)
    if root is None:
        return str(used), None
    at_root = (root / DEFAULT_REGISTRY).resolve()
    if at_root == used or not at_root.exists():
        return str(used), None
    return str(used), (
        f"[H-MAD] wire_registry ambiguous_default: used {used}, but a different "
        f"registry also exists at {at_root}. A relative --registry resolves "
        f"against the CWD, so this command writes a different file depending on "
        f"where it is run. A nested registry is legitimate (see J49), so this is "
        f"a warning; pass --registry <abs path> to be explicit."
    )


def trackedness(path: Path, repo: Path) -> tuple[bool, str | None]:
    try:
        display = path.relative_to(repo).as_posix()
    except ValueError:
        display = str(path)
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", display], cwd=repo, check=False,
        capture_output=True, text=True,
    ).returncode == 0
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", display], cwd=repo, check=False,
        capture_output=True, text=True,
    ).returncode == 0
    if ignored:
        return False, f"add !{display} to .gitignore (then git add {display})"
    if not tracked:
        return False, f"git add {display}"
    return True, None


def verify(
    registry: Path,
    base: str,
    rootdir: Path,
    repo: Path,
    testpaths: tuple[Path, ...] | list[Path] = DEFAULT_TESTPATHS,
    python: str = sys.executable,
    *,
    probe_interpreter: bool = False,
) -> dict:
    if not registry.exists():
        return {
            "verdict": "PASS", "registered": 0, "verified": 0, "broken": 0,
            "missing": 0, "ambiguous": 0, "unverified_renames": 0, "undeclared_removals": 0,
            "unverifiable": 0,
            "token": "WIREREG: PASS registered=0 verified=0 broken=0 missing=0 ambiguous=0 unverified_renames=0 undeclared_removals=0 unverifiable=0",
            "remedy": None,
        }
    if probe_interpreter and not _interpreter_has_pytest(python):
        # Mirror assemble_tdd's candidates, bounding every probe here.
        suggestions = [
            candidate for candidate in (
                sys.executable, "python3.13", "python3.12", "python3.11",
                "/opt/homebrew/bin/python3", "/usr/bin/python3",
            ) if candidate != python and _interpreter_has_pytest(candidate)
        ]
        return {
            "verdict": "UNREADABLE",
            "token": f"WIREREG: UNREADABLE reason=interpreter-has-no-pytest python={python}",
            "remedy": f"Hint: use --python {suggestions[0]}" if suggestions else None,
        }
    tracked, remedy = trackedness(registry, repo)
    head = load(registry)
    base_records = load_base(base, _registry_base_path(registry, repo), repo)
    # `load()` only parses JSON, so a hand-edited record never met `register`'s
    # validation: refuse a bad runner HERE, or it parks a real FAIL in
    # `unverifiable` and 5f reads PASS. A RegistryError reports UNREADABLE.
    for record in head:
        problem = runner_problem(record)
        if problem:  # M:RUNNER-READ
            raise RegistryError(
                f"{record.get('owning_feature')}::{record.get('id')}: {problem}")
        if "runner" in record:
            # A runner record is new with this field, so it gets the whole
            # write-time validation: a playwright record with NO pin otherwise
            # read PASS-with-unverifiable, where the same record without a runner
            # crashed. Older records keep `load()`'s parse-only contract.
            try:
                validate_record(dict(record))
            except RegistryError as exc:
                raise RegistryError(
                    f"{record.get('owning_feature')}::{record.get('id')}: {exc}") from None
    # Split BEFORE partition: a pin with no resolver here can never appear in the
    # pytest collection, so letting it reach `partition` reports it `missing` by
    # construction. `compare` below still sees every head record, so removing an
    # unverifiable record without a tombstone is caught like any other.
    judgeable = [record for record in head if record_runner(record) in RESOLVED_RUNNERS]
    unverifiable = [
        record for record in head
        if record_runner(record) not in RESOLVED_RUNNERS
        and (record.get("status", "active") == "active"
             or record.get("removal_provenance") == "renamed")
    ]
    collected = collect(rootdir, testpaths, python)
    resolving, missing, ambiguous, unverified_renames = partition(judgeable, collected)
    verified, broken = run_pins(resolving, rootdir, python)
    undeclared = [record for record in compare(base_records, head) if record.get("status", "active") == "active"]

    drivers: list[str] = []
    if broken:
        for record in broken:
            for label in pin_labels(record, record.get("broken_pins", [])):
                drivers.append(f"step5f:wire_regression:{label}")
    if missing:
        for record in missing:
            for label in pin_labels(record, unresolved_pins(record, collected)):
                drivers.append(f"step5f:wire_pin_missing:{label}")
    if ambiguous:
        for record in ambiguous:
            field = "pin" if record.get("status", "active") == "active" else "successor_pin"
            for label in pin_labels(record, unresolved_pins(record, collected, field)):
                drivers.append(f"step5f:wire_pin_ambiguous:{label}")
    if undeclared:
        for record in undeclared:
            drivers.append(f"step5f:undeclared_removal:{_record_label(record)}")
    if unverified_renames:
        for record in unverified_renames:
            drivers.append(f"step5f:unverified_rename:{_record_label(record)}")
    # A wire judged at base that is unjudged at head under the same identity is
    # a removal in disguise: no tombstone, and its regression stops being seen.
    judged_at_base = {
        _record_key(record) for record in base_records
        if record.get("status", "active") == "active" and record_runner(record) in RESOLVED_RUNNERS
    }
    for record in unverifiable:
        if _record_key(record) in judged_at_base:  # M:RUNNER-DOWNGRADE
            drivers.append(f"step5f:runner_downgraded:{_record_label(record)}")
    if not tracked:
        drivers.append("step5f:registry_untracked")
    for reason in drivers:
        print(f"[H-MAD] {reason}")
    # Named, never a driver: cannot-judge is not a regression, and a PASS
    # carrying unverifiable>0 says only that the judged records held.
    for record in unverifiable:
        print(f"[H-MAD] step5f:wire_pin_unverifiable:{_record_label(record)} runner={record_runner(record)}")
    verdict = "UNTRACKED" if not tracked else "FAIL" if drivers else "PASS"
    token = (
        f"WIREREG: {verdict} registered={len(head)} verified={len(verified)} "
        f"broken={len(broken)} missing={len(missing)} "
        f"ambiguous={len(ambiguous)} "
        f"unverified_renames={len(unverified_renames)} undeclared_removals={len(undeclared)} "
        f"unverifiable={len(unverifiable)}"
    )
    return {
        "verdict": verdict, "registered": len(head), "verified": len(verified),
        "broken": len(broken), "missing": len(missing), "ambiguous": len(ambiguous),
        "unverified_renames": len(unverified_renames), "undeclared_removals": len(undeclared),
        "unverifiable": len(unverifiable), "unverifiable_records": unverifiable,
        "token": token, "remedy": remedy,
        "verified_records": verified, "broken_records": broken, "missing_records": missing,
        "ambiguous_records": ambiguous,
        "unverified_rename_records": unverified_renames, "undeclared_removal_records": undeclared,
    }


def _interpreter_has_pytest(python: str) -> bool:
    try:
        return subprocess.run(
            [python, "-c", "import pytest"], capture_output=True, timeout=30,
        ).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--registry", type=Path, default=Path(DEFAULT_REGISTRY))
    verify_parser.add_argument("--base")
    verify_parser.add_argument(
        "--rootdir", type=Path, default=Path("."),
        help="repository root used as pytest cwd (default: .)",
    )
    verify_parser.add_argument("--repo", type=Path, default=Path("."))
    verify_parser.add_argument(
        "--testpath", type=Path, action="append", dest="testpaths",
        help="test path passed to pytest; repeatable (default: h-mad/tests)",
    )
    verify_parser.add_argument("--python", default=sys.executable)
    register_parser = subparsers.add_parser("register")
    register_parser.add_argument("--registry", type=Path, default=Path(DEFAULT_REGISTRY))
    register_parser.add_argument("--id", required=True)
    register_parser.add_argument("--caller", required=True)
    register_parser.add_argument("--callee", required=True)
    register_parser.add_argument("--pin", required=True, action="append", metavar="PIN")
    register_parser.add_argument("--feature", required=True)
    register_parser.add_argument(
        "--repo", type=Path, default=Path("."),
        help="repository root, used only to detect the ambiguous-default case (#33)")
    challenge_parser = subparsers.add_parser("challenge")
    challenge_parser.add_argument("--base")
    challenge_parser.add_argument("--impl-plan", type=Path, default=Path(".h-mad/impl-plan.md"))
    challenge_parser.add_argument("--boundaries", type=Path, default=Path(".h-mad/boundaries.json"))
    challenge_parser.add_argument("--ack", "--ack-file", dest="ack", type=Path, default=Path(".h-mad/audit.md"))
    challenge_parser.add_argument("--repo", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    if args.command == "challenge":
        if not args.base:
            print("challenge requires --base", file=sys.stderr)
            return 2
        try:
            result = challenge(args.base, args.impl_plan, args.boundaries, args.ack, args.repo)
        except (OSError, RegistryError, SyntaxError) as exc:
            print(f"[H-MAD] wire_challenge UNREADABLE: {exc}")
            return 2
        print(result["token"])
        for detail in result.get("details", []):
            print(detail)
        return 0
    if args.command == "register":
        from h_mad_assemble_tdd import misrooted_candidates

        try:
            stored = register([{
                "kind": "wire", "id": args.id, "caller": args.caller,
                "callee": args.callee,
                "pin": args.pin[0] if len(args.pin) == 1 else args.pin,
                "owning_feature": args.feature,
            }], args.registry)
        except (OSError, RegistryError) as exc:
            print(f"[H-MAD] wire_registry UNREADABLE: {exc}")
            return 2
        for pin in args.pin:
            pin_file, separator, test = pin.partition("::")
            if separator and not (args.repo / pin_file).exists():
                candidates = misrooted_candidates(args.repo, pin_file)
                if candidates:
                    print(
                        f"WARNING: pin is not repo-relative: {pin} "
                        f"(did you mean {candidates[0]}::{test}?)",
                        file=sys.stderr,
                    )
        used, warning = registry_notice(args.registry, args.repo)
        if warning:
            print(warning)
        print(f"WIREREG: REGISTER registered={len(stored)} registry={used}")
        return 0
    if args.command != "verify":
        return 0
    if not args.base:
        print("verify requires --base", file=sys.stderr)
        return 2
    used, warning = registry_notice(args.registry, args.repo)
    print(f"[H-MAD] wire_registry using={used}")
    if warning:
        print(warning)
    try:
        result = verify(
            args.registry, args.base, args.rootdir, args.repo,
            args.testpaths if args.testpaths is not None else DEFAULT_TESTPATHS,
            python=args.python,
            probe_interpreter=True,
        )
    except (OSError, RegistryError) as exc:
        print(f"[H-MAD] wire_registry UNREADABLE: {exc}")
        return 2
    print(result["token"])
    if result.get("remedy"):
        print(result["remedy"])
    return 2 if result["verdict"] == "UNREADABLE" else 0


if __name__ == "__main__":
    sys.exit(main())
