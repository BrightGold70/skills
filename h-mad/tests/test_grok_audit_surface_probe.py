"""Probe refusal tokens (Task 2) and ledger validation (Task 3)."""

import ast
from collections import Counter
import io
import json
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

from grokauditfixtures import (
    CALIBRATION, CALIBRATION_REF, build_archive, build_ledger, build_repo, git,
    load_probe,
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
