#!/usr/bin/env python3
"""Answer "which model did this dispatch actually run?" from evidence, or refuse.

With nothing pinned, `exec` inherits the agent's own configuration, so the
resolved model is the ONLY evidence of what a 5d/5e dispatch ran — and a model
that cannot execute a single tool (`gpt-5.6-luna`, measured) still writes prose,
so it comes back as a well-formed `STATUS: BLOCKED` that looks exactly like a task
verdict. A wrong answer here is worse than no answer, so every path either prints
one validated value or exits 2 naming what it could not establish.

Two things measured on 2026-09-01 that the prose version of these extractors got
wrong, both of which would have shipped a confident wrong model:

1. **`ls -t` order is not session order for agy.** The newest cli log BY MTIME was
   `cli-20260831_145303.log`, still being appended by a long-lived agy pane, while
   the newest BY NAME was that day's short `exec agy` run. Several agy processes
   log concurrently, so "the newest log" silently answers a different question
   depending on which order you pick. This tool reports the file it used and
   refuses when the two most recent files disagree about the model.
2. **The agy log tears mid-line.** Concurrent goroutines interleave writes, so
   `label="([^"]+)"` matches across a newline and yields values like
   `GeminERROR: logging before google.Init: ...`. Eight such fragments were present
   across 620 logs. Bounding the capture to one line and 60 characters removes all
   eight and keeps every real label (2,670 matches, three distinct values).
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import sys
from pathlib import Path

# codex writes its session header at the top of the --log file.
CODEX_MODEL = re.compile(r"(?m)^model:[ \t]+(.+?)[ \t]*$")
CODEX_EFFORT = re.compile(r"(?m)^reasoning effort:[ \t]+(.+?)[ \t]*$")
CODEX_HEADER_LINES = 20

# The bound is the whole guard, and it was verified to be sufficient rather than
# assumed: over the real 620-log corpus this pattern yields exactly three values
# (`Gemini 3.1 Pro (High)` x2618, `(Low)` x36, `3.7 Flash (Medium)` x16) and not
# one fragment. A substring blacklist on top of it was written first, measured,
# and deleted — it rejected NOTHING, and a guard that cannot fire is a code path
# no test can reach and an invitation to believe the bound is optional. Refusing
# `"` and a newline inside the value is what keeps a torn line local: the tear
# splices a newline into the quoted text, so the match simply does not form.
AGY_LABEL = re.compile(r'Propagating selected model override to backend: label="([^"\n]{1,60})"')


def _fail(msg: str) -> "NoReturn":  # noqa: F821
    print(f"RESOLVED-MODEL: UNKNOWN — {msg}", file=sys.stderr)
    raise SystemExit(2)


def _emit(agent: str, model: str, effort: str, kind: str, source: str) -> None:
    """`kind` is the load-bearing word: `resolved` is proof of what ran."""
    print(f"RESOLVED-MODEL agent={agent} model={model} effort={effort} "
          f"{kind}=1 source={source}")


def codex_from_log(path: str) -> None:
    p = Path(path)
    if not p.is_file():
        _fail(f"no such codex log: {path}")
    head = "".join(p.read_text(errors="replace").splitlines(keepends=True)[:CODEX_HEADER_LINES])
    m = CODEX_MODEL.search(head)
    if not m:
        _fail(f"no `model:` line in the first {CODEX_HEADER_LINES} lines of {path} — "
              "not a codex session log, or the header moved")
    e = CODEX_EFFORT.search(head)
    _emit("codex", m.group(1), e.group(1) if e else "-", "resolved", path)


def codex_from_config(path: str | None) -> None:
    """The CONFIGURED value. Labelled `configured`, never `resolved`.

    `$CODEX_HOME` is not always `~/.codex` — under Orca it is a per-account home,
    and reading the wrong one produced a wrong fix on 2026-08-31. So the env var
    is honoured and the path used is printed.
    """
    home = os.environ.get("CODEX_HOME") or os.path.expanduser("~/.codex")
    cfg = Path(path) if path else Path(home) / "config.toml"
    if not cfg.is_file():
        _fail(f"no codex config at {cfg} (CODEX_HOME={os.environ.get('CODEX_HOME', '<unset>')}) "
              "and no --log given, so nothing establishes the model")
    text = cfg.read_text(errors="replace")
    m = re.search(r'(?m)^model\s*=\s*"?([^"\n]+?)"?\s*$', text)
    if not m:
        _fail(f"no `model =` key in {cfg}")
    e = re.search(r'(?m)^model_reasoning_effort\s*=\s*"?([^"\n]+?)"?\s*$', text)
    _emit("codex", m.group(1), e.group(1) if e else "-", "configured", str(cfg))


def agy_from_cli_logs(log_dir: str | None) -> None:
    d = log_dir or os.path.expanduser("~/.gemini/antigravity-cli/log")
    files = glob.glob(os.path.join(d, "cli-*.log"))
    if not files:
        _fail(f"no cli-*.log under {d}")
    # Newest by MTIME — last written, not last started. Both orders are defensible
    # and they disagree here, which is exactly why the file is reported and a
    # disagreement between the top two refuses instead of guessing.
    files.sort(key=lambda p: os.stat(p).st_mtime, reverse=True)

    def last_label(path: str) -> str | None:
        hits = AGY_LABEL.findall(Path(path).read_text(errors="replace"))
        return hits[-1] if hits else None

    newest = files[0]
    label = last_label(newest)
    if label is None:
        _fail(f"no well-formed model label in {newest} — every match was a torn log line, "
              "or this agy run never logged a model override")
    for other in files[1:2]:
        rival = last_label(other)
        if rival is not None and rival != label:
            _fail(f"ambiguous: {os.path.basename(newest)} says {label!r} and "
                  f"{os.path.basename(other)} says {rival!r}. Concurrent agy processes "
                  "log side by side, so no log can be attributed to a dispatch here — "
                  "read the model off the dispatch you care about.")
    _emit("agy", label, "-", "resolved", newest)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("agent", choices=("codex", "agy"))
    ap.add_argument("--log", help="the dispatch's --log file (codex only)")
    ap.add_argument("--config", help="override the codex config path")
    ap.add_argument("--agy-log-dir", help="override the agy cli log directory")
    a = ap.parse_args(argv)

    if a.agent == "codex":
        codex_from_log(a.log) if a.log else codex_from_config(a.config)
        return 0
    if a.log:
        # Refusing beats answering from a different source: `exec agy` writes
        # stream-json, which carries no model field at all, and silently falling
        # back to the cli log dir would answer about whatever agy wrote last.
        _fail("an `exec agy` --log is stream-json and carries no model field. Omit --log "
              "to read agy's own cli logs, and note that answers the last agy PROCESS, "
              "not necessarily this dispatch.")
    agy_from_cli_logs(a.agy_log_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
