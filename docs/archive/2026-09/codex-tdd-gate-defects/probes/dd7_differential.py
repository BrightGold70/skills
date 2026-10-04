#!/usr/bin/env python3
"""Compare the old and new Claude gates over the published DD-7 cell matrix."""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TESTS = Path(__file__).resolve().parents[4] / "h-mad" / "tests"
sys.path.insert(0, str(TESTS))
from tdd_gate_support import dd7_cells, decision, hook_form, write_state  # noqa: E402


def _run(hook: Path, root: Path, target: str, bin_dir: Path) -> str:
    result = subprocess.run(
        [str(hook), target], stdin=subprocess.DEVNULL, capture_output=True, text=True,
        cwd=root, env={"PATH": f"{bin_dir}:/usr/bin:/bin", "HOME": str(Path.home()),
                       "CLAUDE_PROJECT_DIR": str(root)}, check=False, timeout=60,
    )
    form = hook_form(hook)
    if form:
        value = decision(result, form).decision
    else:
        value = "deny" if result.returncode == 1 else "allow" if result.returncode == 0 else "invalid"
    if value == "invalid":
        raise RuntimeError(f"{hook}: invalid result for {target}: rc={result.returncode} {result.stderr}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old", type=Path, required=True)
    parser.add_argument("--new", type=Path, required=True)
    args = parser.parse_args()
    old = args.old.resolve()
    new = args.new.resolve()
    jq = shutil.which("jq")
    if jq is None:
        parser.error("jq is required to exercise the old hook")
    softened = []
    tightened = []
    with tempfile.TemporaryDirectory(prefix="hmad-dd7-") as scratch:
        base = Path(scratch).resolve()
        bin_dir = base / "bin"
        bin_dir.mkdir()
        for name, source in (("python3", sys.executable), ("jq", jq)):
            (bin_dir / name).symlink_to(source)
        codex = bin_dir / "codex"
        codex.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        codex.chmod(0o755)
        for shape in ("repo", "tests/repo", "fixtures/repo"):
            root = base / shape
            root.mkdir(parents=True)
            for cell in dd7_cells(root, shape):
                records = {"feat": {"phase": "step5"}} if cell.state == "active" else {"other": {"phase": "step3"}}
                write_state(root, records)
                before = _run(old, root, cell.target, bin_dir)
                after = _run(new, root, cell.target, bin_dir)
                if before == "deny" and after == "allow":
                    softened.append(cell.name)
                    print(f"DD7: softened {cell.name}")
                elif before == "allow" and after == "deny":
                    tightened.append(cell.name)
                    print(f"DD7: tightened {cell.name}")
    print(f"DD7: DONE cells=126 softened={len(softened)} tightened={len(tightened)}")
    expected_softened = {
        f"{shape}/relative/{path}/active"
        for shape in ("repo", "tests/repo", "fixtures/repo")
        for path in ("tests/x.py", "fixtures/x.py")
    }
    expected_tightened = {
        f"{shape}/{spelling}/tests/../x.py/active"
        for shape in ("repo", "tests/repo", "fixtures/repo")
        for spelling in ("dot", "absolute")
    } | {
        f"{shape}/absolute/x.py/active" for shape in ("tests/repo", "fixtures/repo")
    }
    return 0 if set(softened) == expected_softened and set(tightened) == expected_tightened else 1


if __name__ == "__main__":
    raise SystemExit(main())
