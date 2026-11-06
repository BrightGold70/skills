"""The shared doc-data definition and path exemption contract."""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest


@pytest.fixture
def identity(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    return importlib.import_module("h_mad_target_identity")


@pytest.fixture(autouse=True)
def hostile_stub_input(monkeypatch):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")


def test_doc_data_suffixes_are_the_spec_nine(identity):
    assert identity.DOC_DATA_SUFFIXES == (
        ".md", ".yaml", ".yml", ".json", ".toml", ".txt", ".rst", ".cfg", ".ini",
    ), "DOC_DATA_SUFFIXES must contain exactly the spec's nine suffixes in order"


@pytest.mark.parametrize(
    "name",
    ["README.md", "NOTES.MD", "Config.Json", "a.tar.md", ".md"],
    ids=["lower", "upper", "mixed", "tar-md", "dotfile"],
)
def test_has_doc_data_suffix_accepts(identity, name):
    assert identity.has_doc_data_suffix(name) is True, (
        f"doc-data suffix matching must accept the ASCII-case suffix of {name!r}"
    )


@pytest.mark.parametrize(
    "name",
    ["x.md.sh", "x.mdx", "x.jsonl", "Makefile", "x.sh"],
    ids=["md-then-sh", "mdx", "jsonl", "makefile", "sh"],
)
def test_has_doc_data_suffix_rejects(identity, name):
    assert identity.has_doc_data_suffix(name) is False, (
        f"doc-data suffix matching must reject {name!r} without an exact final suffix"
    )


def test_is_doc_data_requires_every_name(identity):
    assert identity.is_doc_data(("x.md", "x.sh")) is False, (
        "doc-data classification must reject a collection containing a non-doc-data name"
    )
    assert identity.is_doc_data(("x.md", "y.json")) is True, (
        "doc-data classification must accept a collection when every name qualifies"
    )


def test_is_doc_data_is_vacuously_true_for_no_names(identity):
    assert identity.is_doc_data(()) is True, (
        "doc-data classification must be vacuously true for an identity with no names"
    )


@pytest.mark.parametrize(
    "names,expected",
    [(("x.md", "y.json"), "docdata yes\n"), (("x.md", "x.sh"), "docdata no\n")],
    ids=["yes", "no"],
)
def test_emit_doc_data_prints_exactly_one_line(identity, capsys, names, expected):
    resolved = identity.Identity("/repo", "/repo/x.md", "/repo", names, False, 0, "")
    identity.emit_doc_data(resolved)
    captured = capsys.readouterr()
    assert captured.out == expected, (
        "emit_doc_data must print exactly one docdata yes/no line from the identity names"
    )


@pytest.mark.parametrize(
    "directory",
    ["docs", "tests", "a/tests/b", "fixtures", "src/docs", "docs.py", ""],
    ids=["docs", "tests", "a-tests-b", "fixtures", "src-docs", "docs-py", "root"],
)
def test_is_exempt_location_matches_is_production_python(identity, directory):
    relative = f"{directory}/m.py" if directory else "m.py"
    assert identity._is_production_python(relative) == (
        not identity._is_exempt_location(relative)
    ), f"path exemption for {relative!r} must match the existing production-Python path rule"


def test_is_exempt_location_keeps_a_file_named_tests_non_exempt(identity):
    for relative in ("scripts/tests", "tests"):
        assert identity._is_exempt_location(relative) is False, (
            f"path exemption must inspect parents only; file {relative!r} is not exempt"
        )
