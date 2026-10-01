#!/usr/bin/env python3
"""Assertions and committed rehearsal for the multi-host live smoke (design D10)."""

from __future__ import annotations

import argparse
import json
import os
import posixpath
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
# The only side-effect-free expansion is a plain parameter: $NAME or ${NAME}, not followed by a
# subscript (zsh evaluates $NAME[HOME=7] as math that assigns). Any other `$` (`$(`, `$[`,
# `${op`, `$NAME[`, special parameters) and any backtick can run or assign: an allowlist.
PLAIN_PARAM = re.compile(r"\$(?:[A-Za-z_][A-Za-z0-9_]*|\{[A-Za-z_][A-Za-z0-9_]*\})(?![A-Za-z0-9_\[])")


def active_expansion(text: str) -> bool:
    rest = PLAIN_PARAM.sub("", text)
    return "$" in rest or "`" in rest



class ShapeError(Exception):
    pass


@dataclass
class Event:
    tool: str
    value: str | list[str]
    success: bool
    output: str | None
    output_bad: bool = False
    cwd: str | None = None


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
    ids = [row.get("toolCallId") for row in rows if row.get("type") == "tool_call"]
    if len(ids) != len(set(ids)):
        raise ShapeError("grok input shape unobserved")  # a reused id cannot be paired with its output
    called = set(ids)
    if any(row.get("toolCallId") not in called for row in rows if row.get("type") == "tool_call_update"):
        # A completed update with no tool_call is an action the log does not show the input of.
        events.append(Event("other", "orphan tool_call_update", True, None))
    for row in rows:
        if row.get("type") != "tool_call":
            continue
        tool = row.get("toolName")
        if tool == "grep":
            # grok's search tool: read-only, so it does not touch the filesystem, but it is not a
            # file read either, so it still forfeits the lazy pass.
            events.append(Event("search", str(tool), True, None))
            continue
        if tool not in ("run_terminal_command", "read_file"):
            events.append(Event("other", str(tool), True, None))
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
    tool_steps: set = set()
    other_steps: set = set()
    for row in rows:
        step = row.get("step_update")
        if row.get("event") != "step_update" or not isinstance(step, dict):
            continue
        (tool_steps if step.get("step_type") == "tool" else other_steps).add(step.get("step_index"))
        if step.get("state") == "DONE":
            done[step.get("step_index")] = step
    if tool_steps & other_steps:
        # Another step type on a tool step's index could supply (or hide) its output.
        raise ShapeError("agy input shape unobserved")
    events = []
    seen: dict[object, str] = {}
    for row in rows:
        step = row.get("step_update")
        if row.get("event") != "step_update" or not isinstance(step, dict):
            continue
        if step.get("step_type") != "tool":
            # Step types observed in real agy logs; any other could act, so it is unmapped.
            # system_message is a harness notice (no tool, no parameters), seen in the live smoke.
            if step.get("step_type") not in ("agent_response", "user_input", "checkpoint", "system_message"):
                events.append(Event("other", str(step.get("step_type")), True, None))
            continue
        index = step.get("step_index")
        if index is None:
            raise ShapeError("agy input shape unobserved")
        info = step.get("tool_info")
        identity = json.dumps([step.get("tool_name"), info.get("parameters") if isinstance(info, dict) else None],
                              sort_keys=True, default=str)
        if index in seen:
            if seen[index] != identity:
                raise ShapeError("agy input shape unobserved")
            continue
        seen[index] = identity
        tool = step.get("tool_name")
        if tool not in ("run_command", "view_file"):
            events.append(Event("other", str(tool), True, None))
            continue
        info = step.get("tool_info")
        params = info.get("parameters") if isinstance(info, dict) else None
        # view_file names the file read in FilePath (or AbsolutePath); any other parameter is not it.
        value = (params.get("CommandLine") if isinstance(params, dict) and tool == "run_command" else
                 [params[k] for k in ("FilePath", "AbsolutePath") if isinstance(params, dict) and isinstance(params.get(k), str)])
        if tool == "run_command" and not isinstance(value, str) or tool == "view_file" and not isinstance(params, dict):
            raise ShapeError("agy input shape unobserved")
        finish = done.get(index)
        end_info = finish.get("tool_info") if finish else None
        output = end_info.get("output") if isinstance(end_info, dict) else None
        cwd = params.get("Cwd") if tool == "run_command" and isinstance(params.get("Cwd"), str) else None
        events.append(Event("shell" if tool == "run_command" else "read", value, finish is not None,
                            output if isinstance(output, str) else None,
                            finish is not None and not isinstance(output, str), cwd=cwd))
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
        cwd = body[0].rsplit(" in ", 1)[-1]
        events.append(Event("shell", body[0], success, "\n".join(body[2:]) if success else None, cwd=cwd))
    return events, False


