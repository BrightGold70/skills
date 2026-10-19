"""Probe tokens, ledger, roots, cycle recording and data commits (Tasks 2–6)."""

import ast
from collections import Counter
import hashlib
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import uuid
from pathlib import Path

import pytest

from grokauditfixtures import (
    CALIBRATION, CALIBRATION_REF, EXCLUSIONS, build_archive, build_ledger,
    build_repo, build_root_repo, build_cycle_inputs, build_commit_inputs,
    commit_root_tree, git, load_probe,
)


REPO = Path(__file__).resolve().parents[2]
PROBE = REPO / "docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py"
MODES = (
    "check-ledger", "build-root", "record-cycle", "commit-data", "smoke",
    "extract", "score", "rescore", "main-leak",
)
REFUSALS = {
    "check-ledger": "LEDGER: UNREADABLE",
    "build-root": "ROOT: UNREADABLE",
    "record-cycle": "RECORD: REFUSED",
    "commit-data": "COMMIT: REFUSED",
    "smoke": "SMOKE: UNREADABLE",
    "extract": "FINDINGS: UNREADABLE",
    "score": "SEEDSCORE: UNREADABLE",
    "rescore": "SEEDSCORE: UNREADABLE",
    "main-leak": "MAINLEAK: UNREADABLE",
}


def _minimal_argv(mode: str, root: Path) -> list[str]:
    sha = "a" * 40
    # Agent/human message text uses the payload from HMAD_STUB_HOSTILE=all.
    # These entry-point tests invoke no Orca stub or real agent.
    hostile_message = "h-mad: [a](b) **bold** * [ ⟦/h-mad⟧\nsecond\tline"
    arguments = {
        "check-ledger": ["--tree", str(root)],
        "build-root": [
            "--repo", str(root), "--calibration-sha", sha,
            "--doc", "d1", "--purpose", "s1",
        ],
        "record-cycle": [
            "--stem", str(root / "stem"), "--root", str(root / "root"),
            "--root-record", str(root / "root.txt"),
            "--stdout", str(root / "stdout.txt"),
            "--command", str(root / "command.txt"), "--dest", str(root / "dest"),
        ],
        "commit-data": [
            "--repo", str(root), "--parent", sha, "--src", str(root / "src"),
            "--message", hostile_message,
        ],
        "smoke": ["--data", str(root / "s1")],
        "extract": [
            "--tree", str(root), "--s2", str(root / "s2"),
            "--shuffle-seed", "17", "--out", str(root / "out"),
        ],
        "score": ["--tree", str(root)],
        "rescore": [
            "--repo", str(root), "--calibration-sha", sha,
            "--smoke-sha", sha, "--score-sha", sha,
        ],
        "main-leak": [
            "--repo", str(root), "--calibration-sha", sha, "--smoke-sha", sha,
        ],
    }
    return [mode, *arguments[mode]]


def _expected_refusal(mode: str, exception: str, root: Path) -> str:
    reason = (
        f"input_unparseable:{root / 's1'}"
        if mode == "smoke" else f"internal:{exception}"
    )
    return f"{REFUSALS[mode]} reason={reason}"


@pytest.mark.parametrize("mode", MODES, ids=MODES)
def test_internal_failure_prints_the_mode_token(mode, tmp_path, monkeypatch, capsys):
    probe = load_probe(PROBE)

    def raiser(args):
        raise RuntimeError("injected handler failure")

    monkeypatch.setitem(probe.MODES, mode, raiser)
    rc = probe.main(_minimal_argv(mode, tmp_path))
    out, err = capsys.readouterr()
    expected = _expected_refusal(mode, "RuntimeError", tmp_path)
    n = err.count("Traceback")
    assert (rc, out.splitlines()[-1:]) == (2, [expected]), (
        "an escaping handler RuntimeError must return 2 and end on its mode's "
        "refusal token (smoke names its --data directory)"
    )
    assert n > 0, "an unexpected handler exception must print its traceback on stderr"


@pytest.mark.parametrize("mode", MODES, ids=MODES)
def test_usage_error_prints_the_mode_token(mode, tmp_path):
    argv = [mode]
    if mode == "smoke":
        argv += ["--data", str(tmp_path / "s1")]
    argv += ["--no-such-flag"]
    r = subprocess.run(
        [sys.executable, str(PROBE), *argv], capture_output=True, text=True,
        timeout=15,
    )
    expected = _expected_refusal(mode, "UsageError", tmp_path)
    assert (r.returncode, r.stdout.splitlines()[-1:]) == (2, [expected]), r.stderr
    n = r.stderr.count("Traceback")
    assert n == 0, "a declared UsageError must print its token without a traceback"


@pytest.mark.parametrize("argv", [[], ["no-such-mode"]], ids=["empty", "unknown"])
def test_unknown_mode_prints_the_probe_token(argv):
    r = subprocess.run(
        [sys.executable, str(PROBE), *argv], capture_output=True, text=True,
        timeout=15,
    )
    assert (r.returncode, r.stdout) == (
        2, "PROBE: UNREADABLE reason=unknown_mode\n",
    ), r.stderr
    assert "usage:" in r.stderr, r.stderr
    assert "[H-MAD] grok-audit-surface" in r.stderr, r.stderr


@pytest.mark.parametrize("mode", MODES, ids=MODES)
def test_help_flag_prints_the_mode_token(mode, tmp_path):
    argv = [mode]
    if mode == "smoke":
        argv += ["--data", str(tmp_path / "s1")]
    argv += ["--help"]
    r = subprocess.run(
        [sys.executable, str(PROBE), *argv], capture_output=True, text=True,
        timeout=15,
    )
    expected = _expected_refusal(mode, "UsageError", tmp_path)
    assert (r.returncode, r.stdout.splitlines()) == (2, [expected]), r.stderr


def test_abbreviated_flag_is_a_usage_error(tmp_path, monkeypatch, capsys):
    probe = load_probe(PROBE)
    monkeypatch.setitem(probe.MODES, "check-ledger", lambda args: 0)
    rc = probe.main(["check-ledger", "--tre", str(tmp_path)])
    out, err = capsys.readouterr()
    assert (rc, out.splitlines()[-1:]) == (
        2, ["LEDGER: UNREADABLE reason=internal:UsageError"],
    ), err


@pytest.fixture
def ledger_case(tmp_path, monkeypatch):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    tree = tmp_path / "exported tree [⟦audit⟧]"
    sources = build_archive(tree)
    records = build_ledger(tree, sources)
    return tree, sources, records


def _write_ledger(tree, records):
    (tree / CALIBRATION / "ledger.jsonl").write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )


def _rebuild_document(tree, records, source):
    """Keep copy bytes valid when a placement or uniqueness guard is isolated."""
    document = (tree / source).read_text(encoding="utf-8")
    for record in records:
        if record["source"] == source:
            document = document.replace(record["original"], record["seeded"], 1)
    (tree / CALIBRATION / "seeded" / Path(source).name).write_text(
        document, encoding="utf-8",
    )
    _write_ledger(tree, records)


def _run_ledger(tree, sources, *, repo=None, sha=None):
    arguments = ["--tree", str(tree)] if repo is None else [
        "--repo", ".", "--calibration-sha", sha,
    ]
    return subprocess.run(
        [sys.executable, str(PROBE), "check-ledger", *arguments, "--sources",
         ",".join(f"{feature}={directory}" for feature, directory in sources.items())],
        cwd=repo, capture_output=True, text=True, timeout=15,
    )


def _assert_ledger_refusal(tree, sources, reason, property_name):
    result = _run_ledger(tree, sources)
    assert (result.returncode, result.stdout.splitlines()[-1:]) == (
        2, [f"LEDGER: UNREADABLE reason={reason}"],
    ), f"{property_name}: stdout={result.stdout!r}; stderr={result.stderr!r}"
    assert "Traceback" not in result.stderr, (
        f"{property_name}: a declared ledger refusal must not print a traceback"
    )


def test_ledger_counts_refuses_a_repeated_class_with_totals_kept(ledger_case):
    tree, sources, records = ledger_case
    totals = Counter(record["class"] for record in records)
    records[1]["class"] = "C2"  # d1: C2, C2, C4
    records[10]["class"] = "C3"  # d4: C1, C3, C3
    assert Counter(record["class"] for record in records) == totals
    assert set(Counter(record["source"] for record in records).values()) == {3}
    _write_ledger(tree, records)
    _assert_ledger_refusal(tree, sources, "ledger_counts", "repeated per-document class despite unchanged totals")


