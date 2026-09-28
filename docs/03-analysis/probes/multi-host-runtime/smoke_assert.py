#!/usr/bin/env python3
"""Assertions and committed rehearsal for the multi-host live smoke (design D10)."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path


HERE = Path(__file__).resolve().parent
SCRIPT = re.compile(r"h_mad_[a-z0-9_]+\.py$")
MODULE = re.compile(r"h_mad_[a-z0-9_]+$")
PYTHON = re.compile(r"python(3(\.\d+)?)?$")
MENTION = re.compile(r"(?<![A-Za-z0-9_])h_mad_[a-z0-9_]+\.py\b|(?<![\w-])hmad-dispatch\b")
ASSIGN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=.*", re.S)
REDIRECT = re.compile(r"[<>&|]*[<>][<>&|]*")
PUNCT = set(";&|<>()\n")
SEPARATOR = set(";&|()\n")
CODEX_LINE = re.compile(r"^\S+ -lc .* in \S+$")


class ShapeError(Exception):
    pass


@dataclass
class Event:
    tool: str
    value: str | list[str]
    success: bool
    output: str | None
    output_bad: bool = False


@dataclass
class Command:
    kind: str
    tokens: list[str]
    assignments: list[str]
    name: str = ""


def strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for v in value.values() for s in strings(v)]
    if isinstance(value, list):
        return [s for v in value for s in strings(v)]
    return []


def ndjson(path: Path) -> list[dict]:
    rows = []
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if line.startswith("#hmad-beat "):
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            raise ShapeError(f"unparseable line {number}") from None
        if not isinstance(row, dict):
            raise ShapeError(f"unparseable line {number}")
        rows.append(row)
    return rows


def grok_events(rows: list[dict]) -> tuple[list[Event], bool]:
    updates: dict[str, dict] = {}
    listed = False
    for row in rows:
        if row.get("type") == "available_commands":
            commands = row.get("commands")
            listed |= isinstance(commands, list) and "h-mad" in [c for c in commands if isinstance(c, str)]
        if row.get("type") == "tool_call_update" and row.get("status") == "completed":
            updates[row.get("toolCallId")] = row
    events = []
    for row in rows:
        if row.get("type") != "tool_call":
            continue
        tool = row.get("toolName")
        if tool not in ("run_terminal_command", "read_file"):
            continue
        raw = row.get("rawInput")
        value = raw.get("command" if tool == "run_terminal_command" else "target_file") if isinstance(raw, dict) else None
        if not isinstance(value, str):
            raise ShapeError("grok input shape unobserved")
        update = updates.get(row.get("toolCallId"))
        raw_output = update.get("rawOutput") if update else None
        output = "\n".join(strings(raw_output)) if raw_output is not None else None
        events.append(Event("shell" if tool == "run_terminal_command" else "read", value,
                            update is not None, output, update is not None and not isinstance(output, str)))
    return events, listed


def agy_events(rows: list[dict]) -> tuple[list[Event], bool]:
    done: dict[object, dict] = {}
    for row in rows:
        step = row.get("step_update")
        if row.get("event") == "step_update" and isinstance(step, dict) and step.get("state") == "DONE":
            done[step.get("step_index")] = step
    events = []
    seen = set()
    for row in rows:
        step = row.get("step_update")
        if row.get("event") != "step_update" or not isinstance(step, dict) or step.get("step_type") != "tool":
            continue
        index = step.get("step_index")
        if index in seen:
            continue
        seen.add(index)
        tool = step.get("tool_name")
        if tool not in ("run_command", "view_file"):
            continue
        info = step.get("tool_info")
        params = info.get("parameters") if isinstance(info, dict) else None
        value = params.get("CommandLine") if isinstance(params, dict) and tool == "run_command" else strings(params)
        if tool == "run_command" and not isinstance(value, str) or tool == "view_file" and not isinstance(params, dict):
            raise ShapeError("agy input shape unobserved")
        finish = done.get(index)
        end_info = finish.get("tool_info") if finish else None
        output = end_info.get("output") if isinstance(end_info, dict) else None
        events.append(Event("shell" if tool == "run_command" else "read", value, finish is not None,
                            output if isinstance(output, str) else None,
                            finish is not None and not isinstance(output, str)))
    return events, False


def codex_events(path: Path) -> tuple[list[Event], bool]:
    lines = path.read_text().splitlines()
    starts = [i for i, line in enumerate(lines) if line == "exec"]
    events = []
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(lines)
        body = [line for line in lines[start + 1:end] if not line.startswith("#hmad-beat ")]
        if not body or not CODEX_LINE.match(body[0]):
            raise ShapeError("codex input shape unobserved")
        success = len(body) > 1 and body[1].startswith(" succeeded in")
        events.append(Event("shell", body[0], success, "\n".join(body[2:]) if success else None))
    return events, False


def names_file(value: str, host: str, skill: bool) -> bool:
    filename = "SKILL.md" if skill else f"references/{host}-runtime.md"
    forms = [f"h-mad/{filename}", f"$HMAD_SKILL_ROOT/{filename}", f"${{HMAD_SKILL_ROOT}}/{filename}"]
    return any(value == form or value.endswith("/" + form) for form in forms)


def simple_tokens(text: str) -> list[list[str]]:
    lexer = shlex.shlex(text, posix=True, punctuation_chars=";&|<>()\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    lexer.commenters = ""
    tokens = list(lexer)
    commands: list[list[str]] = []
    current: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if REDIRECT.fullmatch(token):
            if current and current[-1].isdigit():
                current.pop()
            index += 2
            continue
        if token in ("<(", ">(") or token and set(token) <= SEPARATOR:
            if current:
                commands.append(current)
                current = []
        elif token and set(token) <= PUNCT:
            current.append("\0" + token)
        else:
            current.append(token)
        index += 1
    if current:
        commands.append(current)
    return commands


def sed_safe(args: list[str]) -> bool:
    allowed = {"-n", "--quiet", "--silent", "-E", "-r"}
    scripts = []
    i = 0
    while i < len(args):
        item = args[i]
        if item in ("-e", "--expression"):
            i += 1
            if i >= len(args):
                return False
            scripts.append(args[i])
        elif item.startswith("-"):
            if item not in allowed:
                return False
        elif not scripts:
            scripts.append(item)
            break
        i += 1
    return bool(scripts) and all(re.fullmatch(r"(\d+|\$)?(,(\d+|\$))?p", s) for s in scripts)


def classify(tokens: list[str], depth: int = 0) -> list[Command]:
    assignments = []
    while tokens and ASSIGN.fullmatch(tokens[0]):
        assignments.append(tokens.pop(0))
    if not tokens:
        return []
    name = Path(tokens[0]).name
    args = tokens[1:]
    if any(t.startswith("\0") for t in tokens):
        return [Command("unknown", tokens, assignments, name)]
    if name in ("bash", "sh", "zsh"):
        for i, item in enumerate(args):
            if re.fullmatch(r"-[A-Za-z]*c[A-Za-z]*", item):
                if depth >= 2 or i + 1 >= len(args):
                    return [Command("unknown", tokens, assignments, name)]
                inner = [c for part in simple_tokens(args[i + 1]) for c in classify(part, depth + 1)]
                for command in inner:
                    command.assignments = assignments + command.assignments
                return inner
    if PYTHON.fullmatch(name):
        for i, item in enumerate(args):
            if item == "-m" and i + 1 < len(args) and MODULE.fullmatch(args[i + 1].split(".")[-1]):
                return [Command("script", tokens, assignments, name)]
            if item.startswith("-m") and MODULE.fullmatch(item[2:].split(".")[-1]):
                return [Command("script", tokens, assignments, name)]
        operand = next((a for a in args if not a.startswith("-")), "")
        if SCRIPT.fullmatch(Path(operand).name):
            return [Command("script", tokens, assignments, name)]
    if SCRIPT.fullmatch(name):
        return [Command("script", tokens, assignments, name)]
    if re.fullmatch(r"hmad-dispatch(\.sh)?", name):
        return [Command("dispatch", tokens, assignments, name)]
    if name in ("bash", "sh", "zsh"):
        operand = next((a for a in args if not a.startswith("-")), "")
        if re.fullmatch(r"hmad-dispatch(\.sh)?", Path(operand).name):
            return [Command("dispatch", tokens, assignments, name)]
    safe = {"cat", "head", "tail", "nl", "sed", "grep", "rg", "ls", "test", "[", "echo", "printf", "wc", "stat"}
    if name in safe and (name != "sed" or sed_safe(args)) and (name != "rg" or not any(
            a.startswith("--pre") or a in ("-z", "--search-zip") or
            re.fullmatch(r"-[A-Za-z]+", a) and "z" in a for a in args)):
        return [Command("read" if name in {"cat", "head", "tail", "nl", "sed"} else "safe",
                        tokens, assignments, name)]
    return [Command("unknown", tokens, assignments, name)]


def needle(root: Path, host: str, skill: bool) -> str:
    path = root / "h-mad" / ("SKILL.md" if skill else f"references/{host}-runtime.md")
    return next((line for line in path.read_text().splitlines() if line.startswith("# ")), "")


def v111(host: str, log: Path, root: Path) -> tuple[str, int]:
    try:
        adapter, skill = needle(root, host, False), needle(root, host, True)
        if not adapter or not skill:
            return "UNREADABLE V-11.1 reason=no_needle", 2
        if adapter in (root / "h-mad/SKILL.md").read_text() or skill in (root / f"h-mad/references/{host}-runtime.md").read_text():
            return "UNREADABLE V-11.1 reason=needle_not_unique", 2
        if host == "codex":
            events, listed = codex_events(log)
        else:
            rows = ndjson(log)
            events, listed = grok_events(rows) if host == "grok" else agy_events(rows)
        read_adapter = read_skill = declared = script_before_adapter = adapter_seen = False
        for event in events:
            if event.tool == "read":
                paths = [event.value] if isinstance(event.value, str) else event.value
                for is_skill, heading in ((False, adapter), (True, skill)):
                    if any(names_file(p, host, is_skill) for p in paths):
                        if not is_skill:
                            if script_before_adapter and not read_adapter:
                                return "FAIL V-11.1 a script ran before the adapter was read", 0
                            adapter_seen = True
                        if event.success:
                            if event.output_bad:
                                return f"UNVERIFIED V-11.1 {host} output shape unobserved", 0
                            if event.output is not None and heading in event.output:
                                if is_skill:
                                    read_skill = True
                                else:
                                    read_adapter = True
                continue
            for tokens in simple_tokens(event.value):
                for command in classify(tokens.copy()):
                    mentioned = bool(MENTION.search(" ".join(command.tokens)))
                    if not read_adapter:
                        if command.kind in ("script", "dispatch"):
                            if adapter_seen:
                                return "FAIL V-11.1 a script ran before the adapter was read", 0
                            script_before_adapter = True
                        if command.kind == "unknown" and mentioned:
                            return "UNVERIFIED V-11.1 unclassified command before the adapter read", 0
                    if command.kind == "script" and f"HMAD_HOST={host}" in command.assignments:
                        declared = True
                    if command.kind == "read":
                        for is_skill, heading in ((False, adapter), (True, skill)):
                            if any(names_file(t, host, is_skill) for t in command.tokens[1:]):
                                if not is_skill:
                                    if script_before_adapter and not read_adapter:
                                        return "FAIL V-11.1 a script ran before the adapter was read", 0
                                    adapter_seen = True
                                if event.success:
                                    if event.output_bad:
                                        return f"UNVERIFIED V-11.1 {host} output shape unobserved", 0
                                    if event.output is not None and heading in event.output:
                                        if is_skill:
                                            read_skill = True
                                        else:
                                            read_adapter = True
        if not read_adapter:
            return "FAIL V-11.1 no adapter read", 0
        if host == "grok" and not listed:
            return "FAIL V-11.1 grok did not list h-mad", 0
        if not declared:
            return f"FAIL V-11.1 no script call declared HMAD_HOST={host}", 0
        if not read_skill:
            prefix = "UNVERIFIED" if host == "grok" else "FAIL"
            return f"{prefix} V-11.1 no observed SKILL.md read", 0
        return "PASS V-11.1", 0
    except ShapeError as exc:
        return f"UNVERIFIED V-11.1 {exc}", 0
    except (OSError, UnicodeError, ValueError) as exc:
        if isinstance(exc, ValueError):
            return "UNVERIFIED V-11.1 unparseable command", 0
        return "UNREADABLE V-11.1 reason=io", 2


def v112(out: Path, record_text: str, feature: str) -> tuple[str, int]:
    try:
        record = json.loads(record_text)
        lines = [line for line in out.read_text().splitlines() if line.startswith("HMAD-STATUS ")]
        if not isinstance(record, dict) or len(lines) != 1:
            return "FAIL V-11.2 status line count", 0
        match = re.fullmatch(r"HMAD-STATUS feature=(\S+) last_completed_phase=(.*?) halt_reason=(.*)", lines[0])
        if not match or match[1] != feature:
            return "FAIL V-11.2 status line mismatch", 0
        phase, reason = json.loads(match[2]), json.loads(match[3])
        if phase != record.get("last_completed_phase") or reason != record.get("halt_reason"):
            return "FAIL V-11.2 status line mismatch", 0
        return "PASS V-11.2", 0
    except (OSError, UnicodeError, json.JSONDecodeError):
        return "UNREADABLE V-11.2 reason=parse", 2


def rehearse() -> int:
    cases = json.loads((HERE / "rehearsal/cases.json").read_text())
    failures = 0
    for case in cases:
        if case["mode"] == "v111":
            actual, _ = v111(case["host"], HERE / "rehearsal" / case["log"], HERE.parents[3] / case["root"])
        else:
            actual, _ = v112(HERE / "rehearsal" / case["out"], json.dumps(case["record"]), case["feature"])
        print(f"{case['id']}: {actual}")
        failures += actual != case["expected"]
    print(f"REHEARSAL: {'FAIL' if failures else f'PASS n={len(cases)}'}")
    return int(bool(failures))


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)
    p111 = sub.add_parser("v111")
    p111.add_argument("--host", choices=("codex", "agy", "grok"), required=True)
    p111.add_argument("--log", type=Path, required=True)
    p111.add_argument("--root", type=Path, required=True)
    p112 = sub.add_parser("v112")
    p112.add_argument("--out", type=Path, required=True)
    p112.add_argument("--record", required=True)
    p112.add_argument("--feature", required=True)
    sub.add_parser("rehearse")
    args = parser.parse_args()
    if args.mode == "rehearse":
        return rehearse()
    result, code = v111(args.host, args.log, args.root) if args.mode == "v111" else v112(args.out, args.record, args.feature)
    print(result)
    return code


if __name__ == "__main__":
    sys.exit(main())
