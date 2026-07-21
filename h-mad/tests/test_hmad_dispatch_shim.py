"""Tests for the bin/hmad-dispatch shim.

The docs spell the wrapper as a bare `hmad-dispatch <verb>` in 31 places, but
the implementation lives at scripts/hmad-dispatch.sh, so every real call had to
re-derive an absolute path that varies per install and per checkout. The shim
closes that gap; these tests pin that it forwards faithfully and stays
location-independent.
"""

import os
import shutil
import subprocess
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SHIM = SKILL_ROOT / "bin" / "hmad-dispatch"
REAL = SKILL_ROOT / "scripts" / "hmad-dispatch.sh"


def run(args, **kw):
    return subprocess.run(
        [str(SHIM), *args], capture_output=True, text=True, **kw
    )


class TestShimExists:
    def test_shim_is_present_and_executable(self):
        assert SHIM.exists(), f"{SHIM} missing"
        assert os.access(SHIM, os.X_OK), f"{SHIM} not executable"

    def test_target_script_is_present_and_executable(self):
        assert REAL.exists()
        assert os.access(REAL, os.X_OK)


class TestForwarding:
    def test_usage_matches_the_real_script(self):
        """No args: shim output must be identical to calling the script."""
        via_shim = run([])
        direct = subprocess.run(
            ["bash", str(REAL)], capture_output=True, text=True
        )
        assert via_shim.returncode == direct.returncode
        assert via_shim.stdout == direct.stdout
        assert via_shim.stderr == direct.stderr

    def test_unknown_verb_forwards_exit_code(self):
        via_shim = run(["definitely-not-a-verb"])
        direct = subprocess.run(
            ["bash", str(REAL), "definitely-not-a-verb"],
            capture_output=True,
            text=True,
        )
        assert via_shim.returncode == direct.returncode
        assert via_shim.stdout == direct.stdout

    def test_arguments_with_spaces_survive(self):
        """Quoting regression: args must not be re-split by the shim."""
        via_shim = run(["notify", "a title", "a body with spaces"])
        direct = subprocess.run(
            ["bash", str(REAL), "notify", "a title", "a body with spaces"],
            capture_output=True,
            text=True,
        )
        assert via_shim.returncode == direct.returncode
        assert via_shim.stdout == direct.stdout


class TestLocationIndependence:
    def test_works_from_an_unrelated_cwd(self, tmp_path):
        r = subprocess.run(
            [str(SHIM)], capture_output=True, text=True, cwd=tmp_path
        )
        # Reached the real script (its own error), not the shim's
        # "cannot find scripts/hmad-dispatch.sh" bail-out.
        assert r.returncode == 2
        assert "unknown verb" in (r.stdout + r.stderr).lower()
        assert "cannot find" not in (r.stdout + r.stderr).lower()

    def test_resolves_through_a_symlink_on_path(self, tmp_path):
        """The real install is a symlink chain (~/.claude/skills/h-mad ->
        a checkout), so the shim must resolve its own physical location."""
        bindir = tmp_path / "bin"
        bindir.mkdir()
        link = bindir / "hmad-dispatch"
        link.symlink_to(SHIM)

        env = dict(os.environ, PATH=f"{bindir}:{os.environ['PATH']}")
        resolved = shutil.which("hmad-dispatch", path=env["PATH"])
        assert resolved == str(link)

        r = subprocess.run(
            ["hmad-dispatch"],
            capture_output=True,
            text=True,
            env=env,
            cwd=tmp_path,
        )
        assert r.returncode == 2
        assert "unknown verb" in (r.stdout + r.stderr).lower()
        assert "cannot find" not in (r.stdout + r.stderr).lower()
