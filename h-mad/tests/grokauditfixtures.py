"""Synthetic archives, calibration trees and source-only probe loading."""

import json
import os
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


def load_probe(path: Path) -> types.ModuleType:
    """Compile fresh source so same-size mutations cannot reuse stale bytecode."""
    code = compile(path.read_bytes(), str(path), "exec")
    module = types.ModuleType("grok_audit_probe")
    module.__file__ = str(path)
    sys.modules[module.__name__] = module
    exec(code, module.__dict__)
    return module
