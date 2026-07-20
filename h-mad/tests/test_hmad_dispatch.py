import os
import subprocess
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
WRAPPER = SKILL / "scripts" / "hmad-dispatch.sh"
STUBS = SKILL / "tests" / "stubs"


def run(args, *, substrate=None, path_has=("cmux", "orca"), env=None, capture=None):
    """Invoke the wrapper with only the named stub binaries on PATH."""
    bindir = Path(env["_BINDIR"]) if env and "_BINDIR" in env else None
    e = dict(os.environ)
    e.pop("HMAD_SUBSTRATE", None)
    if substrate:
        e["HMAD_SUBSTRATE"] = substrate
    if capture:
        e["HMAD_STUB_CAPTURE"] = str(capture)
    if env:
        e.update({k: v for k, v in env.items() if k != "_BINDIR"})
    # Build an isolated PATH containing only the requested stubs (+ real jq/coreutils).
    # Deliberately excludes the ambient PATH: dev/CI machines may have real
    # cmux/orca binaries installed (e.g. under /opt/homebrew/bin), which would
    # leak into `command -v` lookups and defeat the bindir-only isolation this
    # helper exists to provide.
    e["PATH"] = f"{bindir}:/usr/bin:/bin" if bindir else os.environ["PATH"]
    return subprocess.run(["bash", str(WRAPPER), *args], capture_output=True, text=True, env=e)


def _bindir(tmp_path, names):
    """Create a bin dir symlinking only the requested stub names."""
    b = tmp_path / "bin"
    b.mkdir()
    for n in names:
        (b / n).symlink_to(STUBS / n)
    return b


def test_env_reports_override(tmp_path):
    b = _bindir(tmp_path, ["cmux", "orca"])
    r = run(["env"], substrate="orca", env={"_BINDIR": b})
    assert r.returncode == 0
    assert "orca" in r.stdout


def test_detect_defaults_cmux_when_only_cmux_present(tmp_path):
    b = _bindir(tmp_path, ["cmux"])
    r = run(["env"], env={"_BINDIR": b})
    assert r.returncode == 0
    assert "cmux" in r.stdout


def test_detect_orca_when_only_orca_present(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    r = run(["env"], env={"_BINDIR": b})
    assert r.returncode == 0
    assert "orca" in r.stdout


def test_both_present_defaults_cmux(tmp_path):
    b = _bindir(tmp_path, ["cmux", "orca"])
    r = run(["env"], env={"_BINDIR": b})
    assert r.returncode == 0
    assert "cmux" in r.stdout


def test_no_substrate_errors(tmp_path):
    b = _bindir(tmp_path, [])
    r = run(["env"], env={"_BINDIR": b})
    assert r.returncode == 1
