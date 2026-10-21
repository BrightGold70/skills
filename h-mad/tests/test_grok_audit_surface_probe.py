"""Probe tokens, ledger, roots, cycle recording and data commits (Tasks 2–6)."""

import ast
from collections import Counter
import hashlib
import inspect
import io
import json
import os
import re
import random
import shlex
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import uuid
from pathlib import Path
from fractions import Fraction

import pytest

from grokauditfixtures import (
    CALIBRATION, CALIBRATION_REF, EXCLUSIONS, build_archive, build_ledger,
    build_repo, build_root_repo, build_cycle_inputs, build_commit_inputs,
    build_extract_inputs, extract_report_path, extract_report_text,
    write_extract_cycle, commit_root_tree, git, load_probe,
    build_score_inputs, write_score_tables,
    build_rescore_inputs, commit_fixture_tree, _hostile_text, build_probe_parent_dirs,
    build_pass_cycle_inputs, seed_commit_parent, grok_tool_call,
)


def _rendered_effort_cycle(probe):
    """Produce the exact cycle renderer's Effort: block for parser consumers."""
    cycle = probe._cycle
    results = [cycle.PassResult(
        index=1,
        delivered="report-file",
        collected_path=Path("synthetic-report.md"),
        verdict="PASS",
        must=0,
        should=0,
        findings=[],
        effort={
            "shape": "grok", "tools": 3, "ok": 2,
            "unresolved": 1, "thinking": 4, "readable": True,
        },
        rc=0,
    )]
    return cycle, cycle.render(
        results, "PASS", None, feature="synthetic", size_status="verified", passes=1,
    )


def test_auditcycle_parser_reads_render_output():
    probe = load_probe(PROBE)
    cycle, rendered = _rendered_effort_cycle(probe)

    parsed = probe.parse_auditcycle(rendered)
    unverified = probe.parse_auditcycle(cycle.render(
        [], "UNVERIFIED", "halted", feature="synthetic", size_status="verified", passes=1,
    ))

    assert parsed is not None, "the one AUDITCYCLE line rendered by audit-cycle must parse"
    assert parsed["verdict"] == "PASS"
    assert parsed["delivered"] == "report-file"
    assert unverified is not None, "the UNVERIFIED renderer token must parse"
    assert unverified["verdict"] == "UNVERIFIED"
    assert unverified["reason"] == "halted"
    assert "delivered" not in unverified, "a halted cycle renders no delivered field"


def test_run_line_parser_reads_the_runbook_line():
    probe = load_probe(PROBE)
    text = subprocess.run(
        ["/usr/bin/printf", "RUN: checkout=%s home=%s\n", "/tmp/checkout", "/tmp/home"],
        capture_output=True, text=True, check=True,
    ).stdout
    assert probe.parse_run_line(text) == {"checkout": "/tmp/checkout", "home": "/tmp/home"}, (
        "the runbook's single RUN line must preserve both recorded paths"
    )


@pytest.mark.parametrize("text", [
    "RUN: checkout=/tmp/checkout\n",
    "RUN: checkout=/tmp/checkout checkout=/tmp/other home=/tmp/home\n",
    "RUN: checkout=/tmp/checkout home=/tmp/home\nRUN: checkout=/tmp/other home=/tmp/home2\n",
], ids=["missing-home", "repeated-key", "two-lines"])
def test_run_line_parser_rejects_a_malformed_run_line(text):
    probe = load_probe(PROBE)
    assert probe.parse_run_line(text) is None, "malformed or multiple RUN lines are not authoritative"


def test_profile_line_parser_reads_the_exec_line(tmp_path):
    probe = load_probe(PROBE)
    from test_grok_audit_surface_wrapper import _profile_case

    result, _capture, log_profile, _log, _calls = _profile_case(
        tmp_path, options=["--sandbox", "workspace", "--allow-weaker-sandbox"],
    )
    assert result.returncode == 0, f"exec grok must produce the profile record: {result.stderr}"
    assert log_profile.is_file(), "exec grok must write the profile record beside its log"
    assert probe.parse_profile_line(log_profile.read_text(encoding="utf-8")) == {
        "profile": "workspace", "origin": "override",
    }, "the exec-written profile line must preserve its profile and origin"


@pytest.mark.parametrize("text", [
    "GROK-PROFILE: profile=fixture\n",
    "GROK-PROFILE: profile=fixture origin=elsewhere\n",
    "GROK-PROFILE: origin=default\n",
    "GROK-PROFILE: profile=p origin=default extra=1\n",
], ids=["missing-origin", "origin-outside", "missing-profile", "extra-key"])
def test_profile_line_parser_rejects_a_malformed_profile_line(text):
    probe = load_probe(PROBE)
    assert probe.parse_profile_line(text) is None, "malformed or noncanonical profile records must refuse"


def _t26_ready_extract_case(tmp_path, monkeypatch):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    case = build_extract_inputs(tmp_path)
    case["probe"] = load_probe(PROBE)
    (case["s2"] / "run.txt").write_text(
        f"RUN: checkout={case['tree']} home={tmp_path / 'home'}\n", encoding="utf-8",
    )
    for doc in sorted((case["s2"]).glob("d*")):
        for cycle in sorted(doc.glob("v*")):
            line = (cycle / "root.txt").read_text(encoding="utf-8").strip()
            (cycle / "p1.root.txt").write_text(line + "\n", encoding="utf-8")
            (cycle / "p2.root.txt").write_text(
                line.replace("-synthetic", "-synthetic-p2") + "\n", encoding="utf-8",
            )
    return case


def _t26_extract(case, capsys, *, out=None):
    argv = ["extract", "--tree", str(case["tree"]), "--s2", str(case["s2"]),
            "--shuffle-seed", "1729", "--out", str(out or case["out"]), "--sources",
            ",".join(f"{feature}={directory}" for feature, directory in case["sources"].items())]
    capsys.readouterr()
    rc = case["probe"].main(argv)
    stdout, stderr = capsys.readouterr()
    return subprocess.CompletedProcess(argv, rc, stdout, stderr)


def _t26_refuses(probe, case, reason, capsys):
    result = _t26_extract(case, capsys)
    expected = f"FINDINGS: UNREADABLE reason={reason}"
    assert (result.returncode, result.stdout.splitlines()[-1:]) == (2, [expected]), (
        f"extract must refuse with {reason!r}: stdout={result.stdout!r}; stderr={result.stderr!r}"
    )
    assert "Traceback" not in result.stderr, "declared extraction refusals must not print a traceback"


def _t26_change_root_path(line, path):
    return re.sub(r"path=\S+", f"path={path}", line)


def _t26_three_passes(cycle):
    command = (cycle / "command.txt").read_text(encoding="utf-8")
    command = command.replace("--passes 2", "--passes 3").replace(
        "--surfaces agy,grok", "--surfaces codex,agy,grok",
    )
    (cycle / "command.txt").write_text(command, encoding="utf-8")
    audit = cycle / "auditcycle.txt"
    text = audit.read_text(encoding="utf-8")
    text = text.replace("passes=2 delivered=report-file,none",
                        "passes=3 delivered=report-file,none,none")
    audit.write_text(text, encoding="utf-8")
    first = (cycle / "p1.root.txt").read_text(encoding="utf-8").strip()
    for index in (1, 2, 3):
        (cycle / f"p{index}.root.txt").write_text(
            _t26_change_root_path(first, f"/tmp/gas-root-d1-s2v1-count-{index}") + "\n",
            encoding="utf-8",
        )


def test_cycle_token_more_root_records_than_passes(tmp_path, monkeypatch, capsys):
    probe = load_probe(PROBE)
    case = _t26_ready_extract_case(tmp_path, monkeypatch)
    cycle = case["s2"] / "d1/v1"
    _t26_three_passes(cycle)
    root = (cycle / "p1.root.txt").read_text(encoding="utf-8").strip()
    (cycle / "p4.root.txt").write_text(
        _t26_change_root_path(root, "/tmp/gas-root-d1-s2v1-count-4") + "\n", encoding="utf-8",
    )
    _t26_refuses(probe, case, "cycle_token:d1.v1", capsys)


def test_cycle_token_two_passes_same_root(tmp_path, monkeypatch, capsys):
    probe = load_probe(PROBE)
    case = _t26_ready_extract_case(tmp_path, monkeypatch)
    cycle = case["s2"] / "d1/v1"
    (cycle / "p2.root.txt").write_text(
        (cycle / "p1.root.txt").read_text(encoding="utf-8"), encoding="utf-8",
    )
    _t26_refuses(probe, case, "cycle_token:d1.v1", capsys)


def test_cycle_token_root_inside_another(tmp_path, monkeypatch, capsys):
    probe = load_probe(PROBE)
    case = _t26_ready_extract_case(tmp_path, monkeypatch)
    cycle = case["s2"] / "d1/v1"
    root = (cycle / "p2.root.txt").read_text(encoding="utf-8")
    (cycle / "p2.root.txt").write_text(root.replace(
        "/tmp/gas-root-d1-s2v1-synthetic-p2", "/tmp/gas-root-d1-s2v1-synthetic/nested",
    ), encoding="utf-8")
    _t26_refuses(probe, case, "cycle_token:d1.v1", capsys)


def test_cycle_token_roots_differ_in_calibration(tmp_path, monkeypatch, capsys):
    probe = load_probe(PROBE)
    case = _t26_ready_extract_case(tmp_path, monkeypatch)
    cycle = case["s2"] / "d1/v1"
    path = cycle / "p2.root.txt"
    path.write_text(path.read_text(encoding="utf-8").replace("a" * 40, "d" * 40), encoding="utf-8")
    _t26_refuses(probe, case, "cycle_token:d1.v1", capsys)


def test_cycle_token_roots_differ_in_list_blob(tmp_path, monkeypatch, capsys):
    probe = load_probe(PROBE)
    case = _t26_ready_extract_case(tmp_path, monkeypatch)
    cycle = case["s2"] / "d1/v1"
    path = cycle / "p2.root.txt"
    path.write_text(path.read_text(encoding="utf-8").replace("c" * 40, "e" * 40), encoding="utf-8")
    _t26_refuses(probe, case, "cycle_token:d1.v1", capsys)


def test_cycle_with_one_identical_root_per_pass_does_not_refuse(tmp_path, monkeypatch, capsys):
    probe = load_probe(PROBE)
    case = _t26_ready_extract_case(tmp_path, monkeypatch)
    result = _t26_extract(case, capsys)
    assert result.returncode == 0 and result.stdout.splitlines()[-1].startswith("FINDINGS: WRITTEN "), (
        f"one valid recorded root per pass must allow extraction: {result.stdout!r}; {result.stderr!r}"
    )


def test_list_changed_run_record_absent(tmp_path, monkeypatch, capsys):
    probe = load_probe(PROBE)
    case = _t26_ready_extract_case(tmp_path, monkeypatch)
    (case["s2"] / "run.txt").unlink()
    _t26_refuses(probe, case, "list_changed:unrecorded", capsys)


@pytest.mark.parametrize("bad", [
    "no RUN line\n",
    "RUN: checkout=/tmp/checkout home=/tmp/home\nRUN: checkout=/tmp/other home=/tmp/home2\n",
    "RUN: checkout=/tmp/checkout\n",
    "RUN: checkout=/tmp/checkout home=/tmp/home extra=value\n",
], ids=["no-run-line", "two-run-lines", "missing-home", "extra-key"])
def test_list_changed_run_record_malformed(tmp_path, monkeypatch, bad, capsys):
    probe = load_probe(PROBE)
    case = _t26_ready_extract_case(tmp_path, monkeypatch)
    (case["s2"] / "run.txt").write_text(bad, encoding="utf-8")
    _t26_refuses(probe, case, "list_changed:unrecorded", capsys)


def test_containment_pass_root_record_absent(tmp_path, monkeypatch, capsys):
    probe = load_probe(PROBE)
    case = _t26_ready_extract_case(tmp_path, monkeypatch)
    (case["s2"] / "d1/v1/p1.root.txt").unlink()
    _t26_refuses(probe, case, "list_changed:unrecorded", capsys)


def test_containment_no_ready_line(tmp_path, monkeypatch, capsys):
    probe = load_probe(PROBE)
    case = _t26_ready_extract_case(tmp_path, monkeypatch)
    (case["s2"] / "d1/v1/p1.root.txt").write_text("not a ready line\n", encoding="utf-8")
    _t26_refuses(probe, case, "list_changed:unrecorded", capsys)


def test_containment_two_ready_lines(tmp_path, monkeypatch, capsys):
    probe = load_probe(PROBE)
    case = _t26_ready_extract_case(tmp_path, monkeypatch)
    path = case["s2"] / "d1/v1/p1.root.txt"
    valid = path.read_text(encoding="utf-8")
    path.write_text(valid + valid, encoding="utf-8")
    _t26_refuses(probe, case, "list_changed:unrecorded", capsys)


def test_containment_ready_line_without_list_blob(tmp_path, monkeypatch, capsys):
    probe = load_probe(PROBE)
    case = _t26_ready_extract_case(tmp_path, monkeypatch)
    path = case["s2"] / "d1/v1/p1.root.txt"
    valid = path.read_text(encoding="utf-8")
    path.write_text(re.sub(r" list_blob=\S+", "", valid), encoding="utf-8")
    _t26_refuses(probe, case, "list_changed:unrecorded", capsys)


def _t26_root_line(doc, purpose, path, *, calibration="a", commit="b", blob="c"):
    return (f"ROOT: READY doc={doc} purpose={purpose} path={path} "
            f"calibration={calibration * 40} list_commit={commit * 40} "
            f"list_blob={blob * 40} absent=0\n")


def _t26_list_case(tmp_path, monkeypatch):
    probe = load_probe(PROBE)
    monkeypatch.setattr(probe, "read_exclusions", lambda _repo, _commit: ([], "head", "f" * 40))
    export = tmp_path / "export"
    data = export / CALIBRATION
    (data / "s1/grok").mkdir(parents=True)
    (data / "resmoke/grok").mkdir(parents=True)
    (data / "s2/d1/v1").mkdir(parents=True)
    (data / "s1/grok/root.txt").write_text(
        _t26_root_line("d1", "s1", "/tmp/gas-root-d1-s1", blob="f"), encoding="utf-8",
    )
    (data / "resmoke/grok/root.txt").write_text(
        _t26_root_line("d1", "resmoke", "/tmp/gas-root-d1-resmoke", blob="f"),
        encoding="utf-8",
    )
    cycle = data / "s2/d1/v1"
    (cycle / "root.txt").write_text(
        _t26_root_line("d1", "s2v1", "/tmp/ignored-s2-root", blob="e"), encoding="utf-8",
    )
    (cycle / "command.txt").write_text(
        "hmad-dispatch audit-cycle --passes 2 --surfaces agy,grok\n", encoding="utf-8",
    )
    (cycle / "p1.root.txt").write_text(
        _t26_root_line("d1", "s2v1", "/tmp/gas-root-d1-p1", blob="f"), encoding="utf-8",
    )
    (cycle / "p2.root.txt").write_text(
        _t26_root_line("d1", "s2v1", "/tmp/gas-root-d1-p2", blob="f"), encoding="utf-8",
    )
    return probe, export, cycle


def test_list_changed_one_pass_root_record_absent(tmp_path, monkeypatch):
    probe, export, cycle = _t26_list_case(tmp_path, monkeypatch)
    (cycle / "p2.root.txt").unlink()
    with pytest.raises(probe.Refusal) as caught:
        probe.list_check(export, tmp_path)
    assert caught.value.reason == "list_changed:unrecorded"


def test_list_changed_pass_records_without_surfaces(tmp_path, monkeypatch):
    probe, export, cycle = _t26_list_case(tmp_path, monkeypatch)
    (cycle / "command.txt").write_text("hmad-dispatch audit-cycle --passes 2\n", encoding="utf-8")
    with pytest.raises(probe.Refusal) as caught:
        probe.list_check(export, tmp_path)
    assert caught.value.reason == "list_changed:unrecorded"


def test_list_check_reads_resmoke_records(tmp_path, monkeypatch):
    probe, export, _cycle = _t26_list_case(tmp_path, monkeypatch)
    line = probe.list_check(export, tmp_path)
    assert line == "LIST: recorded=" + ",".join(["f" * 40] * 4) + " current=" + "f" * 40, (
        "list checking must use s1, resmoke, then each S2 pass record in record order"
    )


def test_list_changed_unrecorded_s1_or_resmoke_root_record(tmp_path, monkeypatch):
    for kind in ("s1", "resmoke"):
        probe, export, _cycle = _t26_list_case(tmp_path / kind, monkeypatch)
        assert probe.list_check(export, tmp_path).startswith("LIST: "), "control: every record valid must pass"
        (export / CALIBRATION / kind / "grok/root.txt").unlink()
        with pytest.raises(probe.Refusal) as caught:
            probe.list_check(export, tmp_path)
        assert caught.value.reason == "list_changed:unrecorded", (
            f"a {kind} cycle without its root.txt must refuse even when every S2 pass record is valid"
        )


def test_list_changed_malformed_s1_or_resmoke_root_record(tmp_path, monkeypatch):
    for kind in ("s1", "resmoke"):
        probe, export, _cycle = _t26_list_case(tmp_path / kind, monkeypatch)
        assert probe.list_check(export, tmp_path).startswith("LIST: "), "control: every record valid must pass"
        path = export / CALIBRATION / kind / "grok/root.txt"
        malformed = re.sub(r" list_blob=\S+", "", path.read_text(encoding="utf-8"))
        assert malformed.startswith("ROOT: READY ") and probe.parse_root_line(malformed.strip()) is None
        path.write_text(malformed, encoding="utf-8")
        with pytest.raises(probe.Refusal) as caught:
            probe.list_check(export, tmp_path)
        assert caught.value.reason == "list_changed:unrecorded", (
            f"a malformed {kind} READY record must refuse even when every S2 pass record is valid"
        )


def _t26_score_argv(case, *, run_id=None):
    argv = ["score", "--tree", str(case["tree"]), "--sources", ",".join(
        f"{feature}={directory}" for feature, directory in case["sources"].items()
    )]
    if run_id is not None:
        argv += ["--run-id", run_id]
    return argv


