"""FR-9 differential corpus: only a new caller with a resolving callee changes."""

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from test_h_mad_new_caller_carveout_copies import CANONICAL


CASES = [
    {
        "name": "new-caller", "missing_symbol": "new_caller", "role": "caller",
        "callee_resolves": True, "exception": "AttributeError",
        "source": "def callee():\n    return 'wired'\n",
    },
    {
        "name": "missing-callee", "missing_symbol": "callee", "role": "callee",
        "callee_resolves": False, "exception": "NameError",
        "source": "def new_caller():\n    return callee()\n",
    },
    {
        "name": "both-missing", "missing_symbol": "new_caller", "role": "caller",
        "callee_resolves": False, "exception": "AttributeError", "source": "",
    },
    {
        "name": "unrelated-import", "missing_symbol": "fr9_unrelated_dependency",
        "role": "unrelated", "callee_resolves": True,
        "exception": "ModuleNotFoundError",
        "source": (
            "def callee():\n    return 'wired'\n"
            "def new_caller():\n    import fr9_unrelated_dependency\n    return callee()\n"
        ),
    },
    {
        "name": "other-symbol", "missing_symbol": "other_symbol", "role": "other",
        "callee_resolves": True, "exception": "NameError",
        "source": (
            "def callee():\n    return 'wired'\n"
            "def new_caller():\n    return other_symbol\n"
        ),
    },
]

MISSING_ERRORS = {"ImportError", "ModuleNotFoundError", "AttributeError", "NameError"}


def old_rule(case):
    """Before FR-9: every missing-symbol RED on the wiring pin is a halt."""
    return "halt" if case["exception"] in MISSING_ERRORS else "valid"


def new_rule(case):
    """FR-9: the missing symbol must be the new caller AND the callee resolve."""
    if case["exception"] not in MISSING_ERRORS:
        return "valid"
    missing_is_caller = case["role"] == "caller"
    callee_resolves = case["callee_resolves"]
    return "valid" if missing_is_caller and callee_resolves else "halt"


def run_corpus(base: Path) -> list[dict]:
    """Build five isolated RED repositories and record executed observations."""
    env = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", HMAD_STUB_HOSTILE="all")
    for key in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTHONPATH"):
        env.pop(key, None)
    rows = []
    for declaration in CASES:
        # Exercise argv/cwd handling with hostile text, without a shell or stubs.
        root = base / "agent [input]* 'quoted'\n<!-- HMAD:marker -->" / declaration["name"]
        root.mkdir(parents=True)
        subprocess.run(
            ["git", "init", "-q", str(root)], env=env, check=True,
            capture_output=True, text=True, timeout=20,
        )
        (root / "fr9_api.py").write_text(declaration["source"], encoding="utf-8")
        (root / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
        (root / "test_pin.py").write_text(
            "import fr9_api\n\n"
            "def test_wire_pin():\n"
            "    assert fr9_api.new_caller() == 'wired'\n",
            encoding="utf-8",
        )
        resolution = subprocess.run(
            [sys.executable, "-c", "import fr9_api; getattr(fr9_api, 'callee'); print('RESOLVED')"],
            cwd=root, env=env, capture_output=True, text=True, timeout=20,
        )
        red = subprocess.run(
            [sys.executable, "-m", "pytest", "test_pin.py", "-v", "--tb=short",
             "-c", "pytest.ini", "--rootdir", str(root), "--confcutdir", str(root),
             "-p", "no:cacheprovider"],
            cwd=root, env=env, capture_output=True, text=True, timeout=30,
        )
        output = red.stdout + red.stderr
        exceptions = re.findall(
            r"^E\s+((?:ImportError|ModuleNotFoundError|AttributeError|NameError):[^\n]*)$",
            output, re.M,
        )
        assert len(exceptions) == 1, (
            f"{declaration['name']}: expected one missing-symbol exception line\n{output}"
        )
        exception_line = exceptions[0]
        row = {
            "name": declaration["name"], "missing_symbol": declaration["missing_symbol"],
            "role": declaration["role"], "exception_line": exception_line,
            "exception": exception_line.split(":", 1)[0],
            "callee_resolves": resolution.returncode == 0,
            "callee_resolution": {
                "returncode": resolution.returncode,
                "stdout": resolution.stdout, "stderr": resolution.stderr,
            },
            "red_returncode": red.returncode, "red_output": output,
        }
        row["old_verdict"] = old_rule(row)
        row["new_verdict"] = new_rule(row)
        rows.append(row)
    return rows


@pytest.fixture(scope="module")
def corpus(tmp_path_factory):
    return run_corpus(tmp_path_factory.mktemp("fr9-corpus"))


@pytest.mark.parametrize("declaration", CASES, ids=[case["name"] for case in CASES])
def test_corpus_case_red_is_real(corpus, declaration):
    row = next(case for case in corpus if case["name"] == declaration["name"])
    assert row["red_returncode"] == 1, f"{row['name']}: fixture pin must be real RED"
    assert re.search(r"\b1 failed\b", row["red_output"]), row["red_output"]
    assert "test_pin.py::test_wire_pin FAILED" in row["red_output"], row["red_output"]
    assert row["exception"] == declaration["exception"], row["exception_line"]
    assert f"'{declaration['missing_symbol']}'" in row["exception_line"], (
        f"{row['name']}: exception must name the declared missing symbol: {row['exception_line']}"
    )
    resolution = row["callee_resolution"]
    assert row["callee_resolves"] is declaration["callee_resolves"], (
        f"{row['name']}: executed callee resolution disagrees with fixture: {resolution}"
    )
    if declaration["callee_resolves"]:
        assert resolution["returncode"] == 0 and resolution["stdout"].strip() == "RESOLVED"
        assert resolution["stderr"] == ""
    else:
        assert resolution["returncode"] == 1, resolution
        assert "AttributeError: module 'fr9_api' has no attribute 'callee'" in resolution["stderr"]


def test_changed_verdicts_are_exactly_new_caller(corpus):
    assert {row["name"] for row in corpus} == {case["name"] for case in CASES}
    assert all(row["old_verdict"] == "halt" for row in corpus), corpus
    changed = {row["name"] for row in corpus if row["old_verdict"] != row["new_verdict"]}
    assert changed == {"new-caller"}, f"FR-9 changed verdicts must be exactly new-caller: {changed}"
    assert next(row for row in corpus if row["name"] == "new-caller")["new_verdict"] == "valid"


def test_transcription_is_tied_to_the_canonical_words():
    assert "the missing symbol is the caller the task creates" in CANONICAL, (
        "FR-9 transcription requires the canonical missing-caller condition"
    )
    assert "the callee resolves at the RED base" in CANONICAL, (
        "FR-9 transcription requires the canonical callee-resolution condition"
    )
