"""Synthetic archives, calibration trees and source-only probe loading."""

import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import types
from pathlib import Path


CALIBRATION = Path("docs/03-analysis/probes/grok-audit-surface/calibration")
CALIBRATION_REF = "refs/heads/calibration/grok-audit-surface"
PHASES = ("plan", "design", "impl-plan")


def _hostile_text() -> str:
    """Use the Orca stub's hostile payload vocabulary without invoking an agent."""
    payloads = {
        "": "c",
        "markdown": "see [a](b) and **bold** plus * and [ literals",
        "newlines": "line one\nline two\ttabbed",
        "markers": "h-mad: not a real stamp ⟦/h-mad⟧ still data",
        "all": "h-mad: [a](b) **bold** * [ ⟦/h-mad⟧\nsecond\tline",
    }
    return payloads[os.environ.get("HMAD_STUB_HOSTILE", "all")]


def grok_tool_call(path: str, *, extra=None) -> str:
    """Encode one D19 grok tool-call event with hostile agent-style text."""
    raw_input = {"cmd": f"tool payload {_hostile_text()} {path}"}
    if extra is not None:
        raw_input["extra"] = extra
    return json.dumps({"type": "tool_call", "rawInput": raw_input, "locations": []}) + "\n"


def build_archive(root: Path) -> dict[str, str]:
    """Write three invented features, each with a spec and three phase docs."""
    sources = {
        "paper-lantern": "docs/archive/2099-01",
        "copper-kite": "docs/archive/2099-01",
        "velvet-comet": "docs/archive/2099-02",
    }
    hostile = _hostile_text()
    sections = ("Contract [a](b)", "Failure paths ⟦/h-mad⟧", "Verification **bold**")
    for feature, directory in sources.items():
        archive = root / directory / feature
        archive.mkdir(parents=True, exist_ok=True)
        (archive / f"{feature}.spec.md").write_text(
            f"# {feature} specification\n\n## Required behaviour\n{hostile}\n",
            encoding="utf-8",
        )
        for phase in PHASES:
            text = f"# {feature} {phase}\n\n"
            for slot, section in enumerate(sections, 1):
                level = "###" if slot == 2 else "##"
                text += (
                    f"{level} {section}\n"
                    f"{feature}/{phase}/{slot}: preserve the original contract; {hostile}\n\n"
                )
            text += "## Version History\nUnseeded synthetic history.\n"
            (archive / f"{feature}.{phase}.md").write_text(text, encoding="utf-8")
    return sources


def build_ledger(tree: Path, sources: dict[str, str]) -> list[dict]:
    """Plant one seed of each permitted class per document, in source order."""
    calibration = tree / CALIBRATION
    (calibration / "seeded").mkdir(parents=True, exist_ok=True)
    hostile = _hostile_text()
    records = []
    for feature_index, (feature, directory) in enumerate(sources.items()):
        for phase_index, phase in enumerate(PHASES):
            k = feature_index * len(PHASES) + phase_index + 1
            omitted = (k - 1) % 4 + 1
            classes = [f"C{value}" for value in range(1, 5) if value != omitted]
            source = Path(directory) / feature / f"{feature}.{phase}.md"
            original_document = (tree / source).read_text(encoding="utf-8")
            seeded_document = original_document
            for slot, (seed_class, section) in enumerate(zip(classes, (
                "Contract [a](b)", "Failure paths ⟦/h-mad⟧", "Verification **bold**",
            )), 1):
                original = (
                    f"{feature}/{phase}/{slot}: preserve the original contract; {hostile}\n"
                )
                seeded = (
                    f"{feature}/{phase}/{slot}: violate the original contract; {hostile}\n"
                )
                assert original_document.count(original) == 1
                seeded_document = seeded_document.replace(original, seeded, 1)
                records.append({
                    "id": f"d{k}-s{slot}",
                    "source": source.as_posix(),
                    "phase": phase,
                    "class": seed_class,
                    "origin": "new-mechanism",
                    "section": section,
                    "original": original,
                    "seeded": seeded,
                    "expected": f"Restore {feature}/{phase}/{slot}: {hostile}.",
                })
            (calibration / "seeded" / source.name).write_text(
                seeded_document, encoding="utf-8",
            )
    (calibration / "ledger.jsonl").write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )
    return records