@dataclass
class Places:
    """Where the file may legitimately be read from, as text: the verdict never asks this machine.

    root is the checkout; home is the logged session's HOME (None: `~` and $HOME never count);
    links are host loader links the caller verified point at <root>/h-mad (the smoke checks
    readlink -f before the run). Every comparison is lexical, so a log scores the same anywhere.
    """
    root: str
    home: str | None = None
    links: tuple[str, ...] = ()

    @classmethod
    def build(cls, root: Path, home: str | None = None, links: tuple[str, ...] = ()) -> "Places":
        norm = lambda v: posixpath.normpath(os.path.abspath(v))
        home = norm(home) if home else None
        expand = lambda v: (home + v[1:]) if home and (v == "~" or v.startswith("~/")) else v
        return cls(norm(str(root)), home, tuple(norm(expand(l)) for l in links if not l.startswith("~") or home))


def lexical(value: str, places: Places, relative_ok: bool = True) -> str | None:
    """value as a normalised absolute path, or None when text alone cannot fix what it names."""
    for prefix in ("$HOME/", "${HOME}/"):
        if value.startswith(prefix):
            value = "~/" + value[len(prefix):]
    if value.startswith("~"):
        if places.home is None or not value.startswith("~/"):
            return None
        value = places.home + value[1:]
    if ".." in value.split("/"):
        return None  # through a symlinked component, `..` leaves the directory it lexically names
    if not value.startswith("/") and not relative_ok:
        return None  # the shell's cwd is not known to be the root
    return posixpath.normpath(value if value.startswith("/") else f"{places.root}/{value}")


def names_file(value: str, host: str, skill: bool, places: Places, shell_ok: bool, in_shell: bool,
               fs_ok: bool, at_root: bool = True) -> bool:
    """True when value names this checkout's file, decided from text alone.

    It must be <root>/h-mad/<file>, or <link>/<file> for a verified loader link. A suffix match
    is not enough: /tmp/x/h-mad/SKILL.md is a decoy. In a shell nothing counts unless shell_ok:
    an earlier command could have changed cwd, HOME, a variable, PATH or the reading command
    itself; a relative path also needs at_root. Nothing counts at all unless fs_ok: a read
    proves the file's content only if nothing earlier in the whole log could have written or
    re-pointed it (cp over it, a symlink swap, a redirect), and the filesystem survives a codex
    exec's fresh shell. File tools do not expand `~` or variables, so those spellings never
    count there; their relative paths are workspace-relative and count.
    """
    filename = "SKILL.md" if skill else f"references/{host}-runtime.md"
    if not fs_ok:
        return False  # an earlier event may have written or re-pointed the file
    if in_shell and not shell_ok:
        return False  # a tainted shell may have moved cwd, HOME, a variable, PATH or `cat` itself
    if value in (f"$HMAD_SKILL_ROOT/{filename}", f"${{HMAD_SKILL_ROOT}}/{filename}"):
        return in_shell
    # No character allowlist is needed: the comparison is textual, so a variable, glob, brace or
    # `=cmd` keeps its special character and can never equal the plain target path.
    spelled = re.sub(r"^\$(\{HOME\}|HOME)/", "~/", value)
    if spelled.startswith("~") and not in_shell:
        return False
    path = lexical(value, places, at_root or not in_shell)
    if path is None:
        return False
    return path in {posixpath.normpath(f"{places.root}/h-mad/{filename}")} | {
        posixpath.normpath(f"{link}/{filename}") for link in places.links}


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
    """Every argument is checked: GNU sed accepts options, and -e scripts, after a file operand."""
    allowed = {"-n", "--quiet", "--silent", "-E", "-r"}
    scripts, operands, i = [], [], 0
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
        else:
            operands.append(item)
        i += 1
    if not scripts and operands:
        scripts.append(operands.pop(0))
    return bool(scripts) and all(re.fullmatch(r"(\d+|\$)?(,(\d+|\$))?p", s) for s in scripts)


