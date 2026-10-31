#!/usr/bin/env python3
"""Scan named tool-call paths using the D19 lexical containment rules."""

from __future__ import annotations

import argparse
import json
import os
import posixpath
import re
from pathlib import Path
from urllib.parse import quote


class UsageError(Exception):
    """An invalid scan invocation."""


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise UsageError(message)


def named_paths(strings: list[str], home: str) -> list[str]:
    """Extract the four path spellings, expand home, and fold dot components."""
    tilde = r"~/"  # M:TOOLSCAN-SPELL-TILDE
    home_var = r"\$HOME/"  # M:TOOLSCAN-SPELL-HOME
    brace = r"\$\{HOME\}/"  # M:TOOLSCAN-SPELL-BRACE
    prefix = "|".join((tilde, home_var, brace, r"/[A-Za-z0-9._-]+"))
    pattern = re.compile(
        r"(?:^|(?<=[\s\"'`=(<>|;&,\[{]))(" + prefix
        + r")[^\s\"'`;|&<>(){}\[\],]*"
    )
    paths = []
    for string in strings:
        for match in pattern.finditer(string):
            path = match.group()
            for spelling in ("~/", "$HOME/", "${HOME}/"):
                if path.startswith(spelling):
                    path = home.rstrip("/") + "/" + path[len(spelling):]
                    break
            paths.append(posixpath.normpath(path))
    return paths


def _below(path: str, directory: str) -> bool:
    return path == directory or path.startswith(directory.rstrip("/") + "/")


def _base(value: str) -> str:
    """Normalise a comparison base as `named_paths` normalises a path, without a trailing `/`."""
    if not value:  # M:TOOLSCAN-BASE-EMPTY
        return ""
    value = posixpath.normpath(value)  # M:TOOLSCAN-BASE-NORMPATH
    if value.startswith("//"):  # M:TOOLSCAN-BASE-LEADING
        value = value[1:]
    return value.rstrip("/")  # M:TOOLSCAN-BASE-STRIP


def classify_path(path: str, surface: str, *, root: str, home: str) -> str:
    """Classify one normalized path without inspecting the filesystem."""
    if _below(path, root):  # M:TOOLSCAN-INSIDE
        return "inside"
    if _below(path, "/dev"):  # M:TOOLSCAN-DEV
        return "exempt"
    if surface == "grok":  # M:TOOLSCAN-GROK-ONLY
        own_session = home.rstrip("/") + "/.grok/sessions/" + quote(root, safe="")
        if _below(path, own_session):  # M:TOOLSCAN-OWN-SESSION
            return "exempt"
        if _below(path, home.rstrip("/") + "/.grok/skills"):  # M:TOOLSCAN-SKILLS
            return "exempt"
    return "out"


_GROK_PAYLOAD_ARGS: dict[str, frozenset[str]] = {  # M:TOOLSCAN-PAYLOAD-ARGS
    "grep": frozenset({"pattern"}),
    "write": frozenset({"content"}),
    "search_replace": frozenset({"old_string", "new_string"}),
}


def _strings(value) -> list[str]:
    strings = []
    pending = [value]
    while pending:
        item = pending.pop()
        if isinstance(item, str):
            strings.append(item)
        elif isinstance(item, dict):
            pending.extend(reversed(list(item.values())))
        elif isinstance(item, list):
            pending.extend(reversed(item))
    return strings


def _keyed_strings(value, key: str) -> list[tuple[str, str]]:
    """`_strings`, in the same order, each string paired with its argument key path."""
    strings = []
    pending = [(key, value)]
    while pending:
        key, item = pending.pop()
        if isinstance(item, str):
            strings.append((key, item))
        elif isinstance(item, dict):
            pending.extend(reversed([(f"{key}.{name}", child) for name, child in item.items()]))
        elif isinstance(item, list):
            pending.extend(reversed([(f"{key}[{index}]", child) for index, child in enumerate(item)]))
    return strings


