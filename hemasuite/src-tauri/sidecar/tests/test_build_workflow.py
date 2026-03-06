"""
Build Workflow Validation Tests (Task 5.3)

TDD: Verify the unified build-and-sign script exists with correct
structure for the full build → sign → notarize pipeline.
"""
import os
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "scripts"


class TestBuildScript:
    """Validate unified build-and-sign.sh script."""

    script_path = SCRIPTS_DIR / "build-and-sign.sh"

    def test_build_script_exists(self):
        assert self.script_path.exists(), (
            f"build-and-sign.sh not found at {self.script_path}"
        )

    def test_build_script_is_executable(self):
        assert os.access(self.script_path, os.X_OK)

    def test_build_script_has_tauri_build_step(self):
        content = self.script_path.read_text()
        assert "tauri build" in content

    def test_build_script_calls_sign_r_dylibs(self):
        content = self.script_path.read_text()
        assert "sign-r-dylibs" in content

    def test_build_script_calls_codesign(self):
        content = self.script_path.read_text()
        assert "codesign" in content

    def test_build_script_calls_notarytool(self):
        content = self.script_path.read_text()
        assert "notarytool" in content

    def test_build_script_validates_env_vars(self):
        """Must check for required signing identity and Apple ID."""
        content = self.script_path.read_text()
        assert "APPLE_SIGNING_IDENTITY" in content or "SIGNING_IDENTITY" in content

    def test_build_script_has_dry_run_mode(self):
        """Should support --dry-run to test without signing."""
        content = self.script_path.read_text()
        assert "dry-run" in content or "DRY_RUN" in content

    def test_build_script_uses_strict_mode(self):
        content = self.script_path.read_text()
        assert "set -euo pipefail" in content

    def test_build_script_supports_universal_binary(self):
        """Build script must default to universal-apple-darwin target."""
        content = self.script_path.read_text()
        assert "universal-apple-darwin" in content