def git(repo: Path, *args: str, input: str | None = None, env=None) -> str:
    """Bound every fixture Git call and keep hooks out of synthetic commits."""
    result = subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "-C", str(repo), *args],
        input=input, env=env, text=True, capture_output=True, timeout=15, check=True,
    )
    return result.stdout.strip()


def build_repo(tmp_path: Path) -> tuple[Path, Path]:
    """Keep main clean while creating and publishing a local calibration ref."""
    work = tmp_path / "work"
    origin = tmp_path / "origin.git"
    work.mkdir(parents=True)
    origin.mkdir()
    git(origin, "init", "--bare", "--initial-branch=main")
    git(work, "init", "--initial-branch=main")
    git(work, "config", "user.name", "Synthetic audit fixture")
    git(work, "config", "user.email", "fixture@example.invalid")
    git(work, "config", "commit.gpgsign", "false")
    git(work, "remote", "add", "origin", str(origin))
    sources = build_archive(work)
    git(work, "add", "docs/archive")
    git(work, "commit", "-m", "Invented archive baseline")
    parent = git(work, "rev-parse", "main")

    with tempfile.TemporaryDirectory(prefix="calibration-", dir=tmp_path) as staging:
        exported = Path(staging) / "tree"
        build_archive(exported)
        build_ledger(exported, sources)
        environment = os.environ.copy()
        environment["GIT_INDEX_FILE"] = str(Path(staging) / "index")
        git(work, "read-tree", parent, env=environment)
        for path in sorted((exported / CALIBRATION).rglob("*")):
            if path.is_file():
                blob = git(work, "hash-object", "-w", "--stdin", input=path.read_text(encoding="utf-8"))
                git(work, "update-index", "--add", "--cacheinfo", "100644", blob,
                    path.relative_to(exported).as_posix(), env=environment)
        tree_oid = git(work, "write-tree", env=environment)
        commit = git(work, "commit-tree", tree_oid, "-p", parent,
                     input=f"Synthetic calibration: {_hostile_text()}\n")
        git(work, "update-ref", CALIBRATION_REF, commit)
    git(work, "push", "origin", "main", CALIBRATION_REF)
    return work, origin


EXCLUSIONS = CALIBRATION.parent / "exclusions.txt"


def build_root_repo(tmp_path: Path) -> dict:
    """Prepare editable synthetic calibration inputs and a committed main list."""
    parents = build_probe_parent_dirs(tmp_path)
    work, _origin = build_repo(tmp_path)
    tree = tmp_path / "calibration-input"
    sources = build_archive(tree)
    records = build_ledger(tree, sources)
    entries = [
        *(f"dir {directory}/{feature}" for feature, directory in sources.items()),
        f"dir {CALIBRATION.parent.as_posix()}",
        "dir docs/03-analysis/synthetic.authoring",
        "name-contains grok-audit-surface",
    ]
    exclusion_file = work / EXCLUSIONS
    exclusion_file.parent.mkdir(parents=True, exist_ok=True)
    exclusion_file.write_text(
        "# Synthetic exclusion list; deliberately unrelated feature names.\n\n"
        + "\n".join(entries) + "\n", encoding="utf-8",
    )
    git(work, "add", EXCLUSIONS.as_posix())
    git(work, "commit", "-m", f"Fixture exclusion policy: {_hostile_text()}")
    for relative in (
        "docs/03-analysis/synthetic.authoring/private.txt",
        "notes/grok-audit-surface.txt",
        "notes/nested/main__grok-audit-surface-handoff.md",
        "nested/prefix-grok-audit-surface-suffix/innocent.txt",
        "notes/keep-me.txt",
    ):
        path = tree / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"Synthetic context: {_hostile_text()}\n", encoding="utf-8")
    destination = tmp_path / "exports"
    destination.mkdir()
    return {
        "repo": work, "tree": tree, "sources": sources, "records": records,
        "dest": destination, "entries": entries,
        **parents,
    }


