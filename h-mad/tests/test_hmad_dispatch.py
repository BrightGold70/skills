import os
import shutil
import subprocess
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
WRAPPER = SKILL / "scripts" / "hmad-dispatch.sh"
STUBS = SKILL / "tests" / "stubs"


def run(args, *, substrate=None, env=None, capture=None):
    """Invoke the wrapper with only the named stub binaries on PATH."""
    bindir = Path(env["_BINDIR"]) if env and "_BINDIR" in env else None
    e = dict(os.environ)
    e.pop("HMAD_SUBSTRATE", None)
    # Session-marker env vars checked by _detect_substrate() ABOVE binary
    # presence; must be stripped so an ambient cmux/orca host session doesn't
    # false-resolve substrate detection for stub-only tests.
    e.pop("CMUX", None)
    e.pop("CMUX_PANE", None)
    e.pop("ORCA_SESSION", None)
    e.pop("ORCA_TERMINAL_ID", None)
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
    # Later-task wrappers (identity resolve-from-json, alive) pipe stub
    # output through jq. Provide the real jq under the isolated PATH without
    # widening it to the ambient PATH (which would leak real cmux/orca).
    jq = shutil.which("jq")
    if jq:
        (b / "jq").symlink_to(jq)
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


def test_cmux_identity_defaults(tmp_path):
    b = _bindir(tmp_path, ["cmux"])
    r = run(["env"], substrate="cmux", env={"_BINDIR": b})
    assert "codex -> surface:5" in r.stdout
    assert "agy -> surface:2" in r.stdout


def test_cmux_identity_env_override(tmp_path):
    b = _bindir(tmp_path, ["cmux"])
    r = run(["env"], substrate="cmux",
            env={"_BINDIR": b, "HMAD_CMUX_CODEX_SURFACE": "surface:9"})
    assert "codex -> surface:9" in r.stdout


def test_orca_identity_explicit_pin(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    r = run(["env"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_CODEX_TERMINAL": "t-abc",
                 "HMAD_ORCA_AGY_TERMINAL": "t-def"})
    assert "codex -> t-abc" in r.stdout
    assert "agy -> t-def" in r.stdout


def test_orca_identity_resolves_from_list_json(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    canned = '[{"id":"t-1","command":"codex"},{"id":"t-2","command":"agy --dangerously-skip-permissions"}]'
    r = run(["env"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": canned})
    assert "codex -> t-1" in r.stdout
    assert "agy -> t-2" in r.stdout
