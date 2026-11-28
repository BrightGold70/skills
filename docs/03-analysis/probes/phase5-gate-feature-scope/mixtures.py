"""Measure release compatibility on isolated copies of each file combination."""
from __future__ import annotations

import argparse
import itertools
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))
from discovery_probe import probe_main


SCRIPTS = "h-mad/scripts/"
IDENTITY = SCRIPTS + "h_mad_target_identity.py"
JUDGE = SCRIPTS + "h_mad_tdd_judge.py"
WRITER = SCRIPTS + "h_mad_state_write.py"
ASSEMBLER = SCRIPTS + "h_mad_assemble_tdd.py"
WRITES = (WRITER, IDENTITY, SCRIPTS + "h_mad_state_schema.json",
          SCRIPTS + "h_mad_bkit_guard.py", JUDGE)
FILES = {
    "writes": WRITES, "staging": (ASSEMBLER, IDENTITY),
    "gates": (*WRITES, "h-mad/hooks/h-mad-codex-tdd-gate.py",
              "h-mad/hooks/h-mad-agy-tdd-gate.py", "h-mad/hooks/h-mad-tdd-gate.sh"),
}


def mixtures(files: Sequence[str]) -> Iterator[frozenset[str]]:
    for size in range(len(files) + 1):
        yield from map(frozenset, itertools.combinations(files, size))


def _command(args, cwd, home, **env):
    environment = {k: v for k, v in os.environ.items() if not k.startswith(("HMAD_", "GIT_"))}
    environment.update(HOME=str(home), PYTHONDONTWRITEBYTECODE="1", **env)
    return subprocess.run(args, cwd=cwd, env=environment, stdin=subprocess.DEVNULL,
                          capture_output=True, text=True, timeout=60)


def _gates(tree, work):
    import differential as d

    readings = {}
    for surface in d.SURFACES:
        shell = surface.endswith("-shell")
        for operation in (("safe", "refused") if shell else ("document", "production")):
            name = surface + "-" + operation
            spec = d._fixture_spec(surface, name, ("state:root:live",), operation)
            spec = spec._replace(env={"HOME": str(work / "home")})
            case = d.build_case(spec, work / name)
            decision = d.run_hook(tree, case, sys.executable).decision
            readings[name] = {"allow": True, "deny": False}.get(decision)
    return readings


def _record():
    return dict(feature="fixture", started_ts="2026-01-01T00:00:00Z", current_phase=5,
                last_completed_phase=4, phase="step5", halt_reason=None, halt_ts=None,
                audit_cycles={"plan": 0, "design": 0, "impl_plan": 0}, iterate_cycles=0)


def _switch_answer(result, path, original, pure):
    token = "TDD-IMPLEMENTER: agy chosen=codex switch=codex->agy reason=status"
    lines = result.stdout.splitlines()
    if lines == [token]:
        try:
            after = json.loads(path.read_bytes())
            switch = after["orchestrator_state"]["fixture"].pop("implementer_switch")
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            return None
        if (isinstance(switch, dict) and switch.pop("ts", None) and after == original
                and switch == {"from": "codex", "to": "agy", "reason": "status"}):
            return True
        return None
    answers = [line for line in lines if line.startswith("TDD-IMPLEMENTER:")]
    if (lines if pure else answers) == [token + " record=failed"]:
        return False
    if not pure and not answers and result.returncode:
        return False
    return None