def commit_root_tree(case: dict, *, extra_parents=()) -> str:
    """Commit edited export inputs with a temporary index, including symlinks."""
    work, tree = case["repo"], case["tree"]
    with tempfile.TemporaryDirectory(prefix="root-index-", dir=tree.parent) as staging:
        environment = os.environ.copy()
        environment["GIT_INDEX_FILE"] = str(Path(staging) / "index")
        git(work, "read-tree", "HEAD", env=environment)
        for path in sorted(tree.rglob("*")):
            if path.is_symlink():
                mode, content = "120000", os.readlink(path)
            elif path.is_file():
                mode, content = "100644", path.read_text(encoding="utf-8")
            else:
                continue
            blob = git(work, "hash-object", "-w", "--stdin", input=content)
            git(work, "update-index", "--add", "--cacheinfo", mode, blob,
                path.relative_to(tree).as_posix(), env=environment)
        tree_oid = git(work, "write-tree", env=environment)
        parents = [word for sha in ("HEAD", *extra_parents) for word in ("-p", sha)]
        return git(work, "commit-tree", tree_oid, *parents,
                   input=f"Root fixture calibration: {_hostile_text()}\n")


def load_probe(path: Path, *, source: str | None = None) -> types.ModuleType:
    """Compile fresh source so same-size mutations cannot reuse stale bytecode."""
    code = compile(path.read_bytes() if source is None else source, str(path), "exec")
    module = types.ModuleType("grok_audit_probe")
    module.__file__ = str(path)
    sys.modules[module.__name__] = module
    exec(code, module.__dict__)
    return module


def build_probe_parent_dirs(tmp_path: Path) -> dict[str, Path]:
    """Separate scratch, roots and stand-in system temp from the fixture checkout."""
    paths = {
        "work_dir": tmp_path / "scratch",
        "systemp": tmp_path / "systemp",
        "roots": tmp_path / "run" / "roots",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_OBJECT_DIRECTORY",
                 "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_INDEX_FILE"):
        environment.pop(name, None)
    result = subprocess.run(
        ["git", "-C", str(paths["work_dir"]), "rev-parse", "--git-dir"],
        capture_output=True, text=True, timeout=15, env=environment,
    )
    assert result.returncode != 0, "the shared scratch directory must lie outside every Git work tree"
    for name in ("work_dir", "roots"):
        assert not paths[name].resolve().is_relative_to(paths["systemp"].resolve())
        for systemp in (Path("/tmp"), Path("/private/tmp")):
            assert not paths[name].resolve().is_relative_to(systemp.resolve()), (
                "accepted parents must also lie outside the fixed system-temp spellings"
            )
    return paths