def test_ledger_counts_refuses_a_moved_class(ledger_case):
    tree, sources, records = ledger_case
    totals = Counter(record["class"] for record in records)
    records[0]["class"], records[3]["class"] = records[3]["class"], records[0]["class"]
    assert Counter(record["class"] for record in records) == totals
    assert len({record["class"] for record in records[:3]}) == 3
    assert len({record["class"] for record in records[3:6]}) == 3
    _write_ledger(tree, records)
    _assert_ledger_refusal(tree, sources, "ledger_counts", "class moved into a document that must omit it")


def test_ledger_counts_refuses_an_unparseable_line(ledger_case):
    tree, sources, records = ledger_case
    ledger = tree / CALIBRATION / "ledger.jsonl"
    for bad_line in ("{not-json", "[]"):
        _write_ledger(tree, records)
        lines = ledger.read_text(encoding="utf-8").splitlines()
        lines[0] = bad_line
        ledger.write_text("\n".join(lines) + "\n", encoding="utf-8")
        _assert_ledger_refusal(tree, sources, "ledger_counts", "each ledger line must parse as one JSON object")


def test_ledger_counts_refuses_a_missing_field(ledger_case):
    tree, sources, records = ledger_case
    for field in tuple(records[0]):
        missing = [dict(record) for record in records]
        del missing[0][field]
        _write_ledger(tree, missing)
        _assert_ledger_refusal(tree, sources, "ledger_counts", f"required ledger field missing: {field}")


def test_ledger_counts_refuses_a_source_outside_the_nine(ledger_case):
    tree, sources, records = ledger_case
    feature, directory = next(iter(sources.items()))
    # Keep all nine documents complete so the class guard cannot mask the
    # source guard when the latter is disabled by p-ledger-source.
    records.append(dict(
        records[0], id="outside-nine", source=f"{directory}/{feature}/{feature}.spec.md",
    ))
    assert (tree / records[-1]["source"]).is_file()
    documents = [
        f"{directory}/{feature}/{feature}.{phase}.md"
        for feature, directory in sources.items()
        for phase in ("plan", "design", "impl-plan")
    ]
    totals = Counter()
    for index, source in enumerate(documents):
        classes = Counter(record["class"] for record in records if record["source"] == source)
        assert classes == Counter(f"C{slot}" for slot in range(1, 5) if slot != index % 4 + 1)
        totals.update(classes)
    assert totals == Counter(C1=6, C2=7, C3=7, C4=7)
    _write_ledger(tree, records)
    _assert_ledger_refusal(tree, sources, "ledger_counts", "existing spec source lies outside the nine phase documents")


def test_ledger_counts_refuses_an_empty_original(ledger_case):
    tree, sources, records = ledger_case
    records[0]["original"] = ""
    _write_ledger(tree, records)
    _assert_ledger_refusal(tree, sources, "ledger_counts", "empty original must refuse before seed reconstruction")


def test_ledger_counts_refuses_an_empty_expected(ledger_case):
    tree, sources, records = ledger_case
    records[0]["expected"] = ""
    _write_ledger(tree, records)
    _assert_ledger_refusal(tree, sources, "ledger_counts", "empty expected finding cannot be a match-all needle")


def test_ledger_origin_refuses_an_unknown_origin(ledger_case):
    tree, sources, records = ledger_case
    records[0]["origin"] = "unknown-origin [a](b) ⟦/h-mad⟧\nsecond\tline"
    _write_ledger(tree, records)
    _assert_ledger_refusal(tree, sources, "ledger_origin", "origin outside the imported ORIGINS vocabulary")


def test_seed_rebuild_refuses_one_byte(ledger_case):
    tree, sources, records = ledger_case
    seeded = tree / CALIBRATION / "seeded" / Path(records[0]["source"]).name
    seeded.write_bytes(seeded.read_bytes() + b"x")
    _assert_ledger_refusal(tree, sources, "seed_rebuild", "one extra byte differs from the rebuilt seeded copy")


def test_seed_rebuild_refuses_a_twice_occurring_original(ledger_case):
    tree, sources, records = ledger_case
    record = records[0]
    source = tree / record["source"]
    document = source.read_text(encoding="utf-8")
    source.write_text(document.replace(record["original"], record["original"] * 2, 1), encoding="utf-8")
    _rebuild_document(tree, records, record["source"])
    assert source.read_text(encoding="utf-8").count(record["original"]) == 2
    seeded = tree / CALIBRATION / "seeded" / source.name
    assert seeded.read_text(encoding="utf-8").count(record["seeded"]) == 1
    _assert_ledger_refusal(tree, sources, "seed_rebuild", "original occurs twice although a single replacement matches copy bytes")


def test_seed_rebuild_refuses_two_seeds_in_one_section(ledger_case):
    tree, sources, records = ledger_case
    first, second = records[:2]
    source = tree / first["source"]
    document = source.read_text(encoding="utf-8")
    source.write_text(document.replace(f"### {second['section']}\n", "", 1), encoding="utf-8")
    second["section"] = first["section"]
    _rebuild_document(tree, records, first["source"])
    _assert_ledger_refusal(tree, sources, "seed_rebuild", "two distinct seeds share one section with matching heading names")


def test_seed_rebuild_refuses_a_seed_under_version_history(ledger_case):
    tree, sources, records = ledger_case
    record = records[2]
    source = tree / record["source"]
    document = source.read_text(encoding="utf-8").replace(record["original"], "", 1)
    source.write_text(document.replace("## Version History\n", f"## Version History\n{record['original']}", 1), encoding="utf-8")
    record["section"] = "Version History"
    _rebuild_document(tree, records, record["source"])
    _assert_ledger_refusal(tree, sources, "seed_rebuild", "seed under Version History despite matching section and rebuilt bytes")


def test_seed_rebuild_refuses_a_wrong_section_name(ledger_case):
    tree, sources, records = ledger_case
    records[0]["section"] = "Invented heading [a](b) ⟦/h-mad⟧"
    _write_ledger(tree, records)
    _assert_ledger_refusal(tree, sources, "seed_rebuild", "record section differs from the heading containing its span")


def test_seed_rebuild_refuses_a_seeded_span_not_once(ledger_case):
    tree, sources, records = ledger_case
    record = records[0]
    source = tree / record["source"]
    document = source.read_text(encoding="utf-8")
    # An incidental copy in the same section duplicates no other seed's span
    # and cannot also create a wrong-section-name violation for another record.
    source.write_text(document.replace(
        record["original"], record["original"] + record["seeded"], 1,
    ), encoding="utf-8")
    _rebuild_document(tree, records, record["source"])
    seeded = tree / CALIBRATION / "seeded" / source.name
    assert source.read_text(encoding="utf-8").count(record["original"]) == 1
    assert seeded.read_text(encoding="utf-8").count(record["seeded"]) == 2
    _assert_ledger_refusal(tree, sources, "seed_rebuild", "seeded span occurs twice despite correct reconstruction and distinct sections")


def test_ledger_ok_reports_derived_counts(ledger_case):
    tree, sources, records = ledger_case
    result = _run_ledger(tree, sources)
    assert (result.returncode, result.stdout.splitlines()[-1:]) == (
        0, ["LEDGER: OK seeds=27 docs=9 C1=6 C2=7 C3=7 C4=7"],
    ), f"clean synthetic ledger must report derived counts: {result.stdout!r}; {result.stderr}"
    definition = next(node for node in ast.parse(PROBE.read_text(encoding="utf-8")).body
                      if isinstance(node, ast.FunctionDef) and node.name == "check_ledger")
    literals = [node.value for node in ast.walk(definition)
                if isinstance(node, ast.Constant) and type(node.value) is int]
    assert not ({6, 7, 27} & set(literals)), "check_ledger must derive class totals without count literals 6, 7 or 27"


