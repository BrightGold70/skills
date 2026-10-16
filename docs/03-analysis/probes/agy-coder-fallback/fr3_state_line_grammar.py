#!/usr/bin/env python3
"""FR-3 probe: the new TDD-STATE grammar reads the same in Python `re` and bash ERE.

Derives the new STATE_ACTIVE_RE from the hook's CURRENT literal by inserting the
author-field group before the fallback-tag group, then matches candidate lines with
Python re.fullmatch and with `[[ =~ ]]` under each bash given on the command line.

Run from the repository root:
  python3 docs/03-analysis/probes/agy-coder-fallback/fr3_state_line_grammar.py /bin/bash /opt/homebrew/bin/bash
Prints one line per check and a final `PROBE: PASS|FAIL`.
"""
import re
import subprocess
import sys
from pathlib import Path

HOOK = Path("h-mad/hooks/h-mad-tdd-gate.sh")
OLD_TAIL = ",(absent|null|grok|claude|invalid:[^ ,]+))+$"
NEW_TAIL = ",(codex|agy|peers-out|invalid:[^ ,]+),(absent|null|grok|claude|invalid:[^ ,]+))+$"

lines = [l for l in HOOK.read_text().splitlines() if re.match(r"^STATE_ACTIVE_RE='(.*)'$", l)]
assert len(lines) == 1, f"expected one STATE_ACTIVE_RE literal, found {len(lines)}"
old = re.match(r"^STATE_ACTIVE_RE='(.*)'$", lines[0]).group(1)
assert old.count(OLD_TAIL) == 1 and old.endswith(OLD_TAIL), "hook literal drifted from the probe's tail"
new = old[: -len(OLD_TAIL)] + NEW_TAIL

F = "/x/docs/.bkit-memory.json"
cases = {  # name -> (line, should_match)
    "grok-fold": (f"TDD-STATE: active codex-escape=yes blocker=0 records=1 fallback=grok:1 record=feat,exhausted,{F},peers-out,grok", True),
    "agy-record": (f"TDD-STATE: active codex-escape=no blocker=1 records=1 fallback=none record=feat,available,{F},agy,absent", True),
    "invalid-implementer": (f"TDD-STATE: active codex-escape=no blocker=1 records=2 fallback=none record=a,available,{F},invalid:%22x%22,absent record=b,available,{F},codex,null", True),
    "today-shape": (f"TDD-STATE: active codex-escape=yes blocker=0 records=1 fallback=grok:1 record=feat,exhausted,{F},grok", False),
    "author-grok": (f"TDD-STATE: active codex-escape=yes blocker=0 records=1 fallback=grok:1 record=feat,exhausted,{F},grok,grok", False),
}
CHECK = 'if [[ "$2" =~ $1 ]]; then printf "%s\\n" "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}" "${BASH_REMATCH[3]}" "${BASH_REMATCH[4]}" "${BASH_REMATCH[6]}"; else echo NOMATCH; fi'
ok = True
for name, (line, want) in cases.items():
    m = re.fullmatch(new, line)
    py = [m.group(i) for i in (1, 2, 3, 4, 6)] if m else None
    if (m is not None) != want:
        ok = False
    print(f"{name}: python={'match' if m else 'nomatch'} want={'match' if want else 'nomatch'}")
    if m and m.group(4) != line.split("fallback=")[1].split(" ")[0]:
        ok = False
        print(f"{name}: group(4) != fold")
    for bash in sys.argv[1:]:
        ver = subprocess.run([bash, "-c", "echo $BASH_VERSION"], capture_output=True, text=True).stdout.strip()
        out = subprocess.run([bash, "-c", CHECK, "_", new, line], capture_output=True, text=True).stdout.splitlines()
        sh = None if out == ["NOMATCH"] else [g or None for g in out]
        same = sh == py
        ok &= same
        print(f"{name}: bash {ver} groups 1,2,3,4,6 {'==' if same else '!='} python")
print("PROBE: " + ("PASS" if ok else "FAIL"))
