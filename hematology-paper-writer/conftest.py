"""Pytest configuration — adds project root to sys.path for tool imports."""
import sys
from pathlib import Path

_root = Path(__file__).parent
sys.path.insert(0, str(_root))

# The HPW root __init__.py uses relative imports (from .journal_loader import ...)
# that fail when pytest tries to import it as a standalone module via Package.setup().
# Monkey-patch Package.setup to skip the HPW root package init, which has no
# test setup/teardown functions anyway.
from _pytest import python as _pytest_python

_orig_package_setup = _pytest_python.Package.setup


def _hpw_safe_package_setup(self):
    if self.path == _root:
        return  # Skip the HPW root __init__.py — relative imports break standalone
    _orig_package_setup(self)


_pytest_python.Package.setup = _hpw_safe_package_setup
