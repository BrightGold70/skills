#!/usr/bin/env python3
"""FR-6 probe: what a hand-built Codex-gate tree does when an import is missing.

Rebuilds, in a temporary directory removed afterwards, the two hand-built trees the
Codex gate tests use, and runs the gate as those tests do (stdin payload, cwd=root,
CODEX_PROJECT_DIR=root):
  timeout-tree/unmodified   gate + stub judge + identity copy        (test_codex_gate_judge_timeout_reason)
  timeout-tree/new-module   same, plus one top-level `from h_mad_gate_policy import _safe_shell_command`
  error-tree/unmodified     gate + raising judge, NO identity module (test_codex_gate_kind[judge-error])
  error-tree/G2-mutant      same, with row G2's replace applied to the gate copy

Run from the repository root:
  python3 docs/03-analysis/probes/agy-coder-fallback/fr6_import_failure_pair.py
Prints `<variant>: rc=<n> stdout=<deny kind|none> err=<last stderr line>` and a final
`PROBE: PASS|FAIL` against the expectations in EXPECT.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path.cwd()
GATE = REPO / "h-mad/hooks/h-mad-codex-tdd-gate.py"
IDENTITY = REPO / "h-mad/scripts/h_mad_target_identity.py"
TARGET = "hematology-paper-writer/tools/w.py"
STUB = ("from types import SimpleNamespace\n"
        "def read_chain(root, target):\n    return SimpleNamespace(value='active', records=())\n"
        "def judge(root, target, records):\n"
        "    return SimpleNamespace(decision='DENY', kind='judge-timeout', reason='stub')\n")
G2_FIND, G2_REPLACE = "    except Exception as exc:  # M:G2", "    except ZeroDivisionError as exc:  # M:G2"
EXPECT = {"timeout-tree/unmodified": "judge-timeout", "timeout-tree/new-module": "none",
          "error-tree/unmodified": "judge-error", "error-tree/G2-mutant": "none"}


def build(base: Path, variant: str) -> Path:
    tree = base / variant.replace("/", "-")
    gate = tree / "hooks/h-mad-codex-tdd-gate.py"
    gate.parent.mkdir(parents=True)
    text = GATE.read_text(encoding="utf-8")
    scripts = tree / "scripts"
    scripts.mkdir()
    if variant.startswith("timeout-tree"):
        (scripts / "h_mad_tdd_judge.py").write_text(STUB, encoding="utf-8")
        shutil.copyfile(IDENTITY, scripts / "h_mad_target_identity.py")
        if variant.endswith("new-module"):
            anchor = "\nfrom pathlib import Path\n"
            assert text.count(anchor) == 1, "import anchor drifted"
            text = text.replace(anchor, anchor + "from h_mad_gate_policy import _safe_shell_command\n")
    else:
        (scripts / "h_mad_tdd_judge.py").write_text('raise ImportError("broken judge")\n', encoding="utf-8")
        if variant.endswith("G2-mutant"):
            assert text.count(G2_FIND) == 1, "G2 anchor drifted"
            text = text.replace(G2_FIND, G2_REPLACE)
    gate.write_text(text, encoding="utf-8")
    return gate


def main() -> int:
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        root = base / "root"
        (root / "docs").mkdir(parents=True)
        (root / "docs/.bkit-memory.json").write_text(
            json.dumps({"orchestrator_state": {"feat": {"phase": "step5"}}}), encoding="utf-8")
        (root / TARGET).parent.mkdir(parents=True)
        (root / TARGET).write_text("# governed production\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        payload = json.dumps({"tool_name": "apply_patch",
                              "tool_input": {"patch": f"*** Update File: {TARGET}\n"}})
        env = {**os.environ, "CODEX_PROJECT_DIR": str(root)}
        for variant, want in EXPECT.items():
            gate = build(base, variant)
            proc = subprocess.run([sys.executable, str(gate)], input=payload, capture_output=True,
                                  text=True, cwd=root, env=env, timeout=120)
            kind = "none"
            if proc.stdout.strip():
                reason = json.loads(proc.stdout)["hookSpecificOutput"]["permissionDecisionReason"]
                found = re.search(r"kind=([a-z-]+)", reason)
                kind = found.group(1) if found else "deny-without-kind"
            err = (proc.stderr.strip().splitlines() or [""])[-1]
            ok &= kind == want
            print(f"{variant}: rc={proc.returncode} stdout={kind} want={want} err={err[:100]}")
    print("PROBE: " + ("PASS" if ok else "FAIL"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