def _ndjson_calls(text: str, surface: str):
    """Calls as (start line, tool name, [(argument key, string)]) triples."""
    calls = []
    grouped = {}
    origins = {}
    nonjson = events = 0
    for number, line in enumerate(text.splitlines(), 1):
        try:
            event = json.loads(line)
        except (ValueError, RecursionError):
            nonjson += 1
            continue  # M:TOOLSCAN-NONJSON
        if not isinstance(event, dict):
            continue
        events += 1
        if surface == "grok" and event.get("type") == "tool_call":
            raw_input = event.get("rawInput")
            payload = _GROK_PAYLOAD_ARGS.get(event.get("toolName"))
            if payload is not None and isinstance(raw_input, dict):
                raw_input = {key: value for key, value in raw_input.items() if key not in payload}  # M:TOOLSCAN-PAYLOAD-ARGS
            calls.append((number, event.get("toolName"),
                          _keyed_strings(raw_input, "rawInput") + _keyed_strings(event.get("locations"), "locations")))
        elif surface == "agy" and event.get("event") == "step_update":
            step = event.get("step_update")
            if not isinstance(step, dict) or step.get("step_type") != "tool":
                continue
            key = (step.get("conversation_id"), step.get("step_index"))  # M:TOOLSCAN-AGY-KEY
            info = step.get("tool_info")
            parameters = info.get("parameters") if isinstance(info, dict) else None
            origins.setdefault(key, (number, step.get("tool_name")))
            grouped.setdefault(key, []).extend(_keyed_strings(parameters, "parameters"))
    if surface == "agy":
        calls = [(*origins[key], strings) for key, strings in grouped.items()]
    return calls, nonjson, events


def _codex_calls(text: str):
    lines = text.splitlines()
    boundary = os.environ.get("HMAD_DISPATCH_BOUNDARY", "===HMAD-DISPATCH-BOUNDARY===")
    start = max((i + 1 for i, line in enumerate(lines) if line == boundary), default=0)  # M:TOOLSCAN-CODEX-BOUNDARY
    calls = []
    command = None
    mcp_unmeasured = 0
    exec_line = 0
    for number, line in enumerate(lines[start:], start + 1):
        if re.match(r"^tool [A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\(", line):
            mcp_unmeasured += 1
            continue
        if line == "exec":
            if command is not None:
                calls.append((exec_line, "exec", [("command", "\n".join(command))]))
            command = []
            exec_line = number
        elif line in ("codex", "thinking", "user") or re.match(
            r"^ (succeeded|exited -?[0-9]+|declined|failed)\b", line
        ):
            if command is not None:
                calls.append((exec_line, "exec", [("command", "\n".join(command))]))
                command = None
        elif command is not None:
            command.append(line)
    if command is not None:
        calls.append((exec_line, "exec", [("command", "\n".join(command))]))
    return calls, mcp_unmeasured


def _counted_as(path: str, *, checkout: str, needle_dirs: list[str], home: str) -> str:
    """Name why an out path counted: `out`, or the contamination that also counts it as checkout."""
    if _below(path, checkout):
        return "out:checkout"
    if any(needle + "/" in path for needle in needle_dirs):
        return "out:needle"
    if _below(path, home + "/.local/state/h-mad"):
        return "out:state_tree"
    if _below(path, home + "/.grok/sessions"):
        return "out:grok_sessions"
    return "out"