def read_operands(command: Command) -> list[str] | None:
    """The files a read command prints, or None when an option makes that uncertain.

    Exactly one operand is allowed, after head/tail `-n N` and sed's print-only flags. Any other
    option lands among the operands and fails that limit: an option can take a path-like argument
    that is not read (nl -s <path>) or change what is printed (head -c 0). With two operands,
    head/tail -n and a sed script print only part of each file (or of the joined stream), so the
    heading may come from the other.
    """
    args, ops, i = command.tokens[1:], [], 0
    if command.name not in ("cat", "nl", "head", "tail", "sed"):
        return None
    script = command.name != "sed"
    while i < len(args):
        item = args[i]
        if command.name in ("head", "tail") and item == "-n" and i + 1 < len(args) and re.fullmatch(r"\+?\d+", args[i + 1]):
            i += 2
        elif command.name in ("head", "tail") and re.fullmatch(r"-n?\+?\d+", item):
            i += 1
        elif command.name == "sed" and item in ("-e", "--expression"):
            script, i = True, i + 2
        elif command.name == "sed" and item in ("-n", "--quiet", "--silent", "-E", "-r"):
            i += 1
        elif not script:
            script, i = True, i + 1
        else:
            ops.append(item)
            i += 1
    return ops if len(ops) == 1 else None


def classify(tokens: list[str], depth: int = 0) -> list[Command]:
    assignments = []
    while tokens and ASSIGN.fullmatch(tokens[0]):
        assignments.append(tokens.pop(0))
    if not tokens:
        # A bare assignment runs nothing but rebinds a variable (HOME, PWD ...); keep it visible.
        return [Command("assign", [], assignments)] if assignments else []
    name = Path(tokens[0]).name
    args = tokens[1:]
    if any(t.startswith("\0") for t in tokens):
        return [Command("unknown", tokens, assignments, name)]
    if name in ("bash", "sh", "zsh"):
        for i, item in enumerate(args):
            if not item.startswith("-"):
                break  # `bash <script> -c ...` runs <script>; -c after an operand is the script's argument
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
    # rg is not safe: --pre and --hostname-bin run programs, and its option set is too rich to allowlist.
    safe = {"cat", "head", "tail", "nl", "sed", "grep", "ls", "test", "[", "echo", "wc", "stat"}
    if name in safe and (name != "sed" or sed_safe(args)):
        return [Command("read" if name in {"cat", "head", "tail", "nl", "sed"} else "safe",
                        tokens, assignments, name)]
    return [Command("unknown", tokens, assignments, name)]


def needle(root: Path, host: str, skill: bool) -> str:
    path = root / "h-mad" / ("SKILL.md" if skill else f"references/{host}-runtime.md")
    return next((line for line in path.read_text().splitlines() if line.startswith("# ")), "")