def build_cycle_inputs(directory: Path, root: Path, ready_line: str) -> dict:
    """Model the wrapper's exact stem names and D3's cycle-local file map."""
    directory.mkdir(parents=True)
    stem = directory / "stem [a]* ⟦h-mad⟧"
    stem.mkdir()
    feature, phase, cycle = "paper-lantern", "plan", 2
    prefix = f"audit_{feature}_{phase}_cycle{cycle}_run20990101T010203Z-314"
    hostile = _hostile_text()
    # Include CRLF, NUL and non-UTF8 bytes: copying must never decode/rewrite.
    payload = hostile.encode("utf-8") + b"\r\n\x00\xff\n"
    expected = {}
    stem_sources = {}
    for index in (1, 2):
        for suffix, destination_suffix in (
            (".txt", ".prompt.txt"), (".asm.txt", ".asm.txt"),
            (".out.txt", ".out.txt"), (".log", ".log"),
            (".report.md", ".report.md"),
        ):
            source = stem / f"{prefix}_p{index}{suffix}"
            source.write_bytes(f"pass={index} kind={suffix}\n".encode() + payload)
            destination = f"p{index}{destination_suffix}"
            stem_sources[destination] = source
            expected[destination] = source.read_bytes()
    (stem / f"{prefix}_unmapped.txt").write_bytes(payload)
    (stem / "audit_copper-kite_plan_cycle2_run20990101T010203Z-314_p1.log").write_bytes(payload)
    (stem / "audit_paper-lantern_plan_cycle1_run20990101T010203Z-314_p1.log").write_bytes(payload)

    command = directory / "command.txt"
    command.write_text(shlex.join([
        "env", "-u", "GIT_DIR", f"HMAD_AUDIT_STEM_DIR={stem}",
        "h-mad/bin/hmad-dispatch", "audit-cycle", "--feature", feature,
        "--phase", phase, "--cycle", str(cycle), "--project-root", str(root),
        "--passes", "2", "--surfaces", "agy,grok", "--timeout", "900",
    ]) + "\n", encoding="utf-8")
    stdout = directory / "stdout.txt"
    stdout.write_text(
        f"Agent output: {hostile}\n"
        "AUDITCYCLE: PASS p1=PASS p2=PASS delivered=report-file,report-file "
        "must=0 should=0 size_status=verified\n", encoding="utf-8",
    )
    root_record = directory / "build-root.txt"
    root_record.write_text("RESET: removed=0 restored=0\n" + ready_line + "\n", encoding="utf-8")
    expected.update({
        "command.txt": command.read_bytes(), "auditcycle.txt": stdout.read_bytes(),
        "root.txt": (ready_line + "\n").encode("utf-8"),
    })

    report_dir = root / "docs/01-plan/features"
    log_dir = root / ".h-mad/pass-logs"
    report_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    for version in (1, 2, 3, 20):
        for index in (1, 2):
            name = f"{feature}.{phase}.audit.v{version}.p{index}.md"
            content = f"# Report v{version} p{index}\n{hostile}\n".encode("utf-8")
            report = report_dir / name
            report.write_bytes(content)
            sidecar = report.with_name(name + ".effort.json")
            sidecar.write_text(json.dumps({"comment": hostile, "pass": index}) + "\n", encoding="utf-8")
            report.with_name(name + ".gated.json").write_text('{"gate":"root-local"}\n', encoding="utf-8")
            log = log_dir / (name + ".log")
            log.write_bytes(f"collected pass-log v{version} p{index}\n".encode() + payload)
            if version == cycle:
                expected[f"collected/{name}"] = content
                expected[f"collected/{name}.effort.json"] = sidecar.read_bytes()
                expected[f"pass-logs/{name}.log"] = log.read_bytes()
    for name in ("copper-kite.plan.audit.v2.p1.md", "paper-lantern.design.audit.v2.p1.md"):
        (report_dir / name).write_bytes(payload)
        (log_dir / (name + ".log")).write_bytes(payload)
    return {
        "stem": stem, "prefix": prefix, "root": root, "root_record": root_record,
        "stdout": stdout, "command": command,
        "dest": directory / "not-created/data/s1/agy", "ready_line": ready_line,
        "expected": expected, "stem_sources": stem_sources,
    }


def build_pass_cycle_inputs(case: dict) -> dict:
    """Three ordered roots, with conflicting root-local and stem reports."""
    case = {**case, "expected": dict(case["expected"])}
    roots = [case["root"]]
    for index in (2, 3):
        root = case["root"].parent / f"gas-root-d1-s1-pass{index}"
        root.mkdir()
        roots.append(root)
    records, lines, reports = [], [], {}
    payload = _hostile_text().encode("utf-8") + b"\r\n\x00\xff\n"
    for index, root in enumerate(roots, 1):
        line = case["ready_line"].replace(
            f"path={case['root']}", f"path={root.resolve()}",
        )
        record = case["command"].parent / f"pass {index} [a]* ⟦h-mad⟧.txt"
        record.write_text(f"Agent annotation: {_hostile_text()}\n{line}\n", encoding="utf-8")
        records.append(record)
        lines.append(line)
        stem_report = case["stem"] / f"{case['prefix']}_p{index}.report.md"
        stem_report.write_bytes(f"stem report pass={index}\n".encode() + payload)
        reports[f"p{index}.report.md"] = stem_report.read_bytes()
        # Pass 2 deliberately has no local report, exercising the stem fallback.
        if index != 2:
            local = root / ".hmad-report" / stem_report.name
            local.parent.mkdir()
            local.write_bytes(f"root-local report pass={index}\n".encode() + payload)
            reports[f"p{index}.report.md"] = local.read_bytes()
        # Another pass's report in this root must never be selected.
        decoy = root / ".hmad-report" / f"{case['prefix']}_p{index % 3 + 1}.report.md"
        decoy.parent.mkdir(exist_ok=True)
        decoy.write_bytes(b"wrong pass root\n" + payload)
    command = case["command"].read_text(encoding="utf-8")
    case["command"].write_text(command.replace("--passes 2", "--passes 3"), encoding="utf-8")
    case["stdout"].write_text(
        f"Agent output: {_hostile_text()}\n"
        "AUDITCYCLE: PASS p1=PASS p2=PASS p3=PASS "
        "delivered=report-file,report-file,report-file must=0 should=0 size_status=verified\n",
        encoding="utf-8",
    )
    case.update(pass_roots=roots, pass_root_records=records, pass_ready_lines=lines,
                pass_reports=reports)
    return case


