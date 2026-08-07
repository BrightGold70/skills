#!/usr/bin/env python3
"""h_mad_wire_registry.py — Phase-5d registry schema and JSONL loader."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

VALID_KINDS: frozenset[str] = frozenset({"wire"})
VALID_PROVENANCE: frozenset[str] = frozenset({"superseded", "pinned-a-defect", "renamed"})
DEFAULT_REGISTRY = ".h-mad/wires.jsonl"


class RegistryError(Exception):
    """Malformed registry content — a cannot-judge, never a verdict."""


def validate_record(record: dict) -> dict:
    """Return the record, or raise RegistryError naming the offending field."""
    if not isinstance(record, dict):
        raise RegistryError("record must be an object")
    required = ("kind", "id", "caller", "callee", "pin", "owning_feature", "registered_ts")
    for field in required:
        if field not in record or record[field] in (None, ""):
            raise RegistryError(f"missing required field: {field}")
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
        if provenance == "renamed" and not record.get("successor_pin"):
            raise RegistryError("missing successor_pin")
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
            if existing["id"] == record["id"]:
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
    """Return BASE records whose ids are absent at HEAD."""
    head_ids = {record["id"] for record in head_records}
    return [record for record in base_records if record["id"] not in head_ids]


def partition(
    records: list[dict], collected: set[str]
) -> tuple[list[dict], list[dict], list[dict]]:
    """-> (resolving, missing, unverified_renames). Pure; no subprocess, no git."""
    resolving: list[dict] = []
    missing: list[dict] = []
    unverified_renames: list[dict] = []
    for record in records:
        if record.get("status", "active") == "active":
            if record["pin"] in collected:
                resolving.append(record)
            else:
                missing.append(record)
            continue
        if record.get("removal_provenance") != "renamed":
            continue
        successor = record["successor_pin"]
        if successor in collected:
            resolved = dict(record)
            resolved["pin"] = successor
            resolving.append(resolved)
        else:
            unverified_renames.append(record)
    return resolving, missing, unverified_renames


DEFAULT_TESTPATHS = (Path("h-mad/tests"),)


def collect(repo: Path, testpaths: tuple[Path, ...] | list[Path]) -> set[str]:
    """Collect repo-relative pytest node ids from the requested test paths."""
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest", *[str(path) for path in testpaths],
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
            f"pytest collection failed with exit code {result.returncode}; "
            f"stdout (last 20 lines): {stdout_tail}; "
            f"stderr (last 20 lines): {stderr_tail}"
        )
    node_ids: set[str] = set()
    for line in result.stdout.splitlines():
        line = line.strip()
        if "::" in line and not line.endswith(" tests collected"):
            node_ids.add(line)
    return node_ids


def run_pins(resolving: list[dict], repo: Path) -> tuple[list[dict], list[dict]]:
    """Run resolving pytest pins and return (verified, broken)."""
    if not resolving:
        return [], []
    pins = [record["pin"] for record in resolving]
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-rA", *pins],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    passed: set[str] = set()
    failed: set[str] = set()
    for line in result.stdout.splitlines():
        match = re.match(r"^(PASSED|FAILED)\s+(\S+)", line.strip())
        if not match:
            continue
        (passed if match.group(1) == "PASSED" else failed).add(match.group(2))

    verified: list[dict] = []
    broken: list[dict] = []
    for record in resolving:
        pin = record["pin"]
        if pin in failed:
            broken.append(record)
            print(f"BROKEN {record['owning_feature']}: {pin}")
        elif pin in passed:
            verified.append(record)
        else:
            print(f"INTERNAL INCONSISTENCY: unclassified pin {pin}")
    return verified, broken


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
) -> dict:
    if not registry.exists():
        return {
            "verdict": "PASS", "registered": 0, "verified": 0, "broken": 0,
            "missing": 0, "unverified_renames": 0, "undeclared_removals": 0,
            "token": "WIREREG: PASS registered=0 verified=0 broken=0 missing=0 unverified_renames=0 undeclared_removals=0",
            "remedy": None,
        }
    tracked, remedy = trackedness(registry, repo)
    head = load(registry)
    base_records = load_base(base, DEFAULT_REGISTRY, repo)
    collected = collect(rootdir, testpaths)
    resolving, missing, unverified_renames = partition(head, collected)
    verified, broken = run_pins(resolving, rootdir)
    undeclared = [record for record in compare(base_records, head) if record.get("status", "active") == "active"]

    drivers: list[str] = []
    if broken:
        for record in broken:
            drivers.append(f"step5f:wire_regression:{record['id']}")
    if missing:
        for record in missing:
            drivers.append(f"step5f:wire_pin_missing:{record['id']}")
    if undeclared:
        for record in undeclared:
            drivers.append(f"step5f:undeclared_removal:{record['id']}")
    if unverified_renames:
        for record in unverified_renames:
            drivers.append(f"step5f:unverified_rename:{record['id']}")
    if not tracked:
        drivers.append("step5f:registry_untracked")
    for reason in drivers:
        print(f"[H-MAD] {reason}")
    verdict = "UNTRACKED" if not tracked else "FAIL" if drivers else "PASS"
    token = (
        f"WIREREG: {verdict} registered={len(head)} verified={len(verified)} "
        f"broken={len(broken)} missing={len(missing)} "
        f"unverified_renames={len(unverified_renames)} undeclared_removals={len(undeclared)}"
    )
    return {
        "verdict": verdict, "registered": len(head), "verified": len(verified),
        "broken": len(broken), "missing": len(missing),
        "unverified_renames": len(unverified_renames), "undeclared_removals": len(undeclared),
        "token": token, "remedy": remedy,
        "verified_records": verified, "broken_records": broken, "missing_records": missing,
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
    subparsers.add_parser("register")
    subparsers.add_parser("challenge")
    args = parser.parse_args(argv)
    if args.command != "verify":
        return 0
    if not args.base:
        print("verify requires --base", file=sys.stderr)
        return 2
    try:
        result = verify(
            args.registry, args.base, args.rootdir, args.repo,
            args.testpaths if args.testpaths is not None else DEFAULT_TESTPATHS,
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
