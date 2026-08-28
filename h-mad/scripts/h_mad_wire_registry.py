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

from h_mad_audit_gate import _acknowledged_from_text

VALID_KINDS: frozenset[str] = frozenset({"wire"})
VALID_PROVENANCE: frozenset[str] = frozenset({"superseded", "pinned-a-defect", "renamed"})
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


def unresolved_pins(record: dict, collected: set[str], field: str = "pin") -> list[str]:
    """The pins of `record` that do not resolve to exactly one collected node id."""
    offending: list[str] = []
    for pin in pins(record, field):
        if "::" in pin and pin in collected:
            continue
        if len([node for node in collected if node.endswith("::" + pin)]) != 1:
            offending.append(pin)
    return offending


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

    def resolve(pin: str) -> list[str]:
        if "::" in pin and pin in collected:
            return [pin]
        return [node_id for node_id in collected if node_id.endswith("::" + pin)]

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
            matches = resolve(pin)
            if len(matches) == 1:
                node_ids.append(matches[0])
            elif matches:
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
    result = subprocess.run(
        [python, "-m", "pytest", "-q", "-rA", "-vv", *all_pins],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
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


def _registry_base_path(registry: Path, repo: Path) -> str:
    """Return the registry's repo-relative POSIX path, or the default safely."""
    try:
        return registry.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return DEFAULT_REGISTRY


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
) -> dict:
    if not registry.exists():
        return {
            "verdict": "PASS", "registered": 0, "verified": 0, "broken": 0,
            "missing": 0, "ambiguous": 0, "unverified_renames": 0, "undeclared_removals": 0,
            "token": "WIREREG: PASS registered=0 verified=0 broken=0 missing=0 ambiguous=0 unverified_renames=0 undeclared_removals=0",
            "remedy": None,
        }
    tracked, remedy = trackedness(registry, repo)
    head = load(registry)
    base_records = load_base(base, _registry_base_path(registry, repo), repo)
    collected = collect(rootdir, testpaths, python)
    resolving, missing, ambiguous, unverified_renames = partition(head, collected)
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
    if not tracked:
        drivers.append("step5f:registry_untracked")
    for reason in drivers:
        print(f"[H-MAD] {reason}")
    verdict = "UNTRACKED" if not tracked else "FAIL" if drivers else "PASS"
    token = (
        f"WIREREG: {verdict} registered={len(head)} verified={len(verified)} "
        f"broken={len(broken)} missing={len(missing)} "
        f"ambiguous={len(ambiguous)} "
        f"unverified_renames={len(unverified_renames)} undeclared_removals={len(undeclared)}"
    )
    return {
        "verdict": verdict, "registered": len(head), "verified": len(verified),
        "broken": len(broken), "missing": len(missing), "ambiguous": len(ambiguous),
        "unverified_renames": len(unverified_renames), "undeclared_removals": len(undeclared),
        "token": token, "remedy": remedy,
        "verified_records": verified, "broken_records": broken, "missing_records": missing,
        "ambiguous_records": ambiguous,
        "unverified_rename_records": unverified_renames, "undeclared_removal_records": undeclared,
    }


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
        print(f"WIREREG: REGISTER registered={len(stored)} registry={args.registry}")
        return 0
    if args.command != "verify":
        return 0
    if not args.base:
        print("verify requires --base", file=sys.stderr)
        return 2
    try:
        result = verify(
            args.registry, args.base, args.rootdir, args.repo,
            args.testpaths if args.testpaths is not None else DEFAULT_TESTPATHS,
            python=args.python,
        )
    except (OSError, RegistryError) as exc:
        print(f"[H-MAD] wire_registry UNREADABLE: {exc}")
        return 2
    print(result["token"])
    if result.get("remedy"):
        print(result["remedy"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