def seed_commit_parent(case: dict, files: dict[str, bytes] | None = None) -> str:
    """Put real source blobs and optional calibration paths in the parent tree."""
    contents = {path.relative_to(case["src"]).as_posix(): path.read_bytes()
                for path in case["src"].rglob("*") if path.is_file()}
    contents.update(files or {})
    changes = {(CALIBRATION / relative).as_posix(): content
               for relative, content in contents.items()}
    parent = commit_fixture_tree(case["repo"], case["parent"], changes)
    git(case["repo"], "update-ref", CALIBRATION_REF, parent, case["parent"])
    case["parent"] = parent
    return parent


def build_commit_inputs(tmp_path: Path) -> dict:
    """Keep Git fixtures real; stage and dirty tracked bytes before recording."""
    repo, _origin = build_repo(tmp_path)
    tracked = repo / "docs/archive/2099-01/paper-lantern/paper-lantern.spec.md"
    tracked.write_text(f"Staged human edit: {_hostile_text()}\n", encoding="utf-8")
    git(repo, "add", tracked.relative_to(repo).as_posix())
    tracked.write_text(f"Unstaged human edit: {_hostile_text()}\n", encoding="utf-8")
    (repo / "untracked [a]*.txt").write_text(_hostile_text(), encoding="utf-8")
    src = tmp_path / "kept data [a]* ⟦h-mad⟧"
    data = src / "s1/grok/p1.log"
    data.parent.mkdir(parents=True)
    data.write_bytes(_hostile_text().encode("utf-8") + b"\r\n\x00\xff\n")
    (src / "s1/grok/command.txt").write_text(
        f"Human command annotation: {_hostile_text()}\n", encoding="utf-8",
    )
    return {
        "repo": repo, "src": src, "parent": git(repo, "rev-parse", CALIBRATION_REF),
        "message": f"Record calibration: {_hostile_text()}",
    }


def extract_report_text(must: str | None = None, should: str = "None") -> str:
    """Keep agent text hostile, including literal Markdown and a wrapped line."""
    if must is None:
        must = "- Preserve the seeded contract: " + _hostile_text().replace("\n", "\n  ")
    return f"# Synthetic audit\n\n## Must-fix\n{must}\n\n## Should-fix\n{should}\n"


def extract_report_path(case: dict, doc: str = "d1", cycle: int = 1, index: int = 1) -> Path:
    feature_index, phase_index = divmod(int(doc[1:]) - 1, len(PHASES))
    feature = list(case["sources"])[feature_index]
    name = f"{feature}.{PHASES[phase_index]}.audit.v{cycle}.p{index}.md"
    return case["s2"] / doc / f"v{cycle}" / "collected" / name