def test_check_ledger_tree_and_repo_forms_agree(tmp_path, monkeypatch):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    work, origin = build_repo(tmp_path)
    sources = build_archive(work)
    sha = git(work, "rev-parse", CALIBRATION_REF)
    assert git(origin, "rev-parse", CALIBRATION_REF) == sha
    assert git(work, "rev-parse", "HEAD") == git(work, "rev-parse", "main")
    assert not git(work, "status", "--porcelain"), "building calibration must leave main's work tree clean"
    archive = subprocess.run(
        ["git", "-C", str(work), "archive", sha], capture_output=True, check=True, timeout=15,
    ).stdout
    exported = tmp_path / "exported commit"
    exported.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
        bundle.extractall(exported)
    from_tree = _run_ledger(exported, sources)
    from_repo = _run_ledger(None, sources, repo=work, sha=sha)
    expected = ["LEDGER: OK seeds=27 docs=9 C1=6 C2=7 C3=7 C4=7"]
    assert (from_tree.returncode, from_repo.returncode,
            from_tree.stdout.splitlines()[-1:], from_repo.stdout.splitlines()[-1:]) == (
        0, 0, expected, expected,
    ), ("tree and repo front doors must both validate the same committed content: "
        f"tree={from_tree.stdout!r} {from_tree.stderr}; repo={from_repo.stdout!r} {from_repo.stderr}")


@pytest.fixture
def root_case(tmp_path, monkeypatch):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    # Fixture Git calls must not inherit the invoking agent's Git context.
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR",
                 "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
                 "GIT_INDEX_FILE"):
        monkeypatch.delenv(name, raising=False)
    case = build_root_repo(tmp_path)
    case["probe"] = load_probe(PROBE)
    return case


def _run_root(case, capsys, *, doc="d1", purpose="s1", dest=True, extra=(), sha=None):
    """Exercise the real mode dispatch, with D4 proven valid before each run."""
    probe = case["probe"]
    assert probe.check_ledger(case["tree"], case["sources"])["docs"] == 9
    if sha is None:
        sha = commit_root_tree(case)
    case["sha"] = sha
    arguments = [
        "build-root", "--repo", str(case["repo"]), "--calibration-sha", sha,
        "--doc", doc, "--purpose", purpose, "--sources",
        ",".join(f"{feature}={directory}" for feature, directory in case["sources"].items()),
    ]
    if dest:
        arguments += ["--dest-parent", str(case["dest"])]
    arguments += list(extra)
    rc = probe.main(arguments)
    out, err = capsys.readouterr()
    return subprocess.CompletedProcess(arguments, rc, out, err)


def _assert_root_refusal(result, reason, property_name):
    assert (result.returncode, result.stdout.splitlines()[-1:]) == (
        2, [f"ROOT: UNREADABLE reason={reason}"],
    ), f"{property_name}: stdout={result.stdout!r}; stderr={result.stderr!r}"
    assert "Traceback" not in result.stderr, (
        f"{property_name}: a declared root refusal must not print a traceback"
    )


def _ready_fields(result, property_name):
    lines = result.stdout.splitlines()
    assert result.returncode == 0 and lines and lines[-1].startswith("ROOT: READY "), (
        f"{property_name}: expected exit 0 and a final ROOT: READY line; "
        f"stdout={result.stdout!r}; stderr={result.stderr!r}"
    )
    return dict(word.split("=", 1) for word in lines[-1].split()[2:])


def _plant(case, relative, content):
    path = case["tree"] / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return relative


def _append_archive_member(probe, monkeypatch, name, *, directory=False):
    """Alter only Git's archive response; all blob and reach calls remain real."""
    real_run = probe.subprocess.run

    def run(command, *args, **kwargs):
        result = real_run(command, *args, **kwargs)
        if command[0] == "git" and "archive" in command:
            output = io.BytesIO()
            with tarfile.open(fileobj=io.BytesIO(result.stdout)) as source:
                with tarfile.open(fileobj=output, mode="w") as target:
                    for member in source.getmembers():
                        target.addfile(member, source.extractfile(member) if member.isfile() else None)
                    member = tarfile.TarInfo(name)
                    member.type = tarfile.DIRTYPE if directory else tarfile.REGTYPE
                    payload = b"synthetic archive member\n"
                    member.size = 0 if directory else len(payload)
                    target.addfile(member, None if directory else io.BytesIO(payload))
            return subprocess.CompletedProcess(command, result.returncode, output.getvalue(), result.stderr)
        return result

    monkeypatch.setattr(probe.subprocess, "run", run)


def test_leak_original_hit(root_case, capsys):
    path = _plant(root_case, "notes/original [a]*.txt", root_case["records"][0]["original"])
    # Also pin sorted first-hit order, independently of directory creation order.
    _plant(root_case, "z-later.txt", root_case["records"][0]["expected"])
    _assert_root_refusal(_run_root(root_case, capsys), f"leak:{path}", "original text outside its own paired copy")


def test_leak_expected_hit(root_case, capsys):
    # A different feature/document proves the scan uses every ledger record.
    path = _plant(root_case, "notes/expected [a]*.txt", root_case["records"][-1]["expected"])
    _assert_root_refusal(_run_root(root_case, capsys), f"leak:{path}", "expected finding from a non-target document")


def test_leak_hit_only_after_rewrap(root_case, capsys):
    needle = root_case["records"][0]["original"].encode("utf-8")
    rewrapped = b"\r\n\t".join(needle.split()) + b"\r\n"
    assert needle not in rewrapped, "fixture must not contain a raw-byte original hit"
    path = _plant(root_case, "notes/rewrapped.txt", rewrapped.decode("utf-8"))
    _assert_root_refusal(_run_root(root_case, capsys), f"leak:{path}", "whitespace rewrapping must not hide an original")
    normalise = root_case["probe"].normalise
    assert normalise(needle) == normalise(rewrapped), "one normaliser must handle needle and haystack identically"
    sample = b" \tA\xff\r\nB "
    assert normalise(sample) == " A\ufffd B ", "D6 replaces invalid UTF-8 and collapses whitespace without strip or case folding"


def test_leak_symlink_to_file(root_case, capsys):
    link = root_case["tree"] / "notes/linked-file"
    link.symlink_to("keep-me.txt")
    assert link.is_file() and link.is_symlink()
    _assert_root_refusal(_run_root(root_case, capsys), "leak:notes/linked-file", "symlink to a harmless regular file")


def test_leak_symlink_to_dir(root_case, capsys):
    link = root_case["tree"] / "notes/linked-dir"
    link.symlink_to("nested", target_is_directory=True)
    assert link.is_dir() and link.is_symlink()
    _assert_root_refusal(_run_root(root_case, capsys), "leak:notes/linked-dir", "symlink directory must be refused without following it")


def test_leak_original_in_paired_copy_with_other_sha(root_case, capsys, monkeypatch):
    source = root_case["records"][0]["source"]
    name = Path(source).name
    live = f"docs/01-plan/features/{name}"
    archive_bytes = (root_case["tree"] / source).read_bytes()
    changed_bytes = archive_bytes + b"\nextra paired-copy byte\n"
    assert hashlib.sha256(archive_bytes).digest() != hashlib.sha256(changed_bytes).digest()
    real_scan = getattr(root_case["probe"], "scan_root", None)

    def scan_root(root, ledger, sources, doc):
        # Simulate corruption of the placed copy, leaving its archive source intact.
        path = root / live
        assert path.read_bytes() == archive_bytes, "fixture must alter an otherwise byte-identical paired source"
        path.write_bytes(changed_bytes)
        return real_scan(root, ledger, sources, doc)

    monkeypatch.setattr(root_case["probe"], "scan_root", scan_root, raising=False)
    _assert_root_refusal(_run_root(root_case, capsys, doc="d2"), f"leak:{live}", "paired original exemption requires byte-identical source SHA")


def test_leak_expected_in_byte_identical_paired_copy(root_case, capsys):
    record = root_case["records"][0]
    source = root_case["tree"] / record["source"]
    source.write_text(source.read_text(encoding="utf-8") + record["expected"] + "\n", encoding="utf-8")
    # Rebuilding makes this the exact original archive blob, not a corrupted copy.
    root_case["records"] = build_ledger(root_case["tree"], root_case["sources"])
    live = f"docs/01-plan/features/{source.name}"
    _assert_root_refusal(_run_root(root_case, capsys, doc="d2"), f"leak:{live}", "expected text is never exempt even in an exact paired-source copy")


def test_leak_on_the_seeded_target(root_case, capsys):
    record = root_case["records"][0]
    # D4 still reconstructs this exactly; the seeded target retains an original.
    record["seeded"] = record["original"] + " widened seed still exposes original\n"
    _rebuild_document(root_case["tree"], root_case["records"], record["source"])
    live = f"docs/01-plan/features/{Path(record['source']).name}"
    _assert_root_refusal(_run_root(root_case, capsys), f"leak:{live}", "the seeded target is not a byte-identical paired-source exemption")


