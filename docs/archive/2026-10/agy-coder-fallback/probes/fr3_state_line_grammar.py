#!/usr/bin/env python3
"""FR-3 probe: the TDD-STATE grammar reads the same in Python `re` and bash ERE.

The probe reads the hook's one STATE_ACTIVE_RE literal and picks its mode from it:
- derived (the hook before Task 3's GREEN): the literal ends with OLD_TAIL. The probe inserts
  the author-field group before the fallback-tag group and checks the derived grammar.
- shipped (the hook after Task 3's GREEN): the literal ends with NEW_TAIL. The probe checks the
  literal as shipped, and checks that it equals the grammar derived from the hook at BASE.
A literal ending with neither is drift, reported as `PROBE: FAIL`.

Then it matches candidate lines with Python re.fullmatch and with `[[ =~ ]]` under each bash
given on the command line, comparing capture groups 1, 2, 3, 4 and 6.

Control: `--control` drops `peers-out|` from the grammar under test. The probe must then print
`PROBE: FAIL`, because the grok-fold case stops matching.

Run from the repository root:
  python3 docs/03-analysis/probes/agy-coder-fallback/fr3_state_line_grammar.py [--hook PATH] [--control] /bin/bash /opt/homebrew/bin/bash
`--hook` defaults to h-mad/hooks/h-mad-tdd-gate.sh. Prints one line per check and a final
`PROBE: PASS|FAIL`, and exits 0 on both verdicts. A nonzero exit means the probe could not run
(an unreadable hook, or `git show` of BASE failing).
"""
import re
import subprocess
import sys
from pathlib import Path

BASE = "a8d9ba99"
DEFAULT_HOOK = "h-mad/hooks/h-mad-tdd-gate.sh"
OLD_TAIL = ",(absent|null|grok|claude|invalid:[^ ,]+))+$"
NEW_TAIL = ",(codex|agy|peers-out|invalid:[^ ,]+),(absent|null|grok|claude|invalid:[^ ,]+))+$"
LITERAL = re.compile(r"^STATE_ACTIVE_RE='(.*)'$")


def literals(text):
    return [LITERAL.match(l).group(1) for l in text.splitlines() if LITERAL.match(l)]


def derive(old):
    return old[: -len(OLD_TAIL)] + NEW_TAIL


args = sys.argv[1:]
control = "--control" in args
args = [a for a in args if a != "--control"]
hook = DEFAULT_HOOK
if "--hook" in args:
    i = args.index("--hook")
    hook = args[i + 1]
    del args[i : i + 2]
bashes = args

try:
    found = literals(Path(hook).read_text())
    base_text = subprocess.run(
        ["git", "show", f"{BASE}:{DEFAULT_HOOK}"], capture_output=True, text=True, check=True
    ).stdout
except (OSError, subprocess.CalledProcessError) as exc:
    print(f"probe cannot run: {type(exc).__name__}: {exc}", file=sys.stderr)
    sys.exit(2)

ok = True
base = literals(base_text)
if len(found) != 1 or len(base) != 1:
    print(f"literal count: hook={len(found)} base={len(base)} (each must be 1)")
    print("PROBE: FAIL")
    sys.exit(0)
old = found[0]
if old.endswith(NEW_TAIL) and old.count(NEW_TAIL) == 1:
    mode, new = "shipped", old
    same = new == derive(base[0])
    ok &= same
    print(f"shipped literal {'==' if same else '!='} grammar derived from {BASE}")
elif old.endswith(OLD_TAIL) and old.count(OLD_TAIL) == 1:
    mode, new = "derived", derive(old)
else:
    print("hook literal ends with neither the old nor the new tail: drift")
    print("PROBE: FAIL")
    sys.exit(0)
if control:
    new = new.replace("peers-out|", "", 1)
print(f"mode={mode} control={'yes' if control else 'no'} hook={hook}")

F = "/x/docs/.bkit-memory.json"
cases = {  # name -> (line, should_match)
    "grok-fold": (f"TDD-STATE: active codex-escape=yes blocker=0 records=1 fallback=grok:1 record=feat,exhausted,{F},peers-out,grok", True),
    "agy-record": (f"TDD-STATE: active codex-escape=no blocker=1 records=1 fallback=none record=feat,available,{F},agy,absent", True),
    "invalid-implementer": (f"TDD-STATE: active codex-escape=no blocker=1 records=2 fallback=none record=a,available,{F},invalid:%22x%22,absent record=b,available,{F},codex,null", True),
    "today-shape": (f"TDD-STATE: active codex-escape=yes blocker=0 records=1 fallback=grok:1 record=feat,exhausted,{F},grok", False),
    "author-grok": (f"TDD-STATE: active codex-escape=yes blocker=0 records=1 fallback=grok:1 record=feat,exhausted,{F},grok,grok", False),
}
CHECK = 'if [[ "$2" =~ $1 ]]; then printf "%s\\n" "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}" "${BASH_REMATCH[3]}" "${BASH_REMATCH[4]}" "${BASH_REMATCH[6]}"; else echo NOMATCH; fi'
for name, (line, want) in cases.items():
    m = re.fullmatch(new, line)
    py = [m.group(i) for i in (1, 2, 3, 4, 6)] if m else None
    if (m is not None) != want:
        ok = False
    print(f"{name}: python={'match' if m else 'nomatch'} want={'match' if want else 'nomatch'}")
    if m and m.group(4) != line.split("fallback=")[1].split(" ")[0]:
        ok = False
        print(f"{name}: group(4) != fold")
    for bash in bashes:
        ver = subprocess.run([bash, "-c", "echo $BASH_VERSION"], capture_output=True, text=True).stdout.strip()
        out = subprocess.run([bash, "-c", CHECK, "_", new, line], capture_output=True, text=True).stdout.splitlines()
        sh = None if out == ["NOMATCH"] else [g or None for g in out]
        same = sh == py
        ok &= same
        print(f"{name}: bash {ver} groups 1,2,3,4,6 {'==' if same else '!='} python")
print("PROBE: " + ("PASS" if ok else "FAIL"))
