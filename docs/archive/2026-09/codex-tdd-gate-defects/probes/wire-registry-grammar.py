#!/usr/bin/env python3
"""Where h_mad_wire_registry._production_claims and _parse_tasks disagree today.

Usage: wire-registry-grammar.py <skills-root> <hemasuite-root>
Corpus: tracked, non-archive/ `*.impl-plan.md` files of both repositories (git ls-files).
Prints one `WRGRAMMAR:` line. Units: files, and matching lines.
"""
import re, subprocess, sys
from pathlib import Path

SK, HS = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
sys.path.insert(0, str(SK / "h-mad/scripts"))
sys.dont_write_bytecode = True
from h_mad_wire_pin_gate import _parse_tasks  # noqa: E402

files = []
for root in (SK, HS):
    out = subprocess.run(["git", "-C", str(root), "ls-files", "*.impl-plan.md"],
                         capture_output=True, text=True, check=True).stdout.split()
    files += [root / f for f in out if "archive/" not in f]
TOKEN = re.compile(r"`([^`]+\.py)`")
# The registry's own grammar, copied from _production_claims (task counter and label).
REG_TASK = re.compile(r"^\s*#{2,3}\s+[MT]\d+")
REG_LABEL = re.compile(r"^\s*(?:[-*•]\s+)?\*{0,2}Production file\*{0,2}\s*:\s*(.*)$", re.I)
# The spec FR-2 label axis: Production file | Production files | Production, colon in or out of bold.
AXIS_LABEL = re.compile(r"^\s*(?:[-*•]\s+)?\*{0,2}\s*Production(?: files?)?\s*\*{0,2}\s*:\s*\*{0,2}\s*(.*)$", re.I)
div, multi, unread = [], 0, 0
for f in files:
    text = f.read_text(encoding="utf-8", errors="replace")
    reg_tasks = sum(1 for ln in text.splitlines() if ln.lstrip().startswith("## Task ") or REG_TASK.match(ln))
    if reg_tasks != len(_parse_tasks(text)):
        div.append(f"{f.name}:{len(_parse_tasks(text))}/{reg_tasks}")
    for ln in text.splitlines():
        m = REG_LABEL.match(ln)
        if m and len(TOKEN.findall(m.group(1))) >= 2:
            multi += 1
        if AXIS_LABEL.match(ln) and not m:
            unread += 1
print(f"WRGRAMMAR: files={len(files)} task_counter_divergent_files={len(div)} "
      f"singular_label_multi_path_lines={multi} axis_label_lines_unread_by_registry={unread} "
      f"divergent=[{' '.join(div)}]")