def test_leak_tar_member_leaving_the_root(root_case, capsys, monkeypatch):
    _append_archive_member(root_case["probe"], monkeypatch, "../escaped.txt")
    _assert_root_refusal(_run_root(root_case, capsys), "leak:../escaped.txt", "tar data filter must reject a member leaving the root")
    assert not (root_case["dest"] / "escaped.txt").exists(), "refused archive must not write outside the root"


def test_leak_exclusion_line_outside_the_grammar(root_case, capsys):
    path = root_case["repo"] / EXCLUSIONS
    path.write_text("\n".join(root_case["entries"]) + "\nunrecognised policy [a]*\n", encoding="utf-8")
    git(root_case["repo"], "add", EXCLUSIONS.as_posix())
    git(root_case["repo"], "commit", "-m", "Malformed synthetic exclusion policy")
    _assert_root_refusal(_run_root(root_case, capsys), f"leak:{EXCLUSIONS.as_posix()}", "an exclusion outside dir/name-contains grammar names the list's tree path")


def test_original_in_byte_identical_own_source_copy_does_not_refuse(root_case, capsys):
    result = _run_root(root_case, capsys, doc="d2")
    fields = _ready_fields(result, "original text in its byte-identical own paired plan must be exempt")
    source = root_case["records"][0]["source"]
    live = Path(fields["path"]) / "docs/01-plan/features" / Path(source).name
    assert live.read_bytes() == (root_case["tree"] / source).read_bytes(), "exempt paired copy must retain exact archive bytes"
    assert root_case["records"][0]["original"].encode("utf-8") in live.read_bytes()


def test_root_git_dot_git_directory(root_case, capsys, monkeypatch):
    _append_archive_member(root_case["probe"], monkeypatch, "nested/.git", directory=True)
    _assert_root_refusal(_run_root(root_case, capsys), "root_git:nested/.git", "a nested .git directory makes the exported root git-reachable")


def test_root_git_dot_git_file(root_case, capsys, monkeypatch):
    _append_archive_member(root_case["probe"], monkeypatch, "nested/.git")
    _assert_root_refusal(_run_root(root_case, capsys), "root_git:nested/.git", "a nested .git regular file must be refused regardless of contents")


def test_root_git_root_nested_in_work_tree(root_case, capsys):
    root_case["dest"] = root_case["repo"] / "nested-exports"
    root_case["dest"].mkdir()
    expected = git(root_case["repo"], "rev-parse", "--absolute-git-dir")
    _assert_root_refusal(_run_root(root_case, capsys), f"root_git:{expected}", "rev-parse must detect an ancestor work tree without a .git entry in the root")


def test_root_git_ignores_ambient_git_dir_env(root_case, capsys, monkeypatch):
    actual_run = root_case["probe"].subprocess.run
    observed = []
    names = ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR",
             "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES")
    ambient = {
        "GIT_DIR": str(root_case["repo"] / ".git"),
        "GIT_WORK_TREE": str(root_case["repo"]),
        "GIT_COMMON_DIR": str(root_case["repo"] / ".git"),
        "GIT_OBJECT_DIRECTORY": str(root_case["repo"] / ".git/objects"),
        "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(root_case["repo"] / ".git/objects"),
    }

    def run(command, *args, **kwargs):
        if command[0] == "git" and "--absolute-git-dir" in command:
            environment = kwargs.get("env")
            observed.append(environment)
            assert environment is not None and all(name not in environment for name in names), (
                "D7 reach invocation must remove all five ambient Git variables"
            )
        return actual_run(command, *args, **kwargs)

    # Build/calibration fixture plumbing must complete before contaminating the env.
    sha = commit_root_tree(root_case)
    for name, value in ambient.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(root_case["probe"].subprocess, "run", run)
    result = _run_root(root_case, capsys, sha=sha)
    _ready_fields(result, "an ambient GIT_DIR must not make an isolated export git-reachable")
    assert observed, "the real D7 rev-parse reach check must still run"


def test_build_root_places_only_the_phase_pairs(root_case, capsys):
    expected = {}
    for index, (feature, directory) in enumerate(root_case["sources"].items()):
        archive = f"{directory}/{feature}"
        spec = f"docs/01-plan/features/{feature}.spec.md"
        plan = f"docs/01-plan/features/{feature}.plan.md"
        design = f"docs/02-design/features/{feature}.design.md"
        impl_plan = f"docs/01-plan/features/{feature}.impl-plan.md"
        expected[f"d{index * 3 + 1}"] = {plan: f"{CALIBRATION}/seeded/{feature}.plan.md", spec: f"{archive}/{feature}.spec.md"}
        expected[f"d{index * 3 + 2}"] = {design: f"{CALIBRATION}/seeded/{feature}.design.md", spec: f"{archive}/{feature}.spec.md", plan: f"{archive}/{feature}.plan.md"}
        expected[f"d{index * 3 + 3}"] = {impl_plan: f"{CALIBRATION}/seeded/{feature}.impl-plan.md", design: f"{archive}/{feature}.design.md"}
    roots = []
    sha = commit_root_tree(root_case)
    for index, doc in enumerate(expected):
        purpose = ("s1", "s2v1", "s2v2", "rescore")[index % 4]
        result = _run_root(root_case, capsys, doc=doc, purpose=purpose, sha=sha)
        fields = _ready_fields(result, f"{doc} must place only its target and assembler phase pairs")
        root = Path(fields["path"])
        roots.append(root)
        assert root.is_absolute() and root.parent.resolve() == root_case["dest"].resolve()
        assert root.name.startswith(f"gas-root-{doc}-{purpose}-")
        assert (fields["doc"], fields["purpose"], fields["calibration"]) == (doc, purpose, root_case["sha"])
        actual = {path.relative_to(root).as_posix() for base in (
            root / "docs/01-plan/features", root / "docs/02-design/features",
        ) for path in base.rglob("*") if path.is_file()}
        assert actual == set(expected[doc]), f"{doc} must contain exactly the phase's target and pairs"
        assert root_case["probe"].placements(doc, root_case["sources"]) == expected[doc]
        for live, source in expected[doc].items():
            assert (root / live).read_bytes() == (root_case["tree"] / source).read_bytes(), f"{live} must preserve its selected blob bytes"
    assert len(set(roots)) == 9, "each fresh-root request must allocate a distinct directory"
    definitions = [node for node in ast.walk(ast.parse(PROBE.read_text(encoding="utf-8")))
                   if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "placements"]
    assert len(definitions) == 1, "placements must be the single document-to-live-path mapping definition"


def test_build_root_removes_every_exclusion_entry(root_case, capsys):
    path = root_case["repo"] / EXCLUSIONS
    path.write_text(path.read_text(encoding="utf-8") + "dir absent-from-export\n", encoding="utf-8")
    git(root_case["repo"], "add", EXCLUSIONS.as_posix())
    git(root_case["repo"], "commit", "-m", "One harmless absent exclusion")
    fields = _ready_fields(_run_root(root_case, capsys), "every dir and every name-contains match must be removed")
    root = Path(fields["path"])
    remaining = {path.relative_to(root).as_posix() for path in root.rglob("*")}
    for entry in root_case["entries"]:
        kind, value = entry.split(" ", 1)
        if kind == "dir":
            assert not any(path == value or path.startswith(value + "/") for path in remaining), f"excluded subtree survived re-walk: {value}"
        else:
            assert not any(value in Path(path).name for path in remaining), f"name-contains match survived re-walk: {value}"
    assert fields["absent"] == "1", "only the deliberately missing list entry is counted absent"
    assert (root / "notes/keep-me.txt").read_bytes() == (root_case["tree"] / "notes/keep-me.txt").read_bytes()


def test_build_root_reads_the_list_from_the_commit_not_the_work_tree(root_case, capsys):
    repo = root_case["repo"]
    selected = git(repo, "rev-parse", "HEAD")
    selected_blob = git(repo, "rev-parse", f"HEAD:{EXCLUSIONS.as_posix()}")
    policy = repo / EXCLUSIONS
    policy.write_text("invalid committed replacement [a]*\n", encoding="utf-8")
    git(repo, "add", EXCLUSIONS.as_posix())
    git(repo, "commit", "-m", "Newer list must not override a pinned list commit")
    policy.write_text("invalid work-tree replacement ⟦/h-mad⟧\n", encoding="utf-8")
    result = _run_root(root_case, capsys, extra=("--list-commit", selected))
    fields = _ready_fields(result, "the pinned commit's list must win over both HEAD and work-tree copies")
    assert (fields["list_commit"], fields["list_blob"]) == (selected, selected_blob)
    assert not (Path(fields["path"]) / CALIBRATION).exists(), "selected policy must actually remove the calibration subtree"


