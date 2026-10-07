#!/usr/bin/env python3
"""Find bash/sh doc fences that macOS's /bin/bash (3.2) cannot run.

The runtime guard pins doc-block execution to `/bin/bash`. That pin is only safe
if no executed block needs bash 4+. Two independent instruments, because each is
blind where the other sees:

**Feature regexes** flag constructs that 3.2 lacks (`mapfile`, `declare -A`,
`${x,,}`, `;;&`, ...). They are candidates, not verdicts: a hit inside `bash -c
'...'` resolves `bash` from PATH, not the pin, and a hit in prose-like comments
is noise.

**Parse diffs** run `/bin/bash -n` and a modern bash `-n` over each block. They
catch what no feature list can: bash 3.2 rejects an apostrophe inside a
`$(cat <<'EOF' ... EOF)` heredoc body that bash 5 accepts. A block both shells
reject is a template or a fragment, not a 3.2 problem, and is counted apart.

Blocks are taken with `h_mad_expect_screens.shell_blocks` (every bash/sh fence,
a superset of what any runner executes). Each finding names whether its doc
carries an `# expect <N>` screen or an `hmad:exec` fence, because a doc with
neither is never executed and its finding is latent rather than live.

Exit: 0 no findings · 1 findings · 2 cannot judge (a shell is missing or
`--self-test` failed). `--self-test` runs positive controls: every regex must
fire on its sample and the parse diff must separate a 3.2-only failure.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from h_mad_expect_screens import shell_blocks  # noqa: E402

OLD_BASH = "/bin/bash"
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__"}

# (name, pattern, positive-control sample). Order is report order.
FEATURES: list[tuple[str, str, str]] = [
    ("mapfile", r"\bmapfile\b", "mapfile -t a < f"),
    ("readarray", r"\breadarray\b", "readarray a < f"),
    ("assoc-array", r"\b(?:declare|local|typeset)\s+-[a-zA-Z]*A", "declare -A m"),
    ("nameref", r"\b(?:declare|local|typeset)\s+-[a-zA-Z]*n", "local -n ref=x"),
    ("declare-g-l-u", r"\b(?:declare|local|typeset)\s+-[a-zA-Z]*[glu]", "declare -g x=1"),
    ("case-modify", r"\$\{[A-Za-z_][A-Za-z0-9_]*(?:\[[^]]*\])?(?:\^\^?|,,?)\}", 'echo "${x,,}"'),
    ("case-continue", r";;&", "a) x ;;&"),
    ("case-fallthrough", r"(?<!;);&(?!&)", "a) x ;&"),
    ("append-both", r"&>>", "cmd &>> log"),
    ("pipe-stderr", r"\|&", "cmd |& tee log"),
    ("coproc", r"\bcoproc\b", "coproc cat"),
    ("globstar", r"\bshopt\s+-s\s+(?:\w+\s+)*globstar\b", "shopt -s globstar"),
    ("lastpipe", r"\bshopt\s+-s\s+(?:\w+\s+)*lastpipe\b", "shopt -s lastpipe"),
    ("param-transform", r"\$\{[^}\s]*@[QEPAaKkUuL]\}", 'echo "${x@Q}"'),
    ("negative-index", r"\$\{[A-Za-z_][A-Za-z0-9_]*\[-\d+\]\}", 'echo "${a[-1]}"'),
    ("fd-variable", r"\{[A-Za-z_][A-Za-z0-9_]*\}[<>]", "exec {fd}>log"),
    ("bash5-vars", r"\b(?:EPOCHSECONDS|EPOCHREALTIME|SRANDOM|BASH_ARGV0)\b", "echo $EPOCHSECONDS"),
    ("printf-time", r"%\([^)]*\)T", "printf '%(%F)T' -1"),
    ("wait-n", r"\bwait\s+-n\b", "wait -n"),
    ("test-v", r"(?:\[\[|\btest|\[)\s+-v\s", "[[ -v x ]]"),
]
COMPILED = [(name, re.compile(pat)) for name, pat, _ in FEATURES]

SCREEN = re.compile(r"^\s*#\s*expect\s+\d+", re.M)
EXEC_FENCE = re.compile(r"^\s*(?:```|~~~)\s*(?:bash|sh)\b[^\n]*hmad:exec", re.M)

# 3.2 rejects this; 5.x accepts it. Found in real docs, not invented.
PARSE_CONTROL = "x=$(cat <<'EOF'\nit's here\nEOF\n)\necho \"$x\"\n"


def find_modern_bash(explicit: str | None) -> str | None:
    candidates = [explicit] if explicit else [
        "/opt/homebrew/bin/bash", "/usr/local/bin/bash", shutil.which("bash")]
    for c in candidates:
        if not c or not os.access(c, os.X_OK) or os.path.realpath(c) == os.path.realpath(OLD_BASH):
            continue
        out = subprocess.run([c, "-c", "echo ${BASH_VERSINFO[0]}"], capture_output=True, text=True)
        if out.returncode == 0 and out.stdout.strip().isdigit() and int(out.stdout) >= 4:
            return c
    return None


def parses(shell: str, text: str) -> tuple[bool, str]:
    out = subprocess.run([shell, "-n"], input=text, capture_output=True, text=True, timeout=30)
    err = out.stderr.strip().splitlines()
    return out.returncode == 0, (err[0] if err else "")


def iter_docs(roots: list[str], include_archive: bool):
    for root in roots:
        p = Path(root)
        if p.is_file():
            yield p
            continue
        for dirpath, dirnames, filenames in os.walk(p):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS
                                 and (include_archive or d != "archive"))
            for f in sorted(filenames):
                if f.endswith(".md"):
                    yield Path(dirpath) / f


def probe(roots, include_archive, modern, out=sys.stdout):
    totals = dict(docs=0, blocks=0, regex_hits=0, parse32_only=0, parse_both=0, unreadable=0)
    for doc in iter_docs(roots, include_archive):
        try:
            text = doc.read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError):
            totals["unreadable"] += 1
            print(f"UNREADABLE {doc}", file=out)
            continue
        blocks = [b for b in shell_blocks(text) if b]
        if not blocks:
            continue
        totals["docs"] += 1
        tag = (f"screens={'yes' if SCREEN.search(text) else 'no'} "
               f"exec={'yes' if EXEC_FENCE.search(text) else 'no'}")
        for body in blocks:
            totals["blocks"] += 1
            for lineno, line in body:
                for name, rx in COMPILED:
                    if rx.search(line):
                        totals["regex_hits"] += 1
                        print(f"REGEX {name} {doc}:{lineno} {tag} | {line.strip()[:100]}", file=out)
            script = "\n".join(line for _, line in body) + "\n"
            old_ok, old_err = parses(OLD_BASH, script)
            if old_ok:
                continue
            new_ok, _ = parses(modern, script)
            if new_ok:
                totals["parse32_only"] += 1
                print(f"PARSE32 {doc}:{body[0][0]} {tag} | {old_err[:120]}", file=out)
            else:
                totals["parse_both"] += 1
    print("TOTAL " + " ".join(f"{k}={v}" for k, v in totals.items()), file=out)
    return totals


def self_test(modern) -> list[str]:
    failures = []
    for (name, rx), (_, _, sample) in zip(COMPILED, FEATURES):
        if not rx.search(sample):
            failures.append(f"regex {name} did not fire on {sample!r}")
    if parses(OLD_BASH, PARSE_CONTROL)[0]:
        failures.append("/bin/bash accepted the apostrophe-heredoc control")
    if not parses(modern, PARSE_CONTROL)[0]:
        failures.append(f"{modern} rejected the apostrophe-heredoc control")
    if parses(OLD_BASH, "case x in a) : ;;& esac\n")[0]:
        failures.append("/bin/bash accepted ;;&")
    if not parses(modern, "case x in a) : ;;& esac\n")[0]:
        failures.append(f"{modern} rejected ;;&")
    return failures


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("roots", nargs="*", help="files or directories to scan for .md docs")
    ap.add_argument("--modern-bash", help="bash >= 4 to compare against (default: auto)")
    ap.add_argument("--include-archive", action="store_true", help="also scan dirs named archive")
    ap.add_argument("--self-test", action="store_true", help="run the positive controls only")
    args = ap.parse_args(argv)

    if not os.access(OLD_BASH, os.X_OK):
        print(f"CANNOT_JUDGE {OLD_BASH} missing", file=sys.stderr)
        return 2
    modern = find_modern_bash(args.modern_bash)
    if not modern:
        print("CANNOT_JUDGE no bash >= 4 found (pass --modern-bash)", file=sys.stderr)
        return 2
    if args.self_test:
        failures = self_test(modern)
        for f in failures:
            print(f"SELFTEST_FAIL {f}")
        print(f"SELFTEST {'FAIL' if failures else 'OK'} regexes={len(FEATURES)} modern={modern}")
        return 2 if failures else 0
    if not args.roots:
        ap.error("give at least one root, or --self-test")
    t = probe(args.roots, args.include_archive, modern)
    return 1 if (t["regex_hits"] or t["parse32_only"]) else 0


if __name__ == "__main__":
    sys.exit(main())
