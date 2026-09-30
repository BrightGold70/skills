#!/usr/bin/env python3
"""Measure the two TDD gates on isolated, disposable fixtures.

Usage: reproduce.py SKILLS_ROOT
The script runs gate hooks, never an agent CLI. Manual tool readings are kept
only in reading-unfixed.txt, outside this executable probe.
"""

from __future__ import annotations

import fcntl
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
from pathlib import Path


SKILLS = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(SKILLS / "h-mad" / "tests"))
from tdd_gate_support import decision, hermetic_env, hook_form, write_state  # noqa: E402

CLAUDE = SKILLS / "h-mad/hooks/h-mad-tdd-gate.sh"
CODEX = SKILLS / "h-mad/hooks/h-mad-codex-tdd-gate.py"
FORM = hook_form(CLAUDE)
HEADER = "*** Begin Patch\n"
UPDATE = "@@\n-X = 1\n+X = 2\n"
END = "*** End Patch\n"


def private_bin(base: Path) -> Path:
    target = base / "bin"
    target.mkdir()
    for name, source in (("python3", sys.executable), ("dirname", "/usr/bin/dirname"),
                         ("basename", "/usr/bin/basename"), ("jq", shutil.which("jq"))):
        if source:
            (target / name).symlink_to(source)
    return target


def env_for(root: Path, bin_dir: Path, gate: str) -> dict[str, str]:
    values = {"PATH": f"{bin_dir}:/usr/bin:/bin"}
    if gate == "claude":
        values.update(HOME=str(Path.home()), CLAUDE_PROJECT_DIR=str(root))
    else:
        values.update(CODEX_PROJECT_DIR=str(root))
    return hermetic_env(**values)


def fixture(base: Path, state: str = "step5") -> tuple[Path, Path]:
    root = base / "repo"
    (root / "src").mkdir(parents=True)
    (root / "src/prod.py").write_text("X = 1\n", encoding="utf-8")
    write_state(root, {"feat": {"phase": state, "codex_status": "exhausted"}})
    bin_dir = private_bin(base)
    subprocess.run(["git", "init", "-q", str(root)], check=True, stdin=subprocess.DEVNULL,
                   env=env_for(root, bin_dir, "codex"), timeout=30)
    return root, bin_dir


def run_gate(root: Path, bin_dir: Path, gate: str, target: str | None = None,
             patch: str | None = None) -> tuple[str, str]:
    if patch is None:
        payload = {"tool_name": "Write", "tool_input": {"file_path": target}}
    else:
        payload = {"tool_name": "apply_patch", "tool_input": {"command": patch}}
    if gate == "codex":
        payload["cwd"] = str(root)
    argv = [str(CLAUDE)] if gate == "claude" else [sys.executable, str(CODEX)]
    result = subprocess.run(argv, input=json.dumps(payload), capture_output=True, text=True,
                            cwd=root, env=env_for(root, bin_dir, gate), timeout=60, check=False)
    if gate == "claude":
        outcome = decision(result, FORM)
        verdict = (outcome.decision, outcome.kind)
    elif result.returncode == 0 and result.stdout.strip() in ("", "{}"):
        verdict = ("allow", "")
    else:
        try:
            obj = json.loads(result.stdout)["hookSpecificOutput"]
            reason = obj["permissionDecisionReason"]
            match = re.search(r"kind=([a-z-]+)", reason)
            verdict = ("deny", match.group(1) if match else "outside")
        except (ValueError, KeyError, TypeError):
            verdict = ("invalid", f"rc={result.returncode}")
    if verdict[0] not in ("allow", "deny"):
        raise RuntimeError(f"{gate}: {verdict}: {result.stdout!r} {result.stderr!r}")
    return verdict


def gate_line(cell: str, gate: str, state: str, verdict: tuple[str, str]) -> None:
    decision_word, kind = verdict
    print(f"REPRO: cell={cell} gate={gate} state={state} "
          f"decision={decision_word} kind={kind or '-'}")