def test_build_root_prints_list_commit_and_blob(root_case, capsys):
    repo = root_case["repo"]
    expected_commit = git(repo, "rev-parse", "HEAD")
    expected_blob = git(repo, "rev-parse", f"HEAD:{EXCLUSIONS.as_posix()}")
    fields = _ready_fields(_run_root(root_case, capsys), "ROOT: READY must publish the exact committed exclusion-list provenance")
    assert fields["list_commit"] == expected_commit, "list_commit must be git rev-parse HEAD, not the calibration commit"
    assert fields["list_blob"] == expected_blob, "list_blob must be git rev-parse HEAD:docs/03-analysis/probes/grok-audit-surface/exclusions.txt"
    assert re.fullmatch(r"[0-9a-f]{40}", fields["list_commit"])
    assert re.fullmatch(r"[0-9a-f]{40}", fields["list_blob"])


def test_root_line_parser_reads_build_root_output(root_case, capsys):
    parser = root_case["probe"].parse_root_line
    result = _run_root(root_case, capsys, dest=False)
    fields = _ready_fields(result, "parse_root_line must consume a real build-root success token")
    root = Path(fields["path"])
    try:
        assert root.parent.resolve() == Path(tempfile.gettempdir()).resolve(), "default allocation must use tempfile's directory"
        assert root.name.startswith("gas-root-d1-s1-"), "default allocation must identify its document and purpose"
        parsed = parser(result.stdout.splitlines()[-1])
        assert parsed == fields, "ROOT parser must preserve every D2 field from build-root output"
        assert set(parsed) == {"doc", "purpose", "path", "calibration", "list_commit", "list_blob", "absent"}
    finally:
        shutil.rmtree(root)


def test_root_line_parser_rejects_a_malformed_root_line(root_case, capsys):
    parser = root_case["probe"].parse_root_line
    result = _run_root(root_case, capsys)
    _ready_fields(result, "malformed parser fixtures must originate in a real build-root token")
    line = result.stdout.splitlines()[-1]
    for field in ("list_blob", "doc", "purpose", "path", "calibration", "list_commit", "absent"):
        malformed = " ".join(word for word in line.split() if not word.startswith(field + "="))
        assert parser(malformed) is None, f"ROOT parser must reject a success token missing {field}"
    assert parser("ROOT: UNREADABLE reason=leak:x") is None, "ROOT parser must not accept a refusal token as a ready root"


def _fresh_reset_build(case, capsys, *, doc="d1"):
    extra = ("--list-commit", case["reset_fields"]["list_commit"]) if "reset_fields" in case else ()
    result = _run_root(case, capsys, dest=False, doc=doc, purpose="s1",
                       sha=case.get("sha"), extra=extra)
    fields = _ready_fields(result, "reset fixture must start with a valid S1 build")
    root = Path(fields["path"])
    case["reset_roots"].append(root)
    assert root.parent.resolve() == Path(tempfile.gettempdir()).resolve(), result.stderr
    return root, fields, result.stdout.splitlines()[-1]


@pytest.fixture
def reset_case(root_case, capsys):
    case = root_case
    case["reset_roots"] = []
    try:
        root, fields, line = _fresh_reset_build(case, capsys)
        case.update(reset_live=root, reset_fields=fields, reset_line=line)
        yield case
    finally:
        for root in case["reset_roots"]:
            shutil.rmtree(root, ignore_errors=True)


def _run_reset(case, capsys, *, target=None, purpose="s1", dest=False):
    if target is None:
        target = str(case["reset_live"])
    result = _run_root(
        case, capsys, dest=dest, purpose=purpose, sha=case["sha"],
        extra=("--reset", str(target), "--list-commit", case["reset_fields"]["list_commit"]),
    )
    # At RED the ignored --reset allocates a different root; clean that up too.
    for line in result.stdout.splitlines():
        fields = case["probe"].parse_root_line(line)
        if fields is not None:
            case["reset_roots"].append(Path(fields["path"]))
    return result


def _reset_manifest(root):
    """Record all paths and file hashes, judging links without following them."""
    manifest = {}
    for directory, directories, files in os.walk(root, followlinks=False):
        for name in directories + files:
            path = Path(directory) / name
            mode = path.lstat().st_mode
            digest = hashlib.sha256(path.read_bytes()).hexdigest() if stat.S_ISREG(mode) else None
            manifest[path.relative_to(root).as_posix()] = (stat.S_IFMT(mode), digest)
    return manifest


def _reset_sentinel(root):
    path = root / "sentinel [a]* ⟦h-mad⟧.txt"
    content = b"h-mad: [a](b) **bold** * [ \xe2\x9f\xa6/h-mad\xe2\x9f\xa7\nsecond\tline"
    path.write_bytes(content)
    return path, content


def test_build_root_reset_removes_by_products_and_restores_placed_files(reset_case, capsys):
    case = reset_case
    live = case["reset_live"]
    expected, _, _ = _fresh_reset_build(case, capsys)
    clean = _reset_manifest(expected)
    for relative in (
        "cycle-v1.collected.md", "cycle-v1.effort.json", "cycle-v1.gated.json",
        ".h-mad/pass-logs/p1.log",
    ):
        path = live / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("h-mad: [a](b) **bold** * [ ⟦/h-mad⟧\nsecond\tline", encoding="utf-8")
    target = live / "docs/01-plan/features/paper-lantern.plan.md"
    target.write_bytes(b"edited placed document\n")
    planted_count = len(set(_reset_manifest(live)) - set(clean))

    result = _run_reset(case, capsys)

    assert (result.returncode, result.stdout.splitlines()[-1:]) == (0, [case["reset_line"]]), result.stderr
    assert result.stdout.splitlines() == [
        f"RESET: removed={planted_count} restored=1", case["reset_line"],
    ], result.stderr
    actual = _reset_manifest(live)
    assert set(actual) == set(clean), "reset must leave exactly a fresh build's path set"
    assert actual == clean, "reset must restore every file's sha256 to the fresh build's hash"


def test_build_root_reset_rescans_after_removal(reset_case, capsys, monkeypatch):
    case = reset_case
    relative = "retained-expected [a]*.txt"
    (case["reset_live"] / relative).write_text(case["records"][0]["expected"], encoding="utf-8")
    monkeypatch.setattr(case["probe"], "remove_absent", lambda live, expected: 0, raising=False)
    # Operator choice (b): isolate step 6 while keeping D5's re-walk-first order.
    monkeypatch.setattr(case["probe"], "rewalk_matches", lambda live, expected: None, raising=False)

    result = _run_reset(case, capsys)

    assert (result.returncode, result.stdout.splitlines()[-1:]) == (
        2, [f"ROOT: UNREADABLE reason=leak:{relative}"],
    ), result.stderr
    n = result.stderr.count("Traceback")
    assert n == 0, "a declared live-root scan refusal must not print a traceback"


def test_build_root_reset_runs_the_reach_check(reset_case, capsys, monkeypatch):
    case = reset_case

    def plant_git_after_precondition(live, expected):
        (live / ".git").mkdir()
        return 0

    monkeypatch.setattr(case["probe"], "remove_absent", plant_git_after_precondition, raising=False)
    # Operator choice (b): the new .git must reach step 6 rather than mismatch.
    monkeypatch.setattr(case["probe"], "rewalk_matches", lambda live, expected: None, raising=False)

    result = _run_reset(case, capsys)

    assert (result.returncode, result.stdout.splitlines()[-1:]) == (
        2, ["ROOT: UNREADABLE reason=root_git:.git"],
    ), result.stderr
    n = result.stderr.count("Traceback")
    assert n == 0, "a declared post-reset reach refusal must not print a traceback"


def test_build_root_reset_mismatch_is_internal(reset_case, capsys, monkeypatch):
    case = reset_case
    real_restore = getattr(case["probe"], "restore_expected", None)

    def restore_then_add_path(live, expected):
        restored = real_restore(live, expected)
        (live / "concurrent-extra.txt").write_bytes(b"write before the real re-walk\n")
        return restored

    monkeypatch.setattr(case["probe"], "restore_expected", restore_then_add_path, raising=False)

    result = _run_reset(case, capsys)

    assert (result.returncode, result.stdout.splitlines()[-1:]) == (
        2, ["ROOT: UNREADABLE reason=internal:RootResetMismatch"],
    ), result.stderr
    n = result.stderr.count("Traceback")
    assert n == 0, "a declared re-walk mismatch must not print a traceback"