def v111(host: str, log: Path, root: Path, home: str | None = None, links: tuple[str, ...] = ()) -> tuple[str, int]:
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
        # The lazy pass (operator decision 2026-10-01) needs proof that nothing but reads ran.
        # Only the host's file-read tool can give that proof: any shell command forfeits it,
        # because a shell classifier is a denylist and a denylist leaks.
        shelled = unmapped = False
        # A shell path that depends on shell state (relative, `~`, $HMAD_SKILL_ROOT) names this
        # checkout only while the shell is known untouched: an allowlist, because every way to
        # change cwd, HOME or a variable cannot be enumerated. Any command that is not a read or
        # a safe command (a bare assignment included) and `printf -v` taint what follows. Each codex exec is a
        # fresh shell; agy and grok shells may persist, so their taint does too.
        tainted = False
        # The filesystem outlives every shell, codex execs included: anything not proven
        # read-only (an unmapped tool, a non-read/safe command) may have re-pointed a loader link,
        # so a read through a link counts only before the first such event. Never reset.
        fs_tainted = False
        places = Places.build(root, home, links)
        for event in events:
            if event.tool == "other":
                unmapped = fs_tainted = True
                continue
            if event.tool == "search":
                unmapped = True
                continue
            if event.tool == "read":
                paths = [event.value] if isinstance(event.value, str) else event.value
                for is_skill, heading in ((False, adapter), (True, skill)):
                    # Mention (for the read-before-script ordering) needs no clean filesystem; credit does.
                    if any(names_file(p, host, is_skill, places, True, False, True) for p in paths):
                        if not is_skill:
                            if script_before_adapter and not read_adapter:
                                return "FAIL V-11.1 a script ran before the adapter was read", 0
                            adapter_seen = True
                        if event.success and paths and all(names_file(p, host, is_skill, places, True, False, not fs_tainted)
                                                           for p in paths):
                            if event.output_bad:
                                return f"UNVERIFIED V-11.1 {host} output shape unobserved", 0
                            if event.output is not None and heading in event.output:
                                if is_skill:
                                    read_skill = True
                                else:
                                    read_adapter = True
                continue
            shelled = True
            at_root = event.cwd is None or posixpath.normpath(event.cwd) == places.root
            if host == "codex":
                tainted = False
            # The heading check reads the exec's whole output, so a read is credited only when it
            # is the exec's sole command: otherwise another command could have printed the heading.
            # A zsh modifier glued to a path (`f(:s/a/b/)`) splits off as a second command, so it
            # is never sole either; its text never classifies read/safe, so it also taints.
            every = [c for part in simple_tokens(event.value) for c in classify(part.copy())]
            # simple_tokens drops redirects, so `echo x > f` would classify safe; an output
            # redirect anywhere in the exec writes, so it taints what follows.
            redirects = ">" in event.value
            # A command hidden in an expansion is invisible to classify, so it taints the shell and
            # filesystem from here on. A read in the same exec needs no extra rule: an expansion in
            # its path never equals the plain target, and a split-off $( makes it non-sole.
            active = active_expansion(event.value)
            if active:
                tainted = fs_tainted = True
            sole = len(every) == 1
            for tokens in simple_tokens(event.value):
                commands = classify(tokens.copy())
                for command in commands:
                    # A read whose own command carries a prefix assignment is not credited: whether
                    # its paths expand before or after the assignment is shell-specific. The prefix
                    # lasts one command, so it does not taint later ones; a bare one is kind "assign".
                    relative_ok = not tainted and not command.assignments
                    fs_ok = not fs_tainted
                    # printf is not safe: -v assigns, and zsh evaluates %d arguments as math (HOME=7).
                    if command.kind not in ("read", "safe"):
                        tainted = True
                        # cd/pushd/popd/pwd move or report the cwd but write nothing (a write
                        # through them is a redirect, tainted below); anything else may write.
                        if command.name not in ("cd", "pushd", "popd", "pwd"):
                            fs_tainted = True
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
                        operands = read_operands(command) if sole else None
                        for is_skill, heading in ((False, adapter), (True, skill)):
                            if any(names_file(t, host, is_skill, places, relative_ok, True, True, at_root)
                                   for t in command.tokens[1:]):
                                if not is_skill:
                                    if script_before_adapter and not read_adapter:
                                        return "FAIL V-11.1 a script ran before the adapter was read", 0
                                    adapter_seen = True
                                if event.success and operands is not None and any(names_file(
                                        o, host, is_skill, places, relative_ok, True, fs_ok, at_root) for o in operands):
                                    if event.output_bad:
                                        return f"UNVERIFIED V-11.1 {host} output shape unobserved", 0
                                    if event.output is not None and heading in event.output:
                                        if is_skill:
                                            read_skill = True
                                        else:
                                            read_adapter = True
            if redirects:
                tainted = fs_tainted = True
        if not read_adapter:
            # A read-only call need not load the adapter, provided every event is a file-read tool
            # call: no shell command and no tool or step the classifier does not map. Anything
            # unproven needed the adapter: FAIL. Codex has no file-read tool (every event is a
            # shell exec), so `shelled` keeps it from ever showing itself read-only.
            if script_before_adapter or shelled or unmapped:
                return "FAIL V-11.1 no adapter read", 0
            if host == "grok" and not listed:
                return "FAIL V-11.1 grok did not list h-mad", 0
            if not read_skill:
                prefix = "UNVERIFIED" if host == "grok" else "FAIL"
                return f"{prefix} V-11.1 no observed SKILL.md read", 0
            return "PASS V-11.1 lazy (no script ran)", 0
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
            actual, _ = v111(case["host"], HERE / "rehearsal" / case["log"], HERE.parents[3] / case["root"],
                             case.get("home"), tuple(case.get("links", ())))
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
    p111.add_argument("--home", help="the logged session's HOME; without it `~` and $HOME never count")
    p111.add_argument("--link", action="append", default=[],
                      help="a host loader link already verified to resolve to <root>/h-mad (repeatable)")
    p112 = sub.add_parser("v112")
    p112.add_argument("--out", type=Path, required=True)
    p112.add_argument("--record", required=True)
    p112.add_argument("--feature", required=True)
    sub.add_parser("rehearse")
    args = parser.parse_args()
    if args.mode == "rehearse":
        return rehearse()
    result, code = v111(args.host, args.log, args.root, args.home, tuple(args.link)) if args.mode == "v111" else v112(args.out, args.record, args.feature)
    print(result)
    return code


if __name__ == "__main__":
    sys.exit(main())
