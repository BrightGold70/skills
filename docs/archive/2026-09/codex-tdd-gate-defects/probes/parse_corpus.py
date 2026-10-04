"""Task 11 item 10 (AC-2.9): old-versus-new `_parse_tasks` over the real impl-plan corpus.

Usage: parse_corpus.py BASE_SHA HEMASUITE_ROOT   (run from the skills worktree root)

The base parser is not importable alone: `h_mad_wire_pin_gate` imports `h_mad_wire_registry`,
which imports `h_mad_audit_gate`. So the three base modules are written from `git show` into one
temporary directory, and each version is read in its own child process (never one `sys.modules`).
Each child prints, per file, the JSON of its `_parse_tasks` ids and old fields; the new fields
(`production`, `tests`) are dropped before comparing.

Pass: `id_mismatch_files=0`. The two residual counts (design D5) are recorded, never compared:
  py_symbol_label_lines     — label lines `_PATHS_FIELD_RE` reads whose value carries a `.py::` token
  parenthesised_label_lines — `Production`/`Test` label lines with a parenthesised qualifier
Units: files, files, matching lines, matching lines.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

BASE_MODULES = ("h_mad_wire_pin_gate", "h_mad_wire_registry", "h_mad_audit_gate")
NEW_FIELDS = ("production", "tests")

READER = r"""
import json, sys
sys.path.insert(0, sys.argv[1])
from h_mad_wire_pin_gate import _parse_tasks
out = {}
for f in sys.argv[2:]:
    tasks = _parse_tasks(open(f, encoding="utf-8").read())
    out[f] = [{k: v for k, v in t.items() if k not in %r} for t in tasks]
print(json.dumps(out, sort_keys=True))
""" % (NEW_FIELDS,)

PY_SYMBOL_RE = re.compile(r"`[^`]+\.py::[^`]*`")
PAREN_LABEL_RE = re.compile(
    r"^\s*(?:[-*•]\s+)?\*{0,2}\s*(?:Production|Test)(?:\s+files?)?\*{0,2}\s*\([^)]*\)\s*\*{0,2}\s*:",
    re.IGNORECASE,
)


def corpus(repo: Path) -> list:
    out = subprocess.run(
        ["git", "-C", str(repo), "ls-files", "*.impl-plan.md"],
        capture_output=True, text=True, check=True, stdin=subprocess.DEVNULL, timeout=60.0,
    ).stdout.split()
    return [str(repo / p) for p in out if "archive/" not in p]


def read(scripts: str, files: list) -> dict:
    proc = subprocess.run(
        [sys.executable, "-c", READER, scripts, *files],
        capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=60.0,
    )
    if proc.returncode != 0:
        sys.exit(f"PARSECORPUS: HALT reader rc={proc.returncode} scripts={scripts}\n{proc.stderr}")
    return json.loads(proc.stdout)


def main() -> int:
    base_sha, hemasuite = sys.argv[1], Path(sys.argv[2]).resolve()
    skills = Path.cwd().resolve()
    files = corpus(skills) + corpus(hemasuite)
    with tempfile.TemporaryDirectory() as tmp:
        for name in BASE_MODULES:
            blob = subprocess.run(
                ["git", "show", f"{base_sha}:h-mad/scripts/{name}.py"],
                capture_output=True, text=True, check=True, stdin=subprocess.DEVNULL, timeout=60.0,
            ).stdout
            Path(tmp, f"{name}.py").write_text(blob, encoding="utf-8")
        old = read(tmp, files)
    new = read(str(skills / "h-mad" / "scripts"), files)
    sys.path.insert(0, str(skills / "h-mad" / "scripts"))
    from h_mad_wire_pin_gate import _FIELD_RE, _PATHS_FIELD_RE

    mismatch = [f for f in files if old.get(f) != new.get(f)]
    py_symbol = paren = 0
    for f in files:
        for line in Path(f).read_text(encoding="utf-8").splitlines():
            if _FIELD_RE.match(line) is None:
                m = _PATHS_FIELD_RE.match(line)
                if m is not None and PY_SYMBOL_RE.search(m.group("value")):
                    py_symbol += 1
            if PAREN_LABEL_RE.match(line):
                paren += 1
    for f in mismatch:
        print(f"PARSECORPUS: MISMATCH {f}")
    print(
        f"PARSECORPUS: files={len(files)} id_mismatch_files={len(mismatch)} "
        f"py_symbol_label_lines={py_symbol} parenthesised_label_lines={paren}"
    )
    return 0 if not mismatch else 1


if __name__ == "__main__":
    sys.exit(main())