def scan_log(text: str, surface: str, *, root: str, checkout: str,
             home: str, needle_dirs: list[str]) -> dict:
    """Return per-call counts and the surface's verdict word."""
    if surface not in ("grok", "agy", "codex"):
        raise UsageError("unknown surface")
    # Once, here, as the paths are normalised: the checks below append `/` to a base, and
    # `classify_path` quotes `root` into the own-session key. `/` becomes "", so `/` is appended once.
    home = _base(home)  # M:TOOLSCAN-BASE-HOME
    root = _base(root)  # M:TOOLSCAN-BASE-ROOT
    checkout = _base(checkout)  # M:TOOLSCAN-BASE-CHECKOUT
    needle_dirs = [_base(needle) for needle in needle_dirs]  # M:TOOLSCAN-BASE-NEEDLE
    result = dict(surface=surface, calls=0, out_of_root=0, checkout=0,
                  exempt=0, nonjson=0, mcp_unmeasured=0)
    if surface == "codex":
        calls, result["mcp_unmeasured"] = _codex_calls(text)
    else:
        calls, result["nonjson"], events = _ndjson_calls(text, surface)
        if surface == "grok" and events == 0:  # M:TOOLSCAN-NO-EVENT
            return dict(result, word="UNREADABLE", reason="no_event")
    result["calls"] = len(calls)
    explained = []
    for line, tool, strings in calls:
        # Per string, so each path keeps its key; `named_paths` matches each string alone anyway.
        keyed = [(key, path) for key, string in strings for path in named_paths([string], home)]
        paths = [path for _, path in keyed]
        classes = [classify_path(path, surface, root=root, home=home) for path in paths]
        if "out" in classes:  # M:TOOLSCAN-PER-CALL
            result["out_of_root"] += 1
            for (key, path), kind in zip(keyed, classes):
                entry = (line, tool, key, path, _counted_as(path, checkout=checkout,
                                                            needle_dirs=needle_dirs, home=home))
                if kind == "out" and entry not in explained:
                    explained.append(entry)
            outside = [path for path, kind in zip(paths, classes) if kind == "out"]
            in_checkout = any(_below(path, checkout) for path in outside)  # M:TOOLSCAN-CHECKOUT
            in_needle = any(needle + "/" in path for path in outside for needle in needle_dirs)  # M:TOOLSCAN-NEEDLE
            in_state_tree = any(_below(path, home + "/.local/state/h-mad") for path in outside)  # M:TOOLSCAN-STATE-TREE
            in_grok_sessions = any(_below(path, home + "/.grok/sessions") for path in outside)  # M:TOOLSCAN-SESSIONS-CONTAMINATION
            if in_checkout or in_needle or in_state_tree or in_grok_sessions:
                result["checkout"] += 1
        elif "exempt" in classes:
            result["exempt"] += 1
    word = "OUT_OF_ROOT" if result["out_of_root"] else "CLEAN"  # M:TOOLSCAN-OUT-OF-ROOT
    if surface in ("codex", "agy") and not calls:  # M:TOOLSCAN-CODEX-UNMEASURED
        word = "UNMEASURED"
    return dict(result, word=word, explained=explained)


def main(argv: list[str] | None = None) -> int:
    try:
        parser = _Parser(add_help=False, allow_abbrev=False)
        parser.add_argument("mode", choices=("scan",))
        parser.add_argument("--surface", choices=("grok", "codex", "agy"), required=True)
        for name in ("log", "root", "checkout", "home"):
            parser.add_argument("--" + name, required=True)
        parser.add_argument("--needle-dir", action="append", default=[])
        parser.add_argument("--explain", action="store_true")
        args = parser.parse_args(argv)
        try:
            text = Path(args.log).read_text(encoding="utf-8")
        except FileNotFoundError:
            print("TOOLSCAN: UNREADABLE reason=log_absent")  # M:TOOLSCAN-LOG-ABSENT
            return 2
        except (OSError, UnicodeError):
            print("TOOLSCAN: UNREADABLE reason=log_unreadable")  # M:TOOLSCAN-LOG-UNREADABLE
            return 2
        result = scan_log(text, args.surface, root=args.root, checkout=args.checkout,
                          home=args.home, needle_dirs=args.needle_dir)
        if result["word"] == "UNREADABLE":
            print("TOOLSCAN: UNREADABLE reason=" + result["reason"])
            return 2
        final = (f"mcp_unmeasured={result['mcp_unmeasured']}" if args.surface == "codex"
                 else f"nonjson={result['nonjson']}")
        exempt = result["exempt"]  # M:TOOLSCAN-TOKEN
        # Built before the token prints, so a failure here cannot add a second TOOLSCAN line. The
        # tool and key are agent-controlled: JSON-quoted, they cannot start a line of their own.
        # The token stays first and unchanged; a consumer that reads the LAST line (`require
        # toolscan`) must be given the scan without --explain.
        explain = [f"TOOLSCAN-EXPLAIN: line={line} tool={json.dumps(tool)} arg={json.dumps(key)} "
                   f"path={json.dumps(path)} class={kind}"
                   for line, tool, key, path, kind in result["explained"]] if args.explain else []
        print(f"TOOLSCAN: {result['word']} surface={args.surface} calls={result['calls']} "
              f"out_of_root={result['out_of_root']} checkout={result['checkout']} "
              f"exempt={exempt} {final}")
        for line in explain:
            print(line)
        return 0
    except Exception as exc:
        print(f"TOOLSCAN: UNREADABLE reason=internal:{type(exc).__name__}")  # M:TOOLSCAN-LAST-RESORT
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
