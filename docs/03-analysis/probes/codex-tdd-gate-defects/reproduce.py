#!/usr/bin/env python3
"""Re-derive the codex-tdd-gate-defects spec premises against a skills tree.

Usage: reproduce.py <skills-root> <python-without-pytest> <python-with-pytest>
Prints one `REPRO:` line per reading. Scratch fixtures live in a TemporaryDirectory.
A Claude-gate reading is (rc, stdout permissionDecision or "", first stderr line), so a
refusal in either blocking form reads differently from an allow.
"""
import json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

SK, NOPY, WITHPY = Path(sys.argv[1]).resolve(), sys.argv[2], sys.argv[3]
CODEX_GATE = SK / "h-mad/hooks/h-mad-codex-tdd-gate.py"
CLAUDE_GATE = SK / "h-mad/hooks/h-mad-tdd-gate.sh"
PASSING = "def test_ok():\n    assert True\n"


def fixture(base: Path, sub_state: bool, codex_status: str | None = None) -> Path:
    root = base / "repo"
    (root / "docs").mkdir(parents=True)
    rec = {"phase": "step5"}
    if codex_status:
        rec["codex_status"] = codex_status
    (root / "docs/.bkit-memory.json").write_text(json.dumps({"orchestrator_state": {"feat": rec}}))
    hpw = root / "hematology-paper-writer"
    (hpw / "tools").mkdir(parents=True)
    (hpw / "tests").mkdir()
    (hpw / "tools/w.py").write_text("X = 1\n")
    (hpw / "tests/test_w.py").write_text(PASSING)
    if sub_state:
        (hpw / "docs").mkdir()
        (hpw / "docs/.bkit-memory.json").write_text(json.dumps({"orchestrator_state": {}}))
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    return root.resolve()


def codex(py: str, root: Path, payload: dict, env_root: bool = True, cwd: Path | None = None):
    env = {k: v for k, v in os.environ.items() if k != "CODEX_PROJECT_DIR"}
    if env_root:
        env["CODEX_PROJECT_DIR"] = str(root)
    r = subprocess.run([py, str(CODEX_GATE)], input=json.dumps(payload), text=True,
                       capture_output=True, cwd=cwd or root, env=env)
    out = r.stdout.strip()
    verdict = "deny" if '"deny"' in out else ("allow" if out in ("", "{}") else "other")
    reason = json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"] if verdict == "deny" else ""
    return r.returncode, verdict, reason


def patch(target: str) -> dict:
    return {"tool_name": "apply_patch", "tool_input": {"patch": f"*** Update File: {target}\n"}}


def bindir(base: Path, with_pytest: bool) -> Path:
    b = base / ("bin_py" if with_pytest else "bin_nopy")
    b.mkdir()
    (b / "codex").write_text("#!/bin/sh\nexit 0\n")
    (b / "codex").chmod(0o755)
    for tool in ("jq", "python3", "git", "dirname", "cat", "basename"):
        found = shutil.which(tool)
        if found:
            (b / tool).symlink_to(found)
    if with_pytest:
        (b / "pytest").write_text(f'#!/bin/sh\nexec "{WITHPY}" -m pytest "$@"\n')
        (b / "pytest").chmod(0o755)
    return b


def claude(root: Path, b: Path, arg: str | None = None, stdin: str = ""):
    env = {"HOME": os.environ["HOME"], "PATH": f"{b}:/usr/bin:/bin", "CLAUDE_PROJECT_DIR": str(root)}
    argv = ["bash", str(CLAUDE_GATE)] + ([arg] if arg else [])
    r = subprocess.run(argv, input=stdin, text=True, capture_output=True, cwd=root, env=env)
    try:
        decision = json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"] if r.stdout.strip() else ""
    except (ValueError, KeyError, TypeError):
        decision = "unparsed"
    return r.returncode, decision, (r.stderr.strip().splitlines() or [""])[0][:90]


def run(label, fn):
    with tempfile.TemporaryDirectory() as t:
        print(f"REPRO: {label} {fn(Path(t))}")


t_rel = "hematology-paper-writer/tools/w.py"
# D3: passing test, gate interpreter without pytest -> allowed (fail-open). Control: with pytest.
run("D3 nopytest", lambda t: codex(NOPY, fixture(t, False), patch(t_rel)))
run("D3 control-withpytest", lambda t: codex(WITHPY, fixture(t, False), patch(t_rel)))
# OD-2: cwd-relative target from the sub-project cwd, root found by git from payload cwd.
run("OD-2 cwd-relative", lambda t: (lambda r: codex(WITHPY, r, {**patch("tools/w.py"), "cwd": str(r / "hematology-paper-writer")},
                                                   env_root=False, cwd=r / "hematology-paper-writer"))(fixture(t, False)))
