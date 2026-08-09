#!/usr/bin/env python3
"""Verifier for the security-guidance bare-"exec(" patch.

Run AFTER any plugin update to check whether the patch is still applied:
    python3 docs/patches/claude-security-guidance-bare-exec/verify.py

Exit 0 = patch present and every other rule still fires.
Exit 1 = patch missing (re-apply) or a rule stopped working.

Absolute expectations, so it keeps working across plugin versions.
Set HOOK_PATH to point at a specific copy (used for red-green testing).
"""

import importlib.util
import os
import sys

DEFAULT_HOOK = os.path.expanduser(
    "~/.claude/plugins/cache/claude-plugins-official/"
    "security-guidance/unknown/hooks/security_reminder_hook.py"
)
HOOK_PATH = os.environ.get("HOOK_PATH", DEFAULT_HOOK)

if not os.path.exists(HOOK_PATH):
    print("SKIP - security_reminder_hook.py not found; nothing to verify.")
    sys.exit(0)

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

bad = 0
patch_present = False
for pattern in getattr(hook, "SECURITY_PATTERNS", []):
    if pattern.get("ruleName") == "child_process_exec":
        patch_present = (
            "regexes" in pattern and CALL not in pattern.get("substrings", [])
        )

for name, content, expected in CASES:
    rule, _ = hook.check_patterns(FILE, content)
    if expected == "ANY":
        ok, want = rule is not None, "some rule"
    elif expected is None:
        ok, want = rule is None, "no rule"
    else:
        ok, want = rule == expected, expected
    if not ok:
        bad += 1
        print(f"  FAIL {name}: expected {want}, got {rule!r}")

print(
    f"security-guidance - patch {'PRESENT' if patch_present else 'MISSING'}, "
    f"{len(CASES) - bad}/{len(CASES)} cases correct"
)

if bad and not patch_present:
    print("RESULT: patch NOT applied - re-apply security_reminder_hook.patch (see README.md)")
    sys.exit(1)
if bad:
    print("RESULT: FAIL - behaviour is wrong even though the patch appears present")
    sys.exit(1)
print("RESULT: OK - bare-exec false positive fixed, real detections intact")
sys.exit(0)