def _writes(tree, work, *, pure):
    cases = {
        "create": ("absent", ["--create"]),
        "create-invalid": ("absent", ["--create"]),
        "set": ("plain", ["--set", "phase=step5"]),
        "set-unknown": ("plain", ["--set", "unknown=1"]),
        "append": ("plain", ["--append", 'production_paths_needing_red_tests="src/app.py"']),
        "append-type": ("plain", ["--append", "production_paths_needing_red_tests=1"]),
        "claim": ("plain", ["--claim", "worker"]),
        "claim-owner": ("owned", ["--claim", "other"]),
        "beat": ("owned", ["--beat", "--session-id", "worker"]),
        "beat-owner": ("owned", ["--beat", "--session-id", "other"]),
        "release": ("owned", ["--release", "--session-id", "worker"]),
        "release-owner": ("owned", ["--release", "--session-id", "other"]),
        "drop": ("extra", ["--drop-undeclared"]),
        "drop-absent": ("absent", ["--drop-undeclared"]),
        "switch": ("switch", None), "switch-extra": ("switch-extra", None),
    }
    bins = work / "bin"
    bins.mkdir()
    for name in ("codex", "agy"):
        (bins / name).symlink_to(sys.executable)
    readings = {}
    for link, (case, (shape, args)) in itertools.product((False, True), cases.items()):
        name = ("symlink-" if link else "regular-") + case
        root = work / name
        docs = root / "docs"
        docs.mkdir(parents=True)
        path = docs / ".bkit-memory.json"
        backing = docs / "store.json" if link else path
        if link:
            path.symlink_to(backing.name)
        record = _record()
        if shape == "owned":
            record.update(owner_session_id="worker", owner_heartbeat_ts=datetime.now(timezone.utc).isoformat())
        if shape.startswith("switch"):
            record.update(implementer="codex", codex_status="unavailable", agy_status="available")
        if shape in ("extra", "switch-extra"):
            record["extra"] = True
        data = {"orchestrator_state": {} if shape == "absent" else {"fixture": record}}
        before = json.dumps(data).encode()
        backing.write_bytes(before)
        if args is not None:
            feature = "" if case == "create-invalid" else "fixture"
            result = _command([sys.executable, tree / WRITER, path, "--feature", feature, *args],
                              root, work / "home")
            lines = result.stdout.splitlines()
            ok = any(line.startswith("STATE-WRITE: OK ") for line in lines)
            if not ok and "STATE-WRITE: OK" in lines:
                ok = None
        else:
            result = _command([sys.executable, tree / JUDGE, "implementer", "--root", root,
                               "--feature", "fixture", "--record"], root, work / "home",
                              PATH=os.pathsep.join((str(bins), os.environ["PATH"])))
            ok = _switch_answer(result, path, data, pure)
        if ok is False:
            if not (path.is_file() and backing.is_file() and path.is_symlink() == link
                    and path.read_bytes() == backing.read_bytes() == before):
                ok = None
        readings[name] = ok
    return readings


def _staging(tree, work):
    home = work / "home"
    installed = Path(".gemini/config/skills/h-mad/hooks/h-mad-agy-tdd-gate.py")
    (home / installed).parent.mkdir(parents=True)
    (home / installed).symlink_to(tree / "h-mad/hooks" / installed.name)
    bin_dir = work / "bin"
    bin_dir.mkdir()
    (bin_dir / "python3").symlink_to(sys.executable)
    path_env = os.pathsep.join((str(bin_dir), str(tree / "h-mad/bin"), os.defpath))
    readings = {}
    for phase, state, valid in itertools.product(("red", "green", "gate", "review"),
                                                  ("live", "absent", "unreadable"), (True, False)):
        name = "-".join((phase, state, "complete" if valid else "missing-task"))
        root = work / name
        (root / "docs").mkdir(parents=True)
        _command(["git", "init", "-q"], root, home).check_returncode()
        (root / "test_fixture.py").touch()
        path = root / "docs/.bkit-memory.json"
        if state != "absent":
            path.write_text(json.dumps({"orchestrator_state": {"fixture": _record()}})
                            if state == "live" else "{")
        shape = "gate" if phase == "gate" else "new-behaviour"
        plan = root / "plan.md"
        plan.write_text(f"## Task 1: fixture\n\n**Task shape**: {shape}\n")
        prompt = root / "prompt.txt"
        args = [sys.executable, tree / ASSEMBLER, "--phase", phase, "--feature", "fixture",
                "--task", "Task 1" if valid else "Task 2", "--module", "fixture",
                "--project-root", root, "--impl-plan", plan,
                "--prompt", prompt, "--out", root / "out", "--log", root / "log"]
        if phase == "review":
            config = root / ".agents/hooks.json"
            config.parent.mkdir()
            handler = {"type": "command", "command": f"python3 ~/{installed}", "timeout": 60}
            config.write_text(json.dumps({"h-mad-agy-tdd-gate": {
                "enabled": True, "PreToolUse": [{"matcher": "*", "hooks": [handler]}],
            }}))
            report = root / "report.md"
            report.write_text("STATUS: DONE\n")
            args += ["--codex-report", report, "--diff-path", plan.name]
        else:
            args += ["--python", sys.executable]
            if phase != "gate":
                args += ["--test-path", "test_fixture.py", "--expect-fail", "1", "--expect-pass", "0"]
        result = _command(args, root, home, PATH=path_env)
        lines = result.stdout.splitlines()
        token = any(line.startswith("ASSEMBLE-TDD: PASS ") for line in lines)
        artifacts = (prompt, Path(str(prompt) + ".assembled"))
        if token and result.returncode == 0 and all(path.is_file() for path in artifacts):
            readings[name] = True
        elif not token and "ASSEMBLE-TDD: PASS" not in lines and not any(os.path.lexists(path) for path in artifacts):
            readings[name] = False
        else:
            readings[name] = None
    return readings


