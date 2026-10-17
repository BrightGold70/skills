#!/usr/bin/env python3
"""Execute the FR-9 corpus; print a sha-stamped reading and exit 0 on either verdict.

Run from any directory with the repository's pytest-capable Python interpreter.

Recorded reading (one run, /opt/anaconda3/bin/python3):
sha=03c9da2687fcad3df99a8f05b7c46394baf991f6
new-caller: AttributeError: module 'fr9_api' has no attribute 'new_caller' | callee_resolves=True | old=halt new=valid
missing-callee: NameError: name 'callee' is not defined | callee_resolves=False | old=halt new=halt
both-missing: AttributeError: module 'fr9_api' has no attribute 'new_caller' | callee_resolves=False | old=halt new=halt
unrelated-import: ModuleNotFoundError: No module named 'fr9_unrelated_dependency' | callee_resolves=True | old=halt new=halt
other-symbol: NameError: name 'other_symbol' is not defined | callee_resolves=True | old=halt new=halt
PROBE: PASS
"""

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "h-mad" / "tests"))

from test_h_mad_wire_pin_new_caller_corpus import run_corpus


def main():
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
        text=True, check=True, timeout=20,
    ).stdout.strip()
    print(f"sha={sha}")
    with tempfile.TemporaryDirectory(prefix="fr9-corpus-") as base:
        rows = run_corpus(Path(base))
    for row in rows:
        print(
            f"{row['name']}: {row['exception_line']} | "
            f"callee_resolves={row['callee_resolves']} | "
            f"old={row['old_verdict']} new={row['new_verdict']}"
        )
    changed = {row["name"] for row in rows if row["old_verdict"] != row["new_verdict"]}
    passed = (
        len(rows) == 5 and changed == {"new-caller"}
        and all(row["old_verdict"] == "halt" for row in rows)
        and all(row["red_returncode"] == 1 for row in rows)
    )
    print(f"PROBE: {'PASS' if passed else 'FAIL'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
