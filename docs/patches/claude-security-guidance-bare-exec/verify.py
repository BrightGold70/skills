#!/usr/bin/env python3
"""Verifier for security-guidance bare-"exec(" behaviour.

The local patch is RETIRED: upstream fixed claude-plugins-official#5085 in
security-guidance 2.0.0, and the local patch was dropped on 2026-10-18 at
2.0.14. Run AFTER any plugin update to check the upstream hook against the
same cases:
    python3 docs/patches/claude-security-guidance-bare-exec/verify.py

Exit 0 = every case correct, except the KNOWN_GAPS upstream has not closed.
Exit 1 = a case outside KNOWN_GAPS failed - a rule regressed upstream.

Absolute expectations, so it keeps working across plugin versions.
The live copy is resolved from installed_plugins.json. Set HOOK_PATH to
point at a specific copy (used for red-green testing).
"""

import importlib.util
import json
import os
import sys

INSTALLED = os.path.expanduser("~/.claude/plugins/installed_plugins.json")


def live_hook_path():
    """The hook Claude Code actually executes, per installed_plugins.json."""
    try:
        with open(INSTALLED) as f:
            entries = json.load(f)["plugins"]["security-guidance@claude-plugins-official"]
        root = entries[0]["installPath"]
    except (OSError, KeyError, IndexError, ValueError):
        return None
    return os.path.join(root, "hooks", "security_reminder_hook.py")


HOOK_PATH = os.environ.get("HOOK_PATH") or live_hook_path()

if not HOOK_PATH or not os.path.exists(HOOK_PATH):
    print("SKIP - security_reminder_hook.py not found; nothing to verify.")
    sys.exit(0)

# 2.x splits the hook across sibling modules (patterns.py, extensibility.py).
sys.path.insert(0, os.path.dirname(HOOK_PATH))

# SourceFileLoader is used explicitly so this works on a copy with any
# extension (e.g. a saved .orig), which spec_from_file_location alone rejects.
from importlib.machinery import SourceFileLoader  # noqa: E402

loader = SourceFileLoader("security_reminder_hook", HOOK_PATH)
spec = importlib.util.spec_from_loader(loader.name, loader)
hook = importlib.util.module_from_spec(spec)
loader.exec_module(hook)  # safe: the module guards on __main__

FILE = "src/thing.js"
CALL = "exec" + "("          # built at runtime so this file is not its own fixture
CALL_SP = "exec" + " ("

# (name, content, expected_rule) - None means "must NOT fire"
CASES = [
    # --- false positives this patch fixes -----------------------------------
    ("regex-exec-method",      "const m = START." + CALL + "text);",          None),
    ("regex-exec-loop",        "while ((m = re." + CALL + "s)) !== null) { }", None),
    ("arbitrary-method-exec",  "await queryRunner." + CALL + "sql);",         None),
    ("identifier-ending-exec", "const r = my" + CALL + "cmd);",               None),

    # --- true positives that MUST still fire --------------------------------
    ("bare-exec",              CALL + "'ls -la');",                  "child_process_exec"),
    ("bare-exec-space",        CALL_SP + "'ls -la');",               "child_process_exec"),
    ("destructured-exec",
     "const { exec } = require('child_process');\n" + CALL + "cmd);", "child_process_exec"),
    ("qualified-exec",         "child_process." + CALL + "cmd);",    "child_process_exec"),
    ("exec-sync",              "execSync('ls');",                    "child_process_exec"),

    # --- other rules must be untouched --------------------------------------
    ("eval-rule",              "const x = eval(userInput);",             "eval_injection"),
    ("innerhtml-rule",         "el.innerHTML = userInput;",                   "ANY"),
    ("new-function-rule",      "const f = new Function('a', 'return a');",    "ANY"),
]

# Cases the upstream fix (2.0.0+) still gets wrong. Accepted when the local
# patch was retired; see docs/skill-monitoring.md. Remove an entry once
# upstream closes it - this script says when.
KNOWN_GAPS = {"bare-exec-space"}


def matched_rules(file_path, content):
    """Rule names that fired. 1.x returns (rule, reminder); 2.x returns a list of matches."""
    result = hook.check_patterns(file_path, content)
    if isinstance(result, tuple):
        return [result[0]] if result[0] is not None else []
    return [m["ruleName"] if isinstance(m, dict) else m[0] for m in result]


bad = 0
gaps = 0
for name, content, expected in CASES:
    rules = matched_rules(FILE, content)
    if expected == "ANY":
        ok, want = bool(rules), "some rule"
    elif expected is None:
        ok, want = not rules, "no rule"
    else:
        ok, want = expected in rules, expected
    if ok and name in KNOWN_GAPS:
        print(f"  GAP CLOSED {name}: upstream now gets this right - remove it from KNOWN_GAPS")
    elif not ok and name in KNOWN_GAPS:
        gaps += 1
        print(f"  known gap {name}: expected {want}, got {rules!r}")
    elif not ok:
        bad += 1
        print(f"  FAIL {name}: expected {want}, got {rules!r}")

print(
    f"security-guidance ({HOOK_PATH.split('/security-guidance/')[-1].split('/')[0]}) - "
    f"{len(CASES) - bad - gaps}/{len(CASES)} cases correct, {gaps} known gap(s)"
)

if bad:
    print("RESULT: FAIL - upstream rule behaviour regressed outside the known gaps")
    sys.exit(1)
print("RESULT: OK - upstream behaviour matches, apart from the known gaps")
sys.exit(0)
