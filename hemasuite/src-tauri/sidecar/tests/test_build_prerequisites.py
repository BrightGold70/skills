"""
Build Prerequisites Validation Tests (Task 5.2)

TDD: Verify that Entitlements.plist and signing script exist
with correct content before building the DMG.
"""
import os
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

TAURI_DIR = Path(__file__).resolve().parents[2]


class TestEntitlementsPlist:
    """Validate Entitlements.plist exists and has required keys."""

    plist_path = TAURI_DIR / "Entitlements.plist"

    def test_entitlements_file_exists(self):
        assert self.plist_path.exists(), (
            f"Entitlements.plist not found at {self.plist_path}"
        )

    def test_entitlements_is_valid_xml(self):
        tree = ET.parse(self.plist_path)
        root = tree.getroot()
        assert root.tag == "plist"

    def test_entitlements_allows_unsigned_executable_memory(self):
        keys = self._parse_keys()
        assert "com.apple.security.cs.allow-unsigned-executable-memory" in keys

    def test_entitlements_disables_library_validation(self):
        keys = self._parse_keys()
        assert "com.apple.security.cs.disable-library-validation" in keys

    def test_entitlements_allows_network_client(self):
        keys = self._parse_keys()
        assert "com.apple.security.network.client" in keys

    def test_entitlements_allows_user_file_access(self):
        keys = self._parse_keys()
        assert "com.apple.security.files.user-selected.read-write" in keys

    def _parse_keys(self) -> set[str]:
        tree = ET.parse(self.plist_path)
        dict_elem = tree.find(".//dict")
        assert dict_elem is not None
        return {
            elem.text
            for elem in dict_elem.findall("key")
            if elem.text is not None
        }


class TestSigningScript:
    """Validate R dylib signing script exists and is executable."""

    script_path = TAURI_DIR.parent / "scripts" / "sign-r-dylibs.sh"

    def test_signing_script_exists(self):
        assert self.script_path.exists(), (
            f"sign-r-dylibs.sh not found at {self.script_path}"
        )

    def test_signing_script_is_executable(self):
        assert os.access(self.script_path, os.X_OK)

    def test_signing_script_uses_entitlements(self):
        content = self.script_path.read_text()
        assert "Entitlements.plist" in content

    def test_signing_script_finds_dylibs(self):
        content = self.script_path.read_text()
        assert "*.dylib" in content or "*.so" in content
