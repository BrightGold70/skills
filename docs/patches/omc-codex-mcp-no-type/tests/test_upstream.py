"""upstream.py must report an unfixed OMC build as EMITS and never mistake doubt for FIXED.

All tests use --from-dir with fixture files, so nothing here touches the network.
The fixtures carry the exact upstream emission line, the same text test_verify.py
uses, so a FIXED verdict below is reached only by removing that line.
"""
import subprocess
import sys
from pathlib import Path

PATCH_DIR = Path(__file__).resolve().parents[1]
UPSTREAM = PATCH_DIR / "upstream.py"

DIST_EMIT = "lines.push(`type = ${renderTomlString(entry.type)}`);"
CLI_EMIT = "lines.push(`type = ${renderTomlString(entry2.type)}`);"

DIST = """\
function renderCodexServerBlock(name, entry) {
    const lines = [`[mcp_servers.${name}]`];
    if (entry.url) { lines.push(`url = ${renderTomlString(entry.url)}`); }
    if (entry.type) {
        %s
    }
    return lines.join("\\n");
}
"""
CLI = DIST.replace("entry", "entry2")


def make(tmp_path: Path, dist: str | None = DIST % DIST_EMIT, cli: str | None = CLI % CLI_EMIT) -> Path:
    d = tmp_path / "tag"
    d.mkdir()
    if dist is not None:
        (d / "mcp-registry.js").write_text(dist)
    if cli is not None:
        (d / "cli.cjs").write_text(cli)
    return d


def run(d: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(UPSTREAM), "--from-dir", str(d)],
                          capture_output=True, text=True, timeout=30)


def test_fixture_cli_really_carries_the_entry2_emission():
    # Positive control: CLI is derived by text replacement; prove it produced the
    # bundle spelling, or the EMITS test could pass on the dist file alone.
    assert (CLI % CLI_EMIT).count(CLI_EMIT) == 1


def test_unfixed_build_reports_emits(tmp_path):
    r = run(make(tmp_path))
    assert r.returncode == 1, r.stdout + r.stderr
    assert r.stdout.startswith("UPSTREAM: EMITS")
    assert "mcp-registry.js emission line x1" in r.stdout
    assert "cli.cjs emission line x1" in r.stdout


def test_emission_in_the_bundle_alone_still_reports_emits(tmp_path):
    # 5.8.3's lesson in reverse: one fixed file does not make the build fixed.
    r = run(make(tmp_path, dist=DIST % ""))
    assert r.returncode == 1, r.stdout + r.stderr
    assert "cli.cjs emission line x1" in r.stdout


def test_fixed_build_reports_fixed(tmp_path):
    r = run(make(tmp_path, dist=DIST % "", cli=CLI % ""))
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.startswith("UPSTREAM: FIXED")


def test_respelled_emission_is_unreadable_not_fixed(tmp_path):
    respelled = "lines.push(`type = ${quote(entry.type)}`);"
    r = run(make(tmp_path, dist=DIST % respelled, cli=CLI % ""))
    assert r.returncode == 2, r.stdout + r.stderr
    assert r.stdout.startswith("UPSTREAM: UNREADABLE")
    assert "exact pattern does not match" in r.stdout


def test_missing_file_is_unreadable_not_fixed(tmp_path):
    r = run(make(tmp_path, dist=DIST % "", cli=None))
    assert r.returncode == 2, r.stdout + r.stderr
    assert "cli.cjs unreadable" in r.stdout


def test_file_without_the_renderer_is_unreadable_not_fixed(tmp_path):
    # A moved or renamed renderer has no emission either; that is not a fix.
    r = run(make(tmp_path, dist="export const x = 1;\n", cli=CLI % ""))
    assert r.returncode == 2, r.stdout + r.stderr
    assert "no longer contains renderCodexServerBlock" in r.stdout


def test_empty_file_is_unreadable_not_fixed(tmp_path):
    r = run(make(tmp_path, dist="", cli=CLI % ""))
    assert r.returncode == 2, r.stdout + r.stderr
    assert "mcp-registry.js is empty" in r.stdout