def measure(cell: str, configure=None, *, states=("step5",), gates=("claude", "codex"),
            relative="src/prod.py", patch=None) -> None:
    for state in states:
        with tempfile.TemporaryDirectory() as raw:
            root, bin_dir = fixture(Path(raw), state)
            configured = configure(root, Path(raw)) if configure else None
            target = configured if isinstance(configured, str) else str(root / relative)
            for gate in gates:
                gate_line(cell, gate, state, run_gate(root, bin_dir, gate, target,
                                                     patch(root) if callable(patch) else patch))


def write(path: Path, body: str = "X = 1\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def symlink(path: Path, dest: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.symlink_to(dest)


def primitive_rows() -> None:
    with tempfile.TemporaryDirectory() as raw:
        base = Path(raw)
        write(base / "Case/sub/Prod.py")
        (base / unicodedata.normalize("NFD", "é")).mkdir()
        (base / "Tests").mkdir()
        write(base / "Tests/prod.py")
        (base / "Tests").chmod(0o311)
        for label, path in (("case", base / "case/SUB"),
                            ("unicode", base / unicodedata.normalize("NFC", "é")),
                            ("file-case", base / "case/sub/prod.py"),
                            ("unreadable", base / "tests"),
                            ("child-of-0311", base / "tests/prod.py")):
            try:
                fd = os.open(path, os.O_RDONLY)
                try:
                    data = fcntl.fcntl(fd, fcntl.F_GETPATH, bytes(1024)).rstrip(b"\0")
                    value = os.fsdecode(data)
                finally:
                    os.close(fd)
            except (OSError, AttributeError) as exc:
                value = f"error={getattr(exc, 'errno', 'no-F_GETPATH')}"
            print(f"REPRO: family=primitive cell={label} value={value!r}")
        for label, flag in (("O_RDONLY", os.O_RDONLY), ("O_EVTONLY", 0x8000),
                            ("O_SEARCH", getattr(os, "O_SEARCH", None))):
            if flag is None:
                value = "absent"
            else:
                try:
                    fd = os.open(base / "tests", flag)
                    os.close(fd)
                    value = "opened"
                except OSError as exc:
                    value = f"errno={exc.errno}"
            print(f"REPRO: family=primitive cell={label}-0311 value={value}")
        try:
            os.listdir(base / "tests")
            listing = "ok"
        except OSError as exc:
            listing = f"errno={exc.errno}"
        print(f"REPRO: family=primitive cell=listdir-0311 value={listing}")
        print(f"REPRO: family=primitive cell=capabilities F_GETPATH={hasattr(fcntl, 'F_GETPATH')} "
              f"ALLOW_MISSING={hasattr(os.path, 'ALLOW_MISSING')} O_SEARCH={hasattr(os, 'O_SEARCH')}")
        (base / "Tests").chmod(0o755)


def oq_p1(cell: str, state: str) -> None:
    with tempfile.TemporaryDirectory() as raw:
        root, bin_dir = fixture(Path(raw), state)
        if cell == "a":
            directory, target = root / "Tests", root / "tests/newmod.py"
            directory.mkdir()
        else:
            directory, target = root / "src", root / "src/prod.py"
        directory.chmod(0o311)
        try:
            os.listdir(directory)
            precondition = "ok"
        except OSError as exc:
            precondition = f"errno={exc.errno}"
        print(f"REPRO: family=oq-p1 cell=AC-3.6({cell}) state={state} listdir={precondition}")
        for gate in ("claude", "codex"):
            gate_line(f"OQ-P1 {cell}", gate, state,
                      run_gate(root, bin_dir, gate, str(target)))
        directory.chmod(0o755)


def fr8() -> None:
    from shlex import quote
    script = SKILLS / "h-mad/scripts/h_mad_resume_decision.py"
    for cell, session in (("FR-8 cat-subst", '"$(cat "$(git rev-parse --absolute-git-dir)/h-mad-session-id.feat")"'),
                          ("FR-8 literal-uuid", "00000000-0000-4000-8000-000000000001"),
                          ("FR-8 flag", None)):
        args = "--session-id-from-git-dir" if session is None else f"--session-id {session}"
        # Use the gate's trusted interpreter instead of the fixture's PATH shim.
        command = (f"{quote(sys.executable)} {quote(str(script))} --host codex --state docs/.bkit-memory.json "
                   f"--feature feat {args}")
        with tempfile.TemporaryDirectory() as raw:
            root, bin_dir = fixture(Path(raw))
            payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(root)}
            result = subprocess.run([sys.executable, str(CODEX)], input=json.dumps(payload),
                                    capture_output=True, text=True, cwd=root,
                                    env=env_for(root, bin_dir, "codex"), timeout=60, check=False)
            if result.returncode == 0 and result.stdout.strip() in ("", "{}"):
                verdict = ("allow", "")
            else:
                obj = json.loads(result.stdout)["hookSpecificOutput"]
                match = re.search(r"kind=([a-z-]+)", obj["permissionDecisionReason"])
                verdict = ("deny", match.group(1) if match else "outside")
            gate_line(cell, "codex", "step5", verdict)