def test_score_reads_the_reading_named_by_run_id(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    probe = load_probe(PROBE)
    case = build_score_inputs(tmp_path, probe)
    base = case["tree"] / CALIBRATION
    import shutil
    for run_id in ("run-a", "run-b"):
        reading = base / "runs" / run_id
        reading.mkdir(parents=True)
        for name in ("s2", "findings.jsonl", "key.jsonl", "labels.jsonl", "extract.txt"):
            source = base / name
            destination = reading / name
            if source.is_dir():
                shutil.copytree(source, destination)
            elif source.exists():
                shutil.copy2(source, destination)
        (reading / "s2/run.txt").write_text(
            f"RUN: checkout={case['tree']} home={tmp_path / run_id}\n", encoding="utf-8",
        )
    labels = base / "runs/run-b/labels.jsonl"
    rows = [json.loads(line) for line in labels.read_text(encoding="utf-8").splitlines()]
    for row in rows:
        row["label"] = "REAL" if row["label"] != "REAL" else "FABRICATED"
    labels.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    # Put the reading at the flat calibration location so the no-run-id path
    # derives an independent expected token from exactly run-b's payload.
    expected_case = build_score_inputs(tmp_path / "run-b-flat-tree", probe)
    expected_flat = expected_case["tree"] / CALIBRATION
    for name in ("s2", "findings.jsonl", "key.jsonl", "labels.jsonl", "extract.txt"):
        source, destination = base / "runs/run-b" / name, expected_flat / name
        if destination.is_dir():
            shutil.rmtree(destination)
        elif destination.exists():
            destination.unlink()
        if source.is_dir():
            shutil.copytree(source, destination)
        elif source.exists():
            shutil.copy2(source, destination)
    outputs = []
    for run_id in ("run-a", "run-b"):
        rc = probe.main(_t26_score_argv(case, run_id=run_id))
        out, err = capsys.readouterr()
        assert rc == 0 and out.splitlines()[-1].startswith("SEEDSCORE: "), (
            f"score must read {run_id!r}: stdout={out!r}; stderr={err!r}"
        )
        outputs.append(out.splitlines()[-1])
    expected_rc = probe.main(_t26_score_argv(expected_case))
    expected_out, expected_err = capsys.readouterr()
    assert expected_rc == 0, f"flat run-b expectation must score: {expected_out!r}; {expected_err!r}"
    assert outputs[1] == expected_out.splitlines()[-1], (
        "--run-id=run-b must match the independently scored flat copy of run-b's data"
    )
    assert outputs[0] != outputs[1], "run-id must select the named reading's labels and findings"


def test_score_without_run_id_on_a_namespaced_reading_refuses(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    probe = load_probe(PROBE)
    case = build_score_inputs(tmp_path, probe)
    base = case["tree"] / CALIBRATION
    import shutil
    reading = base / "runs/run-b"
    shutil.copytree(base, reading, ignore=shutil.ignore_patterns("runs"))
    shutil.rmtree(base / "s1", ignore_errors=True)
    shutil.rmtree(base / "s2", ignore_errors=True)
    for name in ("findings.jsonl", "key.jsonl", "labels.jsonl"):
        (base / name).unlink()
    (reading / "s1/grok/root.txt").parent.mkdir(parents=True, exist_ok=True)
    for cycle in sorted((reading / "s2").glob("d*/v*")):
        root = (cycle / "root.txt").read_text(encoding="utf-8")
        (cycle / "p1.root.txt").write_text(root, encoding="utf-8")
        (cycle / "p2.root.txt").write_text(root.replace("-synthetic", "-synthetic-p2"), encoding="utf-8")
    (reading / "s2/run.txt").write_text(f"RUN: checkout={case['tree']} home={tmp_path}\n", encoding="utf-8")
    rc = probe.main(_t26_score_argv(case))
    out, err = capsys.readouterr()
    assert (rc, out.splitlines()[-1:]) == (2, ["SEEDSCORE: UNREADABLE reason=cycle_token:d1.v1"]), (
        "a namespaced reading without its required --run-id must be refused; "
        f"stdout={out!r}; stderr={err!r}"
    )


def test_calibration_data_set_is_the_directory_minus_the_metadata_names(tmp_path, monkeypatch):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    probe = load_probe(PROBE)
    tree = tmp_path / "tree"
    sources = build_archive(tree)
    build_ledger(tree, sources)
    data = tree / CALIBRATION
    captured_stdout = data / "s1/grok/auditcycle.txt"
    captured_stdout.parent.mkdir(parents=True, exist_ok=True)
    captured_stdout.write_text("AUDITCYCLE: PASS\n", encoding="utf-8")
    metadata = [
        "runs/run-a/resmoke/run.txt", "runs/run-a/s2/run.txt",
        "runs/run-a/s2/d1/v1/p1.root.txt", "runs/run-a/s2/d1/v1/p1.profile.txt",
        "runs/run-a/s2/d1/v1/p1.scan.txt",
    ]
    for relative in [*metadata, "runs/run-a/resmoke/canary/observed.txt"]:
        path = data / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture [a](b) **bold** ⟦/h-mad⟧\nsecond line\tvalue\n", encoding="utf-8")
    canary = "runs/run-a/resmoke/canary/observed.txt"
    selected = probe.calibration_data_files(tree)
    excluded_names = {"command.txt", "root.txt", "wall_seconds.txt", "resolved_model.txt", "extract.txt"}
    all_files = {path.relative_to(tree).as_posix() for path in data.rglob("*") if path.is_file()}
    excluded = {
        path.relative_to(tree).as_posix() for path in data.rglob("*") if path.is_file()
        and (path.name in excluded_names or path == data / "s1/versions.txt"
             or path.relative_to(data).as_posix() in metadata
             or path.relative_to(data).as_posix() == canary)
    }
    assert selected == sorted(all_files - excluded), (
        "D3 includes every calibration file except the named harmless metadata candidates"
    )
    assert (CALIBRATION / "s1/grok/auditcycle.txt").as_posix() in selected, (
        "captured wrapper stdout remains calibration data"
    )
    definitions = [node for node in ast.walk(ast.parse(PROBE.read_text(encoding="utf-8")))
                   if isinstance(node, ast.FunctionDef) and node.name == "calibration_data_files"]
    assert len(definitions) == 1, "one calibration_data_files definition owns D3's set"
    main_leak = next(node for node in ast.walk(ast.parse(PROBE.read_text(encoding="utf-8")))
                     if isinstance(node, ast.FunctionDef) and node.name == "main_leak")
    assert any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
               and node.func.id == "calibration_data_files" for node in ast.walk(main_leak)), (
        "main_leak must call the sole D3 set definition"
    )
    assert {f"{CALIBRATION.as_posix()}/{name}" for name in excluded}.isdisjoint(selected), (
        "D3 metadata names must be excluded unless they carry a seeded, expected or finding span"
    )


def test_hint_resolves_a_pass_2_absolute_quote_through_its_pass_record(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    probe = load_probe(PROBE)
    case = _t26_ready_extract_case(tmp_path, monkeypatch)
    cycle = case["s2"] / "d1/v1"
    root_line = (cycle / "root.txt").read_text(encoding="utf-8").strip()
    live_root = tmp_path / "pass-two-root"
    live_root.mkdir()
    quote_file = live_root / "docs/01-plan/features/paper-lantern.plan.md"
    quote_file.parent.mkdir(parents=True)
    seeded_line = case["records"][0]["seeded"].rstrip("\n")
    quote_file.write_text(seeded_line + "\n", encoding="utf-8")
    for index in (1, 2, 3):
        value = root_line.replace("/tmp/gas-root-d1-s2v1-synthetic", str(live_root))
        if index != 2:
            value = value.replace(str(live_root), str(tmp_path / f"pass-{index}-root"))
        (cycle / f"p{index}.root.txt").write_text(value + "\n", encoding="utf-8")
    (cycle / "command.txt").write_text(
        "hmad-dispatch audit-cycle --passes 3 --surfaces codex,agy,grok\n", encoding="utf-8",
    )
    (cycle / "p3.log").write_text(json.dumps({"type": "text", "data": "clean"}) + "\n",
                                   encoding="utf-8")
    auditcycle = cycle / "auditcycle.txt"
    auditcycle.write_text(auditcycle.read_text(encoding="utf-8").replace(
        "passes=2 delivered=report-file,none",
        "passes=3 delivered=none,report-file,none",
    ), encoding="utf-8")
    report = extract_report_path(case, "d1", 1, 2)
    quote = f"quote: {live_root}/docs/01-plan/features/paper-lantern.plan.md › `{seeded_line}`"
    report.write_text(
        "# Synthetic audit\n\n## Must-fix\n- candidate quote\n  " + quote
        + "\n\n## Should-fix\nNone\n", encoding="utf-8",
    )
    (cycle / "root.txt").unlink()
    import shutil
    shutil.rmtree(live_root)
    argv = ["extract", "--tree", str(case["tree"]), "--s2", str(case["s2"]),
            "--shuffle-seed", "1729", "--out", str(tmp_path / "with-hints"),
            "--sources", ",".join(f"{feature}={directory}" for feature, directory in case["sources"].items())]
    assert probe.main(argv) == 0
    with_hints = capsys.readouterr().out.splitlines()
    hint_lines = [line for line in with_hints if line.startswith("HINT:")]
    assert len(hint_lines) == 1 and f"candidate-hit:{case['records'][0]['id']}" in hint_lines[0], (
        "a pass-2 quote must resolve through p2.root.txt after its live root is removed"
    )
    report.write_text(
        "# Synthetic audit\n\n## Must-fix\n- candidate quote\n\n## Should-fix\nNone\n",
        encoding="utf-8",
    )
    argv[argv.index("--out") + 1] = str(tmp_path / "without-hints")
    assert probe.main(argv) == 0
    without_hints = capsys.readouterr().out.splitlines()
    assert with_hints[-1] == without_hints[-1], "advisory quote hints must never move the extraction token"


def test_auditcycle_parser_rejects_two_lines():
    probe = load_probe(PROBE)
    _cycle, rendered = _rendered_effort_cycle(probe)

    parsed = probe.parse_auditcycle(rendered + "AUDITCYCLE: FAIL\n")

    assert parsed is None, "two AUDITCYCLE lines are not one authoritative cycle token"


def test_effort_parser_reads_effort_items_output():
    probe = load_probe(PROBE)
    cycle, rendered = _rendered_effort_cycle(probe)
    expected = cycle._effort_items([cycle.PassResult(
        index=1,
        delivered="report-file",
        collected_path=Path("synthetic-report.md"),
        verdict="PASS",
        must=0,
        should=0,
        findings=[],
        effort={
            "shape": "grok", "tools": 3, "ok": 2,
            "unresolved": 1, "thinking": 4, "readable": True,
        },
        rc=0,
    )])

    parsed = probe.parse_effort_items(rendered)

    assert expected, "the renderer fixture must contain at least one Effort item"
    assert parsed == expected, "the parser must preserve every renderer-written Effort item"


def test_effort_parser_rejects_a_malformed_effort_block():
    probe = load_probe(PROBE)
    malformed_item = (
        "AUDITCYCLE: FAIL\nEffort:\n"
        "- x1 tools=1 ok=1 failed=0 thinking=0\nPremise checklist: empty\n"
    )
    empty_block = "AUDITCYCLE: FAIL\nEffort:\n[H-MAD] synthetic audit-cycle FAIL\n"
    twice = (
        "AUDITCYCLE: FAIL\nEffort:\n"
        "- p1 tools=1 ok=1 failed=0 thinking=0\nPremise checklist: empty\n"
        "Effort:\n- p2 tools=1 ok=1 failed=0 thinking=0\n"
    )
    halted = probe._cycle.render(
        [], "UNVERIFIED", "halted", feature="synthetic", size_status="verified", passes=1,
    )

    assert probe.parse_effort_items(malformed_item) is None, (
        "an Effort item must begin with p followed by digits and a space"
    )
    assert probe.parse_effort_items(empty_block) is None, (
        "an opened Effort block must contain an item"
    )
    assert probe.parse_effort_items(twice) is None, "only one Effort block is permitted"
    assert probe.parse_effort_items(halted) == [], (
        "a rendered halted cycle has no Effort block and is not malformed"
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
    parents = build_probe_parent_dirs(root)
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
            "--smoke-sha", sha, "--score-sha", sha, "--run-id", "fixture-run",
        ],
        "main-leak": [
            "--repo", str(root), "--calibration-sha", sha, "--smoke-sha", sha,
        ],
    }
    argv = [mode, *arguments[mode]]
    if mode in ("build-root", "main-leak", "rescore"):
        argv += ["--work-dir", str(parents["work_dir"])]
    if mode == "build-root":
        argv += ["--dest-parent", str(parents["roots"])]
    return argv


def _expected_refusal(mode: str, exception: str, root: Path) -> str:
    reason = (
        f"input_unparseable:{root / 's1'}"
        if mode == "smoke" else f"internal:{exception}"
    )
    return f"{REFUSALS[mode]} reason={reason}"


@pytest.mark.parametrize("mode", MODES, ids=MODES)
def test_internal_failure_prints_the_mode_token(mode, tmp_path, monkeypatch, capsys, parent_layout):
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
    environment = os.environ.copy()
    if repo is not None:
        parents = build_probe_parent_dirs(repo.parent)
        arguments += ["--work-dir", str(parents["work_dir"])]
        environment["TMPDIR"] = str(parents["systemp"])
    return subprocess.run(
        [sys.executable, str(PROBE), "check-ledger", *arguments, "--sources",
         ",".join(f"{feature}={directory}" for feature, directory in sources.items())],
        cwd=repo, capture_output=True, text=True, timeout=15, env=environment,
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
def root_case(tmp_path, monkeypatch, parent_layout):
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
        "--work-dir", str(case["work_dir"]),
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
    result = _run_root(root_case, capsys)
    fields = _ready_fields(result, "parse_root_line must consume a real build-root success token")
    root = Path(fields["path"])
    try:
        assert root.parent.resolve() == root_case["dest"].resolve(), "allocation must use --dest-parent"
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
    assert Path(_ready_fields(result, "parser fixture must use its requested parent")["path"]).parent == root_case["dest"].resolve()
    line = result.stdout.splitlines()[-1]
    for field in ("list_blob", "doc", "purpose", "path", "calibration", "list_commit", "absent"):
        malformed = " ".join(word for word in line.split() if not word.startswith(field + "="))
        assert parser(malformed) is None, f"ROOT parser must reject a success token missing {field}"
    assert parser("ROOT: UNREADABLE reason=leak:x") is None, "ROOT parser must not accept a refusal token as a ready root"


def _fresh_reset_build(case, capsys, *, doc="d1"):
    extra = ("--list-commit", case["reset_fields"]["list_commit"]) if "reset_fields" in case else ()
    extra += ("--dest-parent", str(case["roots"]))
    result = _run_root(case, capsys, dest=False, doc=doc, purpose="s1",
                       sha=case.get("sha"), extra=extra)
    fields = _ready_fields(result, "reset fixture must start with a valid S1 build")
    root = Path(fields["path"])
    case["reset_roots"].append(root)
    assert root.parent.resolve() == case["roots"].resolve(), result.stderr
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
    target = reset_case["roots"] / f"gas-root-d1-s1-absent-{uuid.uuid4().hex}"
    assert not target.exists(), "missing-target fixture must start absent"
    result = _run_reset(reset_case, capsys, target=target)

    assert (result.returncode, result.stdout.splitlines()[-1:]) == (
        2, ["ROOT: UNREADABLE reason=internal:ResetTargetNotDirectory"],
    ), result.stderr
    assert not target.exists(), "refusing a missing reset target must leave it absent"
    n = result.stderr.count("Traceback")
    assert n == 0, "a declared missing-target refusal must not print a traceback"


def test_build_root_reset_refuses_a_target_in_system_temp(task24_case, capsys):
    case = task24_case
    target = case["systemp"] / "roots" / "gas-root-d1-s1-x"
    target.mkdir(parents=True)
    sentinel, content = _reset_sentinel(target)
    argv = _task24_argv(case, "build-root", dest=False) + ["--reset", str(target)]
    result = _task24_run(case, argv, capsys)

    assert (result.returncode, result.stdout.splitlines()[-1:]) == (
        2, ["ROOT: UNREADABLE reason=internal:ResetTargetInSystemTemp"],
    ), f"reset must refuse a resolved target anywhere inside system temp: {result.stdout!r}; {result.stderr}"
    assert sentinel.read_bytes() == content, "a system-temp reset target must retain its sentinel bytes"
    n = result.stderr.count("Traceback")
    assert n == 0, "a declared system-temp reset refusal must not print a traceback"


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


# Task 25: ordered pass roots, pass-local reports/profiles, and add-only data.
@pytest.fixture
def pass_cycle_case(cycle_case):
    return build_pass_cycle_inputs(cycle_case)


def _run_pass_record(case, capsys, *, single=False, passes=True):
    arguments = ["record-cycle"]
    for key in ("stem", "root", "stdout", "command", "dest"):
        arguments += ["--" + key.replace("_", "-"), str(case[key])]
    if single:
        arguments += ["--root-record", str(case["root_record"])]
    if passes:
        for record in case["pass_root_records"]:
            arguments += ["--pass-root-record", str(record)]
    capsys.readouterr()
    rc = case["probe"].main(arguments)
    out, err = capsys.readouterr()
    return subprocess.CompletedProcess(arguments, rc, out, err)


def test_record_cycle_writes_one_root_record_per_pass(pass_cycle_case, capsys):
    case = pass_cycle_case
    files = _assert_record_ok(case, _run_pass_record(case, capsys),
                              "write all three ordered per-pass root records")
    assert "root.txt" not in files, "per-pass records must not also write root.txt"
    assert {name for name in files if name.endswith(".root.txt")} == {
        "p1.root.txt", "p2.root.txt", "p3.root.txt",
    }, "each pass must have exactly its own numbered root record"
    for index, line in enumerate(case["pass_ready_lines"], 1):
        assert files[f"p{index}.root.txt"] == (line + "\n").encode(), (
            f"pass {index} must preserve only its own READY line in argument order"
        )


def test_record_cycle_copies_the_report_from_its_pass_root(pass_cycle_case, capsys):
    case = pass_cycle_case
    # The legacy form must prefer --root/.hmad-report as well.
    files = _assert_record_ok(case, _run_pass_record(case, capsys, single=True, passes=False),
                              "prefer a root-local report over the conflicting stem copy")
    assert files["p1.report.md"] == case["pass_reports"]["p1.report.md"], (
        "p1.report.md must come from --root/.hmad-report, preserving hostile binary bytes"
    )
    assert files["p2.report.md"] == (
        case["root"] / ".hmad-report" / f"{case['prefix']}_p2.report.md"
    ).read_bytes(), "the single-record form must resolve every pass report against --root"
    assert files["p3.report.md"] == (
        case["stem"] / f"{case['prefix']}_p3.report.md"
    ).read_bytes(), (
        "a missing root-local report must fall back to the stem directory"
    )
    case["dest"] = case["dest"].parent / "per-pass reports [a]* ⟦h-mad⟧"
    files = _assert_record_ok(case, _run_pass_record(case, capsys),
                              "resolve every report against that pass's recorded path")
    for name, content in case["pass_reports"].items():
        assert files[name] == content, f"{name} must use its own pass root or the stem fallback"


def test_record_cycle_copies_the_profile_record(cycle_case, capsys):
    case, expected = cycle_case, {}
    for index in (1, 2):
        content = f"profile pass={index}\n{_hostile_text()}".encode() + b"\r\n\x00\xff"
        (case["stem"] / f"{case['prefix']}_p{index}.log.profile").write_bytes(content)
        expected[f"p{index}.profile.txt"] = content
    (case["stem"] / "audit_copper-kite_plan_cycle2_run20990101T010203Z-314_p1.log.profile").write_bytes(b"decoy")
    files = _assert_record_ok(case, _run_record(case, capsys), "collect each pass's .log.profile")
    assert {name: content for name, content in files.items() if name.endswith(".profile.txt")} == expected, (
        "the selected stem's pN.log.profile files must map byte-for-byte to pN.profile.txt"
    )


@pytest.mark.parametrize("form", ["both", "neither"], ids=["both", "neither"])
def test_record_cycle_refuses_both_root_record_forms(form, pass_cycle_case, capsys):
    case = pass_cycle_case
    result = _run_pass_record(case, capsys, single=form == "both", passes=form == "both")
    _assert_record_refusal(case, result, "internal:UsageError",
                           f"exactly one root-record form is required ({form})")


def test_record_cycle_refuses_a_first_pass_record_for_another_root(pass_cycle_case, capsys):
    case = pass_cycle_case
    wrong = case["pass_ready_lines"][0].replace(
        f"path={case['root']}", f"path={case['pass_roots'][1].resolve()}",
    )
    assert wrong != case["pass_ready_lines"][0], "the first record must actually name another root"
    assert case["probe"].parse_root_line(wrong) is not None, "a wrong path must remain a valid READY line"
    case["pass_root_records"][0].write_text(wrong + "\n", encoding="utf-8")
    _assert_record_refusal(case, _run_pass_record(case, capsys), "root_record:path_mismatch",
                           "the first pass record's path must equal resolved --root")


def test_record_cycle_refuses_a_malformed_second_pass_record(pass_cycle_case, capsys):
    case = pass_cycle_case
    malformed = " ".join(word for word in case["pass_ready_lines"][1].split()
                         if not word.startswith("list_blob="))
    assert case["probe"].parse_root_line(malformed) is None, "removing list_blob must invalidate pass 2"
    assert all(case["probe"].parse_root_line(case["pass_ready_lines"][i]) is not None for i in (0, 2)), (
        "pass 1 and pass 3 must remain valid so only the second record causes refusal"
    )
    case["pass_root_records"][1].write_text(malformed + "\n", encoding="utf-8")
    _assert_record_refusal(case, _run_pass_record(case, capsys), "root_record:no_line",
                           "D5 validation must reach the malformed second of three pass records")


def _assert_task25_commit_ok(case, result, property_name):
    rc, tip = _read_calibration_ref(case["repo"])
    assert rc == 0 and (result.returncode, result.stdout.splitlines()[-1:]) == (
        0, [f"COMMIT: OK sha={tip} ref={CALIBRATION_REF}"],
    ), f"{property_name}: stdout={result.stdout!r}; stderr={result.stderr!r}"
    return tip


def test_commit_data_refuses_a_replaced_blob(commit_case, capsys, monkeypatch):
    case = commit_case
    parent = seed_commit_parent(case)
    # A sorted earlier addition must not be staged before a later conflict is found.
    (case["src"] / "00-new.txt").write_text(_hostile_text(), encoding="utf-8")
    for source in sorted(case["src"].joinpath("s1/grok").iterdir()):
        source.write_bytes(source.read_bytes() + b"changed\n")
    replaced = (CALIBRATION / "s1/grok/command.txt").as_posix()
    state = _observe_commit_git(case, monkeypatch)
    result = _run_commit(case, capsys)
    assert (result.returncode, result.stdout.splitlines()[-1:]) == (
        2, [f"COMMIT: REFUSED reason=would_replace:{replaced}"],
    ), f"refuse the first replaced calibration blob in sorted source order: {result.stdout!r}; {result.stderr!r}"
    assert _read_calibration_ref(case["repo"]) == (0, parent), "replacement refusal must retain the parent ref"
    assert not any(argv[0] in ("update-index", "update-ref") for argv, _env in state["calls"]), (
        "all replacement checks must finish before any update-index, even for an earlier new file"
    )
    assert "Traceback" not in result.stderr, "would_replace must be a declared refusal"


def test_commit_data_accepts_an_identical_re_add(commit_case, capsys):
    case = commit_case
    parent = seed_commit_parent(case)
    tip = _assert_task25_commit_ok(case, _run_commit(case, capsys), "identical re-add must not refuse")
    assert git(case["repo"], "rev-parse", f"{tip}^{{tree}}") == git(case["repo"], "rev-parse", f"{parent}^{{tree}}"), (
        "identical source blobs must leave the complete parent tree unchanged"
    )


def test_commit_data_appends_a_second_reading_after_an_earlier_resmoke(commit_case, tmp_path, capsys):
    case = commit_case
    old_data = {"runs/run-a/resmoke/p1.log": _hostile_text().encode() + b"\r\n\x00\xff",
                "runs/run-a/resmoke/command.txt": f"Earlier reading: {_hostile_text()}\n".encode()}
    parent = seed_commit_parent(case, old_data)
    old_path = (CALIBRATION / "runs/run-a").as_posix()
    old_tree = git(case["repo"], "rev-parse", f"{parent}:{old_path}")
    case["src"] = tmp_path / "reading-b [a]* ⟦h-mad⟧"
    new_file = case["src"] / "runs/run-b/resmoke/p1.log"
    new_file.parent.mkdir(parents=True)
    new_file.write_bytes(f"Second reading: {_hostile_text()}\n".encode() + b"\x00\xff")
    tip = _assert_task25_commit_ok(case, _run_commit(case, capsys), "append run-b after run-a resmoke")
    assert git(case["repo"], "rev-parse", f"{tip}^") == parent, "the new reading must descend from --parent"
    assert git(case["repo"], "rev-parse", f"{tip}:{old_path}") == old_tree, "runs/run-a must remain byte-identical"
    destination = (CALIBRATION / new_file.relative_to(case["src"])).as_posix()
    assert git(case["repo"], "rev-parse", f"{tip}:{destination}") == git(case["repo"], "hash-object", str(new_file)), (
        "the second reading must retain its hostile binary bytes at runs/run-b/resmoke"
    )
    assert git(case["repo"], "diff", "--name-only", parent, tip).splitlines() == [destination], (
        "appending a reading must change only the new run's file"
    )
    stale = _run_commit(case, capsys)  # --parent still names the pre-append commit.
    assert (stale.returncode, stale.stdout.splitlines()[-1:]) == (
        2, [f"COMMIT: REFUSED reason=ref_moved:{tip}"],
    ), f"a stale --parent must name the actual tip in ref_moved: {stale.stdout!r}; {stale.stderr!r}"
    assert _read_calibration_ref(case["repo"]) == (0, tip), "a stale append must not move the calibration ref"
    assert "Traceback" not in stale.stderr, "ref_moved must be a declared refusal"


def test_commit_data_accepts_a_changed_authoring_file(commit_case, capsys):
    case = commit_case
    old = {"ledger.jsonl": b'{"reading":"old"}\n',
           "seeded/d1/plan.md": f"Old seed: {_hostile_text()}\n".encode()}
    parent = seed_commit_parent(case, old)
    changed = {"ledger.jsonl": (json.dumps({"reading": _hostile_text()}) + "\n").encode(),
               "seeded/d1/plan.md": f"Changed seed: {_hostile_text()}\n".encode()}
    for relative, content in changed.items():
        source = case["src"] / relative
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(content)
    tip = _assert_task25_commit_ok(case, _run_commit(case, capsys),
                                  "changed ledger.jsonl and seeded/ authoring files must be exempt")
    assert git(case["repo"], "rev-parse", f"{tip}^") == parent, "authoring changes must retain the supplied parent"
    for relative in changed:
        destination = (CALIBRATION / relative).as_posix()
        blob = git(case["repo"], "rev-parse", f"{tip}:{destination}")
        assert blob == git(case["repo"], "hash-object", str(case["src"] / relative)), (
            f"the changed authoring file must actually be committed: {relative}"
        )
        assert blob != git(case["repo"], "rev-parse", f"{parent}:{destination}"), (
            f"the authoring fixture must replace different parent bytes: {relative}"
        )


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
        # Add a new path for the second commit while keeping its human input hostile.
        (case["src"] / "s1/grok/p2.log").write_bytes(case["src"].joinpath("s1/grok/p1.log").read_bytes() + b"next cycle\n")


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


@pytest.fixture
def extract_case(tmp_path, monkeypatch):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    case = build_extract_inputs(tmp_path)
    case["probe"] = load_probe(PROBE)
    return case


def _run_extract(case, capsys, *, seed=None, out=None):
    arguments = [
        "extract", "--tree", str(case["tree"]), "--s2", str(case["s2"]),
        "--shuffle-seed", str(case["seed"] if seed is None else seed),
        "--out", str(case["out"] if out is None else out), "--sources",
        ",".join(f"{feature}={directory}" for feature, directory in case["sources"].items()),
    ]
    rc = case["probe"].main(arguments)
    stdout, stderr = capsys.readouterr()
    return subprocess.CompletedProcess(arguments, rc, stdout, stderr)


def _extract_tree_report(case, *, doc="d1", cycle=1, index=1):
    return "s2/" + extract_report_path(case, doc, cycle, index).relative_to(case["s2"]).as_posix()


def _assert_extract_written(case, result, *, must, should=0, reports=1, property_name):
    expected = f"FINDINGS: WRITTEN findings={must + should} must={must} should={should} reports={reports}"
    assert result.stdout.splitlines()[-1:] == [expected], (
        f"{property_name}: expected last token {expected!r}; actual stdout={result.stdout!r}"
    )
    assert result.returncode == 0, f"{property_name}: a written extraction must succeed: {result.stderr}"
    rows = []
    for name in ("findings.jsonl", "key.jsonl"):
        path = case["out"] / name
        assert path.is_file(), f"{property_name}: extraction must write {name}, including an empty result"
        rows.append([json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()])
    return rows


def _assert_cycle_refusal(case, capsys, cycle, property_name):
    result = _run_extract(case, capsys)
    expected = f"FINDINGS: UNREADABLE reason=cycle_token:{cycle}"
    assert result.stdout.splitlines()[-1:] == [expected], (
        f"{property_name}: expected {expected!r}; actual stdout={result.stdout!r}"
    )
    assert result.returncode == 2, f"{property_name}: invalid recorded cycles must refuse extraction"
    assert "Traceback" not in result.stderr, f"{property_name}: cycle_token is a declared refusal"
    assert not (case["out"] / "findings.jsonl").exists(), f"{property_name}: refusal must not publish findings"


def _replace_extract_report(case, text, *, index=1):
    extract_report_path(case, index=index).write_text(text, encoding="utf-8")


def _bump_gate_count(case, monkeypatch, field):
    real_classify = case["probe"]._gate.classify
    calls = []

    def fake(text):
        counts = real_classify(text)
        calls.append(text)
        return {**counts, field: counts[field] + 1}

    monkeypatch.setattr(case["probe"]._gate, "classify", fake)
    return calls


def test_must_count_mismatch_through_production_path(extract_case, capsys, monkeypatch):
    case = extract_case
    calls = _bump_gate_count(case, monkeypatch, "must_count")
    result = _run_extract(case, capsys)
    expected = "FINDINGS: UNREADABLE reason=must_count_mismatch:" + _extract_tree_report(case)
    assert result.stdout.splitlines()[-1:] == [expected], (
        f"extract_report must use _gate.classify's must_count: expected {expected!r}; "
        f"actual stdout={result.stdout!r}"
    )
    assert calls == [extract_report_path(case).read_text(encoding="utf-8")], "the production caller must classify its report once"
    assert result.returncode == 2, "a gate/walk must-count difference must refuse extraction"
    assert "Traceback" not in result.stderr, "must_count_mismatch must be a declared refusal"
    assert not (case["out"] / "findings.jsonl").exists(), "a must-count mismatch must not publish findings"


def test_extract_writes_findings_for_clean_reports(extract_case, capsys):
    case = extract_case
    _replace_extract_report(case, extract_report_text("None", "None"))
    result = _run_extract(case, capsys)
    findings, key = _assert_extract_written(case, result, must=0, property_name="clean gate sections yield zero findings")
    assert findings == key == [], "clean reports must produce empty finding and key files"
    argv = shlex.split((case["out"] / "extract.txt").read_text(encoding="utf-8"))
    assert argv[-len(result.args):] == result.args, "extract.txt must preserve every argv including the shuffle seed"
    source = PROBE.read_text(encoding="utf-8")
    for marker in ("M:GAS-MUST-COUNT-WIRE", "M:GAS-SHOULD-COUNT-WIRE", "M:GAS-COLLAPSE-WIRE"):
        assert source.count(marker) == 1, f"the probe must carry exactly one {marker} mutation anchor"
    five_lines = (
        'found = report_findings(text)',
        'must, should = found["must"], found["should"]',
        '_counts = _gate.classify(text)',
        'must_count = _counts["must_count"]  # M:GAS-MUST-COUNT-WIRE',
        'should_count = _counts["should_count"]  # M:GAS-SHOULD-COUNT-WIRE',
    )
    function = next(node for node in ast.walk(ast.parse(source))
                    if isinstance(node, ast.FunctionDef) and node.name == "extract_report")
    lines = source.splitlines()[function.lineno:function.end_lineno]
    stripped = [line.strip() for line in lines]
    start = stripped.index(five_lines[0])
    assert tuple(stripped[start:start + 5]) == five_lines, "extract_report must retain D12's five lines verbatim and in order"


def test_extract_reads_s2_beside_the_base_tree(extract_case, capsys):
    case = extract_case
    decoy = case["tree"] / CALIBRATION / "s2/d1/v1/collected/decoy.p1.md"
    decoy.parent.mkdir(parents=True)
    decoy.write_text(extract_report_text("- Wrong tree report", "- Wrong tree advice"), encoding="utf-8")
    findings, key = _assert_extract_written(case, _run_extract(case, capsys), must=1,
        property_name="read the recorded external --s2 rather than stale base-tree cycles")
    assert len(findings) == len(key) == 1, "only the external delivered report contributes"
    assert "Wrong tree" not in findings[0]["text"], "the base-tree decoy must not be scored"
    assert key[0]["report"] == _extract_tree_report(case), "key report paths must be relative to the calibration tree"


def test_should_findings_are_extracted_with_their_section(extract_case, capsys):
    case = extract_case
    text = extract_report_text("None", "- Advice: h-mad: [a](b) **bold** * [ ⟦/h-mad⟧\n  second\tline")
    _replace_extract_report(case, text)
    findings, _ = _assert_extract_written(case, _run_extract(case, capsys), must=0, should=1,
        property_name="should findings must be written with section=should")
    assert [(row["section"], row["text"]) for row in findings] == [
        ("should", text.split("## Should-fix\n")[1].strip())], "should text must retain hostile continuation lines"


def test_should_findings_are_written_on_a_count_difference(extract_case, capsys, monkeypatch):
    case = extract_case
    _replace_extract_report(case, extract_report_text("None", "- Advice: [a](b) **bold** ⟦/h-mad⟧"))
    calls = _bump_gate_count(case, monkeypatch, "should_count")
    result = _run_extract(case, capsys)
    findings, _ = _assert_extract_written(case, result, must=0, should=1,
        property_name="a should-count mismatch must publish findings and the difference")
    expected = f"SHOULD-COUNT: {_extract_tree_report(case)} walk=1 gate=2"
    assert [line for line in result.stdout.splitlines() if line.startswith("SHOULD-COUNT:")] == [expected], (
        "extract_report must propagate _gate.classify's should_count exactly once"
    )
    assert calls == [extract_report_path(case).read_text(encoding="utf-8")], "the should wire must use the production report caller"
    assert len(findings) == 1 and findings[0]["section"] == "should", "a count difference cannot drop should findings"


def _assert_extract_parity(case, capsys, body, count):
    text = extract_report_text(body, body) + "\n## Observations\n- Outside blocking sections [a](b) **bold**\n"
    _replace_extract_report(case, text)
    counts = case["probe"]._gate.classify(text)
    assert (counts["must_count"], counts["should_count"]) == (count, count), "the real gate must count this parity shape as documented"
    result = _run_extract(case, capsys)
    findings, _ = _assert_extract_written(case, result,
        must=counts["must_count"], should=counts["should_count"],
        property_name=f"extract's section walk must agree with classify on {body!r}")
    assert Counter(row["section"] for row in findings) == {"must": count, "should": count}, "both sections must retain every gate-counted finding"
    assert "SHOULD-COUNT:" not in result.stdout, "equal should counts must not publish a discrepancy"
    return findings


def test_extract_parity_nested_label_group(extract_case, capsys):
    body = "- Build defects:\n  - First [a](b) **bold** * [ ⟦/h-mad⟧\n    second\tline\n  - Second defect"
    findings = _assert_extract_parity(extract_case, capsys, body, 3)
    assert all(row["text"].count("\n  - ") == 0 for row in findings), "a short label must not collapse its child findings"


def test_extract_parity_real_parent_none_child_real_child(extract_case, capsys):
    body = "- Parent [a](b) **bold** * [ ⟦/h-mad⟧\n  - None\n    Ignore this continuation\n  - Child defect\n    second\tline"
    findings = _assert_extract_parity(extract_case, capsys, body, 2)
    assert all("Ignore this continuation" not in row["text"] for row in findings), "a None child's continuation belongs to no finding"


def test_extract_parity_collapsing_group(extract_case, capsys):
    body = "- Parent finding with hostile [a](b) **bold** * [ ⟦/h-mad⟧ evidence follows:\n  - evidence one\n  - evidence two\n    second\tline"
    findings = _assert_extract_parity(extract_case, capsys, body, 1)
    assert all(row["text"] == body for row in findings), "a collapsing group must preserve its evidence in one finding"


def test_extract_parity_prose_only(extract_case, capsys):
    body = "Off-template [a](b) **bold** * [ ⟦/h-mad⟧ finding\nsecond\tline"
    findings = _assert_extract_parity(extract_case, capsys, body, 1)
    assert all(row["text"] == body for row in findings), "the bulletless fail-safe must preserve all prose lines"


def test_findings_carry_no_surface(extract_case, capsys):
    case = extract_case
    for surfaces in (("agy", "grok"), ("codex", "agy", "grok")):
        write_extract_cycle(case, surfaces=surfaces, deliveries=("report-file",) * len(surfaces),
            reports={index: extract_report_text() for index in range(1, len(surfaces) + 1)})
        findings, keys = _assert_extract_written(case, _run_extract(case, capsys), must=len(surfaces),
            reports=len(surfaces), property_name="blind findings while preserving pass-to-surface provenance in the key")
        assert all(set(row) == set("id doc cycle section text quotes".split()) for row in findings), "findings rows must have exactly the blinded D3 fields"
        assert all(set(row) == set("id doc cycle pass surface report".split()) for row in keys), "key rows must have exactly the provenance fields"
        by_id = {row["id"]: row for row in keys}
        assert len(by_id) == len(findings) and set(by_id) == {row["id"] for row in findings}, "ids must be unique and joined one-to-one"
        generator = random.Random(case["seed"])
        expected_ids = [f"F{generator.getrandbits(32):08x}" for _ in findings]
        assert set(by_id) == set(expected_ids), "ids must come from Random(shuffle_seed).getrandbits(32)"
        generator.shuffle(expected_ids)
        assert [row["id"] for row in findings] == expected_ids, "the same seeded generator must shuffle the finding order after assigning ids"
        assert {row["pass"]: row["surface"] for row in keys} == dict(enumerate(surfaces, 1)), "surface must follow command --surfaces by pass index"
        for row in findings:
            assert (row["doc"], row["cycle"]) == ("d1", 1), "blinding must retain document and cycle"
            assert (by_id[row["id"]]["doc"], by_id[row["id"]]["cycle"]) == (row["doc"], row["cycle"]), "key provenance must agree with its finding"
        before = [(case["out"] / name).read_bytes() for name in ("findings.jsonl", "key.jsonl")]
        _assert_extract_written(case, _run_extract(case, capsys), must=len(surfaces), reports=len(surfaces), property_name="the same shuffle seed must reproduce byte-identical findings and key")
        assert before == [(case["out"] / name).read_bytes() for name in ("findings.jsonl", "key.jsonl")], "seeded blinding must be reproducible"
        _assert_extract_written(case, _run_extract(case, capsys, seed=1730), must=len(surfaces), reports=len(surfaces), property_name="a different shuffle seed must remain a valid extraction")
        assert before[0] != (case["out"] / "findings.jsonl").read_bytes(), "a different shuffle seed must change blinded identifiers"


def _assert_no_hint_files(case):
    for root in (case["tree"], case["s2"], case["out"]):
        for path in root.rglob("*"):
            if path.is_file():
                assert not any(line.startswith(b"HINT:") for line in path.read_bytes().splitlines()), f"hints must remain stdout-only: {path}"


def test_hint_resolves_a_live_target_path_to_the_seeded_copy(extract_case, capsys):
    case = extract_case
    record = case["records"][0]
    span = record["seeded"].splitlines()[0]
    root = "/tmp/gas-root-d1-s2v1-pass1"
    quote = f"quote: {root}/docs/01-plan/features/paper-lantern.plan.md › `{span}`"
    _replace_extract_report(case, extract_report_text(f"- Quoted defect\n  {quote}"))
    result = _run_extract(case, capsys)
    findings, _ = _assert_extract_written(case, result, must=1,
        property_name="a live target quote must resolve through placements to the seeded copy")
    assert findings[0]["quotes"], "the finding must retain its quote lines"
    assert f"HINT: {findings[0]['id']} candidate-hit:{record['id']}" in result.stdout.splitlines(), "the seeded target quote must produce a hit hint"
    assert "candidate-fabrication" not in result.stdout, "the live seeded target is present under its mapped tree path"
    _assert_no_hint_files(case)


def test_hint_resolves_a_live_paired_path_to_the_archive(extract_case, capsys):
    case = extract_case
    paired = case["tree"] / case["sources"]["paper-lantern"] / "paper-lantern/paper-lantern.spec.md"
    span = paired.read_text(encoding="utf-8").splitlines()[3]
    for spelling in ("/tmp/gas-root-d1-s2v1-pass1/docs/01-plan/features/paper-lantern.spec.md",
                     "docs/01-plan/features/paper-lantern.spec.md",
                     paired.relative_to(case["tree"]).as_posix()):
        for quoted_span, fabricated in ((span, False), (span + " definitely absent", True)):
            _replace_extract_report(case, extract_report_text(f"- Paired source\n  quote: {spelling} › `{quoted_span}`"))
            result = _run_extract(case, capsys)
            findings, _ = _assert_extract_written(case, result, must=1,
                property_name="paired quotes must resolve to the unseeded archive and distinguish absent text")
            hint = f"HINT: {findings[0]['id']} candidate-fabrication"
            assert (hint in result.stdout.splitlines()) is fabricated, "only an absent paired span should produce candidate-fabrication"
            assert "candidate-hit:" not in result.stdout, "an unseeded paired copy cannot hit a target seed"
            _assert_no_hint_files(case)


def test_cycle_token_no_recorded_line(extract_case, capsys):
    directory = extract_case["s2"] / "d1/v1"
    for text in ("ASSEMBLE: HALT p2:preflight\n", ""):
        (directory / "auditcycle.txt").write_text(text, encoding="utf-8")
        _assert_cycle_refusal(extract_case, capsys, "d1.v1", "a cycle needs one recorded AUDITCYCLE line")


def test_cycle_token_unparseable_line(extract_case, capsys):
    path = extract_case["s2"] / "d1/v1/auditcycle.txt"
    for text in ("AUDITCYCLE: MAYBE delivered=report-file,none\n", "AUDITCYCLE: PASS\nAUDITCYCLE: FAIL\n"):
        path.write_text(text, encoding="utf-8")
        _assert_cycle_refusal(extract_case, capsys, "d1.v1", "a malformed or ambiguous recorded cycle must be refused")


def test_cycle_token_v2_missing_after_unverified_v1(extract_case, capsys):
    write_extract_cycle(extract_case, verdict="UNVERIFIED", reason="no_report:p2", deliveries=("report-file", "none"))
    _assert_cycle_refusal(extract_case, capsys, "d1.v2", "UNVERIFIED v1 requires a second recorded cycle")


def test_cycle_token_v2_present_when_v1_not_unverified(extract_case, capsys):
    for verdict in ("PASS", "FAIL"):
        write_extract_cycle(extract_case, verdict=verdict, deliveries=("report-file", "none"))
        write_extract_cycle(extract_case, cycle=2)
        _assert_cycle_refusal(extract_case, capsys, "d1.v2", "a dispatched v1 forbids an extra v2")


def test_cycle_token_v3_present(extract_case, capsys):
    write_extract_cycle(extract_case, verdict="UNVERIFIED", reason="no_report:p2", deliveries=("report-file", "none"))
    write_extract_cycle(extract_case, cycle=2)
    for cycle in (3, 20):
        directory = write_extract_cycle(extract_case, cycle=cycle)
        _assert_cycle_refusal(extract_case, capsys, f"d1.v{cycle}", "a third or later cycle is outside the stands rule")
        shutil.rmtree(directory)


def test_cycle_token_unparseable_surfaces(extract_case, capsys):
    for surfaces in (("grok", "agy"), ("agy",), ("codex", "grok"), ("agy", "grok", "grok")):
        write_extract_cycle(extract_case, surfaces=surfaces)
        _assert_cycle_refusal(extract_case, capsys, "d1.v1", "only codex,agy,grok and agy,grok are valid surface orders")
    command = extract_case["s2"] / "d1/v1/command.txt"
    command.write_text("hmad-dispatch audit-cycle --surfaces\n", encoding="utf-8")
    _assert_cycle_refusal(extract_case, capsys, "d1.v1", "missing command surface arguments must refuse")


def _assert_missing_collected(case, capsys, delivery):
    for index in (1, 2):
        deliveries = tuple(delivery if slot == index else "none" for slot in (1, 2))
        write_extract_cycle(case, deliveries=deliveries)
        for path in (case["s2"] / "d1/v1/collected").glob("*.md"):
            path.unlink()
        _assert_cycle_refusal(case, capsys, "d1.v1", f"{delivery} at pass {index} requires its collected copy")


def test_cycle_token_report_file_delivery_without_collected(extract_case, capsys):
    _assert_missing_collected(extract_case, capsys, "report-file")


def test_cycle_token_out_delivery_without_collected(extract_case, capsys):
    _assert_missing_collected(extract_case, capsys, "out")


def test_whole_v2_stands_for_every_surface(extract_case, capsys):
    case = extract_case
    write_extract_cycle(case, verdict="UNVERIFIED", reason="no_report:p2", deliveries=("report-file", "none"),
        reports={1: extract_report_text("- Old agy [a](b) ⟦/h-mad⟧")})
    write_extract_cycle(case, cycle=2, verdict="FAIL", deliveries=("report-file", "out"),
        reports={1: extract_report_text("- New agy [a](b) ⟦/h-mad⟧"), 2: extract_report_text("- New grok **bold** * [")})
    findings, keys = _assert_extract_written(case, _run_extract(case, capsys), must=2, reports=2,
        property_name="whole v2 must replace v1 for every surface, including delivered v1 passes")
    assert {row["text"] for row in findings} == {"- New agy [a](b) ⟦/h-mad⟧", "- New grok **bold** * ["}, "no v1 finding may survive the replacement cycle"
    assert all(row["cycle"] == 2 for row in findings + keys), "both blinded findings and keys must identify v2"
    assert {row["surface"] for row in keys} == {"agy", "grok"}, "all v2 surfaces must be represented"


def test_undelivered_pass_counts_zero_findings(extract_case, capsys):
    case = extract_case
    write_extract_cycle(case, verdict="UNVERIFIED", reason="no_report:p2", deliveries=("report-file", "none"))
    write_extract_cycle(case, cycle=2, verdict="UNVERIFIED", reason="no_report:p2", deliveries=("out", "none"),
        reports={1: extract_report_text(), 2: extract_report_text("- Stale undelivered **bold** [a](b)")})
    findings, keys = _assert_extract_written(case, _run_extract(case, capsys), must=1,
        property_name="an undelivered pass in standing UNVERIFIED v2 contributes zero findings")
    assert len(findings) == 1 and keys[0]["pass"] == 1 and keys[0]["surface"] == "agy", "the delivered pass alone contributes"


def test_low_evidence_delivered_report_is_scored(extract_case, capsys):
    case = extract_case
    write_extract_cycle(case, verdict="UNVERIFIED", reason="low_evidence:p1", deliveries=("report-file", "none"))
    write_extract_cycle(case, cycle=2, verdict="UNVERIFIED", reason="low_evidence:p1", deliveries=("report-file", "none"),
        reports={1: extract_report_text()})
    findings, keys = _assert_extract_written(case, _run_extract(case, capsys), must=1,
        property_name="a delivered report is scored even when standing v2 has low evidence")
    assert len(findings) == len(keys) == 1 and keys[0]["cycle"] == 2, "low evidence must not discard a delivered v2 finding"


def _opposed_prompts(case, shape):
    directory = case["s2"] / "d1/v1"
    payload = "Human [a](b) **bold** * [ ⟦/h-mad⟧\nsecond\tline\n"
    first = payload + "Report path: {REPORT}\n"
    second = first
    if shape == "foreign":
        second += "Foreign line [a](b) **bold** ⟦/h-mad⟧\n"
    if shape == "identical":
        first = second = payload
    for index, text in enumerate((first, second), 1):
        (directory / f"p{index}.prompt.txt").write_text(
            text.replace("{REPORT}", str(directory / f"p{index}.report.md")), encoding="utf-8")
    return first, second


def _assert_raw_wrapper_authority(case, tmp_path, *, prompts, halted=False):
    """The real shell decides divergence/halt; isolated stubs replace agents only."""
    from test_hmad_dispatch_audit_cycle import (
        dispatch_args, install_audit_cycle_stubs, project_with_docs, run_audit_cycle,
    )
    scratch = tmp_path / "raw-wrapper"
    scratch.mkdir()
    root = project_with_docs(scratch)
    script_dir, _asm_calls, _cycle_calls = install_audit_cycle_stubs(scratch)
    # Feed the same raw prompt shapes to the real wrapper using its actual
    # transport report path, rather than teaching a second diff implementation.
    assembler = (
        "import sys\nfrom pathlib import Path\n"
        "args = sys.argv[1:]\n"
        "out = Path(args[args.index('--out') + 1])\n"
        "report = args[args.index('--report-file') + 1]\n"
        "index = 2 if out.name.endswith('_p2.txt') else 1\n"
        f"prompts = {prompts!r}\n"
        f"halted = {halted!r}\n"
        "if halted and index == 2:\n    print('ASSEMBLE: HALT p2:preflight')\n"
        "else:\n    out.parent.mkdir(parents=True, exist_ok=True)\n"
        "    out.write_text(prompts[index - 1].replace('{REPORT}', report), encoding='utf-8')\n"
        "    print(f'ASSEMBLE: PASS {out} 123B size_status=verified')\n"
    )
    (script_dir / "h_mad_assemble_audit.py").write_text(assembler, encoding="utf-8")
    result = run_audit_cycle(scratch, dispatch_args(root=root),
        env={"HMAD_AUDIT_CYCLE_SCRIPT_DIR": str(script_dir)})
    assert result.returncode == 0, f"the raw-input wrapper authority must run: {result.stderr}"
    parsed = case["probe"].parse_auditcycle(result.stdout)
    assert parsed is not None, f"the real wrapper must emit its authoritative token: {result.stdout}"
    return parsed


def test_m1_a1_foreign_line_beside_dispatched_token_does_not_fail(extract_case, tmp_path, capsys):
    case = extract_case
    prompts = _opposed_prompts(case, "foreign")
    parsed = _assert_raw_wrapper_authority(case, tmp_path, prompts=prompts)
    assert (parsed["verdict"], parsed["reason"]) == ("UNVERIFIED", "prompt_divergence"), "a raw foreign prompt line really causes divergence"
    _assert_extract_written(case, _run_extract(case, capsys), must=1,
        property_name="recorded PASS must stand despite raw foreign prompt differences")


def test_m1_a2_identical_prompts_beside_dispatched_token_does_not_fail(extract_case, tmp_path, capsys):
    case = extract_case
    prompts = _opposed_prompts(case, "identical")
    parsed = _assert_raw_wrapper_authority(case, tmp_path, prompts=prompts)
    assert (parsed["verdict"], parsed["reason"]) == ("UNVERIFIED", "prompt_divergence"), "byte-identical raw prompts really cause divergence"
    _assert_extract_written(case, _run_extract(case, capsys), must=1,
        property_name="recorded PASS must stand despite byte-identical raw prompts")


def test_m1_b_report_path_only_beside_divergence_token_fails(extract_case, tmp_path, capsys):
    case = extract_case
    write_extract_cycle(case, verdict="UNVERIFIED", reason="prompt_divergence", deliveries=("report-file", "none"))
    prompts = _opposed_prompts(case, "report-only")
    parsed = _assert_raw_wrapper_authority(case, tmp_path, prompts=prompts)
    assert parsed["verdict"] == "PASS", "raw report-path-only differences really permit dispatch"
    _assert_cycle_refusal(case, capsys, "d1.v2", "recorded prompt_divergence requires v2 despite dispatchable raw prompts")


def test_m2_c1_pass_asm_beside_halt_token_is_halted(extract_case, tmp_path, capsys):
    case = extract_case
    write_extract_cycle(case, verdict="UNVERIFIED", reason="assemble_halt:p2", deliveries=("report-file", "none"))
    prompts = _opposed_prompts(case, "report-only")
    parsed = _assert_raw_wrapper_authority(case, tmp_path, prompts=prompts)
    assert parsed["verdict"] == "PASS", "raw PASS assembly outputs really permit dispatch"
    _assert_cycle_refusal(case, capsys, "d1.v2", "recorded assembly halt requires v2 despite PASS asm files")


def test_m2_c2_halt_asm_beside_pass_token_is_not_halted(extract_case, tmp_path, capsys):
    case = extract_case
    prompts = _opposed_prompts(case, "report-only")
    (case["s2"] / "d1/v1/p2.asm.txt").write_text("ASSEMBLE: HALT p2:preflight\n", encoding="utf-8")
    parsed = _assert_raw_wrapper_authority(case, tmp_path, prompts=prompts, halted=True)
    assert (parsed["verdict"], parsed["reason"]) == ("UNVERIFIED", "assemble_halt:p2"), "raw HALT assembly output really halts dispatch"
    _assert_extract_written(case, _run_extract(case, capsys), must=1,
        property_name="recorded PASS must stand despite a raw HALT asm file")


def _assert_raw_delivery(case, expected):
    directory = case["s2"] / "d1/v1"
    cycle = case["probe"]._cycle
    delivery, _ = cycle.collect(cycle.PassSpec(
        1, directory / "p1.report.md", directory / "p1.out.txt", 0, None),
        grace=0, project_root=case["out"].parent / "raw-collect-root",
        feature="paper-lantern", phase="plan", cycle=1)
    assert delivery == expected, "the real collect authority must disagree with the recorded delivered field"
    report = extract_report_path(case)
    result = subprocess.run([sys.executable, str(PROBE.parents[4] / "h-mad/scripts/h_mad_audit_gate.py"), str(report)],
        text=True, capture_output=True, timeout=15)
    assert result.returncode in (0, 2), f"the gate authority must run on the collected copy: {result.stderr}"
    verdict, must, should = cycle._gate_token(result.stdout, report)
    assert (verdict, must, should) == ("FAIL", 1, 0), "the collected copy really contains one gate-scored finding"


def test_m4_e1_score_ignores_report_beside_delivered_none(extract_case, capsys):
    case = extract_case
    directory = write_extract_cycle(case, deliveries=("none", "none"))
    transport = directory / "p1.report.md"
    transport.write_bytes(extract_report_path(case).read_bytes())
    transport.with_name(transport.name + ".done").touch()
    _assert_raw_delivery(case, "report-file")
    findings, key = _assert_extract_written(case, _run_extract(case, capsys), must=0, reports=0,
        property_name="recorded delivered=none must ignore a complete transport and a collected finding")
    assert findings == key == [], "no finding or provenance row may come from an undelivered pass"


def _assert_recorded_delivery(case, capsys, delivery):
    write_extract_cycle(case, deliveries=(delivery, "none"))
    _assert_raw_delivery(case, "none")
    findings, key = _assert_extract_written(case, _run_extract(case, capsys), must=1,
        property_name=f"recorded delivered={delivery} must score its collected report despite absent raw delivery")
    assert len(findings) == len(key) == 1 and key[0]["surface"] == "agy", "the delivered collected finding must retain its pass surface"


def test_m4_e2a_score_reads_collected_beside_report_file(extract_case, capsys):
    _assert_recorded_delivery(extract_case, capsys, "report-file")


def test_m4_e2b_score_reads_collected_beside_out(extract_case, capsys):
    _assert_recorded_delivery(extract_case, capsys, "out")


def _assert_raw_effort(case, *, high):
    from grokfixtures import f0_with_completed
    log = case["s2"] / "d1/v1/p1.log"
    if high:
        log.write_text(log.read_text(encoding="utf-8") + f0_with_completed(4), encoding="utf-8")
    cycle = case["probe"]._cycle
    measured = cycle.measure_effort(log)
    assert measured is not None and measured["ok"] == (4 if high else 0), "raw log must have the effort opposite to the recorded verdict"
    combined = cycle.combine([cycle.PassResult(1, "report-file", extract_report_path(case),
        "PASS", 0, 0, [], measured, 0)])
    assert combined == (("PASS", None) if high else ("UNVERIFIED", "low_evidence:p1")), "the real combine authority must disagree with the recorded verdict"


def test_m5_f1_unverified_token_requires_v2(extract_case, capsys):
    case = extract_case
    write_extract_cycle(case, verdict="UNVERIFIED", reason="low_evidence:p1", deliveries=("report-file", "none"))
    _assert_raw_effort(case, high=True)
    _assert_cycle_refusal(case, capsys, "d1.v2", "recorded UNVERIFIED requires v2 despite high raw evidence")


def test_m5_f2_pass_token_beside_hollow_log_stands(extract_case, capsys):
    case = extract_case
    _assert_raw_effort(case, high=False)
    _assert_extract_written(case, _run_extract(case, capsys), must=1,
        property_name="recorded PASS must stand despite a hollow raw log")


@pytest.fixture
def score_case(tmp_path, monkeypatch):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    return build_score_inputs(tmp_path, load_probe(PROBE))


def _run_score(case, capsys, *, shas=None):
    argv = ["score", "--tree", str(case["tree"]), "--sources",
            ",".join(f"{feature}={directory}" for feature, directory in case["sources"].items())]
    if shas is not None:
        argv += ["--calibration-sha", shas[0], "--score-sha", shas[1]]
    rc = case["probe"].main(argv)
    stdout, stderr = capsys.readouterr()
    return subprocess.CompletedProcess(argv, rc, stdout, stderr)


def _assert_score_token(result, verdict, reason=None, *, shas=None, property_name):
    expected = "SEEDSCORE: " + verdict
    if reason:
        expected += f" reason={reason}"
    if verdict != "UNREADABLE":
        calibration, score_sha = shas or ("unstated", "unstated")
        expected += f" calibration={calibration} score={score_sha}"
    assert result.stdout.splitlines()[-1:] == [expected], (
        f"{property_name}: expected final token {expected!r}; actual stdout={result.stdout!r}; "
        f"stderr={result.stderr!r}"
    )
    assert result.returncode == (2 if verdict == "UNREADABLE" else 0), (
        f"{property_name}: only UNREADABLE exits 2; PASS, MISS and INCONCLUSIVE exit 0"
    )
    assert "Traceback" not in result.stderr, f"{property_name}: a declared outcome must not traceback"
    return result.stdout.splitlines()


def _score_refusal(case, capsys, reason, property_name):
    write_score_tables(case)
    _assert_score_token(_run_score(case, capsys), "UNREADABLE", reason,
                        property_name=property_name)


def _surface_finding(case, surface="grok"):
    identifier = next(row["id"] for row in case["key"] if row["surface"] == surface)
    return next(row for row in case["findings"] if row["id"] == identifier)


def _surface_label(case, surface="grok"):
    identifier = _surface_finding(case, surface)["id"]
    return next(row for row in case["labels"] if row["id"] == identifier)


def test_key_mismatch_id_sets_differ(score_case, capsys):
    score_case["key"].pop()
    _score_refusal(score_case, capsys, "key_mismatch", "finding/key id sets must agree")


def test_key_mismatch_duplicate_id_in_findings(score_case, capsys):
    score_case["findings"].append(dict(score_case["findings"][0]))
    _score_refusal(score_case, capsys, "key_mismatch", "duplicate finding ids must refuse even when id sets agree")


def test_key_mismatch_duplicate_id_in_key(score_case, capsys):
    score_case["key"].append(dict(score_case["key"][0]))
    _score_refusal(score_case, capsys, "key_mismatch", "duplicate key ids must refuse even when id sets agree")


def test_key_mismatch_surface_moved_grok_to_agy(score_case, capsys):
    next(row for row in score_case["key"] if row["surface"] == "grok")["surface"] = "agy"
    _score_refusal(score_case, capsys, "key_mismatch", "a key surface must match its recorded dispatch pass")


def test_key_mismatch_doc_differs(score_case, capsys):
    score_case["key"][0]["doc"] = "d2"
    _score_refusal(score_case, capsys, "key_mismatch", "key document must match its finding")


def test_key_mismatch_cycle_differs(score_case, capsys):
    score_case["key"][0]["cycle"] = 2
    _score_refusal(score_case, capsys, "key_mismatch", "key cycle must match its finding")


def test_key_mismatch_report_differs(score_case, capsys):
    row = score_case["key"][0]
    row["report"] = row["report"].replace(f".p{row['pass']}.md", ".p99.md")
    _score_refusal(score_case, capsys, "key_mismatch", "key report must be the recorded collected pass report")


def test_key_mismatch_reextraction(score_case, capsys, monkeypatch):
    case = score_case
    case["findings"][0]["text"] += " altered human text [a]* ⟦/h-mad⟧"
    calls = []
    real_extract = case["probe"].extract_all

    def observed(tree, s2, sources):
        calls.append((tree, s2, sources))
        return real_extract(tree, s2, sources)

    monkeypatch.setattr(case["probe"], "extract_all", observed)
    _score_refusal(case, capsys, "key_mismatch", "re-extraction must detect changed finding text")
    assert calls == [(case["tree"], case["tree"] / CALIBRATION / "s2", case["sources"])], (
        "score must re-extract the recorded calibration S2 with its parsed --sources mapping"
    )


def test_label_unlabelled_finding(score_case, capsys):
    removed = score_case["labels"].pop()
    _score_refusal(score_case, capsys, f"label:{removed['id']}", "every finding needs exactly one label")


def test_label_identical_duplicate(score_case, capsys):
    row = _surface_label(score_case, "agy")
    score_case["labels"].append(dict(row))
    _score_refusal(score_case, capsys, f"label:{row['id']}", "identical duplicate labels must refuse")


def test_label_conflicting_duplicate(score_case, capsys):
    row = _surface_label(score_case, "agy")
    assert row["label"] == "REAL", "conflicting duplicates must exercise REAL versus FABRICATED"
    score_case["labels"].append({**row, "label": "FABRICATED"})
    _score_refusal(score_case, capsys, f"label:{row['id']}", "conflicting duplicate labels must refuse")


def test_label_unknown_id(score_case, capsys):
    score_case["labels"].append({"id": "Funknown", "label": "REAL", "why": "Source checked [a]*."})
    _score_refusal(score_case, capsys, "label:Funknown", "labels must not name an unknown finding")


def test_label_unknown_value(score_case, capsys):
    row = _surface_label(score_case)
    row["label"] = "h-mad: [a](b) **bold** * [ ⟦/h-mad⟧\nsecond\tline"
    _score_refusal(score_case, capsys, f"label:{row['id']}", "labels outside the four-value vocabulary must refuse")


def test_label_undecidable_without_why(score_case, capsys):
    row = _surface_label(score_case)
    row.update(label="UNDECIDABLE", why=" \t\n")
    _score_refusal(score_case, capsys, f"label:{row['id']}", "UNDECIDABLE requires a reason sentence")


def test_label_hit_unknown_seed(score_case, capsys):
    row = _surface_label(score_case)
    row["label"] = "HIT:d999-s1"
    _score_refusal(score_case, capsys, f"label:{row['id']}", "HIT must name a seed in the ledger")


def test_label_hit_seed_of_other_doc(score_case, capsys):
    row = _surface_label(score_case)
    row["label"] = "HIT:d2-s1"
    _score_refusal(score_case, capsys, f"label:{row['id']}", "HIT seed must belong to the finding document")


def _verdict_inputs(tmp_path, monkeypatch, grok, agy, *, codex=None):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    specs = [(surface, "d1", "must", label)
             for surface, labels in (("grok", grok), ("agy", agy), ("codex", codex or []))
             for label in labels]
    surfaces = ("agy", "grok") if codex is None else ("codex", "agy", "grok")
    return build_score_inputs(tmp_path, load_probe(PROBE), specs, surfaces)


def _assert_surface(lines, surface, hits, musts, fabricated, undecidable, *, low_evidence=0):
    expected = (
        f"SURFACE: {surface} recall={hits}/27 musts={musts} fabricated={fabricated} "
        f"undecidable={undecidable} fab_rate={fabricated}/{musts - undecidable} "
        f"delivered=9 low_evidence={low_evidence}"
    )
    assert expected in lines, f"surface totals must use distinct must seeds and raw fractions: expected {expected!r}; actual={lines!r}"


def test_d3_strictly_lower_fab_equal_recall_pass(tmp_path, monkeypatch, capsys):
    case = _verdict_inputs(tmp_path, monkeypatch, ["HIT:d1-s1", "REAL"], ["HIT:d1-s1", "FABRICATED"])
    assert case["probe"].d3(Fraction(0), 1, Fraction(1, 2), 1), "strictly lower fabrication with equal recall satisfies D3"
    assert not case["probe"].d3(Fraction(0), 0, Fraction(1, 2), 1), "strictly lower fabrication cannot compensate for lower recall"
    lines = _assert_score_token(_run_score(case, capsys), "PASS", property_name="lower fabrication, equal recall passes")
    _assert_surface(lines, "grok", 1, 2, 0, 0, low_evidence=1)
    _assert_surface(lines, "agy", 1, 2, 1, 0)
    assert "SURFACE: codex not_run" in lines, "two-surface scores must explicitly report codex not_run"


def test_d3_equal_fab_greater_recall_pass(tmp_path, monkeypatch, capsys):
    case = _verdict_inputs(tmp_path, monkeypatch, ["HIT:d1-s1", "HIT:d1-s2"], ["HIT:d1-s1", "REAL"])
    assert case["probe"].d3(Fraction(0), 2, Fraction(0), 1), "equal fabrication requires strictly greater recall"
    _assert_score_token(_run_score(case, capsys), "PASS", property_name="equal fabrication with greater recall passes")


def test_d3_full_tie_miss(tmp_path, monkeypatch, capsys):
    case = _verdict_inputs(tmp_path, monkeypatch, ["HIT:d1-s1", "REAL"], ["HIT:d1-s1", "REAL"])
    assert not case["probe"].d3(Fraction(0), 1, Fraction(0), 1), "a full tie must not satisfy D3"
    _assert_score_token(_run_score(case, capsys), "MISS", "bar_missed", property_name="full tie misses the strict bar")


def test_d3_equal_fab_lower_recall_miss(tmp_path, monkeypatch, capsys):
    case = _verdict_inputs(tmp_path, monkeypatch, ["HIT:d1-s1", "REAL"], ["HIT:d1-s1", "HIT:d1-s2"])
    assert not case["probe"].d3(Fraction(0), 1, Fraction(0), 2), "equal fabrication and lower recall must fail D3"
    _assert_score_token(_run_score(case, capsys), "MISS", "bar_missed", property_name="equal fabrication with lower recall misses")


def test_d3_unreduced_equal_fab_equal_recall_miss(tmp_path, monkeypatch, capsys):
    case = _verdict_inputs(tmp_path, monkeypatch,
        ["HIT:d1-s1", "REAL", "REAL", "FABRICATED"],
        ["HIT:d1-s1", *(["REAL"] * 5), "FABRICATED", "FABRICATED"])
    assert Fraction(1, 4) == Fraction(2, 8), "unreduced fractions describe the same fabrication rate"
    lines = _assert_score_token(_run_score(case, capsys), "MISS", "bar_missed",
                               property_name="1/4 versus 2/8 with equal recall is a full tie")
    _assert_surface(lines, "grok", 1, 4, 1, 0, low_evidence=1)
    _assert_surface(lines, "agy", 1, 8, 2, 0)
    assert not case["probe"].d3(Fraction(1, 4), 1, Fraction(2, 8), 1), "D3 compares Fraction values rather than raw numerator/denominator pairs"


def test_undecidable_flips_inconclusive(tmp_path, monkeypatch, capsys):
    case = _verdict_inputs(tmp_path, monkeypatch, ["HIT:d1-s1", "UNDECIDABLE"], ["HIT:d1-s1", "FABRICATED"])
    _assert_score_token(_run_score(case, capsys), "INCONCLUSIVE", "undecidable_flips",
                        property_name="opposed decisions for undecidables straddle the D3 bar")
    other = _verdict_inputs(tmp_path / "agy-undecidable", monkeypatch,
                            ["HIT:d1-s1", "REAL"], ["HIT:d1-s1", "UNDECIDABLE"])
    _assert_score_token(_run_score(other, capsys), "INCONCLUSIVE", "undecidable_flips",
                        property_name="agy undecidables also need optimistic and pessimistic Fraction bounds")


def test_seeds_undetected_inconclusive(tmp_path, monkeypatch, capsys):
    case = _verdict_inputs(tmp_path, monkeypatch, ["REAL"], ["REAL"])
    _assert_score_token(_run_score(case, capsys), "INCONCLUSIVE", "seeds_undetected",
                        property_name="no must hit on any surface is inconclusive")
    # Codex is included in the precedence check even though it is not compared by D3.
    ceiling = _verdict_inputs(tmp_path / "ceiling", monkeypatch, ["REAL"], ["REAL"], codex=["HIT:d1-s1"])
    _assert_score_token(_run_score(ceiling, capsys), "MISS", "bar_missed",
                        property_name="a codex must hit prevents seeds_undetected")


def test_seeds_undetected_outranks_a_fabrication_pass(tmp_path, monkeypatch, capsys):
    case = _verdict_inputs(tmp_path, monkeypatch, ["REAL"], ["FABRICATED"])
    _assert_score_token(_run_score(case, capsys), "INCONCLUSIVE", "seeds_undetected",
                        property_name="zero hits outrank a strictly lower fabrication PASS")


def test_seeds_undetected_outranks_a_fabrication_miss(tmp_path, monkeypatch, capsys):
    case = _verdict_inputs(tmp_path, monkeypatch, ["FABRICATED"], ["REAL"])
    _assert_score_token(_run_score(case, capsys), "INCONCLUSIVE", "seeds_undetected",
                        property_name="zero hits outrank a strictly higher fabrication MISS")


def test_zero_decidable_musts_prints_0_over_0(tmp_path, monkeypatch, capsys):
    case = _verdict_inputs(tmp_path, monkeypatch, ["UNDECIDABLE"], [])
    lines = _assert_score_token(_run_score(case, capsys), "INCONCLUSIVE", "seeds_undetected",
                               property_name="zero decidable musts have a printable 0/0 fabrication rate")
    _assert_surface(lines, "grok", 0, 1, 0, 1, low_evidence=1)
    _assert_surface(lines, "agy", 0, 0, 0, 0)
    assert case["probe"].verdict({"grok": (0, 1, 0, 1), "agy": (0, 0, 0, 0)}) == ("INCONCLUSIVE", "seeds_undetected"), "0/0 must be treated as Fraction(0) without dividing by zero"
    ceiling = _verdict_inputs(tmp_path / "ceiling", monkeypatch, ["UNDECIDABLE"], [], codex=["HIT:d1-s1"])
    lines = _assert_score_token(_run_score(ceiling, capsys), "MISS", "bar_missed",
                               property_name="a zero-must surface must use Fraction(0) when D3 is evaluated")
    _assert_surface(lines, "agy", 0, 0, 0, 0)


def test_score_exit_codes(tmp_path, monkeypatch, capsys):
    for name, grok, agy, verdict, reason in (
        ("pass", ["HIT:d1-s1"], ["HIT:d1-s1", "FABRICATED"], "PASS", None),
        ("miss", ["HIT:d1-s1"], ["HIT:d1-s1"], "MISS", "bar_missed"),
        ("inconclusive", ["REAL"], ["REAL"], "INCONCLUSIVE", "seeds_undetected"),
        ("unreadable", ["HIT:d1-s1"], ["REAL"], "UNREADABLE", "key_mismatch"),
    ):
        case = _verdict_inputs(tmp_path / name, monkeypatch, grok, agy)
        if verdict == "UNREADABLE":
            case["key"].clear()
            write_score_tables(case)
        _assert_score_token(_run_score(case, capsys), verdict, reason,
                            property_name=f"{verdict} exit-code and unstated provenance contract")
    shas = ("a" * 40, "b" * 40)
    case = _verdict_inputs(tmp_path / "provenance", monkeypatch, ["HIT:d1-s1"], ["HIT:d1-s1"])
    _assert_score_token(_run_score(case, capsys, shas=shas), "MISS", "bar_missed", shas=shas,
                        property_name="explicit provenance shas must reach the final score token")
    _assert_score_refusal_precedence(tmp_path / "precedence", monkeypatch, capsys)


def _assert_score_refusal_precedence(tmp_path, monkeypatch, capsys):
    """Repair competing defects in order, proving D13's first-applicable rule."""
    case = _verdict_inputs(tmp_path, monkeypatch, ["HIT:d1-s1"], ["REAL"])
    label = _surface_label(case)
    label["label"] = "UNKNOWN [a]* ⟦/h-mad⟧"
    _surface_finding(case)["text"] += " changed text [a]*"
    write_score_tables(case)
    cycle = case["s2"] / "d1/v1/auditcycle.txt"
    cycle_text = cycle.read_text(encoding="utf-8")
    cycle.write_text("Human annotation without a token [a]*\n", encoding="utf-8")
    seeded = case["tree"] / CALIBRATION / "seeded" / Path(case["records"][0]["source"]).name
    seeded_bytes = seeded.read_bytes()
    seeded.write_bytes(seeded_bytes + b"changed\n")
    record = case["records"][0]
    expected, origin = record.pop("expected"), record["origin"]
    record["origin"] = "UNKNOWN [a]*"
    _write_ledger(case["tree"], case["records"])
    _assert_score_token(_run_score(case, capsys), "UNREADABLE", "ledger_counts",
                        property_name="ledger_counts outranks origin, rebuild, cycle, key and label defects")
    record["expected"] = expected
    _write_ledger(case["tree"], case["records"])
    _assert_score_token(_run_score(case, capsys), "UNREADABLE", "ledger_origin",
                        property_name="ledger_origin outranks rebuild, cycle, key and label defects")
    record["origin"] = origin
    _write_ledger(case["tree"], case["records"])
    _assert_score_token(_run_score(case, capsys), "UNREADABLE", "seed_rebuild",
                        property_name="seed_rebuild outranks cycle, key and label defects")
    seeded.write_bytes(seeded_bytes)
    _assert_score_token(_run_score(case, capsys), "UNREADABLE", "cycle_token:d1.v1",
                        property_name="cycle_token outranks re-extraction, key and label defects")
    cycle.write_text(cycle_text, encoding="utf-8")
    with monkeypatch.context() as scoped:
        _bump_gate_count(case, scoped, "must_count")
        _assert_score_token(_run_score(case, capsys), "UNREADABLE",
                            "must_count_mismatch:" + _extract_tree_report(case),
                            property_name="re-extracted must_count_mismatch outranks key and label defects")
    _assert_score_token(_run_score(case, capsys), "UNREADABLE", "key_mismatch",
                        property_name="key_mismatch outranks label defects")
    _surface_finding(case)["text"] = _surface_finding(case)["text"].removesuffix(" changed text [a]*")
    write_score_tables(case)
    _assert_score_token(_run_score(case, capsys), "UNREADABLE", f"label:{label['id']}",
                        property_name="label validation runs after valid ledger, cycles and key")


def test_split_lines_never_move_the_verdict(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    case = build_score_inputs(tmp_path / "plan", load_probe(PROBE))
    first = _assert_score_token(_run_score(case, capsys), "PASS", property_name="baseline must totals determine verdict")
    other = build_score_inputs(tmp_path / "design", load_probe(PROBE),
        [("grok", "d2", "must", "HIT:d2-s1"), ("agy", "d2", "must", "REAL")])
    second = _assert_score_token(_run_score(other, capsys), "PASS", property_name="moving hits across phase and class keeps verdict")
    assert [line for line in first if line.startswith("SPLIT:")] != [line for line in second if line.startswith("SPLIT:")], "phase and class observations must change when the same hit moves"
    probe = case["probe"]
    assert list(inspect.signature(probe.verdict).parameters) == ["totals"], "verdict must accept only per-surface totals"
    for name in ("verdict", "d3"):
        definition = ast.parse(inspect.getsource(getattr(probe, name)))
        assert not any(isinstance(node, ast.Call) and
                       ((isinstance(node.func, ast.Name) and node.func.id == "observational_lines") or
                        (isinstance(node.func, ast.Attribute) and node.func.attr == "observational_lines"))
                       for node in ast.walk(definition)), f"{name} must never call observational_lines in any branch"

    def forbidden(*args, **kwargs):
        pytest.fail("verdict and d3 must never call observational_lines")

    monkeypatch.setattr(probe, "observational_lines", forbidden)
    assert probe.verdict({"grok": (1, 1, 0, 0), "agy": (0, 1, 0, 0)}) == ("PASS", None), "verdict must decide using only (hits, n, f, u)"
    assert probe.d3(Fraction(0), 1, Fraction(0), 0), "D3 must remain independent of observational rows"


def test_should_hits_never_move_the_verdict(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    case = build_score_inputs(tmp_path, load_probe(PROBE), [
        ("grok", "d1", "must", "HIT:d1-s1"), ("agy", "d1", "must", "REAL"),
        ("grok", "d1", "should", "HIT:d1-s2"), ("agy", "d1", "should", "HIT:d1-s3"),
    ])
    first = _assert_score_token(_run_score(case, capsys), "PASS", property_name="should HIT labels cannot add must recall")
    should_ids = {row["id"] for row in case["findings"] if row["section"] == "should"}
    for row in case["labels"]:
        if row["id"] in should_ids:
            row["label"] = "FABRICATED"
    write_score_tables(case)
    second = _assert_score_token(_run_score(case, capsys), "PASS", property_name="should fabrication cannot change must fabrication")
    assert [line for line in first if line.startswith("SURFACE:")] == [line for line in second if line.startswith("SURFACE:")], "should labels must leave every must surface total unchanged"
    assert [line for line in first if line.startswith("SHOULD:")] != [line for line in second if line.startswith("SHOULD:")], "the opposed should labels must change the observational counts"


def test_should_and_split_lines_are_printed(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    case = build_score_inputs(tmp_path, load_probe(PROBE), [
        ("grok", "d1", "must", "HIT:d1-s1"), ("grok", "d1", "must", "HIT:d1-s1"),
        ("grok", "d2", "must", "FABRICATED"), ("agy", "d1", "must", "REAL"),
        ("grok", "d1", "should", "HIT:d1-s2"), ("grok", "d1", "should", "HIT:d1-s2"),
        ("grok", "d2", "should", "FABRICATED"), ("agy", "d1", "should", "UNDECIDABLE"),
    ])
    lines = _assert_score_token(_run_score(case, capsys), "MISS", "bar_missed",
                               property_name="observations print after must-only surface totals")
    _assert_surface(lines, "grok", 1, 3, 1, 0, low_evidence=1)
    assert "SHOULD: grok hits=1/27 should=3 fabricated=1 undecidable=0" in lines, "should recall counts distinct seeds"
    assert "SHOULD: agy hits=0/27 should=1 fabricated=0 undecidable=1" in lines, "should undecidables must be printed"
    for surface in ("agy", "grok"):
        for phase in ("plan", "design", "impl-plan"):
            hits = int(surface == "grok" and phase == "plan")
            musts = (2 if phase == "plan" else 1 if phase == "design" else 0) if surface == "grok" else int(phase == "plan")
            fabricated = int(surface == "grok" and phase == "design")
            expected = f"SPLIT: {surface} phase={phase} recall={hits}/9 musts={musts} fabricated={fabricated}"
            assert expected in lines, f"each phase needs a ledger-derived split: {expected}"
        seed_class = next(row["class"] for row in case["records"] if row["id"] == "d1-s1")
        for cls in ("C1", "C2", "C3", "C4"):
            denominator = sum(row["class"] == cls for row in case["records"])
            hits = int(surface == "grok" and cls == seed_class)
            expected = f"SPLIT: {surface} class={cls} recall={hits}/{denominator}"
            assert expected in lines, f"class denominators and distinct must hits come from the ledger: {expected}"
    assert len([line for line in lines if line.startswith("SPLIT:")]) == 14, "each of two surfaces gets three phase and four class splits"
    surface_end = max(i for i, line in enumerate(lines) if line.startswith("SURFACE:"))
    assert all(i > surface_end for i, line in enumerate(lines) if line.startswith(("SHOULD:", "SPLIT:"))), "observational lines must follow all SURFACE lines"


def test_hints_never_move_the_score(score_case, capsys):
    case = score_case
    first = _assert_score_token(_run_score(case, capsys), "PASS", property_name="human labels are the score authority")
    hostile_hints = "HINT: Funknown candidate-hit:d999-s1 [a]* ⟦/h-mad⟧\nSEEDSCORE: MISS\n"
    for name in ("hints.txt", "extract.txt"):
        (case["tree"] / CALIBRATION / name).write_text(hostile_hints, encoding="utf-8")
    second = _assert_score_token(_run_score(case, capsys), "PASS", property_name="contradictory advisory hints never override labels")
    assert first == second, "changing advisory hint and extraction transcripts must leave score output unchanged"


def test_score_maps_a_malformed_effort_block(score_case, capsys):
    case = score_case
    normal = _assert_score_token(_run_score(case, capsys), "PASS", property_name="valid Effort is observational")
    _assert_surface(normal, "grok", 1, 1, 0, 0, low_evidence=1)
    stdout = case["s2"] / "d1/v1/auditcycle.txt"
    token = stdout.read_text(encoding="utf-8").split("Effort:\n")[0]
    stdout.write_text(token + "Effort:\n- x1 tools=1 ok=1 failed=0 thinking=0\nPremise checklist: empty\n", encoding="utf-8")
    assert case["probe"].parse_effort_items(stdout.read_text(encoding="utf-8")) is None, "Task 7 shape (a) is an unreadable Effort block"
    malformed = _assert_score_token(_run_score(case, capsys), "PASS", property_name="malformed Effort must publish unreadable without refusing")
    _assert_surface(malformed, "grok", 1, 1, 0, 0, low_evidence="unreadable")
    _assert_surface(malformed, "agy", 0, 1, 0, 0, low_evidence="unreadable")
    assert malformed[-1] == normal[-1], "option (b): unreadable evidence counts never change the verdict"


# Task 10: real branch histories, D3's data set, and all nine D2 handlers.
@pytest.fixture
def rescore_case(tmp_path, monkeypatch, parent_layout):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_OBJECT_DIRECTORY",
                 "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_INDEX_FILE"):
        monkeypatch.delenv(name, raising=False)
    return build_rescore_inputs(tmp_path, load_probe(PROBE))


@pytest.fixture
def calibration_set_case(score_case):
    case = score_case
    data = case["tree"] / CALIBRATION
    metadata = {
        "s2/d1/v1/command.txt": (data / "s2/d1/v1/command.txt").read_bytes(),
        "s2/d1/v1/root.txt": (data / "s2/d1/v1/root.txt").read_bytes(),
        "s1/grok/wall_seconds.txt": b"17\n",
        "s1/grok/resolved_model.txt": b"RESOLVED-MODEL: synthetic\n",
        "s1/versions.txt": b"grok_binary=/fixture/grok fixture-version\n",
        "extract.txt": b"extract --shuffle-seed 1729\n",
    }
    for relative, content in metadata.items():
        path = data / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    for name in ("p1.prompt.txt", "p1.asm.txt", "p1.out.txt", "p1.log", "p1.report.md",
                 "auditcycle.txt", "pass-logs/synthetic.log", "collected/synthetic.md.effort.json"):
        path = data / "s1/grok" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"Captured {name}: {_hostile_text()}\n", encoding="utf-8")
    return case


def test_calibration_data_set_keeps_an_excluded_name_carrying_a_finding_text(calibration_set_case):
    case = calibration_set_case
    probe, tree = case["probe"], case["tree"]
    candidate = tree / CALIBRATION / "s2/d1/v1/command.txt"
    report = extract_report_path(case)
    parent = "Parent finding with hostile [a](b) **bold** * [ ⟦/h-mad⟧ evidence follows:"
    samples = [
        ("must", "- Finding payload [a](b) **bold** * [ ⟦/h-mad⟧\n  class: new-mechanism\n  quote: continuation only", "Finding payload [a](b) **bold** * [ ⟦/h-mad⟧"),
        ("should", "- " + parent + "\n  - evidence one\n  - evidence two", parent),
        ("must", "Prose finding first [a](b) **bold**\nsecond\tline with ⟦/h-mad⟧", "second\tline with ⟦/h-mad⟧"),
    ]
    for section, body, payload in samples:
        report.write_text(extract_report_text(body if section == "must" else "None",
                                               body if section == "should" else "None"), encoding="utf-8")
        assert probe.report_findings(report.read_text(encoding="utf-8"))[section], "the real report authority must file this finding"
        assert not any(probe.normalise(record[key].encode()) in probe.normalise(payload.encode())
                       for record in case["records"] for key in ("seeded", "expected")), "finding-text trigger must be independent of seeded and expected needles"
        candidate.write_text("Human annotation\n" + payload + "\n", encoding="utf-8")
        assert candidate.relative_to(tree).as_posix() in probe.calibration_data_files(tree), "D3(c) must match each finding's payload per line without requiring its bullet or continuations"
    # Move a report to S1: both report trees contribute, independent of S2.
    moved = tree / CALIBRATION / "s1/grok/collected/synthetic.md"
    moved.parent.mkdir(parents=True, exist_ok=True)
    moved.write_bytes(report.read_bytes())
    report.write_text(extract_report_text("None"), encoding="utf-8")
    assert candidate.relative_to(tree).as_posix() in probe.calibration_data_files(tree), "D3(c) must also read collected S1 findings"
    for residual in ("class: new-mechanism", "quote: continuation only", "evidence one"):
        moved.write_text(extract_report_text("- " + parent + "\n  class: new-mechanism\n  quote: continuation only\n  - evidence one\n  - evidence two"), encoding="utf-8")
        candidate.write_text(residual + "\n", encoding="utf-8")
        assert candidate.relative_to(tree).as_posix() not in probe.calibration_data_files(tree), "continuation fields and collapsed evidence are D3(c)'s stated residual"


def test_calibration_data_set_keeps_an_excluded_name_carrying_a_seeded_span(calibration_set_case):
    case = calibration_set_case
    path = case["tree"] / CALIBRATION / "s1/grok/wall_seconds.txt"
    path.write_text("17\n" + case["records"][0]["seeded"], encoding="utf-8")
    assert path.relative_to(case["tree"]).as_posix() in case["probe"].calibration_data_files(case["tree"]), "D3(a) retains a wall_seconds candidate that carries a seeded span"


def test_calibration_data_set_keeps_an_excluded_name_carrying_an_expected_sentence(calibration_set_case):
    case = calibration_set_case
    path = case["tree"] / CALIBRATION / "s2/d1/v1/root.txt"
    path.write_text(path.read_text(encoding="utf-8") + case["records"][0]["expected"], encoding="utf-8")
    assert path.relative_to(case["tree"]).as_posix() in case["probe"].calibration_data_files(case["tree"]), "D3(b) retains a root candidate that carries an expected sentence"


def _publish_fixture_tip(case, tip):
    git(case["repo"], "update-ref", CALIBRATION_REF, tip)
    git(case["repo"], "push", "--force", "origin", CALIBRATION_REF)


def _branch_argv(case, mode, *, with_score=True, work=True):
    argv = [mode, "--repo", str(case["repo"]), "--calibration-sha", case["calibration"],
            "--smoke-sha", case["smoke"], "--sources",
            ",".join(f"{feature}={directory}" for feature, directory in case["sources"].items())]
    if with_score:
        argv += ["--score-sha", case["score"]]
    if mode == "rescore":
        argv += ["--run-id", case["run_id"]]
    if work:
        argv += ["--work-dir", str(case["work_dir"])]
    return argv


def _assert_branch_refusal(case, reason, property_name, *, mode="rescore", with_score=True):
    argv = _branch_argv(case, mode, with_score=with_score)
    result = subprocess.run([sys.executable, str(PROBE), *argv], text=True,
                            capture_output=True, timeout=45,
                            env={**os.environ, "TMPDIR": str(case["systemp"])})
    prefix = "MAINLEAK" if mode == "main-leak" else "SEEDSCORE"
    assert (result.returncode, result.stdout.splitlines()[-1:]) == (
        2, [f"{prefix}: UNREADABLE reason={reason}"],
    ), f"{property_name}: stdout={result.stdout!r}; stderr={result.stderr!r}"
    assert "Traceback" not in result.stderr, f"{property_name}: the refusal must be declared"


def test_drift_outside_calibration_dir(rescore_case):
    case = rescore_case
    path = "notes/outside [a]* ⟦h-mad⟧.txt"
    case["score"] = commit_fixture_tree(case["repo"], case["score"], {path: _hostile_text().encode()})
    _publish_fixture_tip(case, case["score"])
    _assert_branch_refusal(case, f"calibration_drift:{path}", "changes outside the calibration directory must refuse")


def test_drift_not_descendant(rescore_case):
    case = rescore_case
    sibling = commit_fixture_tree(case["repo"], case["main"], {})
    tip = commit_fixture_tree(case["repo"], case["score"], {}, extra_parents=(sibling,))
    _publish_fixture_tip(case, tip)
    case["smoke"] = sibling
    _assert_branch_refusal(case, "calibration_drift:not_descendant", "a known on-ref smoke sibling must descend from calibration", mode="main-leak", with_score=False)


def test_drift_score_not_descendant_of_smoke_commit(rescore_case):
    case = rescore_case
    sibling = commit_fixture_tree(case["repo"], case["calibration"], {})
    tip = commit_fixture_tree(case["repo"], case["score"], {}, extra_parents=(sibling,))
    _publish_fixture_tip(case, tip)
    case["score"] = sibling
    _assert_branch_refusal(case, "calibration_drift:not_descendant", "both on-ref descendants of calibration still require smoke-to-score descent")


def test_drift_seeded_copy_changed_at_score_sha(rescore_case):
    case = rescore_case
    path = CALIBRATION / "seeded" / Path(case["records"][0]["source"]).name
    content = (case["tree"] / path).read_bytes() + b"changed\n"
    case["score"] = commit_fixture_tree(case["repo"], case["score"], {path.as_posix(): content})
    _publish_fixture_tip(case, case["score"])
    _assert_branch_refusal(case, f"calibration_drift:{path}", "a seeded copy present at calibration must stay byte-identical at score")


def test_drift_ledger_changed_at_smoke_commit(rescore_case):
    case = rescore_case
    path = CALIBRATION / "ledger.jsonl"
    case["smoke"] = commit_fixture_tree(case["repo"], case["calibration"], {
        path.as_posix(): (case["tree"] / path).read_bytes() + b"\n",
    })
    _publish_fixture_tip(case, case["smoke"])
    _assert_branch_refusal(case, f"calibration_drift:{path}", "even parse-equivalent ledger bytes must not drift at smoke", mode="main-leak", with_score=False)


def test_drift_ledger_absent_at_score_sha(rescore_case):
    case = rescore_case
    path = CALIBRATION / "ledger.jsonl"
    case["score"] = commit_fixture_tree(case["repo"], case["score"], {path.as_posix(): None})
    _publish_fixture_tip(case, case["score"])
    _assert_branch_refusal(case, f"calibration_drift:{path}", "a calibration ledger must remain present at score")


def _commit_main_blob(case, content, *, path="notes/leak [a]* ⟦h-mad⟧.bin"):
    live = case["repo"] / path
    live.parent.mkdir(parents=True, exist_ok=True)
    live.write_bytes(content)
    git(case["repo"], "add", "--", path)
    git(case["repo"], "commit", "-m", f"Main fixture: {_hostile_text()}")
    case["main"] = git(case["repo"], "rev-parse", "HEAD")
    # The detector must inspect committed blobs even when the work-tree copy is clean.
    live.write_bytes(b"uncommitted replacement has no calibration content\n")
    return path


def test_main_leak_trigger_i_byte_equal_copy(rescore_case):
    case = rescore_case
    content = (case["s2"] / "d1/v1/p1.log").read_bytes()
    path = _commit_main_blob(case, content)
    _assert_branch_refusal(case, f"main_leak:{path}", "trigger i compares complete committed blobs against calibration file bytes", mode="main-leak")


def test_main_leak_trigger_i_on_a_captured_wrapper_stdout(rescore_case):
    case = rescore_case
    path = _commit_main_blob(case, (case["s2"] / "d1/v1/auditcycle.txt").read_bytes())
    _assert_branch_refusal(case, f"main_leak:{path}", "captured wrapper stdout belongs to trigger i's data set", mode="main-leak")


def test_main_leak_trigger_i_smoke_commit_without_score_sha(tmp_path, monkeypatch):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    case = build_rescore_inputs(tmp_path, load_probe(PROBE), smoke_failure=True)
    assert "score" not in case, "a smoke failure must have no score commit"
    path = _commit_main_blob(case, (case["tree"] / CALIBRATION / "s1/grok/p1.log").read_bytes())
    _assert_branch_refusal(case, f"main_leak:{path}", "trigger i must use the smoke tree when no score sha exists", mode="main-leak", with_score=False)


def test_main_leak_trigger_i_on_an_excluded_name_carrying_a_finding_text(rescore_case):
    case = rescore_case
    report = extract_report_path(case).read_text(encoding="utf-8")
    finding = case["probe"].report_findings(report)["must"][0]
    payload = case["probe"]._gate._payload(finding.splitlines()[0])
    content = ("Human command annotation\n" + payload + "\n").encode()
    relative = case["s2"].relative_to(case["tree"]) / "d1/v1/command.txt"
    case["score"] = commit_fixture_tree(case["repo"], case["score"], {relative.as_posix(): content})
    _publish_fixture_tip(case, case["score"])
    path = _commit_main_blob(case, content)
    _assert_branch_refusal(case, f"main_leak:{path}", "a finding-bearing command candidate must remain in trigger i's set", mode="main-leak")


def test_main_leak_trigger_ii_expected(rescore_case):
    case = rescore_case
    rewrapped = "\n\t".join(case["records"][0]["expected"].split())
    path = _commit_main_blob(case, ("Before expected sentence\n" + rewrapped + "\nAfter\n").encode())
    _assert_branch_refusal(case, f"main_leak:{path}", "trigger ii must find a normalised expected sentence inside a larger blob", mode="main-leak")


def test_main_leak_trigger_iii_seeded_span(rescore_case):
    case = rescore_case
    rewrapped = "\n\t".join(case["records"][0]["seeded"].split())
    path = _commit_main_blob(case, ("Before seeded span\n" + rewrapped + "\nAfter\n").encode())
    _assert_branch_refusal(case, f"main_leak:{path}", "trigger iii must find a normalised seeded span absent from its own archive", mode="main-leak")


def _assert_main_clean(case, *, with_score=True):
    result = subprocess.run([sys.executable, str(PROBE), *_branch_argv(case, "main-leak", with_score=with_score)],
                            capture_output=True, text=True, timeout=45,
                            env={**os.environ, "TMPDIR": str(case["systemp"])})
    data_sha = case["score"] if with_score else case["smoke"]
    blobs = len(git(case["repo"], "ls-tree", "-r", "--name-only", "HEAD").splitlines())
    token = f"MAINLEAK: CLEAN scanned={case['main']} data={data_sha} blobs={blobs}"
    assert (result.returncode, result.stdout.splitlines()) == (0, [token]), f"clean main must report the scanned HEAD, data commit and blob count: {result.stdout!r}; {result.stderr!r}"
    return token


def test_seeded_span_also_in_its_own_archive_source_does_not_refuse(tmp_path, monkeypatch, parent_layout):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    case = build_rescore_inputs(tmp_path, load_probe(PROBE), seeded_in_own_source=True)
    record = case["records"][0]
    assert record["seeded"] in (case["repo"] / record["source"]).read_text(encoding="utf-8"), "this span must really occur in its own archived source on main"
    assert case["probe"].check_ledger(case["tree"], case["sources"])["seeds"] == 27, "the exemption fixture must keep a valid ledger"
    _assert_main_clean(case)


def test_main_leak_ignores_a_main_blob_equal_to_wall_seconds(rescore_case):
    case = rescore_case
    _commit_main_blob(case, (case["tree"] / CALIBRATION / "s1/grok/wall_seconds.txt").read_bytes())
    _assert_main_clean(case)


def test_main_leak_prints_the_scanned_commit(rescore_case):
    case = rescore_case
    _commit_main_blob(case, b"safe main addition with [a]* and unicode \xe2\x9f\xa6h-mad\xe2\x9f\xa7\n")
    scanned, data, blobs = case["probe"].main_leak(case["repo"], case["score"], case["sources"], case["work_dir"])
    assert (scanned, data, blobs) == (case["main"], case["score"], 14), "main_leak must return the actual HEAD sha40, data sha40, and all 14 committed blobs"
    _assert_main_clean(case)


def test_ref_fetch_failed_no_remote(rescore_case):
    case = rescore_case
    git(case["repo"], "remote", "remove", "origin")
    _assert_branch_refusal(case, "calibration_ref:fetch_failed", "a missing origin must refuse fetch rather than score local objects")


def test_ref_absent(rescore_case):
    case = rescore_case
    git(case["origin"], "update-ref", "-d", CALIBRATION_REF)
    _assert_branch_refusal(case, "calibration_ref:ref_absent", "an absent remote calibration ref must refuse despite a local branch")


def test_ref_sha_unknown(rescore_case):
    case = rescore_case
    case["score"] = "f" * 40
    _assert_branch_refusal(case, "calibration_ref:sha_unknown:" + case["score"], "every cited sha must resolve to a commit")


def test_ref_not_on_ref(rescore_case):
    case = rescore_case
    case["score"] = commit_fixture_tree(case["repo"], case["calibration"], {
        (CALIBRATION / "off-ref.txt").as_posix(): _hostile_text().encode(),
    })
    _assert_branch_refusal(case, "calibration_ref:not_on_ref:" + case["score"], "a known local commit outside the fetched ref must refuse")


def test_list_changed_recorded_blob_differs(rescore_case):
    case = rescore_case
    old_blob = case["list_blob"]
    listing = case["repo"] / EXCLUSIONS
    listing.write_text(listing.read_text(encoding="utf-8") + "# Changed committed list\n", encoding="utf-8")
    git(case["repo"], "add", EXCLUSIONS.as_posix())
    git(case["repo"], "commit", "-m", "Change only exclusion-list bytes")
    _assert_branch_refusal(case, f"list_changed:{old_blob}", "rescore compares recorded list blobs with its own HEAD list")


def test_list_changed_unrecorded_root_record(rescore_case):
    case = rescore_case
    relative = CALIBRATION / "runs/fixture-run/s2/d1/v1/p1.root.txt"
    case["score"] = commit_fixture_tree(case["repo"], case["score"], {relative.as_posix(): None})
    _publish_fixture_tip(case, case["score"])
    _assert_branch_refusal(case, "list_changed:unrecorded", "a recorded cycle without its p1 root record must refuse")


def test_list_changed_malformed_root_record(rescore_case):
    case = rescore_case
    relative = CALIBRATION / "runs/fixture-run/s2/d1/v1/p1.root.txt"
    original = (case["tree"] / relative).read_text(encoding="utf-8")
    malformed = re.sub(r" list_blob=\S+", "", original)
    assert malformed.startswith("ROOT: READY ") and "list_blob=" not in malformed, "isolate the missing D2 list_blob field"
    assert case["probe"].parse_root_line(malformed.strip()) is None, "Task 4's parser must classify the malformed READY record as absent"
    case["score"] = commit_fixture_tree(case["repo"], case["score"], {relative.as_posix(): malformed.encode()})
    _publish_fixture_tip(case, case["score"])
    _assert_branch_refusal(case, "list_changed:unrecorded", "a malformed READY record must map parser None to unrecorded, never skip the cycle")


def test_main_leak_mode_clean_on_a_smoke_failure_branch(tmp_path, monkeypatch, parent_layout):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    case = build_rescore_inputs(tmp_path, load_probe(PROBE), smoke_failure=True)
    _lines, smoke_token = case["probe"].smoke(
        case["tree"] / CALIBRATION / "s1", REPO / "h-mad/scripts/h_mad_review_evidence.py",
        REPO / "h-mad/scripts/hmad-dispatch.sh",
    )
    assert smoke_token == "SMOKE: FAIL reason=vocab_missing:end", "end-to-end smoke branch must really derive to FAIL"
    assert "score" not in case and git(case["repo"], "rev-parse", CALIBRATION_REF) == case["smoke"], "a failed smoke publishes only the smoke tip"
    _assert_main_clean(case, with_score=False)


def test_rescore_reproduces_the_score_and_removes_its_temp_dirs(rescore_case, monkeypatch, capsys):
    case, created, calls = rescore_case, [], []
    probe = case["probe"]
    expected = subprocess.run([
        sys.executable, str(PROBE), "score", "--tree", str(case["tree"]),
        "--calibration-sha", case["calibration"], "--score-sha", case["score"], "--sources",
        ",".join(f"{feature}={directory}" for feature, directory in case["sources"].items()),
        "--run-id", case["run_id"],
    ], capture_output=True, text=True, timeout=30)
    assert expected.returncode == 0 and expected.stdout.splitlines()[-1].startswith("SEEDSCORE: PASS "), "score --tree must establish a real passing baseline"
    original_mkdtemp = tempfile.mkdtemp

    def tracked_temp(*args, **kwargs):
        path = Path(original_mkdtemp(*args, **kwargs))
        created.append(path)
        return str(path)

    monkeypatch.setattr(probe.tempfile, "mkdtemp", tracked_temp)
    for name in ("ref_checks", "drift_check", "main_leak", "list_check", "check_ledger", "build_root", "score"):
        original = getattr(probe, name, None)
        if original is not None:
            def trace(*args, _name=name, _original=original, **kwargs):
                calls.append((_name, args, kwargs))
                return _original(*args, **kwargs)
            monkeypatch.setattr(probe, name, trace)
    try:
        rc = probe.main(_branch_argv(case, "rescore"))
        out, err = capsys.readouterr()
        assert (rc, out.splitlines()[-1:]) == (0, expected.stdout.splitlines()[-1:]), f"rescore must reproduce score --tree's exact SEEDSCORE token: {out!r}; {err!r}"
        lines = out.splitlines()
        assert f"SCANNED: main={case['main']} data={case['score']} blobs=13" in lines, "rescore must publish the scanned commit and data tree"
        list_lines = [line for line in lines if line.startswith("LIST:")]
        assert len(list_lines) == 1, "rescore must publish one LIST provenance line"
        listing = re.fullmatch(r"LIST: recorded=([0-9a-f,]+) current=([0-9a-f]{40})", list_lines[0])
        assert listing and set(listing[1].split(",")) == {case["list_blob"]} and listing[2] == case["list_blob"], "rescore must publish every recorded/current list blob without inventing provenance"
        assert not any(line.startswith(("LEDGER:", "ROOT:", "MAINLEAK:")) for line in lines), "rescore's internal checks must not publish another mode's token"
        names = [name for name, _args, _kwargs in calls]
        assert names.index("ref_checks") < names.index("drift_check") < names.index("main_leak") < names.index("list_check") < names.index("check_ledger") < names.index("build_root") < names.index("score"), "AC-6.4's checks must run in the specified order"
        roots = [args[0].doc for name, args, _kwargs in calls if name == "build_root"]
        assert roots == [f"d{index}" for index in range(1, 10)], "rescore must rebuild all nine roots in order"
        assert created and all(not path.exists() for path in created), f"finally must remove every mkdtemp directory: {created!r}"
        for parent in {path.parent for path in created}:
            assert not (set(parent.iterdir()) & set(created)), "re-listing must find no probe temporary directories"
        assert "[H-MAD]" in err, "rescore must leave its cleanup/completion marker on stderr"
    finally:
        for path in created:
            if path.exists():
                shutil.rmtree(path)


SUCCESS_TOKENS = {
    "check-ledger": r"LEDGER: OK seeds=27 docs=9 C1=6 C2=7 C3=7 C4=7",
    "build-root": r"ROOT: READY doc=d1 purpose=rescore path=\S+ calibration=[0-9a-f]{40} list_commit=[0-9a-f]{40} list_blob=[0-9a-f]{40} absent=\d+",
    "record-cycle": r"RECORD: OK dest=.+ files=\d+",
    "commit-data": r"COMMIT: OK sha=[0-9a-f]{40} ref=refs/heads/calibration/grok-audit-surface",
    "smoke": r"SMOKE: PASS",
    "extract": r"FINDINGS: WRITTEN findings=2 must=2 should=0 reports=18",
    "score": r"SEEDSCORE: PASS calibration=[0-9a-f]{40} score=[0-9a-f]{40}",
    "rescore": r"SEEDSCORE: PASS calibration=[0-9a-f]{40} score=[0-9a-f]{40}",
    "main-leak": r"MAINLEAK: CLEAN scanned=[0-9a-f]{40} data=[0-9a-f]{40} blobs=\d+",
}


def _successful_mode_run(case, mode, tmp_path, capsys):
    probe = case["probe"]
    sources = ["--sources", ",".join(f"{feature}={directory}" for feature, directory in case["sources"].items())]
    root = None
    if mode in ("rescore", "main-leak"):
        argv = _branch_argv(case, mode)
    elif mode == "check-ledger":
        argv = [mode, "--tree", str(case["tree"]), *sources]
    elif mode == "build-root":
        argv = [mode, "--repo", str(case["repo"]), "--calibration-sha", case["calibration"],
                "--doc", "d1", "--purpose", "rescore", "--work-dir", str(case["work_dir"]),
                "--dest-parent", str(case["roots"]), *sources]
    elif mode == "record-cycle":
        args = probe.build_parser().parse_args([
            "build-root", "--repo", str(case["repo"]), "--calibration-sha", case["calibration"],
            "--doc", "d1", "--purpose", "s1", "--work-dir", str(case["work_dir"]),
            "--dest-parent", str(case["roots"]), *sources,
        ])
        line = probe.build_root(args)
        root = Path(probe.parse_root_line(line)["path"])
        cycle = build_cycle_inputs(tmp_path / f"grammar-cycle-{uuid.uuid4().hex}", root, line)
        argv = [mode, "--stem", str(cycle["stem"]), "--root", str(root), "--root-record", str(cycle["root_record"]),
                "--stdout", str(cycle["stdout"]), "--command", str(cycle["command"]), "--dest", str(cycle["dest"])]
    elif mode == "commit-data":
        src = tmp_path / "grammar-commit"
        src.mkdir(exist_ok=True)
        (src / "grammar.txt").write_text(_hostile_text(), encoding="utf-8")
        argv = [mode, "--repo", str(case["repo"]), "--parent", git(case["repo"], "rev-parse", CALIBRATION_REF),
                "--src", str(src), "--message", _hostile_text()]
    elif mode == "smoke":
        argv = [mode, "--data", str(case["tree"] / CALIBRATION / "s1")]
    elif mode == "extract":
        argv = [mode, "--tree", str(case["tree"]), "--s2", str(case["s2"]),
                "--shuffle-seed", "1729", "--out", str(tmp_path / f"grammar-extract-{uuid.uuid4().hex}"), *sources]
    else:
        argv = [mode, "--tree", str(case["tree"]), "--calibration-sha", case["calibration"],
                "--score-sha", case["score"], *sources]
        if mode == "score":
            argv += ["--run-id", case["run_id"]]
    try:
        capsys.readouterr()
        rc = probe.main(argv)
        out, err = capsys.readouterr()
        if mode == "build-root" and rc == 0:
            root = Path(probe.parse_root_line(out.splitlines()[-1])["path"])
        if mode == "commit-data" and rc == 0:
            git(case["repo"], "push", "origin", CALIBRATION_REF)
        return rc, out.splitlines(), err
    finally:
        if root is not None and root.exists():
            shutil.rmtree(root)


@pytest.mark.parametrize("mode", MODES, ids=MODES)
def test_success_token_shape_per_mode(mode, rescore_case, tmp_path, capsys):
    rc, lines, err = _successful_mode_run(rescore_case, mode, tmp_path, capsys)
    assert rc == 0 and lines and re.fullmatch(SUCCESS_TOKENS[mode], lines[-1]), f"{mode} must end with its full D2 success grammar: rc={rc}; lines={lines!r}; stderr={err!r}"
    prefix = rescore_case["probe"].GRAMMAR[mode][0]
    assert sum(line.startswith(prefix) for line in lines) == 1, f"{mode} must publish exactly one final token"


def test_no_published_line_uses_another_modes_prefix(rescore_case, tmp_path, capsys):
    for mode in MODES:
        rc, lines, err = _successful_mode_run(rescore_case, mode, tmp_path, capsys)
        assert rc == 0 and lines and re.fullmatch(SUCCESS_TOKENS[mode], lines[-1]), f"all nine handlers must execute before checking prefixes: {mode}: {lines!r}; {err!r}"
        prefixes = {grammar[0] for grammar in rescore_case["probe"].GRAMMAR.values()}
        assert not any(line.startswith(tuple(prefixes)) for line in lines[:-1]), f"{mode}'s published lines must not use any mode's token prefix: {lines!r}"


@pytest.mark.parametrize("mode", ["check-ledger", "build-root", "extract", "score", "rescore", "main-leak"])
def test_sources_override_reaches_every_ledger_mode(mode, rescore_case, tmp_path, monkeypatch, capsys):
    case, calls = rescore_case, []
    assert case["sources"] != case["probe"].SOURCES, "synthetic archive override must differ from every default feature"
    for name in ("check_ledger", "main_leak", "score", "build_root"):
        original = getattr(case["probe"], name, None)
        if original is None:
            continue
        signature = inspect.signature(original)

        def check_mapping(*args, _original=original, _signature=signature, _name=name, **kwargs):
            bound = _signature.bind(*args, **kwargs)
            mapping = bound.arguments.get("sources")
            if mapping is None and "args" in bound.arguments:
                mapping = bound.arguments["args"].sources
            assert mapping == case["sources"], f"{mode} must forward the parsed sources mapping into {_name}"
            calls.append(_name)
            return _original(*args, **kwargs)

        monkeypatch.setattr(case["probe"], name, check_mapping)
    rc, lines, err = _successful_mode_run(case, mode, tmp_path, capsys)
    assert rc == 0 and lines and re.fullmatch(SUCCESS_TOKENS[mode], lines[-1]), f"{mode} must successfully read the overridden archive: {lines!r}; {err!r}"
    required = {"main_leak"} if mode == "main-leak" else {"check_ledger"}
    if mode == "rescore":
        required |= {"main_leak", "build_root", "score"}
    assert required <= set(calls), f"{mode} must exercise every ledger/source consumer through the CLI: {calls!r}"


# Task 24: explicit scratch parents and re-anchored reset preconditions.
@pytest.fixture
def parent_layout(tmp_path, monkeypatch):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_OBJECT_DIRECTORY",
                 "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_INDEX_FILE"):
        monkeypatch.delenv(name, raising=False)
    paths = build_probe_parent_dirs(tmp_path)
    monkeypatch.setenv("TMPDIR", str(paths["systemp"]))
    monkeypatch.setattr(tempfile, "tempdir", str(paths["systemp"]))
    return paths


@pytest.fixture
def task24_case(parent_layout, rescore_case):
    return {**rescore_case, **parent_layout}


def _task24_argv(case, mode, *, work=True, dest=True):
    """Valid real inputs let each omitted/invalid parent reach its own guard."""
    sources = ["--sources", ",".join(
        f"{feature}={directory}" for feature, directory in case["sources"].items()
    )]
    if mode == "build-root":
        argv = [mode, "--repo", str(case["repo"]), "--calibration-sha", case["calibration"],
                "--doc", "d1", "--purpose", "s1", *sources]
        if dest:
            argv += ["--dest-parent", str(case["roots"])]
    elif mode in ("main-leak", "rescore"):
        argv = _branch_argv(case, mode, work=False)
    elif mode == "check-ledger-repo":
        argv = ["check-ledger", "--repo", str(case["repo"]),
                "--calibration-sha", case["calibration"], *sources]
    elif mode == "extract-repo":
        argv = ["extract", "--repo", str(case["repo"]), "--base-sha", case["score"],
                "--s2", str(case["s2"]), "--shuffle-seed", "1729",
                "--out", str(case["work_dir"].parent / "task24-extracted"), *sources]
    else:
        raise AssertionError(f"unknown Task 24 fixture mode: {mode}")
    if work:
        argv += ["--work-dir", str(case["work_dir"])]
    return argv


def _task24_run(case, argv, capsys):
    capsys.readouterr()
    rc = case["probe"].main(argv)
    out, err = capsys.readouterr()
    return subprocess.CompletedProcess(argv, rc, out, err)


def test_dest_parent_must_be_a_directory(task24_case, tmp_path, capsys, monkeypatch):
    case = task24_case
    ordinary_file = tmp_path / "parent [a]* ⟦h-mad⟧.txt"
    ordinary_file.write_text(_hostile_text(), encoding="utf-8")
    for parent in (ordinary_file, tmp_path / "missing-parent", Path("relative-parent")):
        argv = _task24_argv(case, "build-root", dest=False) + ["--dest-parent", str(parent)]
        result = _task24_run(case, argv, capsys)
        _assert_root_refusal(result, "internal:ParentNotDirectory",
                             "--dest-parent must be an absolute existing directory")
    # Relative existing directories and None must take the same declared guard.
    monkeypatch.chdir(tmp_path)
    (tmp_path / "relative-parent").mkdir()
    for parent in (None, "relative-parent", str(ordinary_file), str(tmp_path / "missing-parent")):
        with pytest.raises(case["probe"].ParentNotDirectory):
            case["probe"].checked_parent(parent, git_guard=False)


def test_dest_parent_in_system_temp_refuses(task24_case, tmp_path, capsys):
    case = task24_case
    link = tmp_path / "temp-link [a]* ⟦h-mad⟧"
    link.symlink_to(case["systemp"], target_is_directory=True)
    nested = case["systemp"] / "nested"
    nested.mkdir()
    for parent in (case["systemp"], nested, link, Path("/tmp"), Path("/private/tmp")):
        argv = _task24_argv(case, "build-root", dest=False) + ["--dest-parent", str(parent)]
        result = _task24_run(case, argv, capsys)
        _assert_root_refusal(result, "internal:ParentInSystemTemp",
                             "resolved --dest-parent must lie outside every system-temp root")


def test_work_dir_in_system_temp_refuses(task24_case, capsys):
    case = task24_case
    for work_dir in (case["systemp"], Path("/tmp"), Path("/private/tmp")):
        argv = _task24_argv(case, "build-root", work=False) + ["--work-dir", str(work_dir)]
        result = _task24_run(case, argv, capsys)
        _assert_root_refusal(result, "internal:ParentInSystemTemp",
                             "--work-dir must be checked before any scratch allocation")


def test_work_dir_in_a_git_work_tree_refuses(task24_case, capsys, monkeypatch):
    case = task24_case
    nested = case["repo"] / "scratch [a]* ⟦h-mad⟧"
    nested.mkdir()
    # D7 must ignore inherited Git context while deciding the actual work directory.
    monkeypatch.setenv("GIT_DIR", str(case["work_dir"] / "absent.git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(case["work_dir"]))
    for work_dir in (case["repo"], nested):
        argv = _task24_argv(case, "build-root", work=False) + ["--work-dir", str(work_dir)]
        result = _task24_run(case, argv, capsys)
        _assert_root_refusal(result, "internal:WorkDirInGitTree",
                             "--work-dir must reject both a Git work tree and its descendants")


def test_build_root_requires_a_parent(task24_case, capsys):
    result = _task24_run(task24_case, _task24_argv(task24_case, "build-root", dest=False), capsys)
    _assert_root_refusal(result, "internal:UsageError",
                         "build-root requires one of --dest-parent and --reset")
    assert "--dest-parent" in result.stderr and "--reset" in result.stderr, (
        "parser.error must diagnose the missing parent pair, rather than rejecting --work-dir: "
        f"{result.stderr!r}"
    )
    assert "unrecognized arguments" not in result.stderr, "the declared --work-dir flag must parse"


@pytest.mark.parametrize("site", ["ledger-tree", "ledger-repo", "root", "extract", "main-leak", "rescore"])
def test_every_scratch_dir_lies_under_the_work_dir(site, task24_case, monkeypatch, capsys):
    case, recorded = task24_case, []
    real_mkdtemp, real_temporary_directory = tempfile.mkdtemp, tempfile.TemporaryDirectory

    def record_mkdtemp(*args, **kwargs):
        path = real_mkdtemp(*args, **kwargs)
        # Python 3.11's TemporaryDirectory forwards dir as mkdtemp's third argument.
        parent = kwargs.get("dir", args[2] if len(args) > 2 else None)
        recorded.append(("mkdtemp", Path(path).resolve(), parent))
        return path

    def record_temporary_directory(*args, **kwargs):
        directory = real_temporary_directory(*args, **kwargs)
        recorded.append(("TemporaryDirectory", Path(directory.name).resolve(), kwargs.get("dir")))
        return directory

    monkeypatch.setattr(case["probe"].tempfile, "mkdtemp", record_mkdtemp)
    monkeypatch.setattr(case["probe"].tempfile, "TemporaryDirectory", record_temporary_directory)
    mode = {"ledger-tree": "build-root", "ledger-repo": "check-ledger-repo",
            "root": "build-root", "extract": "extract-repo"}.get(site, site)
    result = _task24_run(case, _task24_argv(case, mode), capsys)
    assert result.returncode == 0, (
        f"{site}: exercise the real allocation path before checking its scratch parent; "
        f"stdout={result.stdout!r}; stderr={result.stderr!r}"
    )
    prefix = {"ledger-tree": "gas-ledger-", "ledger-repo": "gas-ledger-",
              "root": "gas-root-", "extract": "gas-extract-",
              "main-leak": "gas-main-leak-", "rescore": "gas-rescore-"}[site]
    assert any(path.name.startswith(prefix) for _kind, path, _parent in recorded), (
        f"{site}: the designated scratch site must actually allocate a directory"
    )
    assert {kind for kind, _path, _parent in recorded} >= {"mkdtemp", "TemporaryDirectory"}, (
        f"{site}: both tempfile entry points must be observed on the real mode path"
    )
    for kind, path, supplied_parent in recorded:
        expected = case["roots"] if mode == "build-root" and path.name.startswith("gas-root-") else case["work_dir"]
        assert supplied_parent is not None and path.is_relative_to(expected.resolve()), (
            f"{site}: every {kind} scratch directory must receive dir= under {expected}; "
            f"allocated {path} with dir={supplied_parent!r}"
        )


def test_build_root_reset_refuses_a_target_outside_a_roots_dir(task24_case, tmp_path, capsys):
    case = task24_case
    target = tmp_path / "other" / "gas-root-d1-s1-x"
    target.mkdir(parents=True)
    sentinel, content = _reset_sentinel(target)
    argv = _task24_argv(case, "build-root", dest=False) + ["--reset", str(target)]
    result = _task24_run(case, argv, capsys)

    assert (result.returncode, result.stdout.splitlines()[-1:]) == (
        2, ["ROOT: UNREADABLE reason=internal:ResetTargetOutsideRoots"],
    ), f"reset must require the resolved parent to be named roots: {result.stdout!r}; {result.stderr}"
    assert sentinel.read_bytes() == content, "a target outside roots must retain its sentinel bytes"
    n = result.stderr.count("Traceback")
    assert n == 0, "a declared roots-parent reset refusal must not print a traceback"


def test_build_root_reset_removes_an_in_root_report_and_tmp(task24_case, capsys):
    case = task24_case
    argv = _task24_argv(case, "build-root")
    built = _task24_run(case, argv, capsys)
    live_fields = _ready_fields(built, "reset report/tmp removal needs a real root outside system temp")
    live = Path(live_fields["path"])
    fresh = _task24_run(case, argv, capsys)
    expected = Path(_ready_fields(fresh, "reset must match a fresh build")["path"])
    stem = "audit_paper-lantern_plan_cycle1_run20990101T010203Z-314"
    paths = [live / ".hmad-report" / f"{stem}_p1.report.md",
             live / "cycle-v1.collected" / f"{stem}_p1.report.md",
             live / ".tmp" / "staged prompt [a]* ⟦h-mad⟧.txt"]
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_hostile_text(), encoding="utf-8")
    reset_argv = _task24_argv(case, "build-root", dest=False) + ["--reset", str(live)]
    result = _task24_run(case, reset_argv, capsys)
    assert (result.returncode, result.stdout.splitlines()[-1:]) == (
        0, [built.stdout.splitlines()[-1]],
    ), f"reset must remove in-root reports and staged prompts: {result.stdout!r}; {result.stderr}"
    assert all(not path.exists() for path in paths), "reset must remove the report, collected copy and staged prompt"
    assert not (live / ".tmp").exists(), "reset must remove the staged-prompt directory itself"
    assert _reset_manifest(live) == _reset_manifest(expected), (
        "reset must leave exactly a fresh build's paths, types and bytes, including removal of dot entries"
    )


@pytest.mark.parametrize("mode", ["build-root", "main-leak", "rescore", "check-ledger-repo", "extract-repo"])
def test_work_dir_is_required_where_a_directory_is_created(mode, task24_case, capsys):
    argv = _task24_argv(task24_case, mode, work=False)
    result = _task24_run(task24_case, argv, capsys)
    actual_mode = argv[0]
    assert (result.returncode, result.stdout.splitlines()[-1:]) == (
        2, [f"{REFUSALS[actual_mode]} reason=internal:UsageError"],
    ), f"{mode}: main must require --work-dir before allocating a directory: {result.stdout!r}; {result.stderr}"
    assert "--work-dir" in result.stderr, f"{mode}: parser.error must name the missing --work-dir"
    assert "Traceback" not in result.stderr, f"{mode}: a required-work-dir refusal must be declared"


_RESET_DIFFERENTIAL = [
    ("systemp-child", "accepted", "ResetTargetInSystemTemp"),
    ("roots-outside-temp", "ResetTargetOutsideTempdir", "accepted"),
    ("roots-inside-temp", "ResetTargetOutsideTempdir", "ResetTargetInSystemTemp"),
    ("non-roots-parent", "ResetTargetOutsideTempdir", "ResetTargetOutsideRoots"),
    ("wrong-doc-prefix", "ResetTargetOutsideTempdir", "ResetTargetPrefix"),
    ("wrong-purpose-prefix", "ResetTargetOutsideTempdir", "ResetTargetPrefix"),
    ("nested-root", "ResetTargetOutsideTempdir", "ResetTargetOutsideRoots"),
    ("sibling-roots-dir", "ResetTargetOutsideTempdir", "accepted"),
    ("symlink-into-roots", "ResetTargetOutsideTempdir", "accepted"),
    ("symlink-into-temp", "accepted", "ResetTargetInSystemTemp"),
    ("physical-spelling", "ResetTargetOutsideTempdir", "accepted"),
    ("git-target", "ResetTargetOutsideTempdir", "Refusal:root_git:.git"),
    ("git-target-in-temp", "Refusal:root_git:.git", "ResetTargetInSystemTemp"),
    ("empty", "ResetTargetNotAbsolute", "ResetTargetNotAbsolute"),
    ("missing", "ResetTargetNotDirectory", "ResetTargetNotDirectory"),
]


@pytest.mark.parametrize("target_id,old_expected,new_expected", _RESET_DIFFERENTIAL,
                         ids=[row[0] for row in _RESET_DIFFERENTIAL])
def test_reset_precondition_old_new_differential(target_id, old_expected, new_expected,
                                                parent_layout, tmp_path):
    old_source = git(REPO, "show", "66ff0894:docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py")
    assert "    if root.parent != Path(tempfile.gettempdir()).resolve():  # M:GAS-RESET-TMPDIR" in old_source.splitlines(), (
        "the differential's old predicate must be the shipped guard, not a reimplementation"
    )
    old_probe = load_probe(PROBE, source=old_source)
    new_probe = load_probe(PROBE)
    roots, systemp = parent_layout["roots"], parent_layout["systemp"]
    normal = roots / "gas-root-d1-s1-x"
    in_temp = systemp / "gas-root-d1-s1-x"
    targets = {
        "systemp-child": in_temp,
        "roots-outside-temp": normal,
        "roots-inside-temp": systemp / "roots" / "gas-root-d1-s1-x",
        "non-roots-parent": tmp_path / "other" / "gas-root-d1-s1-x",
        "wrong-doc-prefix": roots / "gas-root-d2-s1-x",
        "wrong-purpose-prefix": roots / "gas-root-d1-s2v1-x",
        "nested-root": roots / "gas-root-d1-s1-a" / "gas-root-d1-s1-b",
        "sibling-roots-dir": tmp_path / "other-run" / "roots" / "gas-root-d1-s1-x",
        "git-target": normal,
        "git-target-in-temp": in_temp,
    }
    if target_id == "empty":
        target = ""
    elif target_id == "missing":
        target = str(roots / "gas-root-d1-s1-missing")
        assert not Path(target).exists(), "the missing-target guard fixture must stay absent"
    elif target_id in ("symlink-into-roots", "symlink-into-temp", "physical-spelling"):
        normal.mkdir()
        in_temp.mkdir()
        if target_id == "symlink-into-roots":
            link, destination = systemp / "target-link", normal
            target = str(link)
        elif target_id == "symlink-into-temp":
            link, destination = roots / "target-link", in_temp
            target = str(link)
        else:
            link, destination = tmp_path / "run-link", roots.parent
            target = str(link / "roots" / normal.name)
        link.symlink_to(destination, target_is_directory=True)
    else:
        path = targets[target_id]
        path.mkdir(parents=True)
        if target_id.startswith("git-target"):
            git(path, "init", "--initial-branch=main")
        target = str(path)

    def outcome(probe):
        try:
            return probe.check_reset_target(target, "d1")
        except probe.Refusal as exc:
            return f"Refusal:{exc.reason}"
        except probe.ProbeRefusal as exc:
            return type(exc).__name__

    expected_path = Path(target).resolve()
    wanted = tuple(expected_path if value == "accepted" else value
                   for value in (old_expected, new_expected))
    actual = outcome(old_probe), outcome(new_probe)
    assert actual == wanted, (
        f"{target_id}: reset re-anchoring must preserve the exact shipped/new verdict pair; "
        f"expected {wanted!r}, observed {actual!r}"
    )
    softened = {"roots-outside-temp", "sibling-roots-dir", "symlink-into-roots", "physical-spelling"}
    if isinstance(actual[1], Path) and not isinstance(actual[0], Path):
        assert target_id in softened, "no target outside the four designed cases may become accepted"
        resolved = actual[1]
        assert resolved.parent.name == "roots" and resolved.name.startswith("gas-root-d1-s1-")
        assert not any(resolved.is_relative_to(path.resolve()) for path in (
            systemp, Path("/tmp"), Path("/private/tmp"),
        )), "a softened target must be outside every resolved system-temp root"
        new_probe.reach_check(resolved)


# Task 27: caller-visible containment refusals and published scan lines.
@pytest.fixture
def containment_score_case(tmp_path, monkeypatch):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    probe = load_probe(PROBE)
    case = build_score_inputs(
        tmp_path, probe, surfaces=("codex", "agy", "grok"),
    )
    case["probe"] = probe
    return case


def _t27_log(case, doc, index):
    return case["s2"] / doc / "v1" / f"p{index}.log"


def _t27_tool_call(path, extra=None):
    return grok_tool_call(path, extra=extra)


def _t27_score(case, capsys):
    return _run_score(case, capsys)


def _t27_containment_line(case, doc, index, surface, log_text, *, profile=None):
    import h_mad_tool_calls

    cycle = case["s2"] / doc / "v1"
    root_line = (cycle / f"p{index}.root.txt").read_text(encoding="utf-8")
    root = re.search(r"(?:^| )path=(\S+)", root_line).group(1)
    run = case["s2"] / "run.txt"
    run_text = run.read_text(encoding="utf-8")
    checkout = re.search(r"(?:^| )checkout=(\S+)", run_text).group(1)
    home = re.search(r"(?:^| )home=(\S+)", run_text).group(1)
    scan = h_mad_tool_calls.scan_log(
        log_text, surface, root=root, checkout=checkout, home=home,
        needle_dirs=[f"{directory}/{feature}" for feature, directory in case["sources"].items()],
    )
    tail = (f"mcp_unmeasured={scan['mcp_unmeasured']}" if surface == "codex"
            else f"nonjson={scan['nonjson']}")
    line = (f"CONTAINMENT: {doc}.v1 p{index} surface={surface} scan={scan['word']} "
            f"calls={scan['calls']} out_of_root={scan['out_of_root']} "
            f"checkout={scan['checkout']} exempt={scan['exempt']} {tail}")
    if surface == "grok":
        line += (f" profile={profile['profile']} origin={profile['origin']}"
                 if profile else " profile=none")
    return line


def _t27_assert_containment(case, capsys, expected):
    result = _t27_score(case, capsys)
    lines = result.stdout.splitlines()
    actual = [line for line in lines if line.startswith("CONTAINMENT:")]
    assert actual == expected, (
        f"score must publish the scan_log counts and profile for every standing pass: "
        f"expected={expected!r}; actual={actual!r}; stdout={result.stdout!r}; stderr={result.stderr!r}"
    )
    return result


def _t27_refusal(case, capsys, reason="out_of_root:d1.v1"):
    result = _t27_score(case, capsys)
    expected = f"SEEDSCORE: UNREADABLE reason={reason}"
    assert result.stdout.splitlines()[-1:] == [expected], (
        f"score must refuse for {reason}: stdout={result.stdout!r}; stderr={result.stderr!r}"
    )
    return result


def test_out_of_root_absolute_path_outside_the_root(containment_score_case, capsys):
    case = containment_score_case
    _t27_log(case, "d1", 3).write_text(
        _t27_tool_call("/tmp/hostile-outside [a]* ⟦grok⟧.txt"), encoding="utf-8",
    )
    _t27_refusal(case, capsys)


def test_out_of_root_live_checkout(containment_score_case, capsys):
    case = containment_score_case
    _t27_log(case, "d1", 3).write_text(
        _t27_tool_call("/tmp/grok-audit-checkout/live [a]* ⟦grok⟧.txt"), encoding="utf-8",
    )
    _t27_refusal(case, capsys)


def test_out_of_root_after_a_non_json_line(containment_score_case, capsys):
    case = containment_score_case
    log = _t27_log(case, "d1", 3)
    log.write_text("agent note [a]* ⟦grok⟧\n" + _t27_tool_call("/tmp/escape-after-note.txt"), encoding="utf-8")
    _t27_refusal(case, capsys)


def test_out_of_root_absent_log(containment_score_case, capsys):
    case = containment_score_case
    _t27_log(case, "d1", 3).unlink()
    _t27_refusal(case, capsys)


def test_out_of_root_log_without_event(containment_score_case, capsys):
    case = containment_score_case
    _t27_log(case, "d1", 3).write_text("not-json [a]* ⟦grok⟧\n", encoding="utf-8")
    _t27_refusal(case, capsys)


def test_out_of_root_on_a_non_standing_cycle(containment_score_case, capsys):
    case = containment_score_case
    cycle = case["s2"] / "d2/v1"
    audit = cycle / "auditcycle.txt"
    audit.write_text(audit.read_text(encoding="utf-8").replace(
        "AUDITCYCLE: PASS", "AUDITCYCLE: UNVERIFIED reason=halted", 1), encoding="utf-8",
    )
    # A valid v2 stands for d2, so only the non-standing v1's grok scan can refuse.
    write_extract_cycle(case, doc="d2", cycle=2, deliveries=("none", "none", "none"),
                        surfaces=("codex", "agy", "grok"))
    _t27_log(case, "d2", 3).write_text(_t27_tool_call("/tmp/non-standing-escape.txt"), encoding="utf-8")
    _t27_refusal(case, capsys, "out_of_root:d2.v1")


def test_out_of_root_other_session_dir(containment_score_case, capsys):
    case = containment_score_case
    _t27_log(case, "d1", 3).write_text(_t27_tool_call(
        "/tmp/grok-audit-home/.grok/sessions/another-session/notes.txt"), encoding="utf-8")
    _t27_refusal(case, capsys)


def test_out_of_root_sessions_dir_itself(containment_score_case, capsys):
    case = containment_score_case
    _t27_log(case, "d1", 3).write_text(_t27_tool_call(
        "/tmp/grok-audit-home/.grok/sessions"), encoding="utf-8")
    _t27_refusal(case, capsys)


def test_out_of_root_other_grok_path(containment_score_case, capsys):
    case = containment_score_case
    _t27_log(case, "d1", 3).write_text(_t27_tool_call(
        "/tmp/grok-audit-home/.grok/other [a]* ⟦grok⟧/file.txt"), encoding="utf-8")
    _t27_refusal(case, capsys)


def test_out_of_root_mixed_exempt_and_outside(containment_score_case, capsys):
    case = containment_score_case
    _t27_log(case, "d1", 3).write_text(
        _t27_tool_call("/dev/null", "/tmp/mixed-escape.txt"), encoding="utf-8",
    )
    _t27_refusal(case, capsys)


def _t27_assert_not_refused(case, capsys, expected_line):
    result = _t27_score(case, capsys)
    assert result.stdout.splitlines()[-1].startswith("SEEDSCORE: ") and "UNREADABLE" not in result.stdout.splitlines()[-1], (
        f"this scan must not refuse score: stdout={result.stdout!r}; stderr={result.stderr!r}"
    )
    assert expected_line in result.stdout.splitlines(), (
        f"score must publish the scan count beside its successful token: {expected_line!r}; "
        f"stdout={result.stdout!r}"
    )


def test_clean_grok_log_does_not_refuse(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    probe = load_probe(PROBE)
    try:
        case = build_score_inputs(
            tmp_path, probe, surfaces=("codex", "agy", "grok"),
        )
        case["probe"] = probe
    except probe.Refusal as exc:
        pytest.fail(f"a clean grok log must not refuse extraction: {exc.reason}")
    log = _t27_log(case, "d1", 3)
    log.write_text(json.dumps({"type": "text", "data": _hostile_text()}) + "\n", encoding="utf-8")
    _t27_assert_not_refused(case, capsys, _t27_containment_line(case, "d1", 3, "grok", log.read_text()))


def test_exempt_dev_path_does_not_refuse(containment_score_case, capsys):
    case = containment_score_case
    log = _t27_log(case, "d1", 3)
    log.write_text(_t27_tool_call("/dev/null"), encoding="utf-8")
    _t27_assert_not_refused(case, capsys, _t27_containment_line(case, "d1", 3, "grok", log.read_text()))


@pytest.mark.parametrize("spelling", ["absolute", "tilde", "home", "brace"])
def test_exempt_own_session_dir_does_not_refuse(spelling, containment_score_case, capsys):
    from urllib.parse import quote
    case = containment_score_case
    root_line = (case["s2"] / "d1/v1/p3.root.txt").read_text(encoding="utf-8")
    root = re.search(r"(?:^| )path=(\S+)", root_line).group(1)
    home = "/tmp/grok-audit-home"
    own = f"{home}/.grok/sessions/{quote(root, safe='')}/memo.txt"
    values = {"absolute": own, "tilde": own.replace(home + "/", "~/"),
              "home": own.replace(home + "/", "$HOME/"),
              "brace": own.replace(home + "/", "${HOME}/")}
    log = _t27_log(case, "d1", 3)
    log.write_text(_t27_tool_call(values[spelling]), encoding="utf-8")
    _t27_assert_not_refused(case, capsys, _t27_containment_line(case, "d1", 3, "grok", log.read_text()))


@pytest.mark.parametrize("spelling", ["absolute", "tilde", "home", "brace"])
def test_exempt_grok_skills_does_not_refuse(spelling, containment_score_case, capsys):
    case = containment_score_case
    absolute = "/tmp/grok-audit-home/.grok/skills/guide [a]* ⟦grok⟧.md"
    values = {"absolute": absolute, "tilde": absolute.replace("/tmp/grok-audit-home/", "~/"),
              "home": absolute.replace("/tmp/grok-audit-home/", "$HOME/"),
              "brace": absolute.replace("/tmp/grok-audit-home/", "${HOME}/")}
    log = _t27_log(case, "d1", 3)
    log.write_text(_t27_tool_call(values[spelling]), encoding="utf-8")
    _t27_assert_not_refused(case, capsys, _t27_containment_line(case, "d1", 3, "grok", log.read_text()))


def test_codex_or_agy_count_does_not_refuse(containment_score_case, capsys):
    case = containment_score_case
    codex = _t27_log(case, "d1", 1)
    codex.write_text("exec\ncat /tmp/grok-audit-home/.grok/sessions/own-session/file.txt\n succeeded 0\n", encoding="utf-8")
    agy = _t27_log(case, "d1", 2)
    agy.write_text(json.dumps({"event": "step_update", "step_update": {
        "conversation_id": "hostile [a]* ⟦agy⟧", "step_index": 7, "step_type": "tool",
        "tool_info": {"parameters": {"path": "$HOME/.grok/skills/guide.md"}},
    }}) + "\n", encoding="utf-8")
    expected = [
        _t27_containment_line(case, "d1", 1, "codex", codex.read_text()),
        _t27_containment_line(case, "d1", 2, "agy", agy.read_text()),
    ]
    result = _t27_score(case, capsys)
    assert result.stdout.splitlines()[-1].startswith("SEEDSCORE: ") and "UNREADABLE" not in result.stdout.splitlines()[-1], result.stdout
    lines = result.stdout.splitlines()
    assert all(line in lines for line in expected), f"codex/agy scans count outside paths without refusing: {expected!r}; {lines!r}"


def test_containment_lines_name_every_standing_pass(containment_score_case, capsys):
    case = containment_score_case
    log = _t27_log(case, "d1", 3)
    log.write_text(_t27_tool_call("~/../../dev/null"), encoding="utf-8")
    # Non-zero checkout counts on both legs (checkout= and a needle dir) and one recorded profile.
    _t27_log(case, "d1", 1).write_text(
        "exec\ncat /tmp/grok-audit-checkout/answer [a]* key.md\n succeeded 0\n", encoding="utf-8")
    feature, directory = next(iter(case["sources"].items()))
    _t27_log(case, "d1", 2).write_text(json.dumps({"event": "step_update", "step_update": {
        "conversation_id": "c", "step_index": 1, "step_type": "tool",
        "tool_info": {"parameters": {"path": f"/elsewhere/{directory}/{feature}/x.md"}},
    }}) + "\n", encoding="utf-8")
    (case["s2"] / "d2/v1/p3.profile.txt").write_text(
        "GROK-PROFILE: profile=audit-ro origin=override\n", encoding="utf-8")
    expected = []
    for number in range(1, 10):
        for index, surface in enumerate(("codex", "agy", "grok"), 1):
            current = _t27_log(case, f"d{number}", index)
            profile = None
            profile_path = current.parent / f"p{index}.profile.txt"
            if surface == "grok" and profile_path.exists():
                parsed = case["probe"].parse_profile_line(profile_path.read_text(encoding="utf-8"))
                profile = parsed
            expected.append(_t27_containment_line(case, f"d{number}", index, surface,
                                                  current.read_text(encoding="utf-8"), profile=profile))
    _t27_assert_containment(case, capsys, expected)


def test_containment_line_profile_none_without_record(containment_score_case, capsys):
    case = containment_score_case
    profile = case["s2"] / "d1/v1/p3.profile.txt"
    profile.unlink(missing_ok=True)
    result = _t27_score(case, capsys)
    lines = [line for line in result.stdout.splitlines() if line.startswith("CONTAINMENT: d1.v1 p3 ")]
    assert len(lines) == 1 and lines[0].endswith("profile=none"), (
        f"missing or unparseable profile must publish profile=none: {lines!r}; stdout={result.stdout!r}"
    )


def test_containment_lines_never_move_the_verdict(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    probe = load_probe(PROBE)
    case = build_score_inputs(tmp_path, probe, surfaces=("codex", "agy", "grok"))
    log = _t27_log(case, "d1", 3)
    log.write_text(json.dumps({"type": "text", "data": "clean"}) + "\n", encoding="utf-8")
    left = _t27_score(case, capsys)
    log.write_text(_t27_tool_call("/dev/null"), encoding="utf-8")
    right = _t27_score(case, capsys)
    left_score = left.stdout.splitlines()[-1]
    right_score = right.stdout.splitlines()[-1]
    assert left_score == right_score and left_score.startswith("SEEDSCORE: "), (
        f"equal score labels must produce the same verdict token despite different scans: {left_score!r} / {right_score!r}"
    )
    left_lines = [line for line in left.stdout.splitlines() if line.startswith("CONTAINMENT:")]
    right_lines = [line for line in right.stdout.splitlines() if line.startswith("CONTAINMENT:")]
    assert left_lines != right_lines, "different scan counts must change containment lines without changing SEEDSCORE"