def write_extract_cycle(case: dict, *, doc: str = "d1", cycle: int = 1,
                        verdict: str = "PASS", reason: str | None = None,
                        deliveries: tuple[str, ...] = ("none", "none"),
                        reports: dict[int, str] | None = None,
                        surfaces: tuple[str, ...] = ("agy", "grok")) -> Path:
    """Write a D3 cycle without asking an unbuilt extract handler to stage it."""
    directory = case["s2"] / doc / f"v{cycle}"
    directory.mkdir(parents=True, exist_ok=True)
    feature_index, phase_index = divmod(int(doc[1:]) - 1, len(PHASES))
    feature = list(case["sources"])[feature_index]
    # Root tokens have whitespace-delimited fields; hostile data belongs in the
    # reports/prompts, while command argv also exercises quoted physical paths.
    root = Path(f"/tmp/gas-root-{doc}-s2v{cycle}-synthetic")
    (directory / "command.txt").write_text(shlex.join([
        "env", f"HMAD_AUDIT_STEM_DIR={directory / 'stem [a]* ⟦h-mad⟧'}",
        "hmad-dispatch", "audit-cycle", "--feature", feature,
        "--phase", PHASES[phase_index], "--cycle", str(cycle),
        "--project-root", str(root), "--passes", str(len(surfaces)),
        "--surfaces", ",".join(surfaces), "--timeout", "900",
    ]) + "\n", encoding="utf-8")
    token = f"AUDITCYCLE: {verdict}"
    if reason:
        token += f" reason={reason}"
    token += f" passes={len(surfaces)} delivered={','.join(deliveries)} size_status=verified"
    (directory / "auditcycle.txt").write_text(token + "\n", encoding="utf-8")
    (directory / "root.txt").write_text(
        f"ROOT: READY doc={doc} purpose=s2v{cycle} path={root} "
        f"calibration={'a' * 40} list_commit={'b' * 40} list_blob={'c' * 40} absent=0\n",
        encoding="utf-8",
    )
    run_record = case["s2"] / "run.txt"
    if not run_record.exists():
        run_record.write_text("RUN: checkout=/tmp/grok-audit-checkout home=/tmp/grok-audit-home\n",
                              encoding="utf-8")
    for index in range(1, len(surfaces) + 1):
        pass_root = Path(f"/tmp/gas-root-{doc}-s2v{cycle}-pass{index}")
        (directory / f"p{index}.root.txt").write_text(
            f"ROOT: READY doc={doc} purpose=s2v{cycle} path={pass_root} "
            f"calibration={'a' * 40} list_commit={'b' * 40} list_blob={'c' * 40} absent=0\n",
            encoding="utf-8",
        )
        (directory / f"p{index}.prompt.txt").write_text(
            f"Audit pass {index}: {_hostile_text()}\n", encoding="utf-8",
        )
        (directory / f"p{index}.asm.txt").write_text("ASSEMBLE: PASS synthetic\n", encoding="utf-8")
        (directory / f"p{index}.out.txt").write_text("", encoding="utf-8")
        (directory / f"p{index}.log").write_text(
            json.dumps({"type": "text", "data": _hostile_text()}) + "\n"
            + '{"type":"end"}\n', encoding="utf-8",
        )
    for index, text in (reports or {}).items():
        path = extract_report_path(case, doc, cycle, index)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return directory


def build_extract_inputs(tmp_path: Path) -> dict:
    """Nine valid seeded docs, external S2 data, initially one delivered report."""
    tree = tmp_path / "base tree [a]* ⟦h-mad⟧"
    sources = build_archive(tree)
    case = {
        "tree": tree, "sources": sources, "records": build_ledger(tree, sources),
        "s2": tmp_path / "kept data [a]* ⟦h-mad⟧" / "s2",
        "out": tmp_path / "extracted [a]* ⟦h-mad⟧", "seed": 1729,
    }
    for index in range(1, 10):
        write_extract_cycle(case, doc=f"d{index}")
    write_extract_cycle(case, deliveries=("report-file", "none"), reports={1: extract_report_text()})
    return case


def write_score_tables(case: dict) -> None:
    """Persist editable blinded tables without changing the recorded reports."""
    for name in ("findings", "key", "labels"):
        (case["tree"] / CALIBRATION / f"{name}.jsonl").write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in case[name]),
            encoding="utf-8",
        )


