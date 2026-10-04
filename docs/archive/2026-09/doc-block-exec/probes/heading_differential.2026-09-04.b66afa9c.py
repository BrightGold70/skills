#!/usr/bin/env python3.11
"""Heading-selector differential + Setext census, over BOTH corpora.

OLD  = docsections.titled_section's regex today: (?m)^(?P<marks>#+) <title>\\s*$
       -- column 0 only, space required after the hash run, no 1-6 cap,
       no fence awareness, closing hash run kept in the title.
NEW  = the CommonMark ATX selector find_heading implements: 0-3 spaces indent,
       1-6 hashes, then a space, a tab or end of line; fence-aware; closing
       hash run stripped from the title.

Corpora: TRACKED  = git ls-files -- h-mad handoff, filtered to *.md, archive/ out
         GLOB     = Path('.').glob('*/**/*.md') under h-mad/ handoff/, archive/ out
"""
import re
import subprocess
import sys
from pathlib import Path

OLD = re.compile(r"^(?P<marks>#+) (?P<title>.*?)\s*$")
NEW_LINE = re.compile(r"^(?P<ind> {0,3})(?P<marks>#{1,6})(?P<rest>[ \t].*|)$")
CLOSING = re.compile(r"\s+#+\s*$")
FENCE = re.compile(r"^(?P<ind> {0,3})(?P<run>`{3,}|~{3,})(?P<info>.*)$")


def fence_events(lines):
    """Yield (index, in_fence) per line under the full CommonMark fence rule."""
    fence_char = None
    fence_len = 0
    for i, line in enumerate(lines):
        m = FENCE.match(line)
        if fence_char is None:
            if m and not (m.group("run")[0] == "`" and "`" in m.group("info")):
                yield i, False          # the opener line is not body
                fence_char = m.group("run")[0]
                fence_len = len(m.group("run"))
                continue
            yield i, False
        else:
            closes = (
                m is not None
                and m.group("run")[0] == fence_char
                and len(m.group("run")) >= fence_len
                and m.group("info").strip(" \t") == ""
            )
            yield i, True               # inside the fence (closer included)
            if closes:
                fence_char = None


def corpora():
    tracked = subprocess.run(
        ["git", "ls-files", "--", "h-mad", "handoff"],
        capture_output=True, text=True, check=True).stdout.split("\n")
    trk = sorted(Path(p) for p in tracked
                 if p.endswith(".md") and "archive" not in Path(p).parts)
    glob = sorted(p for p in Path(".").glob("*/**/*.md")
                  if "archive" not in p.parts and p.parts[0] in ("h-mad", "handoff"))
    return {"TRACKED (git ls-files)": trk, "GLOB (filesystem)": glob}


def setext_count(lines, fence_state):
    """A ===/--- underline immediately after a paragraph line, outside fences."""
    n = 0
    in_front = lines and lines[0].strip() == "---"
    for i, line in enumerate(lines):
        if in_front:
            if i and line.strip() == "---":
                in_front = False
            continue
        if fence_state[i] or i == 0:
            continue
        s = line.strip()
        if not s or not (set(s) <= {"="} or set(s) <= {"-"}):
            continue
        if len(line) - len(line.lstrip(" ")) > 3:
            continue
        prev = lines[i - 1]
        p = prev.strip()
        if not p or fence_state[i - 1]:
            continue
        if len(prev) - len(prev.lstrip(" ")) >= 4:
            continue                     # indented code, not a paragraph
        if p[0] in "-*+>|#" or re.match(r"^\d+[.)] ", p) or OLD.match(prev):
            continue                     # list, blockquote, table, heading
        n += 1
    return n


def main():
    for label, files in corpora().items():
        both = old_only = new_only = 0
        closing = tab_form = titleless = setext = 0
        old_only_hits = []
        for p in files:
            lines = p.read_text(encoding="utf-8", errors="replace").split("\n")
            state = [f for _, f in fence_events(lines)]
            setext += setext_count(lines, state)
            for i, line in enumerate(lines):
                o = bool(OLD.match(line))
                m = NEW_LINE.match(line)
                n = bool(m) and not state[i]
                if o and n:
                    both += 1
                elif o:
                    old_only += 1
                    if len(old_only_hits) < 3:
                        old_only_hits.append(f"OLD-ONLY {p} {i + 1} {line}")
                elif n:
                    new_only += 1
                if n:
                    rest = m.group("rest")
                    if rest.startswith("\t"):
                        tab_form += 1
                    if rest == "":
                        titleless += 1
                    if CLOSING.search(rest):
                        closing += 1
        print(f"--- {label}")
        print(f"files={len(files)} both={both} old_only={old_only} new_only={new_only}")
        print(f"setext_headings={setext}")
        print(f"softening shapes: closing_hash={closing} tab_form={tab_form} "
              f"titleless={titleless}")
        for h in old_only_hits:
            print(h)
    return 0


if __name__ == "__main__":
    sys.exit(main())
