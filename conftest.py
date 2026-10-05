"""Every pytest session over this repository takes the working-tree lock.

pytest loads a rootdir conftest up front for EVERY invocation under the rootdir
(`pytest.ini` lives here), so this is the one place the lock can be taken for
bare `pytest`, `pytest handoff/tests`, a single `handoff/scripts` file and
`pytest .` alike. A conftest under `h-mad/tests` alone missed all but the first
(review M1 of a9ad4d22). The mechanism itself is `h-mad/tests/tree_lock_plugin.py`;
`h-mad/tests/conftest.py` registers the same plugin for install-path runs, and a
second registration is a no-op.

Nothing else belongs here: this file is imported by every test session in the
repository, so it defines no fixtures and imports nothing at module level.
"""


def pytest_configure(config):
    import importlib.util
    import sys
    from pathlib import Path

    name = "_h_mad_tree_lock_plugin"
    plugin = sys.modules.get(name)
    if plugin is None:
        path = Path(__file__).resolve().parent / "h-mad" / "tests" / "tree_lock_plugin.py"
        if not path.is_file():
            return
        spec = importlib.util.spec_from_file_location(name, path)
        plugin = importlib.util.module_from_spec(spec)
        sys.modules[name] = plugin
        spec.loader.exec_module(plugin)
    plugin.register(config)