def build_score_inputs(tmp_path: Path, probe, specs=None,
                       surfaces=("agy", "grok")) -> dict:
    """Build D13 inputs via the real extractor; specs are (surface, doc, section, label)."""
    tree = tmp_path / "score tree [a]* ⟦h-mad⟧"
    sources = build_archive(tree)
    case = {
        "tree": tree, "sources": sources, "records": build_ledger(tree, sources),
        "s2": tree / CALIBRATION / "s2", "probe": probe,
    }
    if specs is None:
        specs = [("grok", "d1", "must", "HIT:d1-s1"),
                 ("agy", "d1", "must", "REAL")]
    bodies, labels_by_prefix = {}, {}
    hostile = _hostile_text().replace("\n", " ")
    for index, (surface, doc, section, label) in enumerate(specs):
        prefix = f"score-item-{index:04d}:"
        bodies.setdefault((doc, surface, section), []).append(f"- {prefix} {hostile}")
        labels_by_prefix[prefix] = label
    for number in range(1, 10):
        doc = f"d{number}"
        reports = {
            index: extract_report_text(
                "\n".join(bodies.get((doc, surface, "must"), [])) or "None",
                "\n".join(bodies.get((doc, surface, "should"), [])) or "None",
            ) for index, surface in enumerate(surfaces, 1)
        }
        directory = write_extract_cycle(
            case, doc=doc, deliveries=("report-file",) * len(surfaces),
            reports=reports, surfaces=surfaces,
        )
        effort = []
        for index, surface in enumerate(surfaces, 1):
            suffix = " low-evidence (synthetic hollow log)" if doc == "d1" and surface == "grok" else ""
            effort.append(f"- p{index} tools=1 ok=1 unresolved=0 thinking=0 format=parsed{suffix}")
        stdout = directory / "auditcycle.txt"
        stdout.write_text(stdout.read_text(encoding="utf-8") + "Effort:\n"
                          + "\n".join(effort) + "\nPremise checklist: empty\n", encoding="utf-8")
    extracted = probe.extract_all(tree, case["s2"], sources)
    case["findings"], case["key"] = probe.blind(extracted, 1729)
    case["labels"] = []
    for finding in case["findings"]:
        matches = [label for prefix, label in labels_by_prefix.items() if prefix in finding["text"]]
        assert len(matches) == 1, "each hostile finding must retain its unique fixture identity"
        case["labels"].append({"id": finding["id"], "label": matches[0],
                               "why": f"Source checked: {_hostile_text()}."})
    assert len(extracted) == len(specs), "the real gate must extract every fixture finding exactly once"
    write_score_tables(case)
    return case


def commit_fixture_tree(repo: Path, parent: str, changes: dict[str, bytes | None],
                        *, extra_parents=()) -> str:
    """Make adversarial branch history without a checkout or touching the real index."""
    with tempfile.TemporaryDirectory(prefix="fixture-index-") as directory:
        environment = os.environ.copy()
        environment["GIT_INDEX_FILE"] = str(Path(directory) / "index")
        git(repo, "read-tree", parent, env=environment)
        for relative, content in changes.items():
            if content is None:
                git(repo, "update-index", "--force-remove", "--", relative, env=environment)
                continue
            result = subprocess.run(
                ["git", "-C", str(repo), "hash-object", "-w", "--stdin"],
                input=content, capture_output=True, timeout=15, check=True,
            )
            git(repo, "update-index", "--add", "--cacheinfo", "100644",
                result.stdout.decode().strip(), relative, env=environment)
        tree = git(repo, "write-tree", env=environment)
        parents = [word for sha in (parent, *extra_parents) for word in ("-p", sha)]
        return git(repo, "commit-tree", tree, *parents,
                   input=f"Adversarial fixture history: {_hostile_text()}\n")