def test_build_root_reset_and_dest_parent_are_exclusive(reset_case, capsys):
    case = reset_case
    sentinel, content = _reset_sentinel(case["reset_live"])
    # A second invalid argument pins exclusivity before the purpose guard.
    result = _run_reset(case, capsys, dest=True, purpose="s2v1")

    assert (result.returncode, result.stdout.splitlines()[-1:]) == (
        2, ["ROOT: UNREADABLE reason=internal:ResetArgsConflict"],
    ), result.stderr
    assert sentinel.read_bytes() == content, "argument conflict must not remove the live sentinel"
    assert list(case["dest"].iterdir()) == [], "argument conflict must not allocate under --dest-parent"
    n = result.stderr.count("Traceback")
    assert n == 0, "a declared reset argument conflict must not print a traceback"


def test_build_root_reset_refuses_a_non_s1_purpose(reset_case, capsys):
    sentinel, content = _reset_sentinel(reset_case["reset_live"])
    result = _run_reset(reset_case, capsys, purpose="s2v1")

    assert (result.returncode, result.stdout.splitlines()[-1:]) == (
        2, ["ROOT: UNREADABLE reason=internal:ResetPurposeNotS1"],
    ), result.stderr
    assert sentinel.read_bytes() == content, "a non-S1 purpose must leave the S1 root untouched"
    n = result.stderr.count("Traceback")
    assert n == 0, "a declared reset purpose refusal must not print a traceback"


