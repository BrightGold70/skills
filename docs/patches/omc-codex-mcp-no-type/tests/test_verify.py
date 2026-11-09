"""verify.py must catch a dropped omc-codex-mcp-no-type patch, against fixture roots only.

Every test points apply.py / verify.py at a fake OMC install under tmp_path through
OMC_PATCH_ROOTS, so nothing here reads or writes the host's plugin cache or npm tree.
The fake dist module is a real ESM renderer carrying the exact upstream emission line,
so verify.py's node probe runs against code that genuinely emits `type`.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PATCH_DIR = Path(__file__).resolve().parents[1]
APPLY = PATCH_DIR / "apply.py"
VERIFY = PATCH_DIR / "verify.py"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="verify.py's render probe needs node")

EMIT = "lines.push(`type = ${renderTomlString(%s.type)}`);"

DIST = """\
function renderTomlString(value) { return JSON.stringify(value); }
function renderCodexServerBlock(name, entry) {
    const lines = [`[mcp_servers.${name}]`];
    if (entry.command) { lines.push(`command = ${renderTomlString(entry.command)}`); }
    if (entry.url) { lines.push(`url = ${renderTomlString(entry.url)}`); }
    if (entry.type) {
        %s
    }
    return lines.join("\\n");
}
export function renderManagedCodexMcpBlock(registry) {
    return Object.entries(registry).map(([n, e]) => renderCodexServerBlock(n, e)).join("\\n\\n");
}
""" % (EMIT % "entry")

CLI = """\
"use strict";
function renderTomlString(value) { return JSON.stringify(value); }
function renderCodexServerBlock(name, entry2) {
  const lines = [`[mcp_servers.${name}]`];
  if (entry2.type) {
    %s
  }
  return lines.join("\\n");
}
module.exports = { renderCodexServerBlock };
""" % (EMIT % "entry2")


def make_root(tmp_path: Path) -> Path:
    root = tmp_path / "omc"
    (root / "dist/installer").mkdir(parents=True)
    (root / "bridge").mkdir()
    (root / "dist/installer/mcp-registry.js").write_text(DIST)
    (root / "bridge/cli.cjs").write_text(CLI)
    return root


def run(script: Path, roots: str) -> subprocess.CompletedProcess:
    env = dict(os.environ, OMC_PATCH_ROOTS=roots)
    return subprocess.run([sys.executable, str(script)], env=env, capture_output=True,
                          text=True, timeout=60)


def render_type_lines(dist: Path) -> int:
    probe = ("const m = await import(process.argv[1]);"
             "const b = m.renderManagedCodexMcpBlock({s: {command: 'x', type: 'stdio'}});"
             "process.stdout.write(String((b.match(/^type\\s*=/mg) || []).length));")
    out = subprocess.run(["node", "--input-type=module", "-e", probe, str(dist)],
                         capture_output=True, text=True, timeout=30, check=True)
    return int(out.stdout)


def test_fixture_renderer_really_emits_type_before_the_patch(tmp_path):
    # Positive control: without this, a fixture that never emitted `type` would let
    # every "patched" verdict below pass for the wrong reason.
    root = make_root(tmp_path)
    assert render_type_lines(root / "dist/installer/mcp-registry.js") == 1


def test_unpatched_install_is_reported_missing(tmp_path):
    root = make_root(tmp_path)
    r = run(VERIFY, str(root))
    assert r.returncode == 1, r.stdout + r.stderr
    assert "VERIFY: MISSING" in r.stdout


def test_apply_then_verify_passes(tmp_path):
    root = make_root(tmp_path)
    assert run(APPLY, str(root)).returncode == 0
    assert render_type_lines(root / "dist/installer/mcp-registry.js") == 0
    r = run(VERIFY, str(root))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "VERIFY: OK files=2" in r.stdout


def test_dropped_patch_in_the_bundle_alone_is_reported_missing(tmp_path):
    # The discriminating case. dist stays patched, so the render probe passes; only
    # the static check can see that bridge/cli.cjs went back to the upstream text,
    # which is what a plugin or npm reinstall does.
    root = make_root(tmp_path)
    assert run(APPLY, str(root)).returncode == 0
    (root / "bridge/cli.cjs").write_text(CLI)
    r = run(VERIFY, str(root))
    assert r.returncode == 1, r.stdout + r.stderr
    assert "VERIFY: MISSING" in r.stdout
    assert str(root / "bridge/cli.cjs") in r.stdout
    assert "mcp-registry.js" not in r.stdout


def test_render_probe_catches_an_emission_the_regex_does_not_know(tmp_path):
    # Marker present, so the static check passes; a second, differently spelled
    # emission (say, upstream added one) still writes `type`. Only the probe sees it.
    root = make_root(tmp_path)
    assert run(APPLY, str(root)).returncode == 0
    dist = root / "dist/installer/mcp-registry.js"
    dist.write_text(dist.read_text().replace(
        "return lines.join", 'if (entry.type) lines.push("type = " + renderTomlString(entry.type));\n    return lines.join', 1))
    assert render_type_lines(dist) == 1
    r = run(VERIFY, str(root))
    assert r.returncode == 1, r.stdout + r.stderr
    assert "(renderer still emits" in r.stdout  # one line per probe server
    assert "cli.cjs" not in r.stdout


def test_no_roots_is_unreadable_not_a_pass():
    r = run(VERIFY, "")
    assert r.returncode == 2
    assert "VERIFY: UNREADABLE" in r.stdout


def test_an_upstream_fix_without_the_marker_reads_missing(tmp_path):
    # Deliberate: a fixed upstream file has neither the emission nor the marker, and
    # verify.py reports MISSING. The README's "Retiring" section relies on this signal.
    root = make_root(tmp_path)
    for rel in ("dist/installer/mcp-registry.js", "bridge/cli.cjs"):
        path = root / rel
        path.write_text(path.read_text().replace(EMIT % "entry2", "").replace(EMIT % "entry", ""))
    r = run(VERIFY, str(root))
    assert r.returncode == 1
    assert "VERIFY: MISSING" in r.stdout