def m8() -> None:
    with tempfile.TemporaryDirectory() as raw:
        base = Path(raw)
        root = base / "Case/tests/proj"
        write(root / "src/prod.py")
        write_state(root, {"feat": {"phase": "step5", "codex_status": "exhausted"}})
        bin_dir = private_bin(base)
        subprocess.run(["git", "init", "-q", str(root)], check=True,
                       stdin=subprocess.DEVNULL, env=env_for(root, bin_dir, "codex"), timeout=30)
        target = str(base / "case/tests/proj/src/prod.py")
        for gate in ("claude", "codex"):
            gate_line("M-8", gate, "step5", run_gate(root, bin_dir, gate, target))


def m7() -> None:
    with tempfile.TemporaryDirectory() as raw:
        base = Path(raw)
        physical = base / "R/real"
        write(physical / "x.py")
        write_state(physical, {"feat": {"phase": "step5", "codex_status": "exhausted"}})
        (base / "R/tests").mkdir()
        spelled = base / "R/tests/link"
        symlink(spelled, "../real")
        bin_dir = private_bin(base)
        subprocess.run(["git", "init", "-q", str(physical)], check=True,
                       stdin=subprocess.DEVNULL, env=env_for(physical, bin_dir, "codex"), timeout=30)
        for gate in ("claude", "codex"):
            gate_line("M-7", gate, "step5", run_gate(spelled, bin_dir, gate,
                                                    str(spelled / "x.py")))


def outside_root() -> None:
    with tempfile.TemporaryDirectory() as raw:
        base = Path(raw)
        root, bin_dir = fixture(base)
        (base / "out/tests").mkdir(parents=True)
        (base / "out/src").mkdir()
        symlink(base / "out/lnk", "tests")
        for label, relative in (("R-3 symlink-tests", "out/lnk/x.py"),
                                ("R-3 tests", "out/tests/x.py"),
                                ("R-3 src", "out/src/x.py")):
            gate_line(label, "claude", "step5", run_gate(root, bin_dir, "claude",
                                                      str(base / relative)))