def test_build_root_reset_refuses_an_empty_target(reset_case, tmp_path, capsys, monkeypatch):
    sentinel, content = _reset_sentinel(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = _run_reset(reset_case, capsys, target="")

    assert (result.returncode, result.stdout.splitlines()[-1:]) == (
        2, ["ROOT: UNREADABLE reason=internal:ResetTargetNotAbsolute"],
    ), result.stderr
    assert sentinel.read_bytes() == content, "an empty target must not remove the working-directory sentinel"
    n = result.stderr.count("Traceback")
    assert n == 0, "a declared absolute-target refusal must not print a traceback"


def test_build_root_reset_refuses_a_missing_target(reset_case, capsys):
    target = Path(tempfile.gettempdir()) / f"gas-root-d1-s1-absent-{uuid.uuid4().hex}"
    assert not target.exists(), "missing-target fixture must start absent"
    result = _run_reset(reset_case, capsys, target=target)

    assert (result.returncode, result.stdout.splitlines()[-1:]) == (
        2, ["ROOT: UNREADABLE reason=internal:ResetTargetNotDirectory"],
    ), result.stderr
    assert not target.exists(), "refusing a missing reset target must leave it absent"
    n = result.stderr.count("Traceback")
    assert n == 0, "a declared missing-target refusal must not print a traceback"


def test_build_root_reset_refuses_a_target_outside_the_tempdir(reset_case, tmp_path, capsys):
    target = tmp_path / "gas-root-d1-s1-outside"
    target.mkdir()
    sentinel, content = _reset_sentinel(target)
    result = _run_reset(reset_case, capsys, target=target)

    assert (result.returncode, result.stdout.splitlines()[-1:]) == (
        2, ["ROOT: UNREADABLE reason=internal:ResetTargetOutsideTempdir"],
    ), result.stderr
    assert sentinel.read_bytes() == content, "an outside target must retain its sentinel bytes"
    n = result.stderr.count("Traceback")
    assert n == 0, "a declared tempdir-parent refusal must not print a traceback"


def test_build_root_reset_refuses_another_documents_root(reset_case, capsys):
    target, _, _ = _fresh_reset_build(reset_case, capsys, doc="d2")
    sentinel, content = _reset_sentinel(target)
    result = _run_reset(reset_case, capsys, target=target)

    assert (result.returncode, result.stdout.splitlines()[-1:]) == (
        2, ["ROOT: UNREADABLE reason=internal:ResetTargetPrefix"],
    ), result.stderr
    assert sentinel.read_bytes() == content, "another document's root must retain its sentinel bytes"
    n = result.stderr.count("Traceback")
    assert n == 0, "a declared document-prefix refusal must not print a traceback"


def test_build_root_reset_refuses_a_git_target(reset_case, capsys):
    live = reset_case["reset_live"]
    git(live, "init", "--initial-branch=main")
    result = _run_reset(reset_case, capsys)

    assert (result.returncode, result.stdout.splitlines()[-1:]) == (
        2, ["ROOT: UNREADABLE reason=root_git:.git"],
    ), result.stderr
    n = result.stderr.count("Traceback")
    assert n == 0, "a declared reset target reach refusal must not print a traceback"


def test_build_root_reset_accepts_the_physical_spelling_of_its_root(reset_case, capsys):
    case = reset_case
    result = _run_reset(case, capsys, target=case["reset_live"].resolve())

    assert (result.returncode, result.stdout.splitlines()[-1:]) == (
        0, [case["reset_line"]],
    ), result.stderr
    assert result.stdout.splitlines() == ["RESET: removed=0 restored=0", case["reset_line"]], result.stderr


def test_build_root_reset_does_not_delete_through_a_symlinked_by_product_dir(reset_case, tmp_path, capsys):
    case = reset_case
    outside = tmp_path / "outside/logs"
    outside.mkdir(parents=True)
    sentinel, content = _reset_sentinel(outside)
    link = case["reset_live"] / ".h-mad/pass-logs"
    link.parent.mkdir()
    link.symlink_to(outside, target_is_directory=True)

    result = _run_reset(case, capsys)

    assert outside.is_dir(), "reset must not delete the symlink's outside directory"
    assert sentinel.read_bytes() == content, "reset must not delete through a symlinked by-product directory"
    assert not os.path.lexists(link), "reset must unlink the by-product link itself"
    assert (result.returncode, result.stdout.splitlines()[-1:]) == (0, [case["reset_line"]]), result.stderr


def test_restore_expected_does_not_write_through_a_symlinked_placed_document(reset_case, tmp_path, capsys):
    case = reset_case
    expected, _, _ = _fresh_reset_build(case, capsys)
    relative = Path("docs/01-plan/features/paper-lantern.plan.md")
    target = case["reset_live"] / relative
    outside = tmp_path / "outside"
    outside.mkdir()
    victim = outside / "victim.md"
    content = b"h-mad: [a](b) **bold** * [ \xe2\x9f\xa6/h-mad\xe2\x9f\xa7\nsecond\tline"
    victim.write_bytes(content)
    target.unlink()
    target.symlink_to(victim)

    case["probe"].restore_expected(case["reset_live"], expected)

    assert victim.read_bytes() == content, "restore_expected must not write through a symlinked placed document"
    assert stat.S_ISREG(target.lstat().st_mode), "restore_expected must replace the document link with a regular file"
    assert hashlib.sha256(target.read_bytes()).digest() == hashlib.sha256((expected / relative).read_bytes()).digest(), "restored document must equal the expected file's sha256"


def test_restore_expected_does_not_write_through_a_symlinked_parent_directory(reset_case, tmp_path, capsys):
    case = reset_case
    expected, _, _ = _fresh_reset_build(case, capsys)
    relative = Path("docs/01-plan/features/paper-lantern.plan.md")
    parent = (case["reset_live"] / relative).parent
    outside = tmp_path / "outside/features"
    outside.mkdir(parents=True)
    victim = outside / relative.name
    content = b"h-mad: [a](b) **bold** * [ \xe2\x9f\xa6/h-mad\xe2\x9f\xa7\nsecond\tline"
    victim.write_bytes(content)
    shutil.rmtree(parent)
    parent.symlink_to(outside, target_is_directory=True)

    case["probe"].restore_expected(case["reset_live"], expected)

    assert victim.read_bytes() == content, "restore_expected must not write through a linked parent directory"
    assert stat.S_ISDIR(parent.lstat().st_mode), "restore_expected must replace the parent link with a real directory"
    assert (case["reset_live"] / relative).read_bytes() == (expected / relative).read_bytes(), "the restored file under the real parent must equal the expected file"


@pytest.fixture
def cycle_case(root_case, tmp_path, capsys):
    result = _run_root(root_case, capsys)
    fields = _ready_fields(result, "record-cycle fixtures require a real build-root READY line")
    case = build_cycle_inputs(
        tmp_path / "kept cycle [a]* ⟦h-mad⟧", Path(fields["path"]),
        result.stdout.splitlines()[-1],
    )
    case["probe"] = root_case["probe"]
    return case


def _run_record(case, capsys):
    arguments = ["record-cycle"]
    for key in ("stem", "root", "root_record", "stdout", "command", "dest"):
        arguments += ["--" + key.replace("_", "-"), str(case[key])]
    rc = case["probe"].main(arguments)
    out, err = capsys.readouterr()
    return subprocess.CompletedProcess(arguments, rc, out, err)


def _record_files(case):
    return {
        path.relative_to(case["dest"]).as_posix(): path.read_bytes()
        for path in case["dest"].rglob("*") if path.is_file()
    }


def _assert_record_ok(case, result, property_name):
    files = _record_files(case)
    assert (result.returncode, result.stdout.splitlines()[-1:]) == (
        0, [f"RECORD: OK dest={case['dest'].resolve()} files={len(files)}"],
    ), f"{property_name}: stdout={result.stdout!r}; stderr={result.stderr!r}"
    assert files, f"{property_name}: a successful record must write cycle data"
    return files


def _assert_record_refusal(case, result, reason, property_name):
    # Check state even at RED, before the missing handler fails the token assertion.
    assert not _record_files(case), f"{property_name}: refusal must not write any destination file"
    assert (result.returncode, result.stdout.splitlines()[-1:]) == (
        2, [f"RECORD: REFUSED reason={reason}"],
    ), f"{property_name}: stdout={result.stdout!r}; stderr={result.stderr!r}"
    assert "Traceback" not in result.stderr, f"{property_name}: a declared refusal has no traceback"


def test_record_cycle_writes_root_txt(cycle_case, capsys):
    case = cycle_case
    assert not case["dest"].parent.exists(), "destination parents must begin absent"
    files = _assert_record_ok(case, _run_record(case, capsys), "persist the selected root's READY line")
    assert files["root.txt"] == (case["ready_line"] + "\n").encode(), "root.txt must contain only the actual build-root READY line"
    assert files["command.txt"] == case["command"].read_bytes(), "command.txt must retain the exact dispatch argv"
    assert files["auditcycle.txt"] == case["stdout"].read_bytes(), "auditcycle.txt must retain the full wrapper stdout"


def test_record_cycle_refuses_a_root_record_without_a_line(cycle_case, capsys):
    case = cycle_case
    # Both ends of D5's exactly-one requirement, without adding pytest nodes.
    for content in ("RESET: removed=0 restored=0\n", (case["ready_line"] + "\n") * 2):
        case["root_record"].write_text(content, encoding="utf-8")
        _assert_record_refusal(case, _run_record(case, capsys), "root_record:no_line",
                               "require exactly one ROOT: READY line")


def test_record_cycle_refuses_a_root_record_for_another_root(cycle_case, tmp_path, capsys):
    case = cycle_case
    another = tmp_path / "other-root"
    another.mkdir()
    line = case["ready_line"].replace(f"path={case['root']}", f"path={another.resolve()}")
    assert line != case["ready_line"], "the mismatched fixture must actually name another root"
    case["root_record"].write_text(line + "\n", encoding="utf-8")
    _assert_record_refusal(case, _run_record(case, capsys), "root_record:path_mismatch",
                           "tie the recorded root to the cycle's actual root")


def test_record_cycle_refuses_stdout_without_auditcycle(cycle_case, capsys):
    case = cycle_case
    case["stdout"].write_text("ASSEMBLE: HALT p1:preflight\n", encoding="utf-8")
    _assert_record_refusal(case, _run_record(case, capsys), f"no_auditcycle_line:{case['stdout']}",
                           "require the wrapper's AUDITCYCLE line")


def test_record_cycle_copies_only_its_own_cycle_reports(cycle_case, capsys):
    case = cycle_case
    # Existing directories exercise exist_ok=True, while the first success test
    # requires creation of missing parents.
    case["dest"].mkdir(parents=True)
    files = _assert_record_ok(case, _run_record(case, capsys), "copy only cycle 2's D3 file map")
    assert set(files) == set(case["expected"]), "D3 excludes other features/phases, v1/v3/v20, unmapped stem files and gated stamps"
    for relative, expected in case["expected"].items():
        assert files[relative] == expected, f"cycle 2 file must preserve its source: {relative}"


def test_record_cycle_refuses_a_root_record_with_a_malformed_ready_line(cycle_case, capsys):
    case = cycle_case
    malformed = " ".join(word for word in case["ready_line"].split() if not word.startswith("list_blob="))
    assert case["probe"].parse_root_line(malformed) is None, "the real build-root line must become malformed when list_blob is removed"
    case["root_record"].write_text(malformed + "\n", encoding="utf-8")
    _assert_record_refusal(case, _run_record(case, capsys), "root_record:no_line",
                           "map a malformed READY line to no_line rather than path_mismatch")


def test_record_cycle_copies_stem_files_byte_for_byte(cycle_case, capsys):
    case = cycle_case
    files = _assert_record_ok(case, _run_record(case, capsys), "preserve every wrapper stem file byte for byte")
    for destination, source in case["stem_sources"].items():
        assert destination in files, f"the D3 stem mapping must copy {source.name} to {destination}"
        assert hashlib.sha256(files[destination]).digest() == hashlib.sha256(source.read_bytes()).digest(), (
            f"{destination} must have its exact stem source's sha256, including binary/hostile bytes"
        )
    wrapper_log = case["stem"] / f"{case['prefix']}_p1.log"
    assert files["p1.log"] != files["pass-logs/paper-lantern.plan.audit.v2.p1.md.log"], "the wrapper --log input and collected pass log are distinct fixture files"
    assert files["p1.log"] == wrapper_log.read_bytes(), "p1.log must be the exact log[$i] path passed as --log (carry 14)"


def test_record_cycle_refuses_a_missing_input(cycle_case, capsys):
    case = cycle_case
    case["stdout"].unlink()
    _assert_record_refusal(case, _run_record(case, capsys), f"input_missing:{case['stdout']}",
                           "identify the missing stdout input before writing")


def test_record_cycle_refuses_zero_stem_prefixes(cycle_case, capsys):
    case = cycle_case
    for path in case["stem"].glob(case["prefix"] + "*"):
        path.unlink()
    _assert_record_refusal(case, _run_record(case, capsys), "stem_prefix:0",
                           "require a stem prefix matching command feature/phase/cycle")


def test_record_cycle_refuses_two_stem_prefixes(cycle_case, capsys):
    case = cycle_case
    second = case["prefix"].replace("-314", "-315")
    for source in case["stem_sources"].values():
        (case["stem"] / source.name.replace(case["prefix"], second)).write_bytes(source.read_bytes())
    _assert_record_refusal(case, _run_record(case, capsys), "stem_prefix:2",
                           "refuse two runs matching the selected cycle")


def test_record_cycle_refuses_a_command_without_cycle_flags(cycle_case, capsys):
    case = cycle_case
    text = case["command"].read_text(encoding="utf-8")
    assert "--cycle 2" in text, "the valid command must have the cycle flag before removing it"
    case["command"].write_text(text.replace("--cycle 2", ""), encoding="utf-8")
    _assert_record_refusal(case, _run_record(case, capsys), f"command_unparseable:{case['command']}",
                           "require all feature/phase/cycle flags in the command file")


@pytest.fixture
def commit_case(tmp_path, monkeypatch):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR",
                 "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_INDEX_FILE"):
        monkeypatch.delenv(name, raising=False)
    case = build_commit_inputs(tmp_path)
    case["probe"] = load_probe(PROBE)
    return case


def _run_commit(case, capsys):
    arguments = [
        "commit-data", "--repo", str(case["repo"]), "--parent", case["parent"],
        "--src", str(case["src"]), "--message", case["message"],
    ]
    rc = case["probe"].main(arguments)
    out, err = capsys.readouterr()
    return subprocess.CompletedProcess(arguments, rc, out, err)


def _read_calibration_ref(repo):
    # Real Git, deliberately outside the probe's replaceable _git function.
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--verify", CALIBRATION_REF],
        capture_output=True, text=True, timeout=15,
    )
    return result.returncode, result.stdout.strip()


