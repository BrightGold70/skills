#!/usr/bin/env python3
"""Quarantine audit sessions and require the last containment verdict."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import sys


class UsageError(Exception):
    """An invalid containment invocation."""


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise UsageError(message)


def _names(directory: Path) -> list[str]:
    with os.scandir(directory) as entries:
        return [entry.name for entry in entries]


def _matches(name: str) -> bool:
    return "gas-root-" in name  # M:QUARANTINE-MATCH


def quarantine() -> int:
    try:
        home = Path(os.environ["HOME"]).absolute()
        store = home / ".grok/sessions"
        parent = home / ".local/state/h-mad/grok-audit-surface"
        names = [name for name in _names(store) if _matches(name)]
        parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        destination = parent / ("grok-quarantine-" + stamp)
        try:
            os.mkdir(destination)  # M:QUARANTINE-EXISTS
        except FileExistsError:
            print("QUARANTINE: REFUSED reason=quarantine_exists")
            return 0
        failed = moved = 0
        for name in names:
            try:
                os.rename(store / name, destination / name)  # M:QUARANTINE-MOVE
            except OSError:
                failed += 1
                continue
            moved += 1
            print(f"MOVED: {name}")
        if failed:  # M:QUARANTINE-MOVE-FAILED
            print(f"QUARANTINE: REFUSED reason=move_failed:{failed}")
            return 0
        residue = sum(_matches(name) for name in _names(store))
        if residue:  # M:QUARANTINE-RESIDUE
            print(f"QUARANTINE: REFUSED reason=residue:{residue}")
            return 0
        if len(_names(destination)) != len(names):  # M:QUARANTINE-COUNT-MISMATCH
            print("QUARANTINE: REFUSED reason=count_mismatch")
            return 0
        print(f"QUARANTINE: VERIFIED moved={moved} dest={destination}")
        return 0
    except OSError:
        print("QUARANTINE: REFUSED reason=unreadable")  # M:QUARANTINE-UNREADABLE
        return 0


def read_last_line(path: str) -> str:
    """Return only the final line, or no token for an unreadable file."""
    try:
        with open(path, encoding="utf-8") as stream:
            last = ""
            for line in stream:
                last = line.rstrip("\r\n")
            return last
    except (OSError, UnicodeError):
        return ""


def _append_halt(path: str | None, reason: str) -> None:
    if path is not None:
        descriptor = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        with os.fdopen(descriptor, "a", encoding="utf-8") as stream:
            stream.write(reason + "\n")


def require(args: argparse.Namespace) -> int:
    line = read_last_line(args.token_file)
    if args.verb == "toolscan":
        ok = line.startswith("TOOLSCAN: CLEAN surface=grok ")  # M:REQUIRE-OK-TOOLSCAN
    elif args.verb == "grok-canary":
        ok = line == "GROK-CANARY: PASS"  # M:REQUIRE-OK-CANARY
    else:
        ok = line.startswith("QUARANTINE: VERIFIED moved=")  # M:REQUIRE-OK-QUARANTINE
    if ok:
        print("REQUIRE: OK")
        return 0
    reason = line or f"no_token:{args.token_file}"  # M:REQUIRE-NO-TOKEN
    if args.verb == "toolscan":
        _append_halt(args.halt_file, reason)  # M:REQUIRE-TOOLSCAN-STOP
    print(f"REQUIRE: STOP reason={reason}")
    return 0


def _raw_halt_file(argv: list[str]) -> str | None:
    halt = None
    for index, token in enumerate(argv):
        if token == "--halt-file" and index + 1 < len(argv):
            halt = argv[index + 1]
        elif token.startswith("--halt-file="):
            halt = token.split("=", 1)[1]
    return halt


def _require_error(halt: str | None, reason: str) -> int:
    try:
        _append_halt(halt, reason)
    except Exception as exc:
        reason = f"internal:{type(exc).__name__}"
    print(f"REQUIRE: STOP reason={reason}")
    return 2


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    mode = argv[0] if argv else ""
    halt = _raw_halt_file(argv)  # M:REQUIRE-FAIL-CLOSED-ARGV
    try:
        parser = _Parser(add_help=False, allow_abbrev=False)
        commands = parser.add_subparsers(dest="mode", required=True)
        commands.add_parser("quarantine", add_help=False, allow_abbrev=False)
        consume = commands.add_parser("require", add_help=False, allow_abbrev=False)
        consume.add_argument("--verb", choices=("toolscan", "grok-canary", "quarantine"), required=True)
        consume.add_argument("--token-file", required=True)
        consume.add_argument("--halt-file")
        args = parser.parse_args(argv)
        if args.mode == "quarantine":
            return quarantine()
        halt = args.halt_file
        return require(args)
    except UsageError:
        if mode == "require":
            return _require_error(halt, "internal:UsageError")
        print("QUARANTINE: REFUSED reason=internal:UsageError")  # M:QUARANTINE-USAGE
        return 2
    except Exception as exc:
        if mode == "require":
            return _require_error(halt, f"internal:{type(exc).__name__}")  # M:REQUIRE-FAIL-CLOSED
        print(f"QUARANTINE: REFUSED reason=internal:{type(exc).__name__}")
        return 2  # M:QUARANTINE-LAST-RESORT


if __name__ == "__main__":
    raise SystemExit(main())
