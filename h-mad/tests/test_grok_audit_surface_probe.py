"""Task 2: every probe entry-point exit carries its own refusal token."""

import subprocess
import sys
from pathlib import Path

import pytest

from grokauditfixtures import load_probe


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