# OD-3: root state step5, sub-project state without step5, passing test -> allowed. Control: no sub state.
run("OD-3 nearest-state", lambda t: (lambda r: codex(WITHPY, r, patch(str(r / t_rel))))(fixture(t, True)))
run("OD-3 control-nosubstate", lambda t: (lambda r: codex(WITHPY, r, patch(str(r / t_rel))))(fixture(t, False)))
# OD-4: Claude-Code-shaped payload vs top-level file_path, codex on PATH.
run("OD-4 tool_input", lambda t: (lambda r: claude(r, bindir(t, True), stdin=json.dumps(
    {"tool_name": "Write", "tool_input": {"file_path": str(r / t_rel)}})))(fixture(t, False)))
run("OD-4 control-toplevel", lambda t: (lambda r: claude(r, bindir(t, True), stdin=json.dumps(
    {"file_path": str(r / t_rel)})))(fixture(t, False)))
# OD-3c: Claude gate. Root state holds only a step3 record; the sub-project state holds the step5
# record (codex exhausted). The root-first reader never sees the step5 -> allowed. Control: no root state.
def od3c(t: Path, root_state: bool):
    r = fixture(t, True, "exhausted")
    (r / "hematology-paper-writer/docs/.bkit-memory.json").write_text((r / "docs/.bkit-memory.json").read_text())
    if root_state:
        (r / "docs/.bkit-memory.json").write_text(json.dumps({"orchestrator_state": {"other": {"phase": "step3"}}}))
    else:
        (r / "docs/.bkit-memory.json").unlink()
    return claude(r, bindir(t, True), arg=str(r / t_rel))
run("OD-3c claude-root-first", lambda t: od3c(t, True))
run("OD-3c control-noroot", lambda t: od3c(t, False))
# D1: absolute path into the Claude gate's name map (codex declared exhausted).
run("D1 claude-absolute", lambda t: (lambda r: claude(r, bindir(t, True), arg=str(r / t_rel)))(fixture(t, False, "exhausted")))
# OD-5: codex exhausted, relative derivable target, passing test, no pytest on PATH -> allowed.
run("OD-5 nopytest", lambda t: (lambda r: claude(r, bindir(t, False), arg=t_rel))(fixture(t, False, "exhausted")))
run("OD-5 control-withpytest", lambda t: (lambda r: claude(r, bindir(t, True), arg=t_rel))(fixture(t, False, "exhausted")))
# pytest final lines.
with tempfile.TemporaryDirectory() as t:
    for name, body in (("red", "def test_x():\n    assert False\n"), ("green", PASSING),
                       ("importerr", "import not_a_module_xyz\ndef test_x():\n    pass\n"), ("empty", "")):
        f = Path(t) / f"test_{name}.py"
        f.write_text(body)
        r = subprocess.run([WITHPY, "-m", "pytest", str(f), "-x", "-q", "--no-header", "-p", "no:cacheprovider"],
                           capture_output=True, text=True, cwd=t)
        last = [ln for ln in (r.stdout + r.stderr).splitlines() if ln.strip()][-1]
        print(f"REPRO: summary {name} rc={r.returncode} last={last.strip()!r}")
    r = subprocess.run([NOPY, "-m", "pytest", "-q"], capture_output=True, text=True, cwd=t)
    print(f"REPRO: summary nopytest rc={r.returncode} last={(r.stderr.strip().splitlines() or [''])[-1]!r}")
# OD-7: how the audit gate's run_suite scores each summary shape today.
sys.path.insert(0, str(SK / "h-mad/scripts"))
import h_mad_audit_gate as gate  # noqa: E402
with tempfile.TemporaryDirectory() as t:
    for i, line in enumerate(("3 failed in 0.10s", "1 error in 0.06s", "2 passed, 1 error in 0.1s",
                              "1 failed, 1 error in 0.1s", "3 failed, 1 skipped in 0.1s",
                              "no tests ran in 0.01s", "1 failed, 11 passed in 0.2s")):
        sh = Path(t) / f"s{i}.sh"
        sh.write_text(f'#!/bin/sh\necho "{line}"; exit 1\n')
        sh.chmod(0o755)
        out = gate.run_suite(Path(t), [str(sh)])
        print(f"REPRO: run_suite {line!r} summary={gate._suite_summary(line)} "
              f"verdict={out['verdict']} reason={out.get('reason', '-')}")
