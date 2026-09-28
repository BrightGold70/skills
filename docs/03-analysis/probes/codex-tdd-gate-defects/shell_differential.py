#!/usr/bin/env python3
"""Compare old and new Codex shell policies over the 251-row venv corpus."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "h-mad" / "tests"))

from tdd_gate_support import CorpusRow, hermetic_env, shell_corpus  # noqa: E402


def verdict(hook: Path, row: CorpusRow) -> str:
    payload = {
        "tool_name": "shell_command",
        "cwd": str(row.cwd),
        "tool_input": {"command": row.command},
    }
    result = subprocess.run(
        [sys.executable, str(hook)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=row.root,
        env=hermetic_env(CODEX_PROJECT_DIR=str(row.root), HMAD_STUB_HOSTILE="all",
                         PATH="/usr/bin:/bin"),
        timeout=15.0,
        check=False,
    )
    if result.returncode != 0:
        return "invalid"
    output = result.stdout.strip()
    if output in ("", "{}"):
        return "allow"
    try:
        decision = json.loads(output)["hookSpecificOutput"]["permissionDecision"]
    except (ValueError, KeyError, TypeError):
        return "invalid"
    return "deny" if decision == "deny" else "invalid"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old", required=True, type=Path)
    parser.add_argument("--new", required=True, type=Path)
    args = parser.parse_args()
    old_source = args.old.resolve()
    new_hook = args.new.resolve()
    scripts = new_hook.parents[1] / "scripts"

    with tempfile.TemporaryDirectory(prefix="h-mad-shell-diff-") as scratch:
        temporary = Path(scratch)
        old_hook = temporary / "h-mad" / "hooks" / old_source.name
        old_hook.parent.mkdir(parents=True)
        shutil.copyfile(old_source, old_hook)
        (old_hook.parent.parent / "scripts").symlink_to(scripts, target_is_directory=True)
        rows = shell_corpus(temporary / "corpus", scripts)
        softened = tightened = unexpected = 0
        for row in rows:
            before = verdict(old_hook, row)
            after = verdict(new_hook, row)
            if before == "deny" and after == "allow":
                softened += 1
                print(f"SHELLDIFF: softened {row.name}")
            elif before == "allow" and after == "deny":
                tightened += 1
                print(f"SHELLDIFF: tightened {row.name}")
            if before == "invalid" or after != row.expected_new:
                unexpected += 1
        print(f"SHELLDIFF: DONE rows={len(rows)} softened={softened} "
              f"tightened={tightened} unexpected={unexpected}")
        return 0 if unexpected == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