def d5() -> None:
    sys.path.insert(0, str(SKILLS / "h-mad/scripts"))
    from h_mad_tdd_judge import _run_bounded
    with tempfile.TemporaryDirectory() as raw:
        bin_dir = private_bin(Path(raw))
        prior_path = os.environ.get("PATH")
        os.environ["PATH"] = f"{bin_dir}:/usr/bin:/bin"
        start = time.monotonic()
        try:
            result = _run_bounded([sys.executable, "-c",
                                   "import subprocess,time; subprocess.Popen(['sleep','12'], "
                                   "start_new_session=True); time.sleep(30)"],
                                  Path(raw), start + 2.0)
        finally:
            if prior_path is None:
                os.environ.pop("PATH", None)
            else:
                os.environ["PATH"] = prior_path
        print(f"REPRO: family=d5 elapsed={time.monotonic() - start:.1f} "
              f"timed_out={result[3]} rc={result[0]}")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: reproduce.py SKILLS_ROOT")
    primitive_rows()
    with tempfile.TemporaryDirectory() as raw:
        path = f"{private_bin(Path(raw))}:/usr/bin:/bin"
        print("REPRO: agent-cli-reachable=" +
              ("yes" if any(shutil.which(name, path=path) for name in ("codex", "agy", "grok")) else "no"))
    measure("M-1")
    measure("M-2", relative="src/prod.PY")
    measure("M-3", relative="src/new.PY")
    measure("M-4", lambda r, _: symlink(r / "tests", "src"), relative="tests/prod.py")
    measure("M-5", lambda r, _: symlink(r / "tests", "src"), relative="tests/newmod.py")
    measure("M-6", lambda r, _: ((r / "tests").mkdir(),
                                 (r / "src/sub").mkdir(), symlink(r / "tests/l", "../src/sub")),
            relative="tests/l/../prod.py")
    m7()
    m8()
    measure("M-9", lambda r, _: write(r / "Tests/prod.py"), relative="tests/prod.py")
    measure("M-10", lambda r, _: write(r / "fixtures/helper.py"), relative="FIXTURES/helper.py")
    measure("M-11", lambda r, _: (r / "tests").mkdir() or write(r / "tests/helper.py") or
            symlink(r / "src/tl", "../tests"), relative="src/tl/helper.py")
    measure("M-12", lambda r, _: symlink(r / "docs/d.md", "../src/newprod.py"), relative="docs/d.md")
    measure("M-13", lambda r, _: symlink(r / "src/dang.py", "nowhere/x.py"), relative="src/dang.py")
    measure("M-13 intermediate", lambda r, _: symlink(r / "lnk", "nowhere"), relative="lnk/x.py")
    measure("M-14", lambda r, _: (symlink(r / "src/loopa.py", "loopb.py"),
                                  symlink(r / "src/loopb.py", "loopa.py")), relative="src/loopa.py")
    for cell, configure, relative in (
        ("M-13 leaf", lambda r, _: symlink(r / "src/dang.py", "nowhere/x.py"), "src/dang.py"),
        ("M-13 intermediate", lambda r, _: symlink(r / "lnk", "nowhere"), "lnk/x.py"),
        ("M-14", lambda r, _: (symlink(r / "src/loopa.py", "loopb.py"),
                              symlink(r / "src/loopb.py", "loopa.py")), "src/loopa.py"),
    ):
        measure("M-18" if cell == "M-13 leaf" else "M-18 " + cell,
                configure, states=("step3",), relative=relative)
    measure("leaf-symlink", lambda r, _: write(r / "tests/t.py") or
            symlink(r / "src/link.py", "../tests/t.py"), states=("step5", "step3"),
            relative="src/link.py")
    for cell, header in (("M-15", "*** Update File: src/prod.py "),
                         ("M-15 nbsp", "*** Update File: src/prod.py\u00a0"),
                         ("M-15 crlf", "*** Update File: src/prod.py\r"),
                         ("M-16", " *** Update File: src/prod.py"),
                         ("M-21", "*** Update File: src/prod.py\u200b"),
                         ("M-22", "*** update file: src/prod.py")):
        patch = HEADER + header + "\n" + UPDATE + END
        measure(cell, gates=("codex",), patch=patch.replace("\n", "\r\n") if cell == "M-15 crlf" else patch)
    measure("M-17", gates=("codex",), patch=HEADER +
            "*** Add File: docs/x.md\n+x\n  *** Update File: src/prod.py\n" + UPDATE + END)
    measure("M-19", lambda r, _: write(r / "docs/a.md", "a\n"), gates=("codex",),
            patch=HEADER + "*** Update File: docs/a.md\n*** Move to: src/prod2.py \n@@\n-a\n+b\n" + END)
    measure("M-20", gates=("codex",), patch=HEADER + "*** Add File: src/n.py\x1f\n+x\n" + END)
    measure("M-23", lambda r, _: write(r / "docs/a.md", "a\n"), gates=("codex",),
            patch=HEADER + "*** Update File: docs/a.md\n *** Move to: src/new.py\n@@\n-a\n+b\n" + END)
    for state in ("step5", "step3"):
        for cell in ("a", "b"):
            oq_p1(cell, state)
    outside_root()
    fr8()
    d5()


if __name__ == "__main__":
    main()