def build_rescore_inputs(tmp_path: Path, probe, *, smoke_failure=False,
                         seeded_in_own_source=False) -> dict:
    """Real main/origin plus calibration → smoke → score, using Task 6's writer."""
    root_case = build_root_repo(tmp_path)
    case = build_score_inputs(tmp_path / "score-input", probe)
    calibration_dir = case["tree"] / CALIBRATION
    run_id = "fixture-run"
    reading = calibration_dir / "runs" / run_id
    reading.mkdir(parents=True)
    for name in ("s2", "findings.jsonl", "key.jsonl", "labels.jsonl", "extract.txt"):
        source = calibration_dir / name
        if source.exists():
            source.replace(reading / name)
    if not (reading / "extract.txt").exists():
        (reading / "extract.txt").write_text("extract --shuffle-seed 1729\n", encoding="utf-8")
    case["run_id"] = run_id
    case["reading_root"] = reading
    case["s2"] = reading / "s2"
    case.update(repo=root_case["repo"], origin=tmp_path / "origin.git", probe=probe,
                **{name: root_case[name] for name in ("work_dir", "systemp", "roots")})
    if seeded_in_own_source:
        # An identity replacement is valid and puts this span in its own archive.
        for target in (root_case, case):
            record = target["records"][0]
            copy = target["tree"] / CALIBRATION / "seeded" / Path(record["source"]).name
            copy.write_text(copy.read_text(encoding="utf-8").replace(
                record["seeded"], record["original"], 1), encoding="utf-8")
            record["seeded"] = record["original"]
            (target["tree"] / CALIBRATION / "ledger.jsonl").write_text(
                "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in target["records"]),
                encoding="utf-8",
            )
    repo = case["repo"]
    # Preserve both main's exclusion policy and the calibration tip already on
    # origin, so publishing the recorded descendants remains a fast-forward.
    case["calibration"] = commit_root_tree(root_case, extra_parents=(CALIBRATION_REF,))
    git(repo, "update-ref", CALIBRATION_REF, case["calibration"])
    case["main"] = git(repo, "rev-parse", "HEAD")
    case["list_blob"] = git(repo, "rev-parse", f"HEAD:{EXCLUSIONS.as_posix()}")
    data = case["tree"] / CALIBRATION
    from grokfixtures import f0_text
    for cycle_number, surface in enumerate(("grok", "agy"), 1):
        directory = data / "s1" / surface
        directory.mkdir(parents=True)
        report = directory / "collected" / f"paper-lantern.plan.audit.v{cycle_number}.p1.md"
        report.parent.mkdir()
        report.write_text(extract_report_text("None"), encoding="utf-8")
        log = directory / "p1.log"
        log.write_text(f0_text(), encoding="utf-8")
        result = probe._cycle.PassResult(
            1, "report-file", report, "PASS", 0, 0, [],
            probe._cycle.measure_effort(log), 0,
        )
        stdout = probe._cycle.render(
            [result], "PASS", None, feature="paper-lantern", size_status="verified", passes=1,
        )
        if smoke_failure and surface == "grok":
            log.write_text("".join(line + "\n" for line in f0_text().splitlines()
                                   if json.loads(line).get("type") != "end"), encoding="utf-8")
        (directory / "auditcycle.txt").write_text(stdout, encoding="utf-8")
        (directory / "command.txt").write_text(shlex.join([
            "hmad-dispatch", "audit-cycle", "--feature", "paper-lantern", "--phase", "plan",
            "--cycle", str(cycle_number), "--project-root", f"/tmp/gas-root-d1-s1-{surface}",
            "--passes", "1", "--surfaces", surface,
        ]) + "\n", encoding="utf-8")
    (data / "s1/grok/wall_seconds.txt").write_text("17\n", encoding="utf-8")
    (data / "s1/grok/resolved_model.txt").write_text("RESOLVED-MODEL: fixture\n", encoding="utf-8")
    (data / "s1/versions.txt").write_text("grok_binary=/synthetic/grok fixture-version\n", encoding="utf-8")
    (data / "extract.txt").write_text("extract --shuffle-seed 1729\n", encoding="utf-8")
    for directory in [data / "s1/grok", data / "s1/agy", *sorted(case["s2"].glob("d*/v*"))]:
        doc = directory.parent.name if directory.parent.name.startswith("d") else "d1"
        purpose = "s1" if directory.parent.name == "s1" else "s2v1"
        (directory / "root.txt").write_text(
            f"ROOT: READY doc={doc} purpose={purpose} path=/tmp/gas-root-{doc}-{purpose}-synthetic "
            f"calibration={case['calibration']} list_commit={case['main']} "
            f"list_blob={case['list_blob']} absent=0\n", encoding="utf-8",
        )
        if purpose.startswith("s2"):
            command = shlex.split((directory / "command.txt").read_text(encoding="utf-8"))
            surfaces = command[command.index("--surfaces") + 1].split(",")
            for index in range(1, len(surfaces) + 1):
                (directory / f"p{index}.root.txt").write_text(
                    f"ROOT: READY doc={doc} purpose={purpose} path=/tmp/gas-root-{doc}-{purpose}-pass{index} "
                    f"calibration={case['calibration']} list_commit={case['main']} "
                    f"list_blob={case['list_blob']} absent=0\n", encoding="utf-8",
                )
    smoke_src = tmp_path / "smoke-input"
    shutil.copytree(data / "s1", smoke_src / "s1")
    args = types.SimpleNamespace(repo=repo, parent=case["calibration"], src=smoke_src,
                                 message=f"Recorded smoke: {_hostile_text()}")
    case["smoke"] = probe.commit_data(args).split("sha=", 1)[1].split()[0]
    if not smoke_failure:
        args.parent, args.src = case["smoke"], data
        args.message = f"Recorded score: {_hostile_text()}"
        case["score"] = probe.commit_data(args).split("sha=", 1)[1].split()[0]
    git(repo, "push", "origin", CALIBRATION_REF)
    return case