def _definition(path):
    data = json.loads(path.read_text())
    files = data["files"]
    if (not isinstance(files, list) or not files or len(set(files)) != len(files)
            or any(not f or Path(f).is_absolute() or ".." in Path(f).parts for f in files)):
        raise ValueError("invalid file set")
    corpus = data["corpus"]
    if not corpus or len({case["name"] for case in corpus}) != len(corpus):
        raise ValueError("expected distinct corpus case names")

    def read(tree, work):
        return {case["name"]: _command([*data["entry"], *case["argv"]], tree, work / "home").returncode == 0
                for case in corpus}

    return data["name"], files, read


def _measure(args, scratch):
    if args.set_file:
        name, files, run = _definition(args.set_file)
    else:
        name = args.set
        files = FILES[name]
        run = {"writes": _writes, "staging": _staging, "gates": _gates}[name]
    old, new = args.old.resolve(), args.new.resolve()
    ignore = shutil.ignore_patterns(".git", "__pycache__", "*.pyc")

    def observe(selection):
        with tempfile.TemporaryDirectory(dir=scratch) as tmp:
            work = Path(tmp)
            (work / "home").mkdir()
            tree = work / "tree"
            base = new if selection == whole else old
            if args.set_file:
                shutil.copytree(base, tree, ignore=ignore)
            else:
                for folder in ("scripts", "hooks", "bin", "references"):
                    if folder == "references" and name != "staging":
                        continue
                    source = base / "h-mad" / folder
                    if folder == "references" and not source.exists():
                        source = new / "h-mad" / folder
                    shutil.copytree(source, tree / "h-mad" / folder, ignore=ignore)
            for file in selection:
                shutil.copy2(new / file, tree / file)
            if args.set == "writes":
                return run(tree, work, pure=not selection or selection == whole)
            return run(tree, work)

    whole = frozenset(files)
    old_rows = observe(frozenset())
    new_rows = observe(whole)
    if old_rows.keys() != new_rows.keys():
        raise ValueError("pure tree corpora differ")
    # The paired fixtures specify the answer of each release independently.
    if not args.set_file:
        for selection, rows in ((frozenset(), old_rows), (whole, new_rows)):
            for case, allowed in rows.items():
                if name == "writes":
                    operation = case.split("-", 1)[1]
                    expected = operation in {"create", "set", "append", "claim", "beat", "release", "drop", "switch"}
                elif name == "gates":
                    expected = case.endswith(("-safe", "-document"))
                else:
                    expected = case.endswith("-complete")
                if allowed is not expected:
                    chosen = ",".join(f for f in files if f in selection) or "none"
                    return f"MIXTURES: FAIL set={name} mixture={chosen} case={case}"
    count = 0
    for selection in mixtures(files):
        count += 1
        rows = old_rows if not selection else new_rows if selection == whole else observe(selection)
        for case, allowed in rows.items():
            if allowed is None or (allowed and not old_rows[case] and not new_rows[case]):
                chosen = ",".join(f for f in files if f in selection) or "none"
                return f"MIXTURES: FAIL set={name} mixture={chosen} case={case}"
    return f"MIXTURES: PASS set={name} mixtures={count} cases={len(old_rows)}"


@probe_main
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old", type=Path, required=True)
    parser.add_argument("--new", type=Path, required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--set", choices=FILES)
    group.add_argument("--set-file", type=Path)
    args = parser.parse_args(argv)
    with tempfile.TemporaryDirectory() as tmp:
        reading = _measure(args, Path(tmp))
    print(reading)
    return 0


if __name__ == "__main__":
    sys.exit(main())