def _observe_commit_git(case, monkeypatch, *, false_reread=False):
    """Observe real plumbing; replace only the post-update ref-read response."""
    real_git = getattr(case["probe"], "_git", None)
    calls = []
    state = {"calls": calls, "created": None, "updated": False, "rereads": 0}

    def observed(repo, *argv, env=None, stdin=None):
        result = real_git(repo, *argv, env=env, stdin=stdin)
        calls.append((argv, env))
        if argv[0] == "commit-tree" and result.returncode == 0:
            state["created"] = result.stdout.strip().decode()
        if argv[0] == "update-ref" and result.returncode == 0:
            state["updated"] = True
        if state["updated"] and argv[0] == "rev-parse" and CALIBRATION_REF in argv:
            state["rereads"] += 1
            if false_reread:
                return subprocess.CompletedProcess(result.args, 0, (case["parent"] + "\n").encode(), result.stderr)
        return result

    # The helper is new in Task 6; at RED main fails on the missing handler
    # before this observer runs. It never installs a replacement implementation.
    monkeypatch.setattr(case["probe"], "_git", observed, raising=False)
    return state


def _assert_commit_prewrite_refusal(case, capsys, monkeypatch, reason, property_name):
    before = _read_calibration_ref(case["repo"])
    state = _observe_commit_git(case, monkeypatch)
    result = _run_commit(case, capsys)
    assert _read_calibration_ref(case["repo"]) == before, f"{property_name}: the calibration ref must retain its pre-test value/absence"
    assert not any(argv[0] == "update-ref" for argv, _env in state["calls"]), f"{property_name}: refusal must precede update-ref"
    assert (result.returncode, result.stdout.splitlines()[-1:]) == (
        2, [f"COMMIT: REFUSED reason={reason}"],
    ), f"{property_name}: stdout={result.stdout!r}; stderr={result.stderr!r}"
    assert "Traceback" not in result.stderr, f"{property_name}: a declared refusal has no traceback"


def test_commit_data_never_touches_work_tree_or_index(commit_case, capsys, monkeypatch):
    case = commit_case
    repo = case["repo"]
    # Exercise both D9 expected-old forms: first commit and an existing ref.
    git(repo, "update-ref", "-d", CALIBRATION_REF)
    case["parent"] = git(repo, "rev-parse", "HEAD")
    state = _observe_commit_git(case, monkeypatch)
    for first in (True, False):
        previous = case["parent"]
        status = git(repo, "status", "--porcelain")
        index_digest = hashlib.sha256((repo / ".git/index").read_bytes()).digest()
        work_tree = {path.relative_to(repo).as_posix(): path.read_bytes()
                     for path in repo.rglob("*") if path.is_file() and ".git" not in path.relative_to(repo).parts}
        start = len(state["calls"])
        result = _run_commit(case, capsys)
        assert git(repo, "status", "--porcelain") == status, "commit-data must preserve staged, unstaged and untracked status"
        assert hashlib.sha256((repo / ".git/index").read_bytes()).digest() == index_digest, "commit-data must leave the real index byte-identical"
        assert {path.relative_to(repo).as_posix(): path.read_bytes()
                for path in repo.rglob("*") if path.is_file() and ".git" not in path.relative_to(repo).parts} == work_tree, "commit-data must not alter any work-tree file"
        created = state["created"]
        assert (result.returncode, result.stdout.splitlines()[-1:]) == (
            0, [f"COMMIT: OK sha={created} ref={CALIBRATION_REF}"],
        ), f"commit-data must publish a plumbing commit without checkout: stdout={result.stdout!r}; stderr={result.stderr!r}"
        assert re.fullmatch(r"[0-9a-f]{40}", created), "commit-tree must return a full commit oid"
        assert _read_calibration_ref(repo) == (0, created), "the confirmed ref must point at the new commit"
        assert git(repo, "rev-parse", f"{created}^") == previous, "the new commit must descend from --parent"
        assert git(repo, "show", "-s", "--format=%B", created) == case["message"], "commit-tree must preserve the hostile human message"
        for source in case["src"].rglob("*"):
            if source.is_file():
                relative = (CALIBRATION / source.relative_to(case["src"])).as_posix()
                assert git(repo, "rev-parse", f"{created}:{relative}") == git(repo, "hash-object", str(source)), f"the calibration blob must retain every byte of {source.name}"
                assert git(repo, "ls-tree", created, "--", relative).startswith("100644 blob "), "new data blobs must use mode 100644"
        changes = git(repo, "diff", "--name-only", previous, created).splitlines()
        assert changes and all(path.startswith(CALIBRATION.as_posix() + "/") for path in changes), "the commit must change only calibration paths"
        calls = state["calls"][start:]
        assert {"read-tree", "hash-object", "update-index", "write-tree", "commit-tree", "update-ref"} <= {argv[0] for argv, _env in calls}, "D9 must commit through the declared Git plumbing"
        for argv, environment in calls:
            if argv[0] in ("read-tree", "update-index", "write-tree"):
                assert environment and environment.get("GIT_INDEX_FILE"), "tree construction must use a temporary index"
                assert Path(environment["GIT_INDEX_FILE"]).resolve() != (repo / ".git/index").resolve(), "GIT_INDEX_FILE must not select the real index"
        updates = [argv for argv, _env in calls if argv[0] == "update-ref"]
        assert len(updates) == 1 and updates[0][-1] in (("", "0" * 40) if first else (previous,)), "update-ref must compare-and-swap against absence or the exact parent"
        assert state["rereads"] > 0, "success requires re-reading the ref after update-ref"
        case["parent"] = created
        # Make the second commit's data differ while keeping its human input hostile.
        (case["src"] / "s1/grok/p1.log").write_bytes(case["src"].joinpath("s1/grok/p1.log").read_bytes() + b"next cycle\n")


def test_commit_data_refuses_an_unknown_parent(commit_case, capsys, monkeypatch):
    case = commit_case
    git(case["repo"], "update-ref", "-d", CALIBRATION_REF)
    assert _read_calibration_ref(case["repo"])[0] != 0, "the unknown-parent fixture must start with no calibration ref"
    case["parent"] = "f" * 40
    _assert_commit_prewrite_refusal(case, capsys, monkeypatch, f"parent_unknown:{case['parent']}",
                                    "refuse an unknown parent before writing a ref")


def test_commit_data_refuses_a_moved_ref(commit_case, capsys, monkeypatch):
    case = commit_case
    current = case["parent"]
    case["parent"] = git(case["repo"], "rev-parse", "HEAD")
    assert case["parent"] != current, "the supplied parent must be valid but differ from the actual calibration ref"
    _assert_commit_prewrite_refusal(case, capsys, monkeypatch, f"ref_moved:{current}",
                                    "refuse an existing ref that differs from --parent")


def test_commit_data_refuses_outside_calibration_dir(commit_case, tmp_path, capsys, monkeypatch):
    case = commit_case
    outside = tmp_path / "outside [a]*.txt"
    content = case["src"].joinpath("s1/grok/p1.log").read_bytes()
    outside.write_bytes(content)
    escaped = case["src"] / "escape.txt"
    escaped.symlink_to(outside)
    _assert_commit_prewrite_refusal(case, capsys, monkeypatch, f"outside_calibration_dir:{escaped}",
                                    "refuse a source file resolving outside --src")
    assert outside.read_bytes() == content, "refusing an escaped input must preserve its outside bytes"


def test_commit_data_rereads_the_ref(commit_case, capsys, monkeypatch):
    case = commit_case
    state = _observe_commit_git(case, monkeypatch, false_reread=True)
    result = _run_commit(case, capsys)
    assert (result.returncode, result.stdout.splitlines()[-1:]) == (
        2, ["COMMIT: REFUSED reason=ref_unconfirmed"],
    ), f"a mismatched post-write ref read must refuse confirmation: stdout={result.stdout!r}; stderr={result.stderr!r}"
    assert state["updated"] and state["rereads"] > 0, "ref_unconfirmed must follow a successful update-ref and a new ref read"
    assert state["created"] and state["created"] != case["parent"], "the real commit-tree must have made a new commit"
    assert _read_calibration_ref(case["repo"]) == (0, state["created"]), "D9 does not roll back: real Git must see the commit-tree oid even after ref_unconfirmed"
    assert "Traceback" not in result.stderr, "a declared ref_unconfirmed refusal has no traceback"
